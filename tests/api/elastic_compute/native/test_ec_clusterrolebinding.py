"""
弹性计算 Native ClusterRoleBinding 接口测试

测试内容：ClusterRoleBinding 原生接口，针对 ClusterRoleBinding 增删查进行测试
"""
import allure
import pytest

from base.api.entity.elastic_compute import (
    ClusterRoleBindingEntity,
    ClusterRoleBindingNativePublicParams,
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
@allure.story("ClusterRoleBinding 原生接口")
class TestEcNativeClusterRoleBinding:

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, test_env) -> ClusterRoleBindingNativePublicParams:
        """提取 ClusterRoleBinding 测试所需的公共参数。"""
        return ClusterRoleBindingNativePublicParams(
            cluster_id=str(test_env.get("clusterId", "1")),
            namespace=test_env.get("namespace", "test-admin"),
            name="native-test-crb",
            cluster_role_name="test-cr",
            service_account_name="test-sa",
        )

    # ==================== 生命周期测试（每接口一函数）====================

    @pytest.mark.dependency(name="crb_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 ClusterRoleBinding 并清理已有资源")
    @allure.description("查询指定 ClusterRoleBinding 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_crb_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 ClusterRoleBinding，若已存在则删除。"""
        cluster_id = public_params.cluster_id
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, get_resp = native_service.get_cluster_role_binding(
                cluster_id=cluster_id, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 ClusterRoleBinding 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_cluster_role_binding(
                    cluster_id=cluster_id, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 ClusterRoleBinding 失败, status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_crb_created", False)

    @pytest.mark.dependency(name="crb_create", depends=["crb_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 ClusterRoleBinding")
    @allure.description("创建 ClusterRoleBinding 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_crb(self, native_service, public_params, api_cache):
        """创建 ClusterRoleBinding，断言创建成功。"""
        cluster_id = public_params.cluster_id

        with AllureHelper.api_test(native_service):
            create_resp = native_service.create_cluster_role_binding(
                cluster_id=cluster_id,
                crb=ClusterRoleBindingEntity(
                    name=public_params.name,
                    cluster_role_name=public_params.cluster_role_name,
                    service_account_name=public_params.service_account_name,
                    subject_namespace=public_params.namespace,
                ),
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 ClusterRoleBinding 失败, 期望201, 实际: {create_http_code}, 响应: {create_resp}"
            )

            api_cache.set("ec_crb_created", True)

    @pytest.mark.dependency(name="crb_verify_created", depends=["crb_create"])
    @pytest.mark.order(3)
    @allure.title("验证 ClusterRoleBinding 创建成功")
    @allure.description("创建后再次查询 ClusterRoleBinding，验证资源存在且 HTTP 200")
    @allure.severity(allure.severity_level.NORMAL)
    def test_verify_crb_created(self, native_service, public_params):
        """验证创建后 ClusterRoleBinding 可查询到。"""
        cluster_id = public_params.cluster_id
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, get_resp = native_service.get_cluster_role_binding(
                cluster_id=cluster_id, name=name,
            )

            assert get_http_code == HttpStatus.OK, (
                f"创建后查询 ClusterRoleBinding 失败, 期望200, 实际: {get_http_code}"
            )

    @pytest.mark.dependency(name="crb_delete", depends=["crb_verify_created"])
    @pytest.mark.order(4)
    @allure.title("删除 ClusterRoleBinding")
    @allure.description("删除创建的 ClusterRoleBinding 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_crb(self, native_service, public_params, api_cache):
        """删除 ClusterRoleBinding，断言删除成功。"""
        cluster_id = public_params.cluster_id
        name = public_params.name

        with AllureHelper.api_test(native_service):
            native_service.delete_cluster_role_binding(
                cluster_id=cluster_id, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 ClusterRoleBinding 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_crb_created", False)
