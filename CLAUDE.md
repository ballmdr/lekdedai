# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LekdeDai is a Thai Django-based AI lottery prediction system that combines machine learning with traditional Thai lottery culture. The system includes dream interpretation, news analysis, lottery statistics, and AI-powered number prediction.

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python app/manage.py migrate

# Create superuser
python app/manage.py createsuperuser

# Run development server
cd app && python manage.py runserver

# Run tests
cd app && python manage.py test
```

### Docker Development
```bash
# Start services
docker-compose up -d

# Setup fresh database
docker-compose exec web ./setup_new_db.sh

# Access web container
docker-compose exec web bash

# View logs
docker-compose logs -f web
```

### Management Commands
The project includes numerous management commands for data operations:

```bash
# Lottery data operations
python manage.py add_calculate_stats
python manage.py sync_lotto_data
python manage.py clear_and_fetch_lotto

# News and content management
python manage.py add_news_data
python manage.py scrape_thairath
python manage.py scrape_rss_feeds
python manage.py analyze_existing_articles
python manage.py score_existing_news

# AI engine operations
python manage.py collect_prediction_data
python manage.py generate_ai_prediction
python manage.py setup_ai_data_sources

# Dream analysis
python manage.py add_dream_data
python manage.py train_dream_model

# Daily operations
python manage.py update_daily_numbers
```

## Architecture

### Core Django Apps

- **ai_engine**: ML prediction system with three specialized AI models (Journalist, Interpreter, Statistician) that work together via an ensemble approach
- **dreams**: Dream interpretation system with keyword mapping to lottery numbers
- **news**: News scraping and analysis with lottery relevance scoring
- **lotto_stats**: Historical lottery data analysis and statistics
- **home**: Main dashboard and daily number display
- **lottery_checker**: Lottery result checking and validation
- **lucky_spots**: Location-based lucky number suggestions

### Database Architecture

The system uses PostgreSQL with complex relationships between:
- AI prediction sessions with ensemble results
- News articles with extracted numbers and relevance scoring  
- Dream interpretations with symbol-to-number mappings
- Historical lottery data for statistical analysis

### AI System Architecture

The AI engine uses a three-tier approach:
1. **Specialist Models**: Journalist AI (news analysis), Interpreter AI (dreams/astrology), Statistician AI (historical data)
2. **Ensemble Prediction**: Combines results from all specialist models with confidence weighting
3. **Session Management**: Tracks prediction sessions with data collection periods and accuracy tracking

## Key Configuration

- **Language**: Thai (th) with Asia/Bangkok timezone
- **Database**: PostgreSQL via DATABASE_URL environment variable
- **Static Files**: Whitenoise middleware for production
- **Media Files**: Uploaded to app/media/
- **Dependencies**: Includes ML libraries (scikit-learn, pandas, numpy), Thai NLP (pythainlp), web scraping (beautifulsoup4), and caching (redis)

## Data Flow Patterns

### News Processing Pipeline
1. Scrape news from multiple sources (Thairath, RSS feeds)
2. Analyze content for lottery relevance using custom scoring
3. Extract potential numbers from headlines/content
4. Store with confidence scores and categorization

### AI Prediction Flow
1. Create prediction session for specific draw date
2. Collect data from all sources within date range
3. Run specialist AI models in parallel
4. Combine results via ensemble methodology
5. Generate final predictions with confidence scores
6. Track accuracy against actual lottery results

### Dream Analysis Process
1. User submits dream text
2. Extract symbols and keywords using Thai NLP
3. Map symbols to traditional lottery numbers via DreamKeyword model
4. Generate number predictions with interpretation

## Development Guidelines

### Model Patterns
- Use JSONField for complex prediction data and reasoning
- Include confidence scores for all predictions
- Track data sources and processing timestamps
- Implement soft deletes where appropriate (SET_NULL foreign keys)

### Management Command Structure
- Collect data operations for fetching external content
- Analysis operations for ML processing
- Setup operations for initial data seeding
- Daily operations for automated tasks

### URL Patterns
- Thai language support in slugs using custom validators
- Consistent app-based routing (dreams/, news/, ai/, etc.)
- SEO-friendly URLs with proper slug generation

## External Dependencies

- **PostgreSQL**: Primary database
- **Redis**: Caching and session storage  
- **Docker**: Development and production deployment
- **Thai NLP libraries**: pythainlp for text processing
- **ML Stack**: scikit-learn, pandas, numpy for predictions
- **Web Scraping**: beautifulsoup4, requests for news collection

## Production Deployment

```bash
# Collect static files
python manage.py collectstatic

# Run with Gunicorn
gunicorn lekdedai.wsgi:application

# Or via Docker
docker-compose -f docker-compose.prod.yml up -d
```

The system is designed for Thai lottery culture with deep integration of traditional beliefs (dreams, symbols) and modern AI prediction techniques.