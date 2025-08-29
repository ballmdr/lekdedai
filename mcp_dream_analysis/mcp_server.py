"""
MCP Server สำหรับ Dream Analysis Service
Model Context Protocol Server for Dream Number Analysis
"""
import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime
import os
import sys

# Add the parent directory to sys.path to import Django models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dream_ml_model import DreamNumberMLModel

# MCP Protocol Implementation
@dataclass
class MCPRequest:
    """MCP Request structure"""
    method: str
    params: Dict[str, Any]
    id: Optional[str] = None

@dataclass 
class MCPResponse:
    """MCP Response structure"""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class DreamAnalysisMCPServer:
    """MCP Server สำหรับบริการวิเคราะห์ความฝัน"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = DreamNumberMLModel(model_path)
        self.logger = self._setup_logging()
        self.is_initialized = False
        
        # Server info
        self.server_info = {
            'name': 'dream-analysis-mcp-server',
            'version': '1.0.0',
            'description': 'Thai Dream Analysis and Number Prediction MCP Server',
            'capabilities': {
                'dream_analysis': True,
                'number_prediction': True,
                'batch_processing': True,
                'model_training': True
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """ตั้งค่า logging"""
        logger = logging.getLogger('DreamAnalysisMCP')
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
        """เริ่มต้นเซิร์ฟเวอร์"""
        try:
            self.logger.info("🚀 เริ่มต้น Dream Analysis MCP Server...")
            
            # Try to load existing model
            if self.model.load_model():
                self.logger.info("✅ โหลดโมเดลสำเร็จ")
            else:
                self.logger.info("ℹ️  ยังไม่พบโมเดล จะใช้การวิเคราะห์แบบดั้งเดิม")
            
            self.is_initialized = True
            self.logger.info("✅ Dream Analysis MCP Server พร้อมใช้งาน")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ไม่สามารถเริ่มต้นเซิร์ฟเวอร์: {str(e)}")
            return False

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """จัดการคำขอ MCP"""
        try:
            method = request.method
            params = request.params
            
            self.logger.info(f"📨 รับคำขอ: {method}")
            
            # Route to appropriate handler
            if method == 'analyze_dream':
                result = await self._handle_analyze_dream(params)
            elif method == 'predict_numbers':
                result = await self._handle_predict_numbers(params)
            elif method == 'batch_analyze':
                result = await self._handle_batch_analyze(params)
            elif method == 'train_model':
                result = await self._handle_train_model(params)
            elif method == 'get_server_info':
                result = self.server_info
            elif method == 'health_check':
                result = {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
            else:
                return MCPResponse(
                    error={'code': -32601, 'message': f'Method not found: {method}'},
                    id=request.id
                )
            
            return MCPResponse(result=result, id=request.id)
            
        except Exception as e:
            self.logger.error(f"❌ เกิดข้อผิดพลาดในการจัดการคำขอ: {str(e)}")
            return MCPResponse(
                error={'code': -32603, 'message': f'Internal error: {str(e)}'},
                id=request.id
            )

    async def _handle_analyze_dream(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """วิเคราะห์ความฝัน"""
        dream_text = params.get('dream_text', '').strip()
        
        if not dream_text:
            raise ValueError('dream_text is required')
        
        # Advanced analysis with ML + Traditional
        if self.model.is_trained:
            result = self.model.analyze_dream_advanced(dream_text)
        else:
            # Fallback to traditional only
            traditional_result = self.model._traditional_analysis(dream_text)
            result = {
                'success': True,
                'ml_prediction': None,
                'traditional_analysis': traditional_result,
                'combined_numbers': traditional_result['numbers'],
                'confidence': traditional_result['confidence'],
                'analysis_method': 'traditional'
            }
        
        # Add metadata
        result.update({
            'timestamp': datetime.now().isoformat(),
            'input_length': len(dream_text),
            'server_version': self.server_info['version']
        })
        
        self.logger.info(f"✅ วิเคราะห์ความฝันเสร็จสิ้น - ความมั่นใจ: {result['confidence']:.1f}%")
        return result

    async def _handle_predict_numbers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """ทำนายเลขจากความฝัน (ML เท่านั้น)"""
        dream_text = params.get('dream_text', '').strip()
        num_predictions = params.get('num_predictions', 6)
        
        if not dream_text:
            raise ValueError('dream_text is required')
        
        if not self.model.is_trained:
            raise ValueError('ML model is not trained. Use traditional analysis instead.')
        
        result = self.model.predict(dream_text, num_predictions)
        result.update({
            'timestamp': datetime.now().isoformat(),
            'method': 'ml_only'
        })
        
        return result

    async def _handle_batch_analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """วิเคราะห์ความฝันหลายๆ รายการ"""
        dreams = params.get('dreams', [])
        
        if not dreams:
            raise ValueError('dreams list is required')
        
        results = []
        for i, dream_data in enumerate(dreams):
            try:
                dream_text = dream_data.get('text', '').strip()
                if not dream_text:
                    continue
                
                # Analyze each dream
                analysis = await self._handle_analyze_dream({'dream_text': dream_text})
                results.append({
                    'index': i,
                    'dream_text': dream_text,
                    'analysis': analysis,
                    'success': True
                })
                
            except Exception as e:
                results.append({
                    'index': i,
                    'dream_text': dream_data.get('text', ''),
                    'error': str(e),
                    'success': False
                })
        
        return {
            'processed_count': len(results),
            'success_count': sum(1 for r in results if r['success']),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }

    async def _handle_train_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """ฝึกสอนโมเดล ML"""
        training_data = params.get('training_data', [])
        test_size = params.get('test_size', 0.2)
        save_model = params.get('save_model', True)
        
        if not training_data:
            raise ValueError('training_data is required')
        
        self.logger.info(f"🎯 เริ่มฝึกสอนโมเดลด้วยข้อมูล {len(training_data)} รายการ")
        
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
        
        self.logger.info("✅ การฝึกสอนโมเดลเสร็จสิ้น")
        return result

    async def start_server(self, host: str = 'localhost', port: int = 8765):
        """เริ่มต้น MCP Server (สำหรับใช้เป็น WebSocket หรือ HTTP)"""
        if not self.is_initialized:
            await self.initialize()
        
        self.logger.info(f"🌐 เริ่มต้น MCP Server ที่ {host}:{port}")
        
        # สามารถเพิ่ม WebSocket หรือ HTTP server ได้ตามต้องการ
        # ในที่นี้เป็นแค่ placeholder
        while True:
            await asyncio.sleep(1)

# ฟังก์ชันสำหรับใช้เป็น API โดยตรง
class DreamAnalysisAPI:
    """API Wrapper สำหรับใช้งานโดยตรงใน Django"""
    
    def __init__(self):
        self.server = DreamAnalysisMCPServer()
        self._initialized = False
    
    async def _ensure_initialized(self):
        """ตรวจสอบว่าได้เริ่มต้นแล้ว"""
        if not self._initialized:
            await self.server.initialize()
            self._initialized = True
    
    async def analyze_dream(self, dream_text: str) -> Dict[str, Any]:
        """วิเคราะห์ความฝัน (API แบบง่าย)"""
        await self._ensure_initialized()
        
        request = MCPRequest(
            method='analyze_dream',
            params={'dream_text': dream_text}
        )
        
        response = await self.server.handle_request(request)
        
        if response.error:
            raise Exception(response.error['message'])
        
        return response.result
    
    async def predict_numbers_only(self, dream_text: str, num_predictions: int = 6) -> Dict[str, Any]:
        """ทำนายเลขเท่านั้น (ML)"""
        await self._ensure_initialized()
        
        request = MCPRequest(
            method='predict_numbers',
            params={'dream_text': dream_text, 'num_predictions': num_predictions}
        )
        
        response = await self.server.handle_request(request)
        
        if response.error:
            raise Exception(response.error['message'])
        
        return response.result
    
    async def train_model_with_data(self, training_data: List[Dict]) -> Dict[str, Any]:
        """ฝึกสอนโมเดล"""
        await self._ensure_initialized()
        
        request = MCPRequest(
            method='train_model',
            params={'training_data': training_data}
        )
        
        response = await self.server.handle_request(request)
        
        if response.error:
            raise Exception(response.error['message'])
        
        return response.result

# Global instance สำหรับใช้ใน Django
dream_analysis_api = DreamAnalysisAPI()

# CLI สำหรับทดสอบ
if __name__ == "__main__":
    import asyncio
    
    async def test_server():
        server = DreamAnalysisMCPServer()
        await server.initialize()
        
        # Test analyze dream
        test_request = MCPRequest(
            method='analyze_dream',
            params={'dream_text': 'ฝันเห็นงูใหญ่สีเขียวกัดฉัน แล้วฉันก็วิ่งหนี'},
            id='test-1'
        )
        
        response = await server.handle_request(test_request)
        print("🧪 ผลการทดสอบ:")
        print(json.dumps(response.result, ensure_ascii=False, indent=2))
    
    asyncio.run(test_server())