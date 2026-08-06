"""
弹性计算 Native HorizontalPodAutoscaler 接口测试

转换自 JMeter 脚本: hpa.jmx
测试内容：HPA 原生接口完成生命周期测试（查询、创建、列表、更新、删除）
"""
import json

import allure
import pytest

from base.api.entity.elastic_compute import HpaNativeEntity, HpaNativePublicParams
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
@allure.story("HorizontalPodAutoscaler 原生接口")
class TestEcNativeHpa:
    """
    对应 JMeter 脚本: hpa.jmx
    线程组: Thread Group - HorizontalPodAutoscaler
    """

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 HPA 测试所需的公共参数。"""
        return HpaNativePublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            namespace=api_env.get("namespace", "test-admin"),
            name="native-test-hpa",
            paas_owner=api_env.get("user", "panji_probe"),
            workload_kind=api_env.get("nativeHpaWorkloadKind", "Deployment"),
            workload_name=api_env.get("nativeHpaWorkloadName", "app-nginx"),
            min_replicas=1,
            max_replicas=10,
        )

    # ==================== 生命周期测试（每接口一函数）====================

    @pytest.mark.dependency(name="native_hpa_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 HPA 并清理已有资源")
    @allure.description("查询指定 HPA 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_hpa_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 HPA，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, _ = native_service.get_native_hpa(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 HPA 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_native_hpa(
                    cluster_id=cluster_id, namespace=namespace, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 HPA 失败, status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_native_hpa_created", False)

    @pytest.mark.dependency(
        name="native_hpa_create", depends=["native_hpa_query_and_cleanup"]
    )
    @pytest.mark.order(2)
    @allure.title("创建 HPA")
    @allure.description("创建 HPA 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_hpa(self, native_service, public_params, api_cache):
        """创建 HPA，断言创建成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace

        with AllureHelper.api_test(native_service):
            hpa = HpaNativeEntity(
                name=public_params.name,
                paas_owner=public_params.paas_owner,
                workload_kind=public_params.workload_kind,
                workload_name=public_params.workload_name,
                min_replicas=public_params.min_replicas,
                max_replicas=public_params.max_replicas,
            )
            create_resp = native_service.create_native_hpa(
                cluster_id=cluster_id, namespace=namespace, hpa=hpa,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 HPA 失败, 期望201, 实际: {create_http_code}, 响应: {create_resp}"
            )

            api_cache.set("ec_native_hpa_created", True)

    @pytest.mark.dependency(name="native_hpa_list", depends=["native_hpa_create"])
    @pytest.mark.order(3)
    @allure.title("查询 HPA 列表")
    @allure.description("按标签选择器查询 HPA 列表，验证包含新创建的 HPA")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_hpas(self, native_service, public_params):
        """查询 HPA 列表，断言包含目标资源。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            list_resp = native_service.list_native_hpas(
                cluster_id=cluster_id,
                namespace=namespace,
                label_selector=f"name={name}",
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 HPA 列表失败, status={native_service.last_response.status_code}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert f'"name":"{name}"' in resp_str or name in resp_str, (
                f"HPA 列表未找到 {name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="native_hpa_update", depends=["native_hpa_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 HPA")
    @allure.description("全量更新 HPA（CPU 阈值 50→80，追加 test:update 标签），验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_hpa(self, native_service, public_params):
        """PUT 全量更新 HPA，断言更新成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            hpa = HpaNativeEntity(
                name=public_params.name,
                paas_owner=public_params.paas_owner,
                workload_kind=public_params.workload_kind,
                workload_name=public_params.workload_name,
                min_replicas=public_params.min_replicas,
                max_replicas=public_params.max_replicas,
                cpu_utilization=80,
                extra_labels={"test": "update"},
            )
            native_service.update_native_hpa(
                cluster_id=cluster_id, namespace=namespace, name=name, hpa=hpa,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"更新 HPA 失败, status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(name="native_hpa_delete", depends=["native_hpa_update"])
    @pytest.mark.order(5)
    @allure.title("删除 HPA")
    @allure.description("删除创建的 HPA 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_hpa(self, native_service, public_params, api_cache):
        """删除 HPA，断言删除成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            native_service.delete_native_hpa(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 HPA 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_native_hpa_created", False)
