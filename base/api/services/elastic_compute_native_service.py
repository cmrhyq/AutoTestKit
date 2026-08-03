"""
弹性计算 Native K8s API 服务封装（特权接口 - Bearer + X-API-KEY + apikey 鉴权）

基于 auto_test_pro 的 auto-test/files/elastic-compute/native/*.jmx 转换：
- serviceaccount.jmx（3 个去重接口）

Native 类接口直接代理 K8s API Server，路径模式为：
  /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/{resource}

鉴权方式：Bearer Token + X-API-KEY + apikey 三重头。
- Bearer 通过 BaseService 的 auth_type='bearer' 承载于 session.headers（由 service_factory 从 TokenManager 注入）
- X-API-KEY + apikey 为静态头，通过 _get_native_headers() 在每次请求时补充
"""
import logging
from typing import Any, Dict, Optional, Tuple

from base import BaseService
from core.config import env_manager


def _get_native_headers() -> Dict[str, str]:
    """获取 Native K8s API 特权接口的补充请求头（不含 Authorization，由 session.headers 承载）。

    包含：
    - X-API-KEY: 特权 API Key
    - apikey: API 网关 Key
    """
    env = env_manager.get_config()
    return {
        "X-API-KEY": env.get("nativeXApiKey", "814bc561e79c079fc2356c8631bfd3ce"),
        "apikey": env.get("apiKey", ""),
    }


class ElasticComputeNativeService(BaseService):
    """
    弹性计算 Native K8s API 服务（特权接口）

    与 OpenAPI 类接口的区别：
    - 直接代理 K8s API Server
    - 使用 Bearer + X-API-KEY + apikey 三重鉴权
    - 路径前缀为 /elastic-compute/v2/k8s/clusters/{clusterId}/...
    - 响应格式为原生 K8s JSON（非 {code, data} 包装）
    - HTTP 状态码判断成功/失败（200=成功, 201=创建成功, 404=不存在）
    """

    def __init__(self, base_url: str, logger: logging.Logger = None, token: Optional[str] = None):
        """
        Args:
            base_url: API 基础 URL（必传，来自 config/env_*.yaml 的 apiBaseUrl）
            logger: 日志记录器
            token: Bearer Token（必传，由 service_factory 从 TokenManager 注入）

        Raises:
            ValueError: 如果 base_url 为空
        """
        if not base_url:
            raise ValueError(
                "base_url is required. "
                "Configure it in config/env_*.yaml (apiBaseUrl) "
                "and pass via fixture: api_env.get('apiBaseUrl')"
            )
        super().__init__(
            base_url=base_url,
            logger=logger,
            auth_type="bearer" if token else None,
            auth_credentials={"token": token} if token else None,
        )

    # ==================== ServiceAccount（serviceaccount.jmx）====================

    def get_service_account(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 ServiceAccount。

        对应 JMX：弹性计算_native_serviceaccount_查询指定ServiceAccount请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/serviceaccounts/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: ServiceAccount 名称

        Returns:
            Tuple[int, Dict]: (HTTP 状态码, 响应 JSON)
            状态码 200=存在, 404=不存在
        """
        self.logger.info(
            f"Get ServiceAccount: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/serviceaccounts/{name}"
        )
        full_url = self._build_url(url)
        try:
            resp = self.session.get(
                full_url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            self.logger.error(f"Get ServiceAccount failed: {e}")
            raise

    def create_service_account(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 ServiceAccount。

        对应 JMX：弹性计算_native_serviceaccount_创建ServiceAccount请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/serviceaccounts

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            payload: K8s ServiceAccount JSON 对象

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        self.logger.info(
            f"Create ServiceAccount: cluster={cluster_id}, ns={namespace}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/serviceaccounts"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_service_account(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 ServiceAccount。

        对应 JMX：弹性计算_native_serviceaccount_删除指定ServiceAccount请求
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/serviceaccounts/{name}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: ServiceAccount 名称

        Returns:
            响应 JSON（HTTP 200=删除成功）
        """
        self.logger.info(
            f"Delete ServiceAccount: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/serviceaccounts/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()
