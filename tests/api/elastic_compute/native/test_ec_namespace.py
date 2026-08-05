"""
弹性计算 Native Namespace 接口测试

转换自 JMeter 脚本: namespace-api.jmx
测试内容：Namespace API 和 Namespace Event API 原生接口生命周期测试。
        涉及 4 类 K8s 资源：Namespace、ResourceQuota、LimitRange、Events。

流程（参考 JMX）：
  1. 查询 ns → 若存在则删除
  2. 创建 ns
  3. 创建 ResourceQuota → 查询 → 更新
  4. 创建 LimitRange → 查询 → 更新
  5. 查询 ns Events
  6. 查询 ns → 查询 ns 列表 → 更新 ns
  7. 删除 ns（级联清理 rq/lr/events）
"""
import allure
import pytest

from base.api.entity.elastic_compute import (
    LimitRangeNativeEntity,
    NamespaceEntity,
    NamespaceNativePublicParams,
    ResourceQuotaNativeEntity,
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
@allure.story("Namespace 原生接口")
class TestEcNativeNamespace:
    """
    对应 JMeter 脚本: namespace-api.jmx
    线程组: Thread Group - Namespace API
    """

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """
        提取 Namespace 测试所需的公共参数。

        为避免污染业务用 namespace，此处使用独立的测试 ns 名称。
        JMX 中 ResourceQuota / LimitRange 的 name 与 namespace 同名。
        """
        ns = "native-test-namespace"
        return NamespaceNativePublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            namespace=ns,
            rq_name=ns,
            lr_name=ns,
        )

    # ==================== 生命周期测试（每接口一函数）====================

    @pytest.mark.dependency(name="namespace_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询 Namespace 并清理已有资源")
    @allure.description("查询指定 Namespace 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_namespace_and_cleanup(
        self, native_service, public_params, api_cache
    ):
        """查询指定 Namespace，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace

        with AllureHelper.api_test(native_service):
            get_http_code, _ = native_service.get_namespace(
                cluster_id=cluster_id, namespace=namespace,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 Namespace 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_namespace(
                    cluster_id=cluster_id, namespace=namespace,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 Namespace 失败,"
                    f" status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_namespace_created", False)

    @pytest.mark.dependency(
        name="namespace_create", depends=["namespace_query_and_cleanup"]
    )
    @pytest.mark.order(2)
    @allure.title("创建 Namespace")
    @allure.description("创建 Namespace 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_namespace(self, native_service, public_params, api_cache):
        """创建 Namespace，断言创建成功。"""
        cluster_id = public_params.cluster_id

        with AllureHelper.api_test(native_service):
            ns = NamespaceEntity(name=public_params.namespace)
            create_resp = native_service.create_namespace(
                cluster_id=cluster_id, ns=ns,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 Namespace 失败, 期望201, 实际: {create_http_code},"
                f" 响应: {create_resp}"
            )

            api_cache.set("ec_namespace_created", True)

    @pytest.mark.dependency(
        name="namespace_create_rq", depends=["namespace_create"]
    )
    @pytest.mark.order(3)
    @allure.title("创建 ResourceQuota")
    @allure.description("在新建 Namespace 下创建 ResourceQuota，验证 HTTP 201")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_resource_quota(self, native_service, public_params):
        """创建 ResourceQuota。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        rq_name = public_params.rq_name

        with AllureHelper.api_test(native_service):
            rq = ResourceQuotaNativeEntity(name=rq_name)
            native_service.create_resource_quota(
                cluster_id=cluster_id, namespace=namespace, rq=rq,
            )

            assert native_service.last_response.status_code == HttpStatus.CREATED, (
                f"创建 ResourceQuota 失败,"
                f" status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(
        name="namespace_get_rq", depends=["namespace_create_rq"]
    )
    @pytest.mark.order(4)
    @allure.title("查询 ResourceQuota")
    @allure.description("查询指定 ResourceQuota，验证 HTTP 200")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_resource_quota(self, native_service, public_params):
        """查询指定 ResourceQuota。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        rq_name = public_params.rq_name

        with AllureHelper.api_test(native_service):
            native_service.get_resource_quota(
                cluster_id=cluster_id, namespace=namespace, name=rq_name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 ResourceQuota 失败,"
                f" status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(
        name="namespace_update_rq", depends=["namespace_get_rq"]
    )
    @pytest.mark.order(5)
    @allure.title("更新 ResourceQuota")
    @allure.description("PUT 更新指定 ResourceQuota 设置，验证 HTTP 200")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_resource_quota(self, native_service, public_params):
        """更新指定 ResourceQuota。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        rq_name = public_params.rq_name

        with AllureHelper.api_test(native_service):
            rq = ResourceQuotaNativeEntity(name=rq_name)
            native_service.update_resource_quota(
                cluster_id=cluster_id,
                namespace=namespace,
                name=rq_name,
                rq=rq,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"更新 ResourceQuota 失败,"
                f" status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(
        name="namespace_create_lr", depends=["namespace_create"]
    )
    @pytest.mark.order(6)
    @allure.title("创建 LimitRange")
    @allure.description("在新建 Namespace 下创建 LimitRange，验证 HTTP 201")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_limit_range(self, native_service, public_params):
        """创建 LimitRange。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        lr_name = public_params.lr_name

        with AllureHelper.api_test(native_service):
            lr = LimitRangeNativeEntity(name=lr_name)
            native_service.create_limit_range(
                cluster_id=cluster_id, namespace=namespace, lr=lr,
            )

            assert native_service.last_response.status_code == HttpStatus.CREATED, (
                f"创建 LimitRange 失败,"
                f" status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(
        name="namespace_get_lr", depends=["namespace_create_lr"]
    )
    @pytest.mark.order(7)
    @allure.title("查询 LimitRange")
    @allure.description("查询指定 LimitRange，验证 HTTP 200")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_limit_range(self, native_service, public_params):
        """查询指定 LimitRange。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        lr_name = public_params.lr_name

        with AllureHelper.api_test(native_service):
            native_service.get_limit_range(
                cluster_id=cluster_id, namespace=namespace, name=lr_name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 LimitRange 失败,"
                f" status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(
        name="namespace_update_lr", depends=["namespace_get_lr"]
    )
    @pytest.mark.order(8)
    @allure.title("更新 LimitRange")
    @allure.description("PUT 更新指定 LimitRange 设置，验证 HTTP 200")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_limit_range(self, native_service, public_params):
        """更新指定 LimitRange。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        lr_name = public_params.lr_name

        with AllureHelper.api_test(native_service):
            lr = LimitRangeNativeEntity(
                name=lr_name,
                extra_labels={"test": "update"},
            )
            native_service.update_limit_range(
                cluster_id=cluster_id,
                namespace=namespace,
                name=lr_name,
                lr=lr,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"更新 LimitRange 失败,"
                f" status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(
        name="namespace_events", depends=["namespace_create"]
    )
    @pytest.mark.order(9)
    @allure.title("查询 Namespace Events")
    @allure.description("查询指定 Namespace 下的 Events 列表，验证 HTTP 200")
    @allure.severity(allure.severity_level.MINOR)
    def test_get_namespace_events(self, native_service, public_params):
        """查询 Namespace Events。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace

        with AllureHelper.api_test(native_service):
            native_service.get_namespace_events(
                cluster_id=cluster_id, namespace=namespace,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 Namespace Events 失败,"
                f" status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(
        name="namespace_list", depends=["namespace_create"]
    )
    @pytest.mark.order(10)
    @allure.title("查询 Namespace 列表")
    @allure.description("查询集群下所有 Namespace 列表，验证 HTTP 200")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_namespaces(self, native_service, public_params):
        """查询 Namespace 列表。"""
        cluster_id = public_params.cluster_id

        with AllureHelper.api_test(native_service):
            native_service.list_namespaces(cluster_id=cluster_id)

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 Namespace 列表失败,"
                f" status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(
        name="namespace_update",
        depends=[
            "namespace_update_rq",
            "namespace_update_lr",
            "namespace_events",
            "namespace_list",
        ],
    )
    @pytest.mark.order(11)
    @allure.title("PUT 全量更新 Namespace")
    @allure.description("使用 PUT 方法全量更新 Namespace，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_namespace(self, native_service, public_params):
        """PUT 全量更新 Namespace。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace

        with AllureHelper.api_test(native_service):
            ns = NamespaceEntity(
                name=namespace,
                extra_labels={"test": "update"},
            )
            native_service.update_namespace(
                cluster_id=cluster_id, namespace=namespace, ns=ns,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"更新 Namespace 失败,"
                f" status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(
        name="namespace_delete", depends=["namespace_update"]
    )
    @pytest.mark.order(12)
    @allure.title("删除 Namespace")
    @allure.description("删除创建的 Namespace（级联清理其下 rq/lr/events），验证 HTTP 200")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_namespace(self, native_service, public_params, api_cache):
        """删除 Namespace。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace

        with AllureHelper.api_test(native_service):
            native_service.delete_namespace(
                cluster_id=cluster_id, namespace=namespace,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 Namespace 失败,"
                f" status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_namespace_created", False)
