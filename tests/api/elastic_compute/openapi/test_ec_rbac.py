"""
RBAC 管理接口测试

测试内容：RBAC 角色查询（查询 Role 列表、查询指定 Role、查询 RoleBinding 列表、查询指定 RoleBinding）
"""
import allure
import pytest

from base.api.entity.elastic_compute.openapi import RbacPublicParams
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("RBAC 角色管理接口")
class TestEcOpenapiRbac:

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> RbacPublicParams:
        """提取 RBAC 测试所需的公共参数。"""
        return RbacPublicParams(
            cell_code=api_env.get("cellCode", "PROD_PLANE1_CELL3"),
            sys_code=api_env.get("sysCode", "test"),
        )

    # -------------------- 测试用例 --------------------

    @pytest.mark.dependency(name="rbac_list_roles")
    @pytest.mark.order(1)
    @allure.title("查询 Role 列表")
    @allure.description("查询指定命名空间下的 Role 列表，并缓存首条 Role 名称用于后续查询")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_roles(self, ec_service, public_params, api_cache):
        """查询 Role 列表，缓存首条名称。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_rbac_roles(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询 Role 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

            # 提取首条 Role 名称
            items = resp.get("data", {}).get("items", [])
            role_name = items[0]["metadata"]["name"] if items else "test"
            api_cache.set("rbac_role_name", role_name)

    @pytest.mark.dependency(name="rbac_get_role", depends=["rbac_list_roles"])
    @pytest.mark.order(2)
    @allure.title("查询指定 Role")
    @allure.description("根据列表中缓存的 Role 名称查询指定 Role 详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_role(self, ec_service, public_params, api_cache):
        """查询指定 Role 详情。"""
        role_name = api_cache.get("rbac_role_name", "test")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_rbac_role(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=role_name,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询指定 Role 失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @pytest.mark.dependency(name="rbac_list_role_bindings")
    @pytest.mark.order(3)
    @allure.title("查询 RoleBinding 列表")
    @allure.description("查询指定命名空间下的 RoleBinding 列表，并缓存首条名称用于后续查询")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_role_bindings(self, ec_service, public_params, api_cache):
        """查询 RoleBinding 列表，缓存首条名称。"""
        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_rbac_role_bindings(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询 RoleBinding 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

            # 提取首条 RoleBinding 名称
            items = resp.get("data", {}).get("items", [])
            role_binding_name = items[0]["metadata"]["name"] if items else "test"
            api_cache.set("rbac_role_binding_name", role_binding_name)

    @pytest.mark.dependency(name="rbac_get_role_binding", depends=["rbac_list_role_bindings"])
    @pytest.mark.order(4)
    @allure.title("查询指定 RoleBinding")
    @allure.description("根据列表中缓存的 RoleBinding 名称查询指定 RoleBinding 详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_role_binding(self, ec_service, public_params, api_cache):
        """查询指定 RoleBinding 详情。"""
        role_binding_name = api_cache.get("rbac_role_binding_name", "test")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_rbac_role_binding(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=role_binding_name,
            )

            assert resp.get("code") == ApiCode.SUCCESS, (
                f"查询指定 RoleBinding 失败, code: {resp.get('code')}, 响应: {resp}"
            )
