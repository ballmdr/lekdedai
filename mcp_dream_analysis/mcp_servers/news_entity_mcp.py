"""
MCP Server สำหรับ NewsEntity_Model
Numerical Entity Recognition Service
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import os
import sys

# Add models path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.news_entity_model import NewsEntityModel

@dataclass
class MCPRequest:
    method: str
    params: Dict[str, Any]
    id: Optional[str] = None

@dataclass 
class MCPResponse:
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class NewsEntityMCPServer:
    """MCP Server สำหรับ News Entity Extraction"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = NewsEntityModel(model_path)
        self.logger = self._setup_logging()
        self.is_initialized = False
        
        # Server capabilities
        self.server_info = {
            'name': 'news-entity-mcp-server',
            'version': '1.0.0',
            'description': 'Thai News Numerical Entity Recognition MCP Server',
            'model_type': 'NewsEntity_Model',
            'capabilities': {
                'entity_extraction': True,
                'pattern_matching': True,
                'context_awareness': True,
                'ml_classification': True,
                'training': True
            },
            'supported_entities': [
                'license_plate', 'age', 'house_number', 'quantity',
                'date', 'time', 'lottery_number', 'phone_number', 'id_number'
            ],
            'supported_methods': [
                'extract_entities',
                'train_model',
                'get_model_info',
                'health_check',
                'batch_extract'
            ]
        }
    
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('NewsEntityMCP')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    async def initialize(self) -> bool:
        """Initialize the MCP server"""
        try:
            self.logger.info("🔍 เริ่มต้น News Entity MCP Server...")
            
            # Try to load existing model
            if self.model.load_model():
                self.logger.info("✅ โหลด NewsEntity_Model สำเร็จ")
            else:
                self.logger.info("ℹ️  ยังไม่พบโมเดล จะใช้ Pattern-based extraction")
            
            self.is_initialized = True
            self.logger.info("✅ News Entity MCP Server พร้อมใช้งาน")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ไม่สามารถเริ่มต้นเซิร์ฟเวอร์: {str(e)}")
            return False

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP requests"""
        try:
            method = request.method
            params = request.params
            
            self.logger.info(f"🔍 รับคำขอ: {method}")
            
            # Route to appropriate handler
            if method == 'extract_entities':
                result = await self._handle_extract_entities(params)
            elif method == 'batch_extract':
                result = await self._handle_batch_extract(params)
            elif method == 'train_model':
                result = await self._handle_train_model(params)
            elif method == 'get_model_info':
                result = self.model.get_model_info()
            elif method == 'health_check':
                result = {
                    'status': 'healthy',
                    'model_loaded': self.model.is_trained,
                    'timestamp': datetime.now().isoformat(),
                    'server_info': self.server_info
                }
            else:
                return MCPResponse(
                    error={'code': -32601, 'message': f'Method not found: {method}'},
                    id=request.id
                )
            
            return MCPResponse(result=result, id=request.id)
            
        except Exception as e:
            self.logger.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            return MCPResponse(
                error={'code': -32603, 'message': f'Internal error: {str(e)}'},
                id=request.id
            )

    async def _handle_extract_entities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities from news content"""
        news_content = params.get('news_content', '').strip()
        entity_types = params.get('entity_types', self.model.entity_types)
        
        if not news_content:
            raise ValueError('news_content is required')
        
        start_time = datetime.now()
        
        try:
            # Extract entities
            entities = self.model.predict(news_content)
            
            # Filter by requested entity types
            filtered_entities = {
                entity_type: entities.get(entity_type, [])
                for entity_type in entity_types
                if entity_type in self.model.entity_types
            }
            
            # Remove empty entities
            non_empty_entities = {
                k: v for k, v in filtered_entities.items() if v
            }
            
            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                'success': True,
                'news_content_length': len(news_content),
                'entities': filtered_entities,
                'found_entities': non_empty_entities,
                'total_found': sum(len(v) for v in non_empty_entities.values()),
                'method': 'ml_enhanced' if self.model.is_trained else 'pattern_based',
                'latency_ms': round(latency_ms, 2),
                'timestamp': datetime.now().isoformat(),
                'model_info': {
                    'is_trained': self.model.is_trained,
                    'metrics': self.model.training_metrics
                }
            }
            
            self.logger.info(f"✅ สกัด Entity สำเร็จ - พบ {result['total_found']} entities - {latency_ms:.1f}ms")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ สกัด Entity ไม่สำเร็จ: {str(e)}")
            raise

    async def _handle_batch_extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Batch entity extraction"""
        news_articles = params.get('news_articles', [])
        
        if not news_articles:
            raise ValueError('news_articles list is required')
        
        results = []
        total_start = datetime.now()
        total_entities_found = 0
        
        for i, article_data in enumerate(news_articles):
            try:
                news_content = article_data.get('content', '').strip()
                entity_types = article_data.get('entity_types', self.model.entity_types)
                
                if not news_content:
                    continue
                
                # Extract entities from each article
                extraction = await self._handle_extract_entities({
                    'news_content': news_content,
                    'entity_types': entity_types
                })
                
                results.append({
                    'index': i,
                    'article_id': article_data.get('id', f'article_{i}'),
                    'content_length': len(news_content),
                    'result': extraction,
                    'success': True
                })
                
                total_entities_found += extraction.get('total_found', 0)
                
            except Exception as e:
                results.append({
                    'index': i,
                    'article_id': article_data.get('id', f'article_{i}'),
                    'error': str(e),
                    'success': False
                })
        
        total_latency = (datetime.now() - total_start).total_seconds() * 1000
        
        return {
            'total_processed': len(results),
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'total_entities_found': total_entities_found,
            'total_latency_ms': round(total_latency, 2),
            'avg_latency_per_article': round(total_latency / max(len(results), 1), 2),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

    async def _handle_train_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Train the model"""
        training_data = params.get('training_data', [])
        test_size = params.get('test_size', 0.2)
        save_model = params.get('save_model', True)
        
        if not training_data:
            raise ValueError('training_data is required')
        
        self.logger.info(f"🎯 เริ่มฝึกสอน NewsEntity_Model ด้วย {len(training_data)} samples")
        
        # Train the model
        metrics = self.model.train(training_data, test_size)
        
        # Save model if requested
        if save_model:
            self.model.save_model()
        
        result = {
            'success': True,
            'training_samples': len(training_data),
            'test_size': test_size,
            'metrics': metrics,
            'model_saved': save_model,
            'entity_types_trained': list(metrics.keys()),
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info("✅ การฝึกสอน NewsEntity_Model เสร็จสิ้น")
        return result


# API Wrapper for Django Integration
class NewsEntityAPI:
    """API Wrapper for Django integration"""
    
    def __init__(self):
        self.server = NewsEntityMCPServer()
        self._initialized = False
    
    async def _ensure_initialized(self):
        if not self._initialized:
            await self.server.initialize()
            self._initialized = True
    
    async def extract_entities(self, news_content: str, entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Extract entities from news content"""
        await self._ensure_initialized()
        
        params = {'news_content': news_content}
        if entity_types:
            params['entity_types'] = entity_types
        
        request = MCPRequest(
            method='extract_entities',
            params=params
        )
        
        response = await self.server.handle_request(request)
        
        if response.error:
            raise Exception(response.error['message'])
        
        return response.result
    
    async def train_model(self, training_data: List[Dict]) -> Dict[str, Any]:
        """Train the model"""
        await self._ensure_initialized()
        
        request = MCPRequest(
            method='train_model',
            params={'training_data': training_data}
        )
        
        response = await self.server.handle_request(request)
        
        if response.error:
            raise Exception(response.error['message'])
        
        return response.result


# Global API instance
news_entity_api = NewsEntityAPI()

# CLI for testing
if __name__ == "__main__":
    async def test_server():
        server = NewsEntityMCPServer()
        await server.initialize()
        
        # Test entity extraction
        test_content = """
        เมื่อวานนี้ คุณสมชาย อายุ 45 ปี ขับรถทะเบียน กข 1234 
        ไปที่บ้านเลขที่ 123/45 หมู่ 7 ตำบลบางพลี 
        เพื่อซื้อลอตเตอรี่เลข 123456 ในราคา 2,500 บาท
        โทรติดต่อได้ที่ 081-234-5678
        """
        
        test_request = MCPRequest(
            method='extract_entities',
            params={'news_content': test_content},
            id='test-1'
        )
        
        response = await server.handle_request(test_request)
        print("🧪 ผลการทดสอบ News Entity:")
        print(json.dumps(response.result, ensure_ascii=False, indent=2))
    
    asyncio.run(test_server())