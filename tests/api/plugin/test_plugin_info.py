"""
插件中心 OpenAPI 插件信息接口测试

测试内容：
- 查询指定插件的安装信息
- 获取当前环境插件数据
- 验证任务配置
- 验证feature
- 获取所有支持权限转让的插件
"""

from typing import Dict, Any

import allure
import pytest

from base.api.services.plugin_open_service import PluginOpenService
from core.reporting.allure_helper import AllureHelper
from core.constants import Tenant

@pytest.mark.api
@pytest.mark.plugin
@allure.epic("磐基API自动化测试")
@allure.feature("磐基插件中心OpenAPI接口")
@allure.story("Plugin Info 插件信息接口")
class TestPluginInfo:

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def plugin_open_service(self, service_factory):
        with service_factory(PluginOpenService, self.TENANT) as svc:
            yield svc

    @allure.title("查询指定插件的安装信息")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_plugin_install_info(self, plugin_open_service, api_env, api_cache):
        with AllureHelper.api_test(plugin_open_service):
            plugin_name = api_env.get("pluginName", "kubectl")

            with AllureHelper.step(f"发送 GET 请求查询插件 {plugin_name} 的安装信息"):
                response_json = plugin_open_service.get_plugin_install_info(plugin_name=plugin_name)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "code" in response_json, "响应应包含 code 字段"

    @allure.title("获取当前环境插件数据")
    @allure.description("查询当前环境的插件版本数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_current_env_list(self, plugin_open_service, api_cache):
        with AllureHelper.api_test(plugin_open_service):
            with AllureHelper.step("发送 GET 请求获取当前环境插件数据"):
                response_json = plugin_open_service.get_current_env_list()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "code" in response_json, "响应应包含 code 字段"

    @allure.title("验证任务配置")
    @allure.description("校验 Kubernetes 任务配置的格式合法性")
    @allure.severity(allure.severity_level.NORMAL)
    def test_verify_task_config(self, plugin_open_service, api_cache):
        with AllureHelper.api_test(plugin_open_service):
            with AllureHelper.step("发送 POST 请求验证任务配置"):
                response_json = plugin_open_service.verify_task_config()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "code" in response_json, "响应应包含 code 字段"

    @allure.title("验证feature")
    @allure.description("校验 Feature 配置的格式合法性")
    @allure.severity(allure.severity_level.NORMAL)
    def test_verify_task_feature(self, plugin_open_service, api_cache):
        with AllureHelper.api_test(plugin_open_service):
            with AllureHelper.step("发送 POST 请求验证feature"):
                response_json = plugin_open_service.verify_task_feature()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "code" in response_json, "响应应包含 code 字段"

    @allure.title("获取所有支持权限转让的插件")
    @allure.description("查询支持权限转让的插件列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_plugin_support_permission_transfer(self, plugin_open_service, api_cache):
        with AllureHelper.api_test(plugin_open_service):
            with AllureHelper.step("发送 GET 请求获取支持权限转让的插件"):
                response_json = plugin_open_service.get_plugin_support_permission_transfer()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert "code" in response_json, "响应应包含 code 字段"
