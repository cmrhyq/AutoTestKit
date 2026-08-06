"""
弹性计算 Native Ingress 接口测试

转换自 JMeter 脚本: ingress-api.jmx
测试内容：Ingress 原生接口完成生命周期测试（查询、创建、列表、更新、删除）
"""
import json

import allure
import pytest

from base.api.entity.elastic_compute import IngressNativeEntity, IngressNativePublicParams
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
@allure.story("Ingress 原生接口")
class TestEcNativeIngress:
    """
    对应 JMeter 脚本: ingress-api.jmx
    线程组: Thread Group - Ingress API
    """

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Ingress 测试所需的公共参数。"""
        return IngressNativePublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            namespace=api_env.get("namespace", "test"),
            name="native-test-ingress001",
            paas_owner=api_env.get("user", "panji_probe"),
        )

    # ==================== 生命周期测试（每接口一函数）====================

    @pytest.mark.dependency(name="ingress_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 Ingress 并清理已有资源")
    @allure.description("查询指定 Ingress 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_ingress_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 Ingress，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, _ = native_service.get_ingress(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 Ingress 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_ingress(
                    cluster_id=cluster_id, namespace=namespace, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 Ingress 失败, status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_ingress_created", False)

    @pytest.mark.dependency(name="ingress_create", depends=["ingress_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 Ingress")
    @allure.description("创建 Ingress 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_ingress(self, native_service, public_params, api_cache):
        """创建 Ingress，断言创建成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace

        with AllureHelper.api_test(native_service):
            ingress = IngressNativeEntity(
                name=public_params.name,
                paas_owner=public_params.paas_owner,
            )
            create_resp = native_service.create_ingress(
                cluster_id=cluster_id, namespace=namespace, ingress=ingress,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 Ingress 失败, 期望201, 实际: {create_http_code}, 响应: {create_resp}"
            )

            api_cache.set("ec_ingress_created", True)

    @pytest.mark.dependency(name="ingress_list", depends=["ingress_create"])
    @pytest.mark.order(3)
    @allure.title("查询 Ingress 列表")
    @allure.description("查询 Ingress 列表，验证包含新创建的 Ingress")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_ingresses(self, native_service, public_params):
        """查询 Ingress 列表，断言包含目标资源。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            list_resp = native_service.list_ingresses(
                cluster_id=cluster_id, namespace=namespace,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 Ingress 列表失败, status={native_service.last_response.status_code}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert name in resp_str, (
                f"Ingress 列表未找到 {name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="ingress_update", depends=["ingress_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 Ingress")
    @allure.description("全量更新 Ingress，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_ingress(self, native_service, public_params):
        """PUT 全量更新 Ingress，断言更新成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            ingress = IngressNativeEntity(
                name=public_params.name,
                paas_owner=public_params.paas_owner,
                extra_labels={"test": "update"},
            )
            native_service.update_ingress(
                cluster_id=cluster_id, namespace=namespace, name=name, ingress=ingress,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"更新 Ingress 失败, status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(name="ingress_delete", depends=["ingress_update"])
    @pytest.mark.order(5)
    @allure.title("删除 Ingress")
    @allure.description("删除创建的 Ingress 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_ingress(self, native_service, public_params, api_cache):
        """删除 Ingress，断言删除成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            native_service.delete_ingress(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 Ingress 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_ingress_created", False)
