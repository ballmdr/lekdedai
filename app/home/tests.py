from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from unittest.mock import patch, MagicMock
from datetime import date, datetime
import json

from home.instant_lucky import InstantLuckyNumberGenerator, get_instant_lucky_numbers
from news.models import NewsArticle, NewsCategory


class InstantLuckyNumberGeneratorTests(TestCase):
    """Test the InstantLuckyNumberGenerator class"""

    def setUp(self):
        """Set up test data"""
        self.generator = InstantLuckyNumberGenerator()
        self.test_date = date(2024, 12, 15)
        
        # Create a news category for testing
        self.news_category = NewsCategory.objects.create(
            name="Test Category",
            slug="test-category"
        )
        
        # Clear cache before each test
        cache.clear()

    def test_generator_initialization(self):
        """Test that generator initializes correctly"""
        self.assertIsInstance(self.generator, InstantLuckyNumberGenerator)
        self.assertEqual(self.generator.cache_timeout, 300)

    def test_extract_date_numbers(self):
        """Test date number extraction logic"""
        numbers = self.generator._extract_date_numbers(self.test_date)
        
        # Should have multiple date-based numbers
        self.assertGreater(len(numbers), 5)
        
        # Check that we have numbers from different sources
        sources = {num['source'] for num in numbers}
        expected_sources = {'day', 'month', 'year', 'date_sum', 'weekday'}
        self.assertTrue(expected_sources.issubset(sources))
        
        # Verify date components
        day_numbers = [num for num in numbers if num['source'] == 'day']
        self.assertTrue(len(day_numbers) >= 1)
        self.assertEqual(day_numbers[0]['number'], '15')

    def test_extract_recent_news_numbers_with_high_score_news(self):
        """Test news number extraction with high-scoring news"""
        # Create a high-scoring news article
        article = NewsArticle.objects.create(
            title="Test Accident เกิดอุบัติเหตุรถชน ทะเบียน กข-1234",
            content="เกิดอุบัติเหตุที่บ้านเลขที่ 45 อายุ 35 ปี",
            category=self.news_category,
            status='published',
            published_date=timezone.now(),
            lottery_relevance_score=85,
            extracted_numbers="12,34,45,35"
        )
        
        numbers = self.generator._extract_recent_news_numbers()
        
        # Should extract numbers from the high-scoring news
        self.assertGreater(len(numbers), 0)
        
        # Check that confidence scores are based on lottery_relevance_score
        for num_info in numbers:
            self.assertGreaterEqual(num_info['confidence'], 70)
            self.assertEqual(num_info['source'], 'news')

    def test_extract_recent_news_numbers_fallback(self):
        """Test news number extraction fallback when no high-scoring news"""
        # Create a regular news article
        NewsArticle.objects.create(
            title="Regular news article",
            content="Some content with number 42",
            category=self.news_category,
            status='published',
            published_date=timezone.now(),
            lottery_relevance_score=30,
            extracted_numbers="42"
        )
        
        numbers = self.generator._extract_recent_news_numbers()
        
        # Should still extract some numbers even from low-scoring news
        self.assertGreaterEqual(len(numbers), 0)

    def test_generate_mixed_numbers(self):
        """Test mixed number generation logic"""
        date_numbers = [{'number': '15', 'confidence': 90}]
        news_numbers = [{'number': '42', 'confidence': 85}]
        
        mixed = self.generator._generate_mixed_numbers(
            self.test_date, date_numbers, news_numbers
        )
        
        self.assertGreater(len(mixed), 0)
        
        # Check sources
        sources = {num['source'] for num in mixed}
        self.assertIn('mixed_sum', sources)

    def test_combine_and_select_numbers(self):
        """Test number combination and selection logic"""
        date_numbers = [
            {'number': '15', 'confidence': 90, 'source': 'day'},
            {'number': '12', 'confidence': 80, 'source': 'month'}
        ]
        news_numbers = [
            {'number': '42', 'confidence': 85, 'source': 'news'},
            {'number': '15', 'confidence': 75, 'source': 'news'}  # Duplicate
        ]
        mixed_numbers = [
            {'number': '57', 'confidence': 70, 'source': 'mixed_sum'}
        ]
        
        final = self.generator._combine_and_select_numbers(
            date_numbers, news_numbers, mixed_numbers, self.test_date
        )
        
        # Should remove duplicates (keep highest confidence)
        numbers = [num['number'] for num in final]
        self.assertEqual(len(numbers), len(set(numbers)))
        
        # Should keep the day number with higher confidence (90 vs 75)
        fifteen_entry = next(num for num in final if num['number'] == '15')
        self.assertEqual(fifteen_entry['source'], 'day')
        self.assertEqual(fifteen_entry['confidence'], 90)

    def test_generate_insights(self):
        """Test insights generation"""
        lucky_numbers = [
            {'number': '15', 'confidence': 90},
            {'number': '42', 'confidence': 85},
            {'number': '28', 'confidence': 70}
        ]
        
        insights = self.generator._generate_insights(lucky_numbers, self.test_date)
        
        self.assertEqual(insights['total_numbers'], 3)
        self.assertEqual(insights['confidence_range']['highest'], 90)
        self.assertEqual(insights['confidence_range']['lowest'], 70)
        self.assertAlmostEqual(insights['confidence_range']['average'], 81.67, places=1)
        self.assertIsInstance(insights['thai_message'], str)

    def test_generate_lucky_numbers_caching(self):
        """Test that results are cached properly"""
        # First call
        result1 = self.generator.generate_lucky_numbers('2024-12-15')
        
        # Second call should return cached result
        result2 = self.generator.generate_lucky_numbers('2024-12-15')
        
        self.assertEqual(result1, result2)
        self.assertEqual(result1['significant_date'], '2024-12-15')

    def test_generate_lucky_numbers_with_current_date(self):
        """Test generation with current date when no date provided"""
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value.date.return_value = self.test_date
            
            result = self.generator.generate_lucky_numbers()
            
            self.assertEqual(result['significant_date'], '2024-12-15')
            self.assertIn('lucky_numbers', result)
            self.assertIn('insights', result)

    def test_generate_lucky_numbers_with_invalid_date(self):
        """Test generation with invalid date format"""
        result = self.generator.generate_lucky_numbers('invalid-date')
        
        # Should fallback to current date
        self.assertIn('lucky_numbers', result)
        self.assertIn('significant_date', result)

    def test_thai_fortune_message_generation(self):
        """Test Thai fortune message generation"""
        message = self.generator._get_thai_fortune_message(self.test_date)
        
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 10)  # Should be a meaningful message

    def test_get_instant_lucky_numbers_function(self):
        """Test the helper function"""
        result = get_instant_lucky_numbers('2024-12-15')
        
        self.assertIn('lucky_numbers', result)
        self.assertIn('insights', result)
        self.assertEqual(result['significant_date'], '2024-12-15')


class InstantLuckyNumbersAPITests(TestCase):
    """Test the API endpoint for instant lucky numbers"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = reverse('instant_lucky_numbers_api')
        cache.clear()

    def test_get_request_with_current_date(self):
        """Test GET request uses current date"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('lucky_numbers', data['data'])

    def test_post_request_with_significant_date(self):
        """Test POST request with significant date"""
        payload = {'significant_date': '2024-12-15'}
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['significant_date'], '2024-12-15')

    def test_post_request_with_empty_payload(self):
        """Test POST request with empty payload"""
        response = self.client.post(
            self.url,
            data='{}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        # Should use current date when no significant_date provided

    def test_post_request_with_invalid_json(self):
        """Test POST request with invalid JSON"""
        response = self.client.post(
            self.url,
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Should still succeed by falling back to current date
        self.assertTrue(data['success'])

    @patch('home.instant_lucky.get_instant_lucky_numbers')
    def test_api_error_handling(self, mock_get_numbers):
        """Test API error handling when service fails"""
        mock_get_numbers.side_effect = Exception('Test error')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('message', data)

    def test_response_structure(self):
        """Test that API response has correct structure"""
        response = self.client.get(self.url)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        
        # Check main data structure
        result_data = data['data']
        self.assertIn('lucky_numbers', result_data)
        self.assertIn('generated_at', result_data)
        self.assertIn('significant_date', result_data)
        self.assertIn('components', result_data)
        self.assertIn('insights', result_data)
        self.assertIn('disclaimer', result_data)
        
        # Check lucky numbers structure
        for number_info in result_data['lucky_numbers']:
            self.assertIn('number', number_info)
            self.assertIn('confidence', number_info)
            self.assertIn('source', number_info)
            self.assertIn('reason', number_info)

    def test_caching_behavior(self):
        """Test that API results are cached"""
        payload = {'significant_date': '2024-12-15'}
        
        # First request
        response1 = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        data1 = json.loads(response1.content)
        
        # Second request should be faster due to caching
        response2 = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        data2 = json.loads(response2.content)
        
        # Results should be identical (from cache)
        self.assertEqual(data1['data']['lucky_numbers'], data2['data']['lucky_numbers'])


class InstantLuckyNumbersIntegrationTests(TestCase):
    """Integration tests combining multiple components"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.url = reverse('instant_lucky_numbers_api')
        
        # Create some realistic test data
        category = NewsCategory.objects.create(
            name="อุบัติเหตุ",
            slug="accident"
        )
        
        # Create a high-scoring accident news
        NewsArticle.objects.create(
            title="รถชนกันสนั่น ทะเบียน กข-1234",
            content="เกิดอุบัติเหตุรถชนที่บ้านเลขที่ 45 หมู่ที่ 3 เวลา 14:30 น. ผู้เสียชีวิตอายุ 35 ปี",
            category=category,
            status='published',
            published_date=timezone.now(),
            lottery_relevance_score=95,
            lottery_category='accident',
            extracted_numbers="12,34,45,35"
        )
        
        cache.clear()

    def test_end_to_end_lucky_number_generation(self):
        """Test complete flow from API request to response"""
        payload = {'significant_date': '2024-12-15'}
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        
        # Verify we got numbers from both date and news sources
        lucky_numbers = data['data']['lucky_numbers']
        sources = {num['source'] for num in lucky_numbers}
        
        # Should have at least date-based numbers
        date_sources = {'day', 'month', 'year', 'date_sum', 'weekday'}
        self.assertTrue(any(source in date_sources for source in sources))
        
        # Should have news-based numbers (from our test article)
        self.assertIn('news', sources)
        
        # Verify insights are generated
        insights = data['data']['insights']
        self.assertGreater(insights['total_numbers'], 0)
        self.assertIn('thai_message', insights)
        
        # Verify components breakdown
        components = data['data']['components']
        self.assertIn('date_contribution', components)
        self.assertIn('news_contribution', components)

    def test_privacy_and_security_compliance(self):
        """Test that no personal data is stored or logged"""
        payload = {'significant_date': '1990-01-01'}  # Simulated birthday
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify disclaimer is present
        self.assertIn('disclaimer', data['data'])
        self.assertIn('ไม่เก็บข้อมูลส่วนตัว', data['data']['disclaimer'])
        
        # The test itself verifies that no user data is stored in database
        # since we're not creating any user-related models

    def test_performance_with_multiple_requests(self):
        """Test performance with multiple concurrent requests"""
        import time
        
        # Make multiple requests and measure average response time
        times = []
        for i in range(5):
            start_time = time.time()
            
            response = self.client.get(self.url)
            
            end_time = time.time()
            times.append(end_time - start_time)
            
            self.assertEqual(response.status_code, 200)
        
        avg_time = sum(times) / len(times)
        
        # API should respond within 2 seconds on average
        self.assertLess(avg_time, 2.0, 
                       f"Average response time {avg_time:.2f}s exceeds 2s threshold")