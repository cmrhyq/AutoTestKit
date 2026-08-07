"""
插件中心 统计插件安装数 接口测试

测试内容：统计插件安装数量接口
"""

from typing import Dict, Any

import allure
import pytest

from base.api.services.plugin_inner_service import PluginInnerService
from core.log import get_logger
from core.reporting.allure_helper import AllureHelper
from core.constants import Tenant

logger = get_logger(__name__)

@pytest.mark.api
@pytest.mark.plugin
@allure.epic("磐基API自动化测试")
@allure.feature("磐基插件中心InnerAPI接口")
@allure.story("Plugin Count 接口")
class TestPluginCount:

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def plugin_inner_service(self, test_env):
        """创建 Plugin Inner API 服务实例"""
        service = PluginInnerService(
            base_url=test_env.get("apiInnerBaseUrl"),
        )
        yield service
        service.close()

    @allure.title("统计插件安装数")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_plugin_install_count(self, plugin_inner_service, api_cache):
        with AllureHelper.api_test(plugin_inner_service):
            with AllureHelper.step("发送 GET 请求统计插件安装数"):
                response_json = plugin_inner_service.get_plugin_install_count()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "data" in response_json, "响应应包含 data 字段"
