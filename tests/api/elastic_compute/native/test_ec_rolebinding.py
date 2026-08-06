"""
弹性计算 Native RoleBinding 接口测试

测试内容：RoleBinding 原生接口生命周期测试（查询、创建、删除）
"""
import allure
import pytest

from base.api.entity.elastic_compute import (
    RoleBindingEntity,
    RoleBindingNativePublicParams,
)
from base.api.services.elastic_compute_native_service import (
    ElasticComputeNativeService,
)
from core.log import get_logger
from core.reporting.allure_helper import AllureHelper
from core.constants import HttpStatus, Tenant

logger = get_logger(__name__)



@pytest.mark.api
@pytest.mark.native
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Native接口")
@allure.story("RoleBinding 原生接口")
class TestEcNativeRoleBinding:

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> RoleBindingNativePublicParams:
        """提取 RoleBinding 测试所需的公共参数。"""
        return RoleBindingNativePublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            namespace=api_env.get("namespace", "test-admin"),
            name="native-test-rolebinding-001",
            role_name="test-role",
            service_account_name="test-sa",
        )

    @pytest.mark.dependency(name="rb_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 RoleBinding 并清理已有资源")
    @allure.description("查询指定 RoleBinding 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_rb_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 RoleBinding，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, _ = native_service.get_role_binding(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 RoleBinding 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_role_binding(
                    cluster_id=cluster_id, namespace=namespace, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 RoleBinding 失败, "
                    f"status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_rb_created", False)

    @pytest.mark.dependency(name="rb_create", depends=["rb_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 RoleBinding")
    @allure.description("创建 RoleBinding 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_rb(self, native_service, public_params, api_cache):
        """创建 RoleBinding，断言创建成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace

        with AllureHelper.api_test(native_service):
            create_resp = native_service.create_role_binding(
                cluster_id=cluster_id,
                namespace=namespace,
                rb=RoleBindingEntity(
                    name=public_params.name,
                    role_name=public_params.role_name,
                    service_account_name=public_params.service_account_name,
                    namespace=public_params.namespace,
                ),
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 RoleBinding 失败, 期望201, 实际: {create_http_code}, "
                f"响应: {create_resp}"
            )

            api_cache.set("ec_rb_created", True)

    @pytest.mark.dependency(name="rb_get", depends=["rb_create"])
    @pytest.mark.order(3)
    @allure.title("查询新创建的 RoleBinding")
    @allure.description("查询指定的 RoleBinding，验证返回 200")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_rb(self, native_service, public_params):
        """查询新创建的 RoleBinding。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, resp = native_service.get_role_binding(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code == HttpStatus.OK, (
                f"查询 RoleBinding 失败, 期望200, 实际: {get_http_code}"
            )
            assert resp.get("metadata", {}).get("name") == name, (
                f"RoleBinding 名称不匹配, 期望 {name}, 响应: {resp}"
            )

    @pytest.mark.dependency(name="rb_delete", depends=["rb_get"])
    @pytest.mark.order(4)
    @allure.title("删除 RoleBinding")
    @allure.description("删除创建的 RoleBinding 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_rb(self, native_service, public_params, api_cache):
        """删除 RoleBinding，断言删除成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            native_service.delete_role_binding(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 RoleBinding 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_rb_created", False)
