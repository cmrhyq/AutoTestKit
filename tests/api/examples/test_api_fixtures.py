"""
API Fixtures 功能测试

测试 API fixtures 的核心功能
"""

import pytest
from unittest.mock import Mock, patch
from base.api.services.base_service import BaseService
from core.cache.data_cache import DataCache


@pytest.mark.api
class TestAPIFixtures:
    """API Fixtures 的功能测试"""
    
    def test_base_service_fixture(self, base_service):
        """测试 base_service fixture"""
        assert isinstance(base_service, BaseService)
        assert base_service.base_url is not None
        assert base_service.session is not None
        assert base_service.logger is not None
    
    def test_api_logger_fixture(self):
        """测试模块级 logger"""
        from base.api.fixtures import logger

        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
    
    def test_api_cache_fixture(self, api_cache):
        """测试 api_cache fixture"""
        assert isinstance(api_cache, DataCache)
        
        # 测试缓存功能
        api_cache.set('test_key', 'test_value')
        assert api_cache.get('test_key') == 'test_value'
        assert api_cache.has('test_key') is True
        
        # 清理
        api_cache.clear()
    
    def test_custom_service_fixture(self, custom_service):
        """测试 custom_service fixture"""
        # 创建自定义服务
        service1 = custom_service(base_url="https://api1.example.com")
        assert service1.base_url == "https://api1.example.com"
        
        service2 = custom_service(
            base_url="https://api2.example.com",
            auth_type='bearer',
            auth_credentials={'token': 'test_token'}
        )
        assert service2.base_url == "https://api2.example.com"
        assert 'Authorization' in service2.session.headers
    
    def test_api_test_context_fixture(self, api_test_context):
        """测试 api_test_context fixture"""
        assert 'logger' in api_test_context
        assert 'cache' in api_test_context
        assert 'attach_to_allure' in api_test_context
        
        # 测试日志记录器
        logger = api_test_context['logger']
        logger.info("Test log message")
        
        # 测试缓存
        cache = api_test_context['cache']
        cache.set('context_test', 'value')
        assert cache.get('context_test') == 'value'
        cache.clear()
    
    @patch('base.api.services.base_service.requests.Session.request')
    def test_attach_request_response_to_allure(
        self,
        mock_request,
        attach_request_response_to_allure
    ):
        """测试 attach_request_response_to_allure fixture"""
        # 创建模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 1, 'name': 'Test'}
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.url = "https://api.example.com/test"
        mock_response.text = '{"id": 1, "name": "Test"}'
        
        # 模拟请求对象
        mock_response.request = Mock()
        mock_response.request.method = 'GET'
        mock_response.request.url = "https://api.example.com/test"
        mock_response.request.headers = {'User-Agent': 'test'}
        mock_response.request.body = None
        
        # 测试附加功能（不会实际附加到 Allure，但应该不报错）
        attach_request_response_to_allure(mock_response, "Test Request")
    
    @patch('base.api.services.base_service.requests.Session.request')
    def test_base_service_with_cache_integration(self, mock_request, base_service, api_cache):
        """测试 BaseService 与缓存的集成"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'user_id': 12345, 'username': 'testuser'}
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.elapsed.total_seconds.return_value = 0.3
        mock_response.url = "https://api.example.com/user"
        mock_request.return_value = mock_response
        
        # 发送请求
        response = base_service.get("/user")
        
        # 提取并缓存数据
        user_id = base_service.extract_and_cache(response, 'user_id', 'user_id')
        assert user_id == 12345
        
        # 验证缓存
        cached_id = api_cache.get('user_id')
        assert cached_id == 12345
        
        # 清理
        api_cache.clear()
