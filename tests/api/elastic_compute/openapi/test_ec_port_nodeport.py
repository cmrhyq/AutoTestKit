"""
Port/NodePort 接口测试

测试内容：Port 和 NodePort 端口管理（查询使用中端口列表、查询指定端口可用性、分配端口范围、查询指定集群端口范围、查询全部端口范围）
"""
import allure
import pytest

from base.api.entity.elastic_compute.openapi import (
    PortAllocationEntity,
    PortNodePortPublicParams,
)
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("Port/NodePort 端口管理接口")
class TestEcOpenapiPortNodePort:

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> PortNodePortPublicParams:
        """提取 Port/NodePort 测试所需的公共参数。"""
        return PortNodePortPublicParams(
            cell_code=api_env.get("cellCode", "testCellCode"),
            node_port=api_env.get("nodePort", "10001"),
            tenant_code=api_env.get("tenant_code", "monitor-group"),
            ports=api_env.get("ports", "30011-30030"),
        )

    # -------------------- 测试用例 --------------------

    @pytest.mark.dependency(name="nodeport_list_used")
    @pytest.mark.order(1)
    @allure.title("查询租户指定集群使用中 NodePort 列表")
    @allure.description("查询指定集群实际使用的 NodePort 端口列表，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_node_ports(self, ec_service, public_params):
        """查询租户指定集群使用中 NodePort 列表，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_nodeports(cell_code=public_params.cell_code)

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询 NodePort 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.dependency(name="nodeport_check_available")
    @pytest.mark.order(2)
    @allure.title("查询指定 NodePort 是否可用")
    @allure.description("查询指定 NodePort 端口号是否可以使用，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_node_port_available(self, ec_service, public_params):
        """查询指定 NodePort 是否可用，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_nodeport(
                cell_code=public_params.cell_code,
                nodeport=public_params.node_port,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询指定 NodePort 可用性失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.dependency(name="port_allocate", depends=["nodeport_list_used"])
    @pytest.mark.order(3)
    @allure.title("租户 NodePort 端口范围分配")
    @allure.description("为租户分配指定集群的 NodePort 端口范围，验证分配成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_allocate_ports(self, ec_service, public_params):
        """租户 NodePort 端口范围分配，断言分配成功。"""
        with AllureHelper.api_test(ec_service):
            allocation = PortAllocationEntity(
                tenant_code=public_params.tenant_code,
                ports=public_params.ports,
            )
            resp = ec_service.allocate_ports(
                cell_code=public_params.cell_code,
                allocation=allocation,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"端口范围分配失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.dependency(name="port_list_by_cell", depends=["port_allocate"])
    @pytest.mark.order(4)
    @allure.title("查询租户指定集群 NodePort 端口范围")
    @allure.description("查询租户在指定集群已分配的 NodePort 端口范围，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_ports_by_cell(self, ec_service, public_params):
        """查询租户指定集群 NodePort 端口范围，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_ports_by_cell(cell_code=public_params.cell_code)

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询指定集群端口范围失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.dependency(name="port_list_all", depends=["port_allocate"])
    @pytest.mark.order(5)
    @allure.title("查询租户全部 NodePort 端口范围")
    @allure.description("查询租户在所有集群已分配的全部 NodePort 端口范围，验证返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_all_ports(self, ec_service):
        """查询租户全部 NodePort 端口范围，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_all_ports()

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询全部端口范围失败, code: {resp.get('code')}, 响应: {resp}"
            )
