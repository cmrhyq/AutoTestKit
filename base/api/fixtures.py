"""
API 测试 Fixtures 模块

该模块提供 API 测试所需的 pytest fixtures，包括：
- BaseService 实例化 fixture
- 请求/响应日志记录 fixture
- 数据缓存集成
- API 测试环境设置
"""

import pytest
import allure
from typing import Optional, Dict

from base.api.services.base_service import BaseService
from core.config import env_manager
from core.log import get_logger
from core.cache.data_cache import DataCache
from core.config import Settings

logger = get_logger("API")


@pytest.fixture(scope="session")
def api_cache():
    """
    Session-level data cache fixture
    
    提供数据缓存实例用于存储和共享 API 测试数据
    
    Returns:
        DataCache: 数据缓存实例
    """
    cache = DataCache.get_instance()
    return cache


@pytest.fixture(scope="session")
def api_env():
    env = env_manager.get_config()
    return env


@pytest.fixture(scope="function")
def base_service():
    """
    Function-level BaseService fixture
    
    为每个测试函数创建一个新的 BaseService 实例，
    使用配置文件中的 API_BASE_URL 作为基础 URL

    Yields:
        BaseService: 配置好的 API 服务实例
    """
    logger.info(f"Creating BaseService with base_url: {Settings.API_BASE_URL}")
    
    service = BaseService(base_url=Settings.API_BASE_URL)
    
    yield service
    
    # 清理：关闭 session
    service.close()
    logger.info("BaseService closed")


@pytest.fixture(scope="function")
def authenticated_service(api_env):
    """
    Function-level authenticated BaseService fixture
    
    创建带有认证配置的 BaseService 实例
    根据环境变量自动选择认证方式（Bearer Token, Basic Auth, API Key）
    
    Args:
        api_env: 环境配置字典
        
    Yields:
        BaseService: 配置好认证的 API 服务实例
    """
    # 确定认证类型
    auth_type = None
    auth_credentials = None
    
    if api_env.get("bearer_token"):
        auth_type = 'bearer'
        auth_credentials = {'token': api_env.get("bearer_token")}
        logger.info("Using Bearer token authentication")
    elif api_env.get("basic_auth_username") and api_env.get("basic_auth_password"):
        auth_type = 'basic'
        auth_credentials = {
            'username': api_env.get("basic_auth_username"),
            'password': api_env.get("basic_auth_password")
        }
        logger.info("Using Basic authentication")
    elif api_env.get("api_key"):
        auth_type = 'api_key'
        auth_credentials = {
            'api_key': api_env.get("api_key"),
            'header_name': api_env.get("api_key_header")
        }
        logger.info("Using API Key authentication")
    else:
        logger.warning("No authentication credentials configured")
    
    service = BaseService(
        base_url=Settings.API_BASE_URL,
        auth_type=auth_type,
        auth_credentials=auth_credentials
    )
    
    yield service
    
    # 清理：关闭 session
    service.close()
    logger.info("Authenticated BaseService closed")


@pytest.fixture(scope="function")
def custom_service():
    """
    Function-level custom BaseService factory fixture
    
    提供一个工厂函数，允许测试用例创建自定义配置的 BaseService 实例
    
    Yields:
        function: 工厂函数，接受 base_url, auth_type, auth_credentials 参数
    """
    created_services = []
    
    def _create_service(
        base_url: str = None,
        auth_type: Optional[str] = None,
        auth_credentials: Optional[Dict[str, str]] = None
    ) -> BaseService:
        service = BaseService(
            base_url=base_url or Settings.API_BASE_URL,
            auth_type=auth_type,
            auth_credentials=auth_credentials
        )
        created_services.append(service)
        return service
    
    yield _create_service
    
    # 清理：关闭所有创建的 service
    for service in created_services:
        service.close()
    logger.info(f"Closed {len(created_services)} custom service(s)")


@pytest.fixture(scope="function", autouse=True)
def log_api_test_info(request):
    """
    Function-level auto-use fixture for logging API test information
    
    自动记录每个 API 测试的开始和结束信息
    """
    test_name = request.node.name
    test_location = request.node.nodeid

    logger.info(f"API Test Started: {test_name}")
    logger.info(f"Test Location: {test_location}")
    
    with allure.step(f"Starting API test: {test_name}"):
        pass
    
    yield

    logger.info(f"API Test Finished: {test_name}")
    
    with allure.step(f"Finished API test: {test_name}"):
        pass


@pytest.fixture(scope="function")
def attach_request_response_to_allure():
    """
    Function-level fixture for attaching request/response to Allure
    """
    def _attach(response, request_name: str = "API Request"):
        # 附加请求信息
        request_info = f"""
Method: {response.request.method}
URL: {response.request.url}
Headers: {dict(response.request.headers)}
Body: {response.request.body or 'None'}
"""
        allure.attach(
            request_info,
            name=f"{request_name} - Request",
            attachment_type=allure.attachment_type.TEXT
        )
        
        # 附加响应信息
        response_info = f"""
Status Code: {response.status_code}
Headers: {dict(response.headers)}
Response Time: {response.elapsed.total_seconds()}s
"""
        allure.attach(
            response_info,
            name=f"{request_name} - Response Info",
            attachment_type=allure.attachment_type.TEXT
        )
        
        # 附加响应体
        try:
            response_body = response.json()
            allure.attach(
                str(response_body),
                name=f"{request_name} - Response Body",
                attachment_type=allure.attachment_type.JSON
            )
        except Exception:
            allure.attach(
                response.text,
                name=f"{request_name} - Response Body",
                attachment_type=allure.attachment_type.TEXT
            )
        
        logger.info(f"Attached request/response to Allure: {request_name}")
    
    return _attach


@pytest.fixture(scope="function")
def api_test_context(api_cache, attach_request_response_to_allure):
    """
    Function-level comprehensive API test context fixture
    """
    context = {
        'logger': logger,
        'cache': api_cache,
        'attach_to_allure': attach_request_response_to_allure
    }
    
    logger.info("API test context created")
    
    return context


@pytest.fixture(scope="session", autouse=True)
def setup_api_test_environment():
    """
    Session-level auto-use fixture for API test environment setup
    """
    logger.info("Setting up API test environment")
    
    # 验证配置
    is_valid, errors = Settings.validate()
    if not is_valid:
        logger.warning("Configuration validation errors:")
        for error in errors:
            logger.warning(f"  - {error}")
    
    # 记录配置摘要
    config_summary = Settings.get_config_summary()
    logger.info(f"Environment: {config_summary.get('environment')}")
    
    yield
    
    # 清理
    logger.info("Cleaning up API test environment")
    
    # 清理数据缓存
    cache = DataCache.get_instance()
    cache_size = cache.size()
    cache.clear()
    logger.info(f"Cleared {cache_size} items from data cache")
    
    # 附加日志到 Allure
    from core.log.logger import TestLogger
    TestLogger.attach_log_to_allure()
    logger.info("Attached logs to Allure report")
