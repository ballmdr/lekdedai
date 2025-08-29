"""
MCP Server สำหรับ DreamSymbol_Model
Symbolic Interpretation Service
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

from models.dream_symbol_model import DreamSymbolModel

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

class DreamSymbolMCPServer:
    """MCP Server สำหรับ Symbolic Dream Interpretation"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = DreamSymbolModel(model_path)
        self.logger = self._setup_logging()
        self.is_initialized = False
        
        # Server capabilities
        self.server_info = {
            'name': 'dream-symbol-mcp-server',
            'version': '1.0.0',
            'description': 'Thai Dream Symbolic Interpretation MCP Server',
            'model_type': 'DreamSymbol_Model',
            'capabilities': {
                'symbolic_interpretation': True,
                'confidence_scoring': True,
                'thai_tokenization': True,
                'multi_output_prediction': True,
                'training': True
            },
            'supported_methods': [
                'interpret_dream',
                'train_model',
                'get_model_info',
                'health_check',
                'batch_interpret'
            ]
        }
    
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('DreamSymbolMCP')
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
            self.logger.info("🔮 เริ่มต้น Dream Symbol MCP Server...")
            
            # Try to load existing model
            if self.model.load_model():
                self.logger.info("✅ โหลด DreamSymbol_Model สำเร็จ")
            else:
                self.logger.info("ℹ️  ยังไม่พบโมเดล จะใช้การวิเคราะห์พื้นฐาน")
            
            self.is_initialized = True
            self.logger.info("✅ Dream Symbol MCP Server พร้อมใช้งาน")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ไม่สามารถเริ่มต้นเซิร์ฟเวอร์: {str(e)}")
            return False

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP requests"""
        try:
            method = request.method
            params = request.params
            
            self.logger.info(f"🔮 รับคำขอ: {method}")
            
            # Route to appropriate handler
            if method == 'interpret_dream':
                result = await self._handle_interpret_dream(params)
            elif method == 'batch_interpret':
                result = await self._handle_batch_interpret(params)
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

    async def _handle_interpret_dream(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret dream symbols"""
        dream_text = params.get('dream_text', '').strip()
        top_k = params.get('top_k', 6)
        
        if not dream_text:
            raise ValueError('dream_text is required')
        
        start_time = datetime.now()
        
        try:
            # Use ML model if available
            if self.model.is_trained:
                predictions = self.model.predict(dream_text, top_k)
                method_used = 'ml_prediction'
            else:
                # Fallback to symbolic mapping
                predictions = self._fallback_interpretation(dream_text, top_k)
                method_used = 'symbolic_mapping'
            
            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                'success': True,
                'dream_text': dream_text,
                'predictions': predictions,
                'method': method_used,
                'latency_ms': round(latency_ms, 2),
                'timestamp': datetime.now().isoformat(),
                'model_info': {
                    'is_trained': self.model.is_trained,
                    'metrics': self.model.training_metrics
                }
            }
            
            # Add expert interpretation if available from expert interpreter
            if hasattr(self.model, 'expert_interpreter'):
                try:
                    expert_result = self.model.expert_interpreter.interpret_dream(dream_text)
                    if expert_result:
                        result['expert_interpretation'] = expert_result.get('interpretation', '')
                        result['main_symbols'] = expert_result.get('main_symbols', [])
                        result['context_analysis'] = expert_result.get('context_analysis', {})
                except Exception:
                    pass  # Don't fail if expert interpretation fails
            
            self.logger.info(f"✅ ตีความฝันสำเร็จ - {len(predictions)} เลข - {latency_ms:.1f}ms")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ ตีความฝันไม่สำเร็จ: {str(e)}")
            raise

    def _fallback_interpretation(self, dream_text: str, top_k: int) -> List[Dict]:
        """Fallback interpretation using symbolic mappings"""
        all_symbols = {}
        all_symbols.update(self.model.symbol_mappings['animal_symbols'])
        all_symbols.update(self.model.symbol_mappings['people_symbols'])
        all_symbols.update(self.model.symbol_mappings['object_symbols'])
        all_symbols.update(self.model.symbol_mappings['color_symbols'])
        
        found_symbols = []
        dream_lower = dream_text.lower()
        
        for symbol, data in all_symbols.items():
            if symbol in dream_lower:
                found_symbols.append((symbol, data))
        
        # Generate predictions
        predictions = []
        base_confidence = 0.7
        
        if found_symbols:
            # Use found symbols
            for i, (symbol, data) in enumerate(found_symbols[:top_k//2]):
                for j, combo in enumerate(data['combinations'][:2]):
                    if len(predictions) >= top_k:
                        break
                    
                    confidence = base_confidence * (0.9 ** (i + j))
                    predictions.append({
                        "number": combo,
                        "score": round(confidence, 3)
                    })
        
        # Fill remaining with default numbers
        default_numbers = ["12", "34", "56", "78", "90", "13", "24", "35"]
        for i, num in enumerate(default_numbers):
            if len(predictions) >= top_k:
                break
            if not any(p["number"] == num for p in predictions):
                predictions.append({
                    "number": num,
                    "score": round(0.4 * (0.9 ** i), 3)
                })
        
        return predictions[:top_k]

    async def _handle_batch_interpret(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Batch dream interpretation"""
        dreams = params.get('dreams', [])
        
        if not dreams:
            raise ValueError('dreams list is required')
        
        results = []
        total_start = datetime.now()
        
        for i, dream_data in enumerate(dreams):
            try:
                dream_text = dream_data.get('text', '').strip()
                top_k = dream_data.get('top_k', 6)
                
                if not dream_text:
                    continue
                
                # Interpret each dream
                interpretation = await self._handle_interpret_dream({
                    'dream_text': dream_text,
                    'top_k': top_k
                })
                
                results.append({
                    'index': i,
                    'dream_text': dream_text,
                    'result': interpretation,
                    'success': True
                })
                
            except Exception as e:
                results.append({
                    'index': i,
                    'dream_text': dream_data.get('text', ''),
                    'error': str(e),
                    'success': False
                })
        
        total_latency = (datetime.now() - total_start).total_seconds() * 1000
        
        return {
            'total_processed': len(results),
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'total_latency_ms': round(total_latency, 2),
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
        
        self.logger.info(f"🎯 เริ่มฝึกสอน DreamSymbol_Model ด้วย {len(training_data)} samples")
        
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
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info("✅ การฝึกสอน DreamSymbol_Model เสร็จสิ้น")
        return result


# API Wrapper for Django Integration
class DreamSymbolAPI:
    """API Wrapper for Django integration"""
    
    def __init__(self):
        self.server = DreamSymbolMCPServer()
        self._initialized = False
    
    async def _ensure_initialized(self):
        if not self._initialized:
            await self.server.initialize()
            self._initialized = True
    
    async def interpret_dream(self, dream_text: str, top_k: int = 6) -> Dict[str, Any]:
        """Interpret dream symbols"""
        await self._ensure_initialized()
        
        request = MCPRequest(
            method='interpret_dream',
            params={'dream_text': dream_text, 'top_k': top_k}
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
dream_symbol_api = DreamSymbolAPI()

# CLI for testing
if __name__ == "__main__":
    async def test_server():
        server = DreamSymbolMCPServer()
        await server.initialize()
        
        # Test dream interpretation
        test_request = MCPRequest(
            method='interpret_dream',
            params={'dream_text': 'ฝันเห็นพญานาคสีทองใหญ่มาหาฉัน'},
            id='test-1'
        )
        
        response = await server.handle_request(test_request)
        print("🧪 ผลการทดสอบ Dream Symbol:")
        print(json.dumps(response.result, ensure_ascii=False, indent=2))
    
    asyncio.run(test_server())