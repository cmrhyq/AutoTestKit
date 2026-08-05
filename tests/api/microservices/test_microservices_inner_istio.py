"""
微服务 Inner API 接口测试脚本

覆盖 ISTIO 网关 Inner API 相关 10 个用例：
- KEM 统一校验/创建/删除
- 虚拟服务查询/精确/新增/删除
- 网关配置名称查询、节点列表查询
- 批量上传证书

Inner API 使用 apikey 鉴权（不走 Bearer），从 ms_apikey 配置读取。
"""

import allure
import pytest

from base.api.entity.microservices import (
    InnerIstioPublicParams,
    Kem,
    MeshNode,
    MeshVS,
)
from base.api.services.microservices_inner_service import (
    MicroservicesInnerService,
)
from core.log import get_logger
from core.reporting.allure_helper import AllureHelper
from core.constants import Tenant

logger = get_logger(__name__)

@pytest.mark.api
@pytest.mark.microservice
@allure.epic("磐基API自动化测试")
@allure.feature("磐基微服务InnerAPI接口")
@allure.story("ISTIO 网关 Inner API 接口")
class TestMicroservicesInnerIstio:
    """
    Microservices ISTIO Inner API 测试

    数据流：统一校验 → 统一创建 → 查询/精确 → 删除虚拟服务 → 新增虚拟服务 → 统一删除
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def inner_service(self, api_env):
        service = MicroservicesInnerService(
            base_url=api_env.get("apiInnerBaseUrl") or api_env.get("apiBaseUrl"),
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> InnerIstioPublicParams:
        """提取 Inner Istio 测试所需的公共参数。"""
        return InnerIstioPublicParams(
            mesh_gateway_name=api_env.get("meshGatewayName"),
            mesh_vs_name=api_env.get("meshVsName"),
            sys_code=api_env.get("sysCode"),
            cell_code=api_env.get("cellCode"),
            plane_code=api_env.get("planeCode"),
            cluster_id=api_env.get("clusterId"),
            tenant_code=api_env.get("tenantCode"),
            basic_auth_username=api_env.get("basicAuthUsername"),
        )

    # ==================== KEM 统一操作 ====================

    @allure.title("统一校验接口")
    @allure.description("对 KEM 参数进行统一校验")
    @allure.severity(allure.severity_level.NORMAL)
    def test_kem_check(self, inner_service, public_params):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求统一校验"):
                response_json = inner_service.kem_check(
                    Kem.from_public_params(public_params, gateway_node_port="30080")
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("统一创建接口")
    @allure.description("基于 KEM 参数一键创建网关、规则、虚拟服务等")
    @allure.severity(allure.severity_level.NORMAL)
    def test_kem_create(self, inner_service, public_params):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求统一创建"):
                response_json = inner_service.kem_create(
                    Kem.from_public_params(public_params, gateway_node_port="30080")
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== 虚拟服务查询 ====================

    @allure.title("查询虚拟服务列表")
    @allure.description("查询指定网关下的虚拟服务列表（Inner API）")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_virtual_service(self, inner_service, public_params):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求查询虚拟服务列表"):
                response_json = inner_service.list_virtual_service(
                    MeshVS.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询网关配置名称")
    @allure.description("查询当前租户可用的网关配置名称列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_gateway_name(self, inner_service):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 GET 请求查询网关配置名称"):
                response_json = inner_service.get_gateway_name()
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询节点列表")
    @allure.description("查询指定集群下的网关节点列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_node(self, inner_service, public_params):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求查询节点列表"):
                response_json = inner_service.list_node(
                    MeshNode.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("批量上传证书")
    @allure.description("为网关批量上传 TLS 证书")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_create_secret(self, inner_service, public_params):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求批量上传证书"):
                response_json = inner_service.batch_create_secret(
                    Kem.from_public_params(public_params, gateway_node_port="30080")
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("精确查询虚拟服务信息")
    @allure.description("按名称精确查询虚拟服务详情（Inner API）")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_virtual_service(self, inner_service, public_params):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求精确查询虚拟服务"):
                response_json = inner_service.get_virtual_service(
                    MeshVS.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== 虚拟服务变更 ====================

    @allure.title("删除虚拟服务")
    @allure.description("删除指定虚拟服务（Inner API）")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_virtual_service(self, inner_service, public_params):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求删除虚拟服务"):
                response_json = inner_service.delete_virtual_service(
                    MeshVS.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("新增虚拟服务")
    @allure.description("新增虚拟服务（Inner API）")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_virtual_service(self, inner_service, public_params):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求新增虚拟服务"):
                response_json = inner_service.add_virtual_service(
                    MeshVS.from_public_params(public_params)
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== KEM 统一删除 ====================

    @allure.title("统一删除接口")
    @allure.description("基于 KEM 参数一键清理网关、规则、虚拟服务等")
    @allure.severity(allure.severity_level.NORMAL)
    def test_kem_delete(self, inner_service, public_params):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求统一删除"):
                response_json = inner_service.kem_delete(
                    Kem.from_public_params(public_params, gateway_node_port="30080")
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json
