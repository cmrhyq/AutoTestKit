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
    
