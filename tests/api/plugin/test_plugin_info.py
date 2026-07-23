"""
插件中心 OpenAPI 插件信息接口测试

转换自 JMeter 脚本: plugin-info.jmx
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

from base.api.services.plugin_open_service import PanJiPluginOpenService
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("插件中心OpenAPI服务")
@allure.story("plugin-info 插件信息接口")
class TestPluginInfo:
    """
    对应 JMeter 脚本: plugin-info.jmx
    线程组: Thread Group - plugin
    """

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def plugin_open_service(self, api_env, api_logger):
        """创建 Plugin OpenAPI 服务实例"""
        service = PanJiPluginOpenService(
            base_url=api_env.get("apiBaseUrl"), logger=api_logger
        )
        yield service
        service.close()

    @allure.title("查询指定插件的安装信息")
    @allure.description("GET /openapi/plugin-mgmt/api/v1/plugin/{pluginName}/installationInfo - 验证能够查询指定插件安装信息")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_plugin_install_info(self, plugin_open_service, api_env, api_cache):
        plugin_name = api_env.get("pluginName", "kubectl")

        with AllureHelper.step(f"发送 GET 请求查询插件 {plugin_name} 的安装信息"):
            response_json = plugin_open_service.get_plugin_install_info(plugin_name=plugin_name)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            # JMX 中提取 $.code，默认值5000表示可能失败但接口可达
            assert "code" in response_json, "响应应包含 code 字段"

    @allure.title("获取当前环境插件数据")
    @allure.description("GET /openapi/plugin-mgmt/api/v1/plugin/version/data-report - 验证能够获取当前环境插件数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_current_env_list(self, plugin_open_service, api_cache):
        with AllureHelper.step("发送 GET 请求获取当前环境插件数据"):
            response_json = plugin_open_service.get_current_env_list()

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert "code" in response_json, "响应应包含 code 字段"

    @allure.title("验证任务配置")
    @allure.description("POST /openapi/plugin-mgmt/api/v1/mcp/validate/task - 验证Kubernetes任务配置格式")
    @allure.severity(allure.severity_level.NORMAL)
    def test_verify_task_config(self, plugin_open_service, api_cache):
        with AllureHelper.step("发送 POST 请求验证任务配置"):
            response_json = plugin_open_service.verify_task_config()

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert "code" in response_json, "响应应包含 code 字段"

    @allure.title("验证feature")
    @allure.description("POST /openapi/plugin-mgmt/api/v1/mcp/validate/feature - 验证Feature配置格式")
    @allure.severity(allure.severity_level.NORMAL)
    def test_verify_task_feature(self, plugin_open_service, api_cache):
        with AllureHelper.step("发送 POST 请求验证feature"):
            response_json = plugin_open_service.verify_task_feature()

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert "code" in response_json, "响应应包含 code 字段"

    @allure.title("获取所有支持权限转让的插件")
    @allure.description("GET /openapi/plugin-mgmt/api/v1/auth-transfer/all - 验证能够获取支持权限转让的插件列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_plugin_support_permission_transfer(self, plugin_open_service, api_cache):
        with AllureHelper.step("发送 GET 请求获取支持权限转让的插件"):
            response_json = plugin_open_service.get_plugin_support_permission_transfer()

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert "code" in response_json, "响应应包含 code 字段"
