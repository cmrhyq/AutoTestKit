"""
插件中心 统计插件安装数 接口测试

转换自 JMeter 脚本: plugin-count.jmx
测试内容：统计插件安装数量接口
"""

from typing import Dict, Any

import allure
import pytest

from base.api.services.plugin_inner_service import PanJiPluginInnerService
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("插件中心InnerAPI服务")
@allure.story("plugin-count 统计插件安装数")
class TestPluginCount:
    """
    对应 JMeter 脚本: plugin-count.jmx
    线程组: 插件接口测试
    """

    @pytest.fixture(scope="class")
    def plugin_inner_service(self, api_env, api_logger):
        """创建 Plugin Inner API 服务实例"""
        service = PanJiPluginInnerService(
            base_url=api_env.get("api_inner_base_url"), logger=api_logger
        )
        yield service
        service.close()

    @allure.title("统计插件安装数")
    @allure.description("GET /plugin/api/v1/plugin/list/instance - 验证能够成功获取插件安装数量列表")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_plugin_install_count(self, plugin_inner_service, api_cache):
        with AllureHelper.step("发送 GET 请求统计插件安装数"):
            response_json = plugin_inner_service.get_plugin_install_count()

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert "data" in response_json, "响应应包含 data 字段"
