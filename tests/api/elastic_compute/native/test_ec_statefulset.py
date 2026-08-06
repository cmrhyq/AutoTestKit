"""
弹性计算 Native StatefulSet 接口测试

转换自 JMeter 脚本: statefulset.jmx
测试内容：StatefulSet 原生接口完成生命周期测试（查询、创建、列表、更新、删除）
"""
import json
import time

import allure
import pytest

from base.api.entity.elastic_compute import StatefulSetNativePublicParams, WorkloadNativeEntity
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
@allure.story("StatefulSet 原生接口")
class TestEcNativeStatefulSet:
    """
    对应 JMeter 脚本: statefulset.jmx
    线程组: Thread Group - statefulset
    """

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> StatefulSetNativePublicParams:
        """提取 StatefulSet 测试所需的公共参数。"""
        return StatefulSetNativePublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            namespace=api_env.get("namespace", "test-admin"),
            name="native-test-app-sts",
            paas_app_code=api_env.get("appCodeSts", "test-app-sts"),
            paas_env_code=api_env.get("paasEnvCode", "ENV1"),
            paas_owner=api_env.get("user", "panji_probe"),
            paas_plane_code=api_env.get("paasPlaneCode", "PLANE1"),
            paas_tenant_code=api_env.get("paasTenantCode", "tenant-001"),
            paas_unit_code=api_env.get("paasUnitCode", "TEST"),
            image=api_env.get("nginxImageUrl", "hpe_containers/nginx:latest"),
            replicas=1,
        )

    @pytest.mark.dependency(name="sts_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 StatefulSet 并清理已有资源")
    @allure.description("查询指定 StatefulSet 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_sts_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 StatefulSet，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, _ = native_service.get_statefulset(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 StatefulSet 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_statefulset(
                    cluster_id=cluster_id, namespace=namespace, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 StatefulSet 失败, "
                    f"status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_sts_created", False)

    @pytest.mark.dependency(name="sts_create", depends=["sts_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 StatefulSet")
    @allure.description("创建 StatefulSet 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_sts(self, native_service, public_params, api_cache):
        """创建 StatefulSet，断言创建成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace

        with AllureHelper.api_test(native_service):
            workload = WorkloadNativeEntity(
                name=public_params.name,
                namespace=public_params.namespace,
                kind="StatefulSet",
                paas_app_code=public_params.paas_app_code,
                paas_env_code=public_params.paas_env_code,
                paas_owner=public_params.paas_owner,
                paas_plane_code=public_params.paas_plane_code,
                paas_tenant_code=public_params.paas_tenant_code,
                paas_unit_code=public_params.paas_unit_code,
                image=public_params.image,
                replicas=public_params.replicas,
            )
            create_resp = native_service.create_statefulset(
                cluster_id=cluster_id, namespace=namespace, workload=workload,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 StatefulSet 失败, 期望201, 实际: {create_http_code}, 响应: {create_resp}"
            )

            api_cache.set("ec_sts_created", True)

    @pytest.mark.dependency(name="sts_list", depends=["sts_create"])
    @pytest.mark.order(3)
    @allure.title("查询 StatefulSet 列表")
    @allure.description("按标签选择器查询 StatefulSet 列表，验证包含新创建的 StatefulSet")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_sts(self, native_service, public_params):
        """查询 StatefulSet 列表，断言包含目标资源。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        time.sleep(3)

        with AllureHelper.api_test(native_service):
            list_resp = native_service.list_statefulsets(
                cluster_id=cluster_id,
                namespace=namespace,
                label_selector=f"paas-workload-name={name}",
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 StatefulSet 列表失败, status={native_service.last_response.status_code}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert name in resp_str, (
                f"StatefulSet 列表未找到 {name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="sts_update", depends=["sts_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 StatefulSet")
    @allure.description("全量更新 StatefulSet（含 replicas 与 test 标签变更），验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_sts(self, native_service, public_params):
        """PUT 全量更新 StatefulSet，断言更新成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            workload = WorkloadNativeEntity(
                name=public_params.name,
                namespace=public_params.namespace,
                kind="StatefulSet",
                paas_app_code=public_params.paas_app_code,
                paas_env_code=public_params.paas_env_code,
                paas_owner=public_params.paas_owner,
                paas_plane_code=public_params.paas_plane_code,
                paas_tenant_code=public_params.paas_tenant_code,
                paas_unit_code=public_params.paas_unit_code,
                image=public_params.image,
                replicas=public_params.replicas + 1,
                container_port=8090,
                extra_labels={"test": "update"},
            )
            native_service.update_statefulset(
                cluster_id=cluster_id, namespace=namespace, name=name, workload=workload,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"更新 StatefulSet 失败, status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(name="sts_delete", depends=["sts_update"])
    @pytest.mark.order(5)
    @allure.title("删除 StatefulSet")
    @allure.description("删除创建的 StatefulSet 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_sts(self, native_service, public_params, api_cache):
        """删除 StatefulSet，断言删除成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            native_service.delete_statefulset(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 StatefulSet 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_sts_created", False)
