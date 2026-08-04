"""
弹性计算 Native ServiceAccount 接口测试

转换自 JMeter 脚本: serviceaccount.jmx
测试内容：ServiceAccount 原生接口生命周期测试（查询、创建、删除）

注意：JMX 中仅包含 GET/POST/DELETE，没有 update / list 接口。
Service 层的 get_service_account / create_service_account / delete_service_account
在文件顶部已存在，直接复用。
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
@allure.story("ServiceAccount 原生接口")
class TestEcNativeServiceAccount:
    """
    对应 JMeter 脚本: serviceaccount.jmx
    线程组: Thread Group - serviceaccount
    """

    TENANT = "tenant_admin"

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 ServiceAccount 测试所需的公共参数。"""
        return {
            "cluster_id": str(api_env.get("clusterId", "1")),
            "namespace": api_env.get("namespace", "test-admin"),
            "name": "native-test-sa",
        }

    @staticmethod
    def _build_sa_create_payload(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建 ServiceAccount 创建请求体。

        对应 JMX 中的 POST body。结构最简单：仅 metadata.name。
        """
        return {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"name": params["name"]},
        }

    @pytest.mark.dependency(name="sa_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 ServiceAccount 并清理已有资源")
    @allure.description("查询指定 ServiceAccount 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_sa_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 ServiceAccount，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        name = public_params["name"]

        with AllureHelper.api_test(native_service):
            get_http_code, _ = native_service.get_service_account(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code in (HTTP_OK, HTTP_NOT_FOUND), (
                f"查询 ServiceAccount 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HTTP_OK:
                native_service.delete_service_account(
                    cluster_id=cluster_id, namespace=namespace, name=name,
                )
                assert native_service.last_response.status_code == HTTP_OK, (
                    f"删除已存在的 ServiceAccount 失败, "
                    f"status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_sa_created", False)

    @pytest.mark.dependency(name="sa_create", depends=["sa_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 ServiceAccount")
    @allure.description("创建 ServiceAccount 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_sa(self, native_service, public_params, api_cache):
        """创建 ServiceAccount，断言创建成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]

        with AllureHelper.api_test(native_service):
            payload = self._build_sa_create_payload(public_params)
            create_resp = native_service.create_service_account(
                cluster_id=cluster_id, namespace=namespace, payload=payload,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HTTP_CREATED, (
                f"创建 ServiceAccount 失败, 期望201, 实际: {create_http_code}, "
                f"响应: {create_resp}"
            )

            api_cache.set("ec_sa_created", True)

    @pytest.mark.dependency(name="sa_delete", depends=["sa_create"])
    @pytest.mark.order(3)
    @allure.title("删除 ServiceAccount")
    @allure.description("删除创建的 ServiceAccount 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_sa(self, native_service, public_params, api_cache):
        """删除 ServiceAccount，断言删除成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        name = public_params["name"]

        with AllureHelper.api_test(native_service):
            native_service.delete_service_account(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert native_service.last_response.status_code == HTTP_OK, (
                f"删除 ServiceAccount 失败, "
                f"status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_sa_created", False)
