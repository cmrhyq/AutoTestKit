"""
弹性计算 Native PVC 接口测试

转换自 JMeter 脚本: pvc-pv-api.jmx
测试内容：PersistentVolumeClaim 原生接口生命周期测试（查询、创建、删除）

注意：JMX 中仅包含 PVC 部分，没有 PV / update / list 接口。
"""
from typing import Any, Dict

import allure
import pytest

from base.api.services.elastic_compute_native_service import (
    ElasticComputeNativeService,
)
from core.log import get_logger
from core.reporting.allure_helper import AllureHelper

logger = get_logger(__name__)

HTTP_OK = 200
HTTP_CREATED = 201
HTTP_NOT_FOUND = 404


@pytest.mark.api
@pytest.mark.native
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Native接口")
@allure.story("PersistentVolumeClaim 原生接口")
class TestEcNativePvc:
    """
    对应 JMeter 脚本: pvc-pv-api.jmx
    线程组: Thread Group - PVC/PV API原生接口
    """

    TENANT = "tenant_admin"

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 PVC 测试所需的公共参数。"""
        return {
            "cluster_id": str(api_env.get("clusterId", "1")),
            "namespace": api_env.get("namespace", "test-admin"),
            "pvc_name": "test-pvc001",
            "paas_owner": api_env.get("user", "panji_probe"),
        }

    @staticmethod
    def _build_pvc_create_payload(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建 PVC 创建请求体。

        对应 JMX 中的 POST body。
        """
        return {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": params["pvc_name"],
                "labels": {
                    "operation-source": "api",
                    "paas-resource-category": "tenant-app",
                    "paas-owner": params["paas_owner"],
                    "paas-cluster-code": params["cluster_id"],
                },
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {
                    "requests": {"storage": "10Mi"},
                },
                "storageClassName": "demo-sss-001",
                "volumeMode": "Filesystem",
            },
        }

    @pytest.mark.dependency(name="pvc_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 PVC 并清理已有资源")
    @allure.description("查询指定 PVC 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_pvc_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 PVC，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        name = public_params["pvc_name"]

        with AllureHelper.api_test(native_service):
            get_http_code, _ = native_service.get_pvc(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code in (HTTP_OK, HTTP_NOT_FOUND), (
                f"查询 PVC 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HTTP_OK:
                native_service.delete_pvc(
                    cluster_id=cluster_id, namespace=namespace, name=name,
                )
                assert native_service.last_response.status_code == HTTP_OK, (
                    f"删除已存在的 PVC 失败, "
                    f"status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_pvc_created", False)

    @pytest.mark.dependency(name="pvc_create", depends=["pvc_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 PVC")
    @allure.description("创建 PVC 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_pvc(self, native_service, public_params, api_cache):
        """创建 PVC，断言创建成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]

        with AllureHelper.api_test(native_service):
            payload = self._build_pvc_create_payload(public_params)
            create_resp = native_service.create_pvc(
                cluster_id=cluster_id, namespace=namespace, payload=payload,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HTTP_CREATED, (
                f"创建 PVC 失败, 期望201, 实际: {create_http_code}, 响应: {create_resp}"
            )

            api_cache.set("ec_pvc_created", True)

    @pytest.mark.dependency(name="pvc_delete", depends=["pvc_create"])
    @pytest.mark.order(3)
    @allure.title("删除 PVC")
    @allure.description("删除创建的 PVC 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_pvc(self, native_service, public_params, api_cache):
        """删除 PVC，断言删除成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        name = public_params["pvc_name"]

        with AllureHelper.api_test(native_service):
            native_service.delete_pvc(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert native_service.last_response.status_code == HTTP_OK, (
                f"删除 PVC 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_pvc_created", False)
