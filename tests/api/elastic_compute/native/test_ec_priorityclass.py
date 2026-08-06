"""
弹性计算 Native PriorityClass 接口测试

转换自 JMeter 脚本: priorityclass.jmx
测试内容：PriorityClass 原生接口完成生命周期测试（查询、创建、更新、删除）

注意：PriorityClass 是 cluster-scoped 资源，无 namespace，也无 list 接口。
"""
import allure
import pytest

from base.api.entity.elastic_compute import PriorityClassNativeEntity, PriorityClassNativePublicParams
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
@allure.story("PriorityClass 原生接口")
class TestEcNativePriorityClass:
    """
    对应 JMeter 脚本: priorityclass.jmx
    线程组: Thread Group - PriorityClass
    """

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 PriorityClass 测试所需的公共参数。"""
        return PriorityClassNativePublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            name="native-test-pc",
        )

    # ==================== 生命周期测试（每接口一函数）====================

    @pytest.mark.dependency(name="priorityclass_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 PriorityClass 并清理已有资源")
    @allure.description("查询指定 PriorityClass 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_priorityclass_and_cleanup(
        self, native_service, public_params, api_cache
    ):
        """查询指定 PriorityClass，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params.cluster_id
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, _ = native_service.get_priority_class(
                cluster_id=cluster_id, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 PriorityClass 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_priority_class(
                    cluster_id=cluster_id, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 PriorityClass 失败,"
                    f" status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_priorityclass_created", False)

    @pytest.mark.dependency(
        name="priorityclass_create", depends=["priorityclass_query_and_cleanup"]
    )
    @pytest.mark.order(2)
    @allure.title("创建 PriorityClass")
    @allure.description("创建 PriorityClass 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_priorityclass(self, native_service, public_params, api_cache):
        """创建 PriorityClass，断言创建成功。"""
        cluster_id = public_params.cluster_id

        with AllureHelper.api_test(native_service):
            pc = PriorityClassNativeEntity(name=public_params.name)
            create_resp = native_service.create_priority_class(
                cluster_id=cluster_id, pc=pc,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 PriorityClass 失败, 期望201, 实际: {create_http_code},"
                f" 响应: {create_resp}"
            )

            api_cache.set("ec_priorityclass_created", True)

    @pytest.mark.dependency(
        name="priorityclass_update", depends=["priorityclass_create"]
    )
    @pytest.mark.order(3)
    @allure.title("PUT 全量更新 PriorityClass")
    @allure.description("全量更新 PriorityClass，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_priorityclass(self, native_service, public_params):
        """PUT 全量更新 PriorityClass，断言更新成功。"""
        cluster_id = public_params.cluster_id
        name = public_params.name

        with AllureHelper.api_test(native_service):
            pc = PriorityClassNativeEntity(
                name=name,
                description="this is a update test",
                extra_labels={"test": "update"},
            )
            native_service.update_priority_class(
                cluster_id=cluster_id, name=name, pc=pc,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"更新 PriorityClass 失败,"
                f" status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(
        name="priorityclass_delete", depends=["priorityclass_update"]
    )
    @pytest.mark.order(4)
    @allure.title("删除 PriorityClass")
    @allure.description("删除创建的 PriorityClass 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_priorityclass(self, native_service, public_params, api_cache):
        """删除 PriorityClass，断言删除成功。"""
        cluster_id = public_params.cluster_id
        name = public_params.name

        with AllureHelper.api_test(native_service):
            native_service.delete_priority_class(
                cluster_id=cluster_id, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 PriorityClass 失败,"
                f" status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_priorityclass_created", False)
