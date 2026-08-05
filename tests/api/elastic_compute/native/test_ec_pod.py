"""
弹性计算 Native Pod 接口测试

转换自 JMeter 脚本: pod.jmx
测试内容：Pod 原生接口生命周期测试（查询、创建、列表、日志、删除）

注意：Pod 无 PUT 更新接口（K8s 中 Pod 是不可变的，只能重建）。
      本测试覆盖 5 个接口：GET, CREATE, LIST, LOG, DELETE。
"""
import json
import time
from typing import Any, Dict

import allure
import pytest

from base.api.entity import ContainerPort, ContainerSpec, PaasLabels, PodPayload
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
@allure.story("Pod 原生接口")
class TestEcNativePod:
    """
    对应 JMeter 脚本: pod.jmx
    线程组: Thread Group - pod
    """

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Pod 测试所需的公共参数。"""
        return {
            "cluster_id": str(api_env.get("clusterId", "1")),
            "namespace": api_env.get("namespace", "test-admin"),
            "name": "native-test-pod-nginx",
            "paas_app_code": api_env.get("appCodePod", "test-app-pod"),
            "paas_env_code": api_env.get("paasEnvCode", "ENV1"),
            "paas_owner": api_env.get("user", "panji_probe"),
            "paas_plane_code": api_env.get("paasPlaneCode", "PLANE1"),
            "paas_tenant_code": api_env.get("paasTenantCode", "tenant-001"),
            "paas_unit_code": api_env.get("paasUnitCode", "TEST"),
            "image": api_env.get("nginxImageUrl", "hpe_containers/nginx:latest"),
        }

    @staticmethod
    def _build_pod_create_payload(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建 Pod 创建请求体。

        对应 JMX 中的 POST body（XML 实体还原后）。
        除 PaasLabels 12 字段外，Pod payload 还额外携带 `kind: Pod` 标签
        以便按 kind 过滤查询。
        """
        name = params["name"]
        labels = PaasLabels(
            paas_owner=params["paas_owner"],
            paas_cluster_code=params["cluster_id"],
            paas_app_code=params["paas_app_code"],
            paas_env_code=params["paas_env_code"],
            paas_plane_code=params["paas_plane_code"],
            paas_tenant_code=params["paas_tenant_code"],
            paas_unit_code=params["paas_unit_code"],
            paas_system_code=params["namespace"],
            paas_workload_name=name,
        ).merged_with({"kind": "Pod"})
        return PodPayload(
            name=name,
            labels=labels,
            containers=[
                ContainerSpec(
                    image=params["image"],
                    name="container0",
                    ports=[ContainerPort(containerPort=8080)],
                )
            ],
        ).to_dict()

    # ==================== 生命周期测试（每接口一函数）====================

    @pytest.mark.dependency(name="pod_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 Pod 并清理已有资源")
    @allure.description("查询指定 Pod 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_pod_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 Pod，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        name = public_params["name"]

        with AllureHelper.api_test(native_service):
            get_http_code, _ = native_service.get_pod(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 Pod 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_pod(
                    cluster_id=cluster_id, namespace=namespace, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 Pod 失败,"
                    f" status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_pod_created", False)

    @pytest.mark.dependency(name="pod_create", depends=["pod_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 Pod")
    @allure.description("创建 Pod 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_pod(self, native_service, public_params, api_cache):
        """创建 Pod，断言创建成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]

        with AllureHelper.api_test(native_service):
            payload = self._build_pod_create_payload(public_params)
            create_resp = native_service.create_pod(
                cluster_id=cluster_id, namespace=namespace, payload=payload,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 Pod 失败, 期望201, 实际: {create_http_code}, 响应: {create_resp}"
            )

            api_cache.set("ec_pod_created", True)

    @pytest.mark.dependency(name="pod_list", depends=["pod_create"])
    @pytest.mark.order(3)
    @allure.title("查询 Pod 列表")
    @allure.description("按标签选择器查询 Pod 列表，验证包含新创建的 Pod")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_pods(self, native_service, public_params):
        """查询 Pod 列表，断言包含目标资源。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        name = public_params["name"]

        time.sleep(5)

        with AllureHelper.api_test(native_service):
            list_resp = native_service.list_pods(
                cluster_id=cluster_id,
                namespace=namespace,
                label_selector=f"paas-workload-name={name},kind=Pod",
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 Pod 列表失败,"
                f" status={native_service.last_response.status_code}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert f'"name":"{name}"' in resp_str or name in resp_str, (
                f"Pod 列表未找到 {name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="pod_log", depends=["pod_create"])
    @pytest.mark.order(4)
    @allure.title("查询 Pod 日志")
    @allure.description("查询指定 Pod 的 container0 容器日志，验证返回 200")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_pod_log(self, native_service, public_params):
        """
        查询 Pod 日志。

        对应 JMX：弹性计算_native_pod_查询指定Pod日志请求
        注意：Pod 可能还未就绪，日志可能为空，但只要 HTTP 200 即通过。
        """
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        name = public_params["name"]

        with AllureHelper.api_test(native_service):
            log_text = native_service.get_pod_log(
                cluster_id=cluster_id,
                namespace=namespace,
                name=name,
                container="container0",
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 Pod 日志失败,"
                f" status={native_service.last_response.status_code}"
            )
            assert log_text is not None, "Pod 日志响应体为 None"
            logger.info(f"Pod log length: {len(log_text)} chars")

    @pytest.mark.dependency(name="pod_delete", depends=["pod_log"])
    @pytest.mark.order(5)
    @allure.title("删除 Pod")
    @allure.description("删除创建的 Pod 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_pod(self, native_service, public_params, api_cache):
        """删除 Pod，断言删除成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        name = public_params["name"]

        with AllureHelper.api_test(native_service):
            native_service.delete_pod(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 Pod 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_pod_created", False)
