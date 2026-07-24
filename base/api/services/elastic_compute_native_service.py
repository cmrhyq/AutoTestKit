"""
弹性计算 Native K8s API 服务封装（特权接口 - Bearer + X-API-KEY + apikey 鉴权）

基于 auto_test_pro 的 auto-test/files/elastic-compute/native/*.jmx 转换：
- serviceaccount.jmx（3 个去重接口）

Native 类接口直接代理 K8s API Server，路径模式为：
  /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/{resource}

鉴权方式：Bearer Token + X-API-KEY + apikey 三重头。
所有敏感值从 DataCache 和 env yaml 读取，杜绝硬编码。
"""
import logging
from typing import Any, Dict, Tuple

from base import BaseService
from core import DataCache
from core.config import env_manager


def _get_native_headers() -> Dict[str, str]:
    """获取 Native K8s API 特权接口的默认请求头。

    包含：
    - Authorization: Bearer token（Portal 登录后的 token）
    - X-API-KEY: 特权 API Key
    - apikey: API 网关 Key
    """
    cache = DataCache.get_instance()
    env = env_manager.get_config()
    return {
        "Authorization": cache.get("token"),
        "X-API-KEY": env.get("nativeXApiKey", "814bc561e79c079fc2356c8631bfd3ce"),
        "apikey": env.get("apiKey", ""),
    }


class PanJiElasticComputeNativeService(BaseService):
    """
    弹性计算 Native K8s API 服务（特权接口）

    与 OpenAPI 类接口的区别：
    - 直接代理 K8s API Server
    - 使用 Bearer + X-API-KEY + apikey 三重鉴权
    - 路径前缀为 /elastic-compute/v2/k8s/clusters/{clusterId}/...
    - 响应格式为原生 K8s JSON（非 {code, data} 包装）
    - HTTP 状态码判断成功/失败（200=成功, 201=创建成功, 404=不存在）
    """

    DEFAULT_BASE_URL = "http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030"

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        super().__init__(base_url=base_url or self.DEFAULT_BASE_URL, logger=logger)

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
