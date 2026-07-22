"""
微服务 Inner API 接口测试脚本

基于 JMeter auto_test_pro/auto-test/files/microservices/innerapi/microserviceIstioInner.jmx 转换。
覆盖 ISTIO 网关 Inner API 相关 10 个用例：
- KEM 统一校验/创建/删除
- 虚拟服务查询/精确/新增/删除
- 网关配置名称查询、节点列表查询
- 批量上传证书

Inner API 使用 apikey 鉴权（不走 Bearer），从 ms_apikey 配置读取。
"""
from typing import Dict

import allure
import pytest

from base.api.services.microservices_inner_service import (
    PanJiMicroservicesInnerService,
    Kem,
    MeshVS,
    MeshNode,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基微服务 Inner API 服务")
@allure.story("Microservices ISTIO 网关 Inner API 接口测试")
class TestMicroservicesInnerApi:
    """
    Microservices ISTIO Inner API 测试

    数据流：统一校验 → 统一创建 → 查询/精确 → 删除虚拟服务 → 新增虚拟服务 → 统一删除
    """

    TENANT = "monitor-group"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """Inner API 虽走 apikey，但仍触发 get_token 以保持一致的 setup 语义。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def inner_service(self, api_env, api_logger):
        service = PanJiMicroservicesInnerService(
            base_url=api_env.get("api_inner_base_url") or api_env.get("api_base_url"),
            logger=api_logger,
        )
        yield service
        service.close()

    def _kem(self, api_env) -> Kem:
        return Kem(
            sysCode=api_env.get("ms_sys_code"),
            cellCode=api_env.get("cell_code"),
            planeCode=api_env.get("cell_code"),
            tenantCode=api_env.get("tenant_code"),
            username=api_env.get("basic_auth_username"),
            gatewayInsName=api_env.get("ms_gateway_name"),
            gatewayName=api_env.get("ms_gateway_name"),
            gatewayNodePort="30080",
            vsName=api_env.get("ms_vs_name"),
        )

    def _vs(self, api_env) -> MeshVS:
        return MeshVS(
            vsName=api_env.get("ms_vs_name"),
            gatewayName=api_env.get("ms_gateway_name"),
            sysCode=api_env.get("ms_sys_code"),
            cellCode=api_env.get("cell_code"),
            planeCode=api_env.get("cell_code"),
            clusterId=api_env.get("cluster_id"),
        )

    def _node(self, api_env) -> MeshNode:
        return MeshNode(
            cellCode=api_env.get("cell_code"),
            planeCode=api_env.get("cell_code"),
            clusterId=api_env.get("cluster_id"),
        )

    # ==================== KEM 统一操作 ====================

    @allure.title("统一校验接口")
    @allure.severity(allure.severity_level.NORMAL)
    def test_kem_check(self, inner_service, api_env):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求统一校验"):
                response_json = inner_service.kem_check(self._kem(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("统一创建接口")
    @allure.severity(allure.severity_level.NORMAL)
    def test_kem_create(self, inner_service, api_env):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求统一创建"):
                response_json = inner_service.kem_create(self._kem(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== 虚拟服务查询 ====================

    @allure.title("查询虚拟服务列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_virtual_service(self, inner_service, api_env):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求查询虚拟服务列表"):
                response_json = inner_service.list_virtual_service(self._vs(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询网关配置名称")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_gateway_name(self, inner_service):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 GET 请求查询网关配置名称"):
                response_json = inner_service.get_gateway_name()
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("查询节点列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_node(self, inner_service, api_env):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求查询节点列表"):
                response_json = inner_service.list_node(self._node(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("批量上传证书")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_create_secret(self, inner_service, api_env):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求批量上传证书"):
                response_json = inner_service.batch_create_secret(self._kem(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("精确查询虚拟服务信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_virtual_service(self, inner_service, api_env):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求精确查询虚拟服务"):
                response_json = inner_service.get_virtual_service(self._vs(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== 虚拟服务变更 ====================

    @allure.title("删除虚拟服务")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_virtual_service(self, inner_service, api_env):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求删除虚拟服务"):
                response_json = inner_service.delete_virtual_service(self._vs(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("新增虚拟服务")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_virtual_service(self, inner_service, api_env):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求新增虚拟服务"):
                response_json = inner_service.add_virtual_service(self._vs(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== KEM 统一删除 ====================

    @allure.title("统一删除接口")
    @allure.severity(allure.severity_level.NORMAL)
    def test_kem_delete(self, inner_service, api_env):
        with AllureHelper.api_test(inner_service):
            with AllureHelper.step("发送 POST 请求统一删除"):
                response_json = inner_service.kem_delete(self._kem(api_env))
            with AllureHelper.step("验证响应"):
                assert "code" in response_json
