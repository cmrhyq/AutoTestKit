"""
微服务 Istio Gateway OpenAPI 接口测试脚本

基于 JMeter auto_test_pro/auto-test/files/microservices/openapi/msistiogateway.jmx 转换。
覆盖 Istio Gateway 相关 17 个用例：
- 入口网关实例 CRUD
- 网关规则 CRUD
- 虚拟服务 CRUD
- 网关配置查询
"""
from typing import Dict

import allure
import pytest

from base.api.services.microservices_open_service import (
    PanJiMicroservicesOpenService,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基微服务 Istio Gateway OpenAPI 服务")
@allure.story("Microservices Istio Gateway OpenAPI 接口测试")
class TestMicroservicesIstioOpenApi:
    """
    Microservices Istio Gateway OpenAPI 测试

    数据流：新建网关实例 → 查询/更新 → 新建规则 → 新建虚拟服务 → 删除虚拟服务 → 删除规则 → 删除实例
    """

    TENANT = "monitor-group"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def istio_service(self, api_env, api_logger):
        service = PanJiMicroservicesOpenService(
            base_url=api_env.get("api_base_url"),
            logger=api_logger,
        )
        yield service
        service.close()

    def _base_meta(self, api_env) -> Dict:
        return {
            "systemCode": api_env.get("ms_sys_code"),
            "cellCode": api_env.get("ms_cell_code"),
            "planeCode": api_env.get("ms_plane_code"),
        }

    # ==================== 入口网关实例 ====================

    @allure.title("新增入口网关实例")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_gateway_instance(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求新增网关实例"):
                data = {
                    **self._base_meta(api_env),
                    "name": api_env.get("ms_gateway_name"),
                    "type": "INGRESS",
                }
                response_json = istio_service.add_gateway_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("精确查询入口网关实例信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_gateway_instance(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求精确查询网关实例"):
                data = {
                    **self._base_meta(api_env),
                    "name": api_env.get("ms_gateway_name"),
                }
                response_json = istio_service.get_gateway_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询入口网关实例信息 分页展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_gateway_instance(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求分页查询网关实例"):
                data = {
                    **self._base_meta(api_env),
                    "page": 1,
                    "rows": 10,
                    "type": "INGRESS",
                }
                response_json = istio_service.list_gateway_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("更新入口网关实例")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_gateway_instance(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求更新网关实例"):
                data = {
                    **self._base_meta(api_env),
                    "name": api_env.get("ms_gateway_name"),
                    "type": "INGRESS",
                    "remark": "updated by autotest",
                }
                response_json = istio_service.update_gateway_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询网关实例信息 分页展示包含入口和出口网关")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_ingress_egress_gateway(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求分页查询入口/出口网关"):
                data = {**self._base_meta(api_env), "page": 1, "rows": 10}
                response_json = istio_service.list_ingress_egress_gateway(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== 网关规则 ====================

    @allure.title("新增网关规则")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_gateway_rule(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求新增网关规则"):
                data = {
                    **self._base_meta(api_env),
                    "gatewayName": api_env.get("ms_gateway_name"),
                    "ruleName": api_env.get("ms_rule_name"),
                    "port": 80,
                    "protocol": "HTTP",
                }
                response_json = istio_service.add_gateway_rule(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询网关规则信息 分页展示")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_gateway_rule(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求分页查询网关规则"):
                data = {
                    **self._base_meta(api_env),
                    "gatewayName": api_env.get("ms_gateway_name"),
                    "page": 1,
                    "rows": 10,
                }
                response_json = istio_service.list_gateway_rule(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("精确查询网关配置信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_gateway_rule(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求精确查询网关配置"):
                data = {
                    **self._base_meta(api_env),
                    "gatewayName": api_env.get("ms_gateway_name"),
                    "ruleName": api_env.get("ms_rule_name"),
                }
                response_json = istio_service.get_gateway_rule(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("更新网关规则")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_gateway_rule(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求更新网关规则"):
                data = {
                    **self._base_meta(api_env),
                    "gatewayName": api_env.get("ms_gateway_name"),
                    "ruleName": api_env.get("ms_rule_name"),
                    "port": 80,
                    "protocol": "HTTP",
                    "remark": "updated by autotest",
                }
                response_json = istio_service.update_gateway_rule(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== 虚拟服务 ====================

    @allure.title("新增虚拟服务")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_virtual_service(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求新增虚拟服务"):
                data = {
                    **self._base_meta(api_env),
                    "gatewayName": api_env.get("ms_gateway_name"),
                    "ruleName": api_env.get("ms_rule_name"),
                    "vsName": api_env.get("ms_vs_name"),
                }
                response_json = istio_service.add_virtual_service(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据网关规则查询虚拟服务列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_virtualservice_by_gateway_config(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求按网关规则查询虚拟服务列表"):
                data = {
                    **self._base_meta(api_env),
                    "gatewayName": api_env.get("ms_gateway_name"),
                    "ruleName": api_env.get("ms_rule_name"),
                }
                response_json = istio_service.list_virtualservice_by_gateway_config(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("精确查询虚拟服务信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_virtual_service(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求精确查询虚拟服务"):
                data = {
                    **self._base_meta(api_env),
                    "vsName": api_env.get("ms_vs_name"),
                }
                response_json = istio_service.get_virtual_service(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("更新虚拟服务")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_virtual_service(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求更新虚拟服务"):
                data = {
                    **self._base_meta(api_env),
                    "vsName": api_env.get("ms_vs_name"),
                    "gatewayName": api_env.get("ms_gateway_name"),
                    "ruleName": api_env.get("ms_rule_name"),
                    "remark": "updated by autotest",
                }
                response_json = istio_service.update_virtual_service(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询虚拟服务列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_virtual_service(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求分页查询虚拟服务列表"):
                data = {**self._base_meta(api_env), "page": 1, "rows": 10}
                response_json = istio_service.list_virtual_service(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== 清理操作 ====================

    @allure.title("删除虚拟服务")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_virtual_service(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求删除虚拟服务"):
                data = {
                    **self._base_meta(api_env),
                    "vsName": api_env.get("ms_vs_name"),
                }
                response_json = istio_service.delete_virtual_service(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("删除网关规则")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_gateway_rule(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求删除网关规则"):
                data = {
                    **self._base_meta(api_env),
                    "gatewayName": api_env.get("ms_gateway_name"),
                    "ruleName": api_env.get("ms_rule_name"),
                }
                response_json = istio_service.delete_gateway_rule(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("删除入口网关实例")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_gateway_instance(self, istio_service, api_env):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求删除网关实例"):
                data = {
                    **self._base_meta(api_env),
                    "name": api_env.get("ms_gateway_name"),
                }
                response_json = istio_service.delete_gateway_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json
