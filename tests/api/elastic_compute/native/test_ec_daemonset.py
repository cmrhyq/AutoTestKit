"""
弹性计算 Native DaemonSet 接口测试

转换自 JMeter 脚本: daemonset.jmx
测试内容：DaemonSet 原生接口完成生命周期测试（查询、创建、列表、更新、删除）
"""
import json
import time
from typing import Any, Dict

import allure
import pytest

from base.api.entity import (
    ContainerPort,
    ContainerSpec,
    PaasLabels,
    PodTemplate,
    WorkloadPayload,
)
from base.api.services.elastic_compute_native_service import (
    ElasticComputeNativeService,
)
from core.log import get_logger
from core.reporting.allure_helper import AllureHelper
from core.constants import HttpStatus, Tenant, Timing

logger = get_logger(__name__)



@pytest.mark.api
@pytest.mark.native
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Native接口")
@allure.story("DaemonSet 原生接口")
class TestEcNativeDaemonset:
    """
    对应 JMeter 脚本: daemonset.jmx
    线程组: Thread Group - daemonset
    """

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 DaemonSet 测试所需的公共参数。"""
        return {
            "cluster_id": str(api_env.get("clusterId", "1")),
            "namespace": api_env.get("namespace", "test-admin"),
            "name": "native-test-nginx-ds",
            "paas_app_code": api_env.get("appCodeDaemonset", "test-app-ds"),
            "paas_env_code": api_env.get("paasEnvCode", "ENV1"),
            "paas_owner": api_env.get("user", "panji_probe"),
            "paas_plane_code": api_env.get("paasPlaneCode", "PLANE1"),
            "paas_tenant_code": api_env.get("paasTenantCode", "tenant-001"),
            "paas_unit_code": api_env.get("paasUnitCode", "TEST"),
            "image": api_env.get("nginxImageUrl", "hpe_containers/nginx:latest"),
        }

    @staticmethod
    def _paas_labels(params: Dict[str, Any]) -> PaasLabels:
        """根据 public_params 组装 PaasLabels 实体（12 字段）。"""
        return PaasLabels(
            paas_owner=params["paas_owner"],
            paas_cluster_code=params["cluster_id"],
            paas_app_code=params["paas_app_code"],
            paas_env_code=params["paas_env_code"],
            paas_plane_code=params["paas_plane_code"],
            paas_tenant_code=params["paas_tenant_code"],
            paas_unit_code=params["paas_unit_code"],
            paas_system_code=params["namespace"],
            paas_workload_name=params["name"],
        )

    @classmethod
    def _build_workload(
        cls,
        params: Dict[str, Any],
        *,
        container_port: int,
        extra_labels: Dict[str, str] | None = None,
    ) -> Dict[str, Any]:
        """
        使用 WorkloadPayload + PaasLabels + PodTemplate 组装 DaemonSet payload。

        DaemonSet 无 replicas 字段（每节点一个 Pod）。
        """
        name = params["name"]
        template_labels = {"name": name, "test": "deploy"}
        return WorkloadPayload(
            name=name,
            apiVersion="apps/v1",
            kind="DaemonSet",
            labels=cls._paas_labels(params).merged_with(extra_labels),
            match_labels=dict(template_labels),
            template=PodTemplate(
                labels=dict(template_labels),
                containers=[
                    ContainerSpec(
                        image=params["image"],
                        name="container0",
                        imagePullPolicy="Always",
                        ports=[ContainerPort(containerPort=container_port)],
                    )
                ],
            ),
        ).to_dict()

    @classmethod
    def _build_daemonset_create_payload(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建 DaemonSet 创建请求体。

        对应 JMX 中的 POST body（XML 实体还原后）。
        """
        return cls._build_workload(params, container_port=8080)

    @classmethod
    def _build_daemonset_update_payload(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建 DaemonSet 更新请求体。

        对应 JMX 中的 PUT body（XML 实体还原后）。
        区别：增加了 test: update 标签，containerPort 变为 8090。
        """
        return cls._build_workload(
            params,
            container_port=8090,
            extra_labels={"test": "update"},
        )

    # ==================== 生命周期测试（每接口一函数）====================

    @pytest.mark.dependency(name="daemonset_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 DaemonSet 并清理已有资源")
    @allure.description("查询指定 DaemonSet 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_daemonset_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 DaemonSet，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        name = public_params["name"]

        with AllureHelper.api_test(native_service):
            get_http_code, get_resp = native_service.get_daemonset(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 DaemonSet 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_daemonset(
                    cluster_id=cluster_id, namespace=namespace, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 DaemonSet 失败, status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_daemonset_created", False)

    @pytest.mark.dependency(name="daemonset_create", depends=["daemonset_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 DaemonSet")
    @allure.description("创建 DaemonSet 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_daemonset(self, native_service, public_params, api_cache):
        """创建 DaemonSet，断言创建成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]

        with AllureHelper.api_test(native_service):
            payload = self._build_daemonset_create_payload(public_params)
            create_resp = native_service.create_daemonset(
                cluster_id=cluster_id, namespace=namespace, payload=payload,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 DaemonSet 失败, 期望201, 实际: {create_http_code}, 响应: {create_resp}"
            )

            api_cache.set("ec_daemonset_created", True)

    @pytest.mark.dependency(name="daemonset_list", depends=["daemonset_create"])
    @pytest.mark.order(3)
    @allure.title("查询 DaemonSet 列表")
    @allure.description("按标签选择器查询 DaemonSet 列表，验证包含新创建的 DaemonSet")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_daemonsets(self, native_service, public_params):
        """查询 DaemonSet 列表，断言包含目标资源。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        name = public_params["name"]

        time.sleep(Timing.DS_CREATE_WAIT_SECONDS)

        with AllureHelper.api_test(native_service):
            list_resp = native_service.list_daemonsets(
                cluster_id=cluster_id,
                namespace=namespace,
                label_selector=f"paas-workload-name={name}",
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 DaemonSet 列表失败, status={native_service.last_response.status_code}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert f'"name":"{name}"' in resp_str or name in resp_str, (
                f"DaemonSet 列表未找到 {name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="daemonset_update", depends=["daemonset_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 DaemonSet")
    @allure.description("使用 PUT 方法全量更新 DaemonSet，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_daemonset(self, native_service, public_params):
        """PUT 全量更新 DaemonSet，断言更新成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        name = public_params["name"]

        with AllureHelper.api_test(native_service):
            payload = self._build_daemonset_update_payload(public_params)
            native_service.update_daemonset(
                cluster_id=cluster_id, namespace=namespace, name=name, payload=payload,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"更新 DaemonSet 失败, status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(name="daemonset_delete", depends=["daemonset_update"])
    @pytest.mark.order(5)
    @allure.title("删除 DaemonSet")
    @allure.description("删除创建的 DaemonSet 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_daemonset(self, native_service, public_params, api_cache):
        """删除 DaemonSet，断言删除成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        name = public_params["name"]

        with AllureHelper.api_test(native_service):
            native_service.delete_daemonset(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 DaemonSet 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_daemonset_created", False)
