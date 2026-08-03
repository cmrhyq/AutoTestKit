"""
微服务 Istio Gateway OpenAPI 接口测试脚本

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
    MicroservicesOpenService,
)
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.microservice
@allure.epic("磐基API自动化测试")
@allure.feature("磐基微服务OpenAPI接口")
@allure.story("Istio Gateway OpenAPI 接口")
class TestMicroservicesIstio:
    """
    Microservices Istio Gateway OpenAPI 测试

    数据流：新建网关实例 → 查询/更新 → 新建规则 → 新建虚拟服务 → 删除虚拟服务 → 删除规则 → 删除实例
    """

    TENANT = "monitor-group"

    @pytest.fixture(scope="class")
    def istio_service(self, service_factory):
        with service_factory(MicroservicesOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Istio Gateway 测试所需的公共参数。"""
        return {
            "sys_code": api_env.get("sysCode"),
            "cell_code": api_env.get("cellCode"),
            "plane_code": api_env.get("planeCode"),
            "mesh_gateway_name": api_env.get("meshGatewayName"),
            "rule_name": api_env.get("ruleName"),
            "mesh_vs_name": api_env.get("meshVsName"),
        }

    def _base_meta(self, public_params) -> Dict:
        return {
            "systemCode": public_params["sys_code"],
            "cellCode": public_params["cell_code"],
            "planeCode": public_params["plane_code"],
        }

    # ==================== 入口网关实例 ====================

    @allure.title("新增入口网关实例")
    @allure.description("新增 Istio 入口网关实例")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_gateway_instance(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求新增网关实例"):
                data = {
                    **self._base_meta(public_params),
                    "name": public_params["mesh_gateway_name"],
                    "type": "INGRESS",
                }
                response_json = istio_service.add_gateway_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("精确查询入口网关实例信息")
    @allure.description("按名称精确查询指定入口网关实例的详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_gateway_instance(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求精确查询网关实例"):
                data = {
                    **self._base_meta(public_params),
                    "name": public_params["mesh_gateway_name"],
                }
                response_json = istio_service.get_gateway_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询入口网关实例信息 分页展示")
    @allure.description("分页查询入口网关实例列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_gateway_instance(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求分页查询网关实例"):
                data = {
                    **self._base_meta(public_params),
                    "page": 1,
                    "rows": 10,
                    "type": "INGRESS",
                }
                response_json = istio_service.list_gateway_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("更新入口网关实例")
    @allure.description("更新指定入口网关实例的配置信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_gateway_instance(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求更新网关实例"):
                data = {
                    **self._base_meta(public_params),
                    "name": public_params["mesh_gateway_name"],
                    "type": "INGRESS",
                    "remark": "updated by autotest",
                }
                response_json = istio_service.update_gateway_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询网关实例信息 分页展示包含入口和出口网关")
    @allure.description("分页查询包含入口/出口在内的所有网关实例列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_ingress_egress_gateway(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求分页查询入口/出口网关"):
                data = {**self._base_meta(public_params), "page": 1, "rows": 10}
                response_json = istio_service.list_ingress_egress_gateway(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== 网关规则 ====================

    @allure.title("新增网关规则")
    @allure.description("为指定网关新增路由规则")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_gateway_rule(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求新增网关规则"):
                data = {
                    **self._base_meta(public_params),
                    "gatewayName": public_params["mesh_gateway_name"],
                    "ruleName": public_params["rule_name"],
                    "port": 80,
                    "protocol": "HTTP",
                }
                response_json = istio_service.add_gateway_rule(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询网关规则信息 分页展示")
    @allure.description("分页查询指定网关下的规则列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_gateway_rule(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求分页查询网关规则"):
                data = {
                    **self._base_meta(public_params),
                    "gatewayName": public_params["mesh_gateway_name"],
                    "page": 1,
                    "rows": 10,
                }
                response_json = istio_service.list_gateway_rule(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("精确查询网关配置信息")
    @allure.description("按网关名和规则名精确查询网关配置详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_gateway_rule(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求精确查询网关配置"):
                data = {
                    **self._base_meta(public_params),
                    "gatewayName": public_params["mesh_gateway_name"],
                    "ruleName": public_params["rule_name"],
                }
                response_json = istio_service.get_gateway_rule(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("更新网关规则")
    @allure.description("更新指定网关规则的配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_gateway_rule(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求更新网关规则"):
                data = {
                    **self._base_meta(public_params),
                    "gatewayName": public_params["mesh_gateway_name"],
                    "ruleName": public_params["rule_name"],
                    "port": 80,
                    "protocol": "HTTP",
                    "remark": "updated by autotest",
                }
                response_json = istio_service.update_gateway_rule(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== 虚拟服务 ====================

    @allure.title("新增虚拟服务")
    @allure.description("新增 Istio 虚拟服务并绑定到指定网关规则")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_virtual_service(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求新增虚拟服务"):
                data = {
                    **self._base_meta(public_params),
                    "gatewayName": public_params["mesh_gateway_name"],
                    "ruleName": public_params["rule_name"],
                    "vsName": public_params["mesh_vs_name"],
                }
                response_json = istio_service.add_virtual_service(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据网关规则查询虚拟服务列表")
    @allure.description("按网关规则查询关联的虚拟服务列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_virtualservice_by_gateway_config(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求按网关规则查询虚拟服务列表"):
                data = {
                    **self._base_meta(public_params),
                    "gatewayName": public_params["mesh_gateway_name"],
                    "ruleName": public_params["rule_name"],
                }
                response_json = istio_service.list_virtualservice_by_gateway_config(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("精确查询虚拟服务信息")
    @allure.description("按名称精确查询虚拟服务详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_virtual_service(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求精确查询虚拟服务"):
                data = {
                    **self._base_meta(public_params),
                    "vsName": public_params["mesh_vs_name"],
                }
                response_json = istio_service.get_virtual_service(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("更新虚拟服务")
    @allure.description("更新指定虚拟服务的配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_virtual_service(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求更新虚拟服务"):
                data = {
                    **self._base_meta(public_params),
                    "vsName": public_params["mesh_vs_name"],
                    "gatewayName": public_params["mesh_gateway_name"],
                    "ruleName": public_params["rule_name"],
                    "remark": "updated by autotest",
                }
                response_json = istio_service.update_virtual_service(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询虚拟服务列表")
    @allure.description("分页查询当前范围下的虚拟服务列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_virtual_service(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求分页查询虚拟服务列表"):
                data = {**self._base_meta(public_params), "page": 1, "rows": 10}
                response_json = istio_service.list_virtual_service(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== 清理操作 ====================

    @allure.title("删除虚拟服务")
    @allure.description("删除指定的虚拟服务")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_virtual_service(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求删除虚拟服务"):
                data = {
                    **self._base_meta(public_params),
                    "vsName": public_params["mesh_vs_name"],
                }
                response_json = istio_service.delete_virtual_service(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("删除网关规则")
    @allure.description("删除指定的网关规则")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_gateway_rule(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求删除网关规则"):
                data = {
                    **self._base_meta(public_params),
                    "gatewayName": public_params["mesh_gateway_name"],
                    "ruleName": public_params["rule_name"],
                }
                response_json = istio_service.delete_gateway_rule(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("删除入口网关实例")
    @allure.description("删除指定的入口网关实例")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_gateway_instance(self, istio_service, public_params):
        with AllureHelper.api_test(istio_service):
            with AllureHelper.step("发送 POST 请求删除网关实例"):
                data = {
                    **self._base_meta(public_params),
                    "name": public_params["mesh_gateway_name"],
                }
                response_json = istio_service.delete_gateway_instance(data)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json
