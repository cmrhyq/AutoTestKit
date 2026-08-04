"""
弹性计算 Native K8s API 服务封装（特权接口 - Bearer + X-API-KEY + apikey 鉴权）

基于 auto_test_pro 的 auto-test/files/elastic-compute/native/*.jmx 转换：
- serviceaccount.jmx（3 个去重接口）
- daemonset.jmx（4 个去重接口：查询/创建/更新/删除）
- clusterrolebinding.jmx（3 个去重接口：查询/创建/删除）
- configmap.jmx（5 个去重接口：查询/创建/列表/更新/删除）
- crd.jmx（4 个去重接口：查询/创建/列表/删除）

Native 类接口直接代理 K8s API Server，路径模式为：
  /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/{resource}
  /elastic-compute/v2/k8s/clusters/{clusterId}/apis/{apiGroup}/{version}/...

鉴权方式：Bearer Token + X-API-KEY + apikey 三重头。
- Bearer 通过 BaseService 的 auth_type='bearer' 承载于 session.headers（由 service_factory 从 TokenManager 注入）
- X-API-KEY + apikey 为静态头，通过 _get_native_headers() 在每次请求时补充
"""
from typing import Any, Dict, Optional, Tuple

from base import BaseService
from core import get_logger

logger = get_logger(__name__)


def _get_native_headers() -> Dict[str, str]:
    """获取 Native K8s API 特权接口的补充请求头（不含 Authorization，由 session.headers 承载）。

    包含：
    - X-API-KEY: 特权 API Key
    - apikey: API 网关 Key
    """
    return {
        "X-API-KEY": "186cc9f603c4fed3742ff4160f2beec2",
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

    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        Args:
            base_url: API 基础 URL（必传，来自 config/env_*.yaml 的 apiBaseUrl）
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
            auth_type="api_key",
            auth_credentials={
                "api_key": "186cc9f603c4fed3742ff4160f2beec2",
                "header_name": "apikey"
            },
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
        logger.info(
            f"Get ServiceAccount: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/serviceaccounts/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get ServiceAccount failed: {e}")
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
        logger.info(
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
        logger.info(
            f"Delete ServiceAccount: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/serviceaccounts/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    # ==================== DaemonSet（daemonset.jmx）====================

    def get_daemonset(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 DaemonSet。

        对应 JMX：弹性计算_native_daemonset_查询指定DaemonSet请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/daemonsets/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: DaemonSet 名称

        Returns:
            Tuple[int, Dict]: (HTTP 状态码, 响应 JSON)
        """
        logger.info(
            f"Get DaemonSet: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/daemonsets/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get DaemonSet failed: {e}")
            raise

    def create_daemonset(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 DaemonSet。

        对应 JMX：弹性计算_native_daemonset_创建DaemonSet请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/daemonsets

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            payload: K8s DaemonSet JSON 对象

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create DaemonSet: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/daemonsets"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_daemonset(
        self, cluster_id: str, namespace: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 DaemonSet。

        对应 JMX：弹性计算_native_daemonset_更新指定DaemonSet
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/daemonsets/{name}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: DaemonSet 名称
            payload: K8s DaemonSet JSON 对象（完整）

        Returns:
            响应 JSON（HTTP 200=更新成功）
        """
        logger.info(
            f"Update DaemonSet: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/daemonsets/{name}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_daemonset(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 DaemonSet。

        对应 JMX：弹性计算_native_daemonset_删除指定DaemonSet请求
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/daemonsets/{name}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: DaemonSet 名称

        Returns:
            响应 JSON（HTTP 200=删除成功）
        """
        logger.info(
            f"Delete DaemonSet: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/daemonsets/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def list_daemonsets(
        self, cluster_id: str, namespace: str, label_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询 DaemonSet 列表。

        对应 JMX：弹性计算_native_daemonset_查询DaemonSet列表请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/daemonsets

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            label_selector: 标签选择器（如 paas-workload-name=xxx）

        Returns:
            响应 JSON（HTTP 200=查询成功）
        """
        logger.info(
            f"List DaemonSets: cluster={cluster_id}, ns={namespace}, selector={label_selector}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/daemonsets"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), params=params, timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List DaemonSets failed: {e}")
            raise

    # ==================== ClusterRoleBinding（clusterrolebinding.jmx）====================

    def get_cluster_role_binding(
        self, cluster_id: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 ClusterRoleBinding。

        对应 JMX：弹性计算_native_clusterrolebinding_查询指定ClusterRoleBinding请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/rbac.authorization.k8s.io/v1/clusterrolebindings/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。

        Args:
            cluster_id: 集群 ID
            name: ClusterRoleBinding 名称

        Returns:
            Tuple[int, Dict]: (HTTP 状态码, 响应 JSON)
        """
        logger.info(f"Get ClusterRoleBinding: cluster={cluster_id}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/rbac.authorization.k8s.io/v1/clusterrolebindings/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get ClusterRoleBinding failed: {e}")
            raise

    def create_cluster_role_binding(
        self, cluster_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 ClusterRoleBinding。

        对应 JMX：弹性计算_native_clusterrolebinding_创建ClusterRoleBinding请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/rbac.authorization.k8s.io/v1/clusterrolebindings

        Args:
            cluster_id: 集群 ID
            payload: K8s ClusterRoleBinding JSON 对象

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create ClusterRoleBinding: cluster={cluster_id}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/rbac.authorization.k8s.io/v1/clusterrolebindings"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_cluster_role_binding(
        self, cluster_id: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 ClusterRoleBinding。

        对应 JMX：弹性计算_native_clusterrolebinding_删除指定ClusterRoleBinding
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/rbac.authorization.k8s.io/v1/clusterrolebindings/{name}

        Args:
            cluster_id: 集群 ID
            name: ClusterRoleBinding 名称

        Returns:
            响应 JSON（HTTP 200=删除成功）
        """
        logger.info(f"Delete ClusterRoleBinding: cluster={cluster_id}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/rbac.authorization.k8s.io/v1/clusterrolebindings/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    # ==================== ConfigMap - Native（configmap.jmx）====================

    def get_native_configmap(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 ConfigMap（Native 接口）。

        对应 JMX：弹性计算_native_configmap_查询指定ConfigMap请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/configmaps/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: ConfigMap 名称

        Returns:
            Tuple[int, Dict]: (HTTP 状态码, 响应 JSON)
        """
        logger.info(
            f"Get Native ConfigMap: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/configmaps/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get Native ConfigMap failed: {e}")
            raise

    def create_native_configmap(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 ConfigMap（Native 接口）。

        对应 JMX：弹性计算_native_configmap_创建ConfigMap请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/configmaps

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            payload: K8s ConfigMap JSON 对象

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create Native ConfigMap: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/configmaps"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_native_configmap(
        self, cluster_id: str, namespace: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新 ConfigMap（Native 接口）。

        对应 JMX：弹性计算_native_configmap_更新指定ConfigMap
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/configmaps/{name}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: ConfigMap 名称
            payload: K8s ConfigMap JSON 对象（完整）

        Returns:
            响应 JSON（HTTP 200=更新成功）
        """
        logger.info(
            f"Update Native ConfigMap: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/configmaps/{name}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_native_configmap(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 ConfigMap（Native 接口）。

        对应 JMX：弹性计算_native_configmap_删除指定ConfigMap
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/configmaps/{name}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: ConfigMap 名称

        Returns:
            响应 JSON（HTTP 200=删除成功）
        """
        logger.info(
            f"Delete Native ConfigMap: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/configmaps/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def list_native_configmaps(
        self, cluster_id: str, namespace: str, label_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询 ConfigMap 列表（Native 接口）。

        对应 JMX：弹性计算_native_configmap_查询ConfigMap列表请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/configmaps

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            label_selector: 标签选择器（如 name=xxx）

        Returns:
            响应 JSON（HTTP 200=查询成功）
        """
        logger.info(
            f"List Native ConfigMaps: cluster={cluster_id}, ns={namespace}, selector={label_selector}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/configmaps"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), params=params, timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List Native ConfigMaps failed: {e}")
            raise

    # ==================== CRD（crd.jmx）====================

    def get_crd(
        self, cluster_id: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 CustomResourceDefinition。

        对应 JMX：弹性计算_native_crd_查询指定CustomResourceDefinition请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apiextensions.k8s.io/v1/customresourcedefinitions/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。

        Args:
            cluster_id: 集群 ID
            name: CRD 名称

        Returns:
            Tuple[int, Dict]: (HTTP 状态码, 响应 JSON)
        """
        logger.info(f"Get CRD: cluster={cluster_id}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apiextensions.k8s.io/v1/customresourcedefinitions/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get CRD failed: {e}")
            raise

    def create_crd(
        self, cluster_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 CustomResourceDefinition。

        对应 JMX：弹性计算_native_crd_创建CustomResourceDefinition请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apiextensions.k8s.io/v1/customresourcedefinitions

        Args:
            cluster_id: 集群 ID
            payload: K8s CRD JSON 对象

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create CRD: cluster={cluster_id}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apiextensions.k8s.io/v1/customresourcedefinitions"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_crd(
        self, cluster_id: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 CustomResourceDefinition。

        对应 JMX：弹性计算_native_crd_删除指定CustomResourceDefinition
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apiextensions.k8s.io/v1/customresourcedefinitions/{name}

        Args:
            cluster_id: 集群 ID
            name: CRD 名称

        Returns:
            响应 JSON（HTTP 200=删除成功）
        """
        logger.info(f"Delete CRD: cluster={cluster_id}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apiextensions.k8s.io/v1/customresourcedefinitions/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def list_crds(
        self, cluster_id: str, label_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询 CustomResourceDefinition 列表。

        对应 JMX：弹性计算_native_crd_查询CustomResourceDefinition列表请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apiextensions.k8s.io/v1/customresourcedefinitions

        Args:
            cluster_id: 集群 ID
            label_selector: 标签选择器（如 name=xxx,test=crd）

        Returns:
            响应 JSON（HTTP 200=查询成功）
        """
        logger.info(f"List CRDs: cluster={cluster_id}, selector={label_selector}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apiextensions.k8s.io/v1/customresourcedefinitions"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), params=params, timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List CRDs failed: {e}")
            raise

    # ==================== Job（job.jmx）====================

    def get_job(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Job。

        对应 JMX：弹性计算_native_job_查询指定Job请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/batch/v1/namespaces/{namespace}/jobs/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Job 名称

        Returns:
            Tuple[int, Dict]: (HTTP 状态码, 响应 JSON)
        """
        logger.info(f"Get Job: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/batch/v1/namespaces/{namespace}/jobs/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get Job failed: {e}")
            raise

    def create_job(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 Job。

        对应 JMX：弹性计算_native_job_创建Job请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/batch/v1/namespaces/{namespace}/jobs

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            payload: K8s Job JSON 对象

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create Job: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/batch/v1/namespaces/{namespace}/jobs"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_job(
        self, cluster_id: str, namespace: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Job。

        对应 JMX：弹性计算_native_job_更新指定Job
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/batch/v1/namespaces/{namespace}/jobs/{name}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Job 名称
            payload: K8s Job JSON 对象（完整）

        Returns:
            响应 JSON（HTTP 200=更新成功）
        """
        logger.info(f"Update Job: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/batch/v1/namespaces/{namespace}/jobs/{name}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_job(
        self,
        cluster_id: str,
        namespace: str,
        name: str,
        propagation_policy: str = "Background",
    ) -> Dict[str, Any]:
        """
        删除指定 Job。

        对应 JMX：弹性计算_native_job_删除指定Job请求
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/batch/v1/namespaces/{namespace}/jobs/{name}

        JMX 中 DELETE 携带请求体 {"propagationPolicy": "Background"} 以级联删除关联 Pod。

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Job 名称
            propagation_policy: 传播策略（Background/Foreground/Orphan）

        Returns:
            响应 JSON（HTTP 200=删除成功）
        """
        logger.info(f"Delete Job: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/batch/v1/namespaces/{namespace}/jobs/{name}"
        )
        resp = self.delete(
            endpoint=url,
            json={"propagationPolicy": propagation_policy},
            headers=_get_native_headers(),
        )
        return resp.json()

    def list_jobs(
        self, cluster_id: str, namespace: str, label_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询 Job 列表。

        对应 JMX：弹性计算_native_job_查询Job列表请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/batch/v1/namespaces/{namespace}/jobs

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            label_selector: 标签选择器（如 paas-workload-name=xxx）

        Returns:
            响应 JSON（HTTP 200=查询成功）
        """
        logger.info(
            f"List Jobs: cluster={cluster_id}, ns={namespace}, selector={label_selector}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/batch/v1/namespaces/{namespace}/jobs"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), params=params, timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List Jobs failed: {e}")
            raise

    # ==================== Deployment（deployment.jmx）====================

    def get_deployment(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Deployment。

        对应 JMX：弹性计算_native_deployment_查询指定Deployment请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/deployments/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Deployment 名称

        Returns:
            Tuple[int, Dict]: (HTTP 状态码, 响应 JSON)
        """
        logger.info(
            f"Get Deployment: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/deployments/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get Deployment failed: {e}")
            raise

    def create_deployment(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 Deployment。

        对应 JMX：弹性计算_native_deployment_创建Deployment请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/deployments

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            payload: K8s Deployment JSON 对象

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create Deployment: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/deployments"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_deployment(
        self, cluster_id: str, namespace: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Deployment。

        对应 JMX：弹性计算_native_deployment_更新指定Deployment
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/deployments/{name}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Deployment 名称
            payload: K8s Deployment JSON 对象（完整）

        Returns:
            响应 JSON（HTTP 200=更新成功）
        """
        logger.info(
            f"Update Deployment: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/deployments/{name}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_deployment(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Deployment。

        对应 JMX：弹性计算_native_deployment_删除指定Deployment
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/deployments/{name}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Deployment 名称

        Returns:
            响应 JSON（HTTP 200=删除成功）
        """
        logger.info(
            f"Delete Deployment: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/deployments/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def list_deployments(
        self, cluster_id: str, namespace: str, label_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询 Deployment 列表。

        对应 JMX：弹性计算_native_deployment_查询Deployment列表请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/deployments

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            label_selector: 标签选择器（如 paas-workload-name=xxx）

        Returns:
            响应 JSON（HTTP 200=查询成功）
        """
        logger.info(
            f"List Deployments: cluster={cluster_id}, ns={namespace}, selector={label_selector}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/deployments"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), params=params, timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List Deployments failed: {e}")
            raise

    # ==================== HorizontalPodAutoscaler（hpa.jmx）====================

    def get_native_hpa(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 HorizontalPodAutoscaler（Native 接口）。

        对应 JMX：弹性计算_native_hpa_查询指定HorizontalPodAutoscaler请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: HPA 名称

        Returns:
            Tuple[int, Dict]: (HTTP 状态码, 响应 JSON)
        """
        logger.info(
            f"Get Native HPA: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get Native HPA failed: {e}")
            raise

    def create_native_hpa(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 HorizontalPodAutoscaler（Native 接口）。

        对应 JMX：弹性计算_native_hpa_创建HorizontalPodAutoscaler请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            payload: K8s HPA JSON 对象

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create Native HPA: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_native_hpa(
        self, cluster_id: str, namespace: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 HorizontalPodAutoscaler（Native 接口）。

        对应 JMX：弹性计算_native_hpa_更新指定HorizontalPodAutoscaler
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers/{name}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: HPA 名称
            payload: K8s HPA JSON 对象（完整）

        Returns:
            响应 JSON（HTTP 200=更新成功）
        """
        logger.info(
            f"Update Native HPA: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers/{name}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_native_hpa(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 HorizontalPodAutoscaler（Native 接口）。

        对应 JMX：弹性计算_native_hpa_删除指定HorizontalPodAutoscaler
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers/{name}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: HPA 名称

        Returns:
            响应 JSON（HTTP 200=删除成功）
        """
        logger.info(
            f"Delete Native HPA: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def list_native_hpas(
        self, cluster_id: str, namespace: str, label_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询 HorizontalPodAutoscaler 列表（Native 接口）。

        对应 JMX：弹性计算_native_hpa_查询HorizontalPodAutoscaler列表请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            label_selector: 标签选择器（如 name=xxx）

        Returns:
            响应 JSON（HTTP 200=查询成功）
        """
        logger.info(
            f"List Native HPAs: cluster={cluster_id}, ns={namespace}, selector={label_selector}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), params=params, timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List Native HPAs failed: {e}")
            raise

    # ==================== Ingress（ingress-api.jmx）====================

    def get_ingress(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Ingress。

        对应 JMX：弹性计算_native_ingress-api_查询Ingress
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Ingress 名称

        Returns:
            Tuple[int, Dict]: (HTTP 状态码, 响应 JSON)
        """
        logger.info(f"Get Ingress: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get Ingress failed: {e}")
            raise

    def create_ingress(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 Ingress。

        对应 JMX：弹性计算_native_ingress-api_创建Ingress
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            payload: K8s Ingress JSON 对象

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create Ingress: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_ingress(
        self, cluster_id: str, namespace: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Ingress。

        对应 JMX：弹性计算_native_ingress-api_更新Ingress
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses/{name}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Ingress 名称
            payload: K8s Ingress JSON 对象（完整）

        Returns:
            响应 JSON（HTTP 200=更新成功）
        """
        logger.info(
            f"Update Ingress: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses/{name}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_ingress(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Ingress。

        对应 JMX：弹性计算_native_ingress-api_删除Ingress
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses/{name}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Ingress 名称

        Returns:
            响应 JSON（HTTP 200=删除成功）
        """
        logger.info(
            f"Delete Ingress: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def list_ingresses(
        self, cluster_id: str, namespace: str, label_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询 Ingress 列表。

        对应 JMX：弹性计算_native_ingress-api_查询Ingress list
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            label_selector: 标签选择器（可选）

        Returns:
            响应 JSON（HTTP 200=查询成功）
        """
        logger.info(
            f"List Ingresses: cluster={cluster_id}, ns={namespace}, selector={label_selector}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), params=params, timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List Ingresses failed: {e}")
            raise

    # ==================== PriorityClass（priorityclass.jmx）====================

    def get_priority_class(
        self, cluster_id: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 PriorityClass（cluster-scoped）。

        对应 JMX：弹性计算_native_priorityclass_查询指定PriorityClass请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/scheduling.k8s.io/v1/priorityclasses/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。

        Args:
            cluster_id: 集群 ID
            name: PriorityClass 名称

        Returns:
            Tuple[int, Dict]: (HTTP 状态码, 响应 JSON)
        """
        logger.info(f"Get PriorityClass: cluster={cluster_id}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/scheduling.k8s.io/v1/priorityclasses/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get PriorityClass failed: {e}")
            raise

    def create_priority_class(
        self, cluster_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 PriorityClass。

        对应 JMX：弹性计算_native_priorityclass_创建PriorityClass请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/scheduling.k8s.io/v1/priorityclasses

        Args:
            cluster_id: 集群 ID
            payload: K8s PriorityClass JSON 对象

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create PriorityClass: cluster={cluster_id}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/scheduling.k8s.io/v1/priorityclasses"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_priority_class(
        self, cluster_id: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 PriorityClass。

        对应 JMX：弹性计算_native_priorityclass_更新指定PriorityClass
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/scheduling.k8s.io/v1/priorityclasses/{name}

        Args:
            cluster_id: 集群 ID
            name: PriorityClass 名称
            payload: K8s PriorityClass JSON 对象（完整）

        Returns:
            响应 JSON（HTTP 200=更新成功）
        """
        logger.info(f"Update PriorityClass: cluster={cluster_id}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/scheduling.k8s.io/v1/priorityclasses/{name}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_priority_class(
        self, cluster_id: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 PriorityClass。

        对应 JMX：弹性计算_native_priorityclass_删除指定PriorityClass
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/scheduling.k8s.io/v1/priorityclasses/{name}

        Args:
            cluster_id: 集群 ID
            name: PriorityClass 名称

        Returns:
            响应 JSON（HTTP 200=删除成功）
        """
        logger.info(f"Delete PriorityClass: cluster={cluster_id}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/scheduling.k8s.io/v1/priorityclasses/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    # ==================== Namespace（namespace-api.jmx）====================

    def get_namespace(
        self, cluster_id: str, namespace: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Namespace。

        对应 JMX：弹性计算_native_namespace-api_查询namespace
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。
        """
        logger.info(f"Get Namespace: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get Namespace failed: {e}")
            raise

    def create_namespace(
        self, cluster_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 Namespace。

        对应 JMX：弹性计算_native_namespace-api_创建namespace
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces
        """
        logger.info(f"Create Namespace: cluster={cluster_id}")
        url = f"/elastic-compute/v2/k8s/clusters/{cluster_id}/api/v1/namespaces"
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_namespace(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Namespace。

        对应 JMX：弹性计算_native_namespace-api_更新namespace
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}
        """
        logger.info(f"Update Namespace: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_namespace(
        self, cluster_id: str, namespace: str
    ) -> Dict[str, Any]:
        """
        删除指定 Namespace。

        对应 JMX：弹性计算_native_namespace-api_删除namespace
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}
        """
        logger.info(f"Delete Namespace: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def list_namespaces(self, cluster_id: str) -> Dict[str, Any]:
        """
        查询 Namespace 列表。

        对应 JMX：弹性计算_native_namespace-api_查询namespace list
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces
        """
        logger.info(f"List Namespaces: cluster={cluster_id}")
        url = f"/elastic-compute/v2/k8s/clusters/{cluster_id}/api/v1/namespaces"
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List Namespaces failed: {e}")
            raise

    def get_namespace_events(
        self, cluster_id: str, namespace: str
    ) -> Dict[str, Any]:
        """
        查询指定 Namespace 下的 Events。

        对应 JMX：弹性计算_native_namespace-api_获取namespace events
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/events
        """
        logger.info(f"Get Namespace Events: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/events"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"Get Namespace Events failed: {e}")
            raise

    # ==================== ResourceQuota（namespace-api.jmx）====================

    def get_resource_quota(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        查询指定 ResourceQuota。

        对应 JMX：弹性计算_native_namespace-api_获取资源配额（ResourceQuota）信息
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/resourcequotas/{name}
        """
        logger.info(
            f"Get ResourceQuota: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/resourcequotas/{name}"
        )
        resp = self.get(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def create_resource_quota(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 ResourceQuota。

        对应 JMX：弹性计算_native_namespace-api_创建资源配额（ResourceQuota）
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/resourcequotas
        """
        logger.info(f"Create ResourceQuota: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/resourcequotas"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_resource_quota(
        self, cluster_id: str, namespace: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 ResourceQuota。

        对应 JMX：弹性计算_native_namespace-api_更新资源配额（ResourceQuota）设置
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/resourcequotas/{name}
        """
        logger.info(
            f"Update ResourceQuota: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/resourcequotas/{name}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    # ==================== LimitRange（namespace-api.jmx）====================

    def get_limit_range(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        查询指定 LimitRange。

        对应 JMX：弹性计算_native_namespace-api_获取资源限制（LimitRange）信息
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/limitranges/{name}
        """
        logger.info(
            f"Get LimitRange: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/limitranges/{name}"
        )
        resp = self.get(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def create_limit_range(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 LimitRange。

        对应 JMX：弹性计算_native_namespace-api_创建资源限制（LimitRange）
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/limitranges
        """
        logger.info(f"Create LimitRange: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/limitranges"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_limit_range(
        self, cluster_id: str, namespace: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 LimitRange。

        对应 JMX：弹性计算_native_namespace-api_更新资源限制（LimitRange）设置
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/limitranges/{name}
        """
        logger.info(
            f"Update LimitRange: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/limitranges/{name}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    # ==================== Node（node-api.jmx）====================

    def list_nodes(self, cluster_id: str) -> Dict[str, Any]:
        """
        查询 Node 列表。

        对应 JMX：弹性计算_native_node-api_查询node list
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/nodes
        """
        logger.info(f"List Nodes: cluster={cluster_id}")
        url = f"/elastic-compute/v2/k8s/clusters/{cluster_id}/api/v1/nodes"
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List Nodes failed: {e}")
            raise

    def get_node(self, cluster_id: str, name: str) -> Dict[str, Any]:
        """
        查询指定 Node。

        对应 JMX：弹性计算_native_node-api_查询node
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/nodes/{name}
        """
        logger.info(f"Get Node: cluster={cluster_id}, name={name}")
        url = f"/elastic-compute/v2/k8s/clusters/{cluster_id}/api/v1/nodes/{name}"
        resp = self.get(endpoint=url, headers=_get_native_headers())
        return resp.json()

    # ==================== Pod（pod.jmx）====================

    def get_pod(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Pod。

        对应 JMX：弹性计算_native_pod_查询指定Pod请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/pods/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。
        """
        logger.info(f"Get Pod: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/pods/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get Pod failed: {e}")
            raise

    def create_pod(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 Pod。

        对应 JMX：弹性计算_native_pod_创建Pod请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/pods
        """
        logger.info(f"Create Pod: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/pods"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_pod(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Pod。

        对应 JMX：弹性计算_native_pod_删除指定Pod请求
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/pods/{name}
        """
        logger.info(f"Delete Pod: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/pods/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def list_pods(
        self, cluster_id: str, namespace: str, label_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询 Pod 列表。

        对应 JMX：弹性计算_native_pod_查询Pod列表请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/pods
        """
        logger.info(
            f"List Pods: cluster={cluster_id}, ns={namespace}, selector={label_selector}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/pods"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        try:
            resp = self.session.get(
                url,
                headers=_get_native_headers(),
                params=params,
                timeout=self.timeout,
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List Pods failed: {e}")
            raise

    def get_pod_log(
        self,
        cluster_id: str,
        namespace: str,
        name: str,
        container: Optional[str] = None,
    ) -> str:
        """
        查询指定 Pod 的日志。

        对应 JMX：弹性计算_native_pod_查询指定Pod日志请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/pods/{name}/log

        注意：响应为纯文本日志（非 JSON），返回字符串。
        """
        logger.info(
            f"Get Pod Log: cluster={cluster_id}, ns={namespace}, name={name},"
            f" container={container}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/pods/{name}/log"
        )
        params = {}
        if container:
            params["container"] = container
        try:
            resp = self.session.get(
                url,
                headers=_get_native_headers(),
                params=params,
                timeout=self.timeout,
            )
            self.last_response = resp
            self._log_response(resp)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.error(f"Get Pod Log failed: {e}")
            raise

    # ==================== StatefulSet（statefulset.jmx）====================

    def get_statefulset(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 StatefulSet。

        对应 JMX：弹性计算_native_statefulset_查询指定StatefulSet请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/statefulsets/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。
        """
        logger.info(
            f"Get StatefulSet: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/statefulsets/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get StatefulSet failed: {e}")
            raise

    def create_statefulset(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 StatefulSet。

        对应 JMX：弹性计算_native_statefulset_创建StatefulSet请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/statefulsets
        """
        logger.info(f"Create StatefulSet: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/statefulsets"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_statefulset(
        self, cluster_id: str, namespace: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 StatefulSet。

        对应 JMX：弹性计算_native_statefulset_更新指定StatefulSet
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/statefulsets/{name}
        """
        logger.info(
            f"Update StatefulSet: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/statefulsets/{name}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_statefulset(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 StatefulSet。

        对应 JMX：弹性计算_native_statefulset_删除指定StatefulSet
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/statefulsets/{name}
        """
        logger.info(
            f"Delete StatefulSet: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/statefulsets/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def list_statefulsets(
        self, cluster_id: str, namespace: str, label_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询 StatefulSet 列表。

        对应 JMX：弹性计算_native_statefulset_查询StatefulSet列表请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/statefulsets
        """
        logger.info(
            f"List StatefulSets: cluster={cluster_id}, ns={namespace},"
            f" selector={label_selector}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/statefulsets"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        try:
            resp = self.session.get(
                url,
                headers=_get_native_headers(),
                params=params,
                timeout=self.timeout,
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List StatefulSets failed: {e}")
            raise

    # ==================== PVC（pvc-pv-api.jmx）====================

    def get_pvc(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 PersistentVolumeClaim。

        对应 JMX：弹性计算_native_pvc-pv-api_查询PVC
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/persistentvolumeclaims/{name}

        注意：此方法允许 404 返回，不抛出异常。
        """
        logger.info(f"Get PVC: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/persistentvolumeclaims/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get PVC failed: {e}")
            raise

    def create_pvc(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 PersistentVolumeClaim。

        对应 JMX：弹性计算_native_pvc-pv-api_创建PVC
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/persistentvolumeclaims
        """
        logger.info(f"Create PVC: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/persistentvolumeclaims"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_pvc(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 PersistentVolumeClaim。

        对应 JMX：弹性计算_native_pvc-pv-api_删除PVC
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/persistentvolumeclaims/{name}
        """
        logger.info(f"Delete PVC: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/persistentvolumeclaims/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    # ==================== RoleBinding（rolebinding.jmx）====================

    def get_role_binding(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 RoleBinding。

        对应 JMX：弹性计算_native_rolebinding_查询指定RoleBinding请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/rolebindings/{name}

        注意：此方法允许 404 返回，不抛出异常。
        """
        logger.info(
            f"Get RoleBinding: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/rolebindings/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get RoleBinding failed: {e}")
            raise

    def create_role_binding(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 RoleBinding。

        对应 JMX：弹性计算_native_rolebinding_创建RoleBinding请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/rolebindings
        """
        logger.info(f"Create RoleBinding: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/rolebindings"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_role_binding(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 RoleBinding。

        对应 JMX：弹性计算_native_rolebinding_删除指定RoleBinding
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/rolebindings/{name}
        """
        logger.info(
            f"Delete RoleBinding: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/rolebindings/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    # ==================== Secret（secret.jmx）====================

    def get_secret(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Secret。

        对应 JMX：弹性计算_native_secret_查询指定Secret请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/secrets/{name}

        注意：此方法允许 404 返回，不抛出异常。
        """
        logger.info(f"Get Secret: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/secrets/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get Secret failed: {e}")
            raise

    def create_secret(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 Secret。

        对应 JMX：弹性计算_native_secret_创建Secret请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/secrets
        """
        logger.info(f"Create Secret: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/secrets"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_secret(
        self, cluster_id: str, namespace: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Secret。

        对应 JMX：弹性计算_native_secret_更新指定Secret
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/secrets/{name}
        """
        logger.info(
            f"Update Secret: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/secrets/{name}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_secret(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Secret。

        对应 JMX：弹性计算_native_secret_删除指定Secret
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/secrets/{name}
        """
        logger.info(f"Delete Secret: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/secrets/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def list_secrets(
        self, cluster_id: str, namespace: str, label_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询 Secret 列表。

        对应 JMX：弹性计算_native_secret_查询Secret列表请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/secrets
        """
        logger.info(
            f"List Secrets: cluster={cluster_id}, ns={namespace},"
            f" selector={label_selector}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/secrets"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        try:
            resp = self.session.get(
                url,
                headers=_get_native_headers(),
                params=params,
                timeout=self.timeout,
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List Secrets failed: {e}")
            raise

    # ==================== Service（service.jmx）====================

    def get_service_resource(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Service（K8s Service 资源，非本项目服务层的 service）。

        对应 JMX：弹性计算_native_service_查询指定Service请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/services/{name}

        注意：此方法允许 404 返回，不抛出异常。
        方法名末尾附 `_resource` 后缀以避免与 BaseService 潜在同名冲突。
        """
        logger.info(f"Get Service: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/services/{name}"
        )
        try:
            resp = self.session.get(
                url, headers=_get_native_headers(), timeout=self.timeout
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.status_code, resp.json()
        except Exception as e:
            logger.error(f"Get Service failed: {e}")
            raise

    def create_service_resource(
        self, cluster_id: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 Service。

        对应 JMX：弹性计算_native_service_创建Service请求
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/services
        """
        logger.info(f"Create Service: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/services"
        )
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_service_resource(
        self, cluster_id: str, namespace: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Service。

        对应 JMX：弹性计算_native_service_更新指定Service
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/services/{name}
        """
        logger.info(
            f"Update Service: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/services/{name}"
        )
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_service_resource(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Service。

        对应 JMX：弹性计算_native_service_删除指定Service
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/services/{name}
        """
        logger.info(
            f"Delete Service: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/services/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    def list_service_resources(
        self, cluster_id: str, namespace: str, label_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询 Service 列表。

        对应 JMX：弹性计算_native_service_查询Service列表请求
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/services
        """
        logger.info(
            f"List Services: cluster={cluster_id}, ns={namespace},"
            f" selector={label_selector}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/services"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        try:
            resp = self.session.get(
                url,
                headers=_get_native_headers(),
                params=params,
                timeout=self.timeout,
            )
            self.last_response = resp
            self._log_response(resp)
            return resp.json()
        except Exception as e:
            logger.error(f"List Services failed: {e}")
            raise

    # ==================== ServiceAccount：新增查询/创建/删除（serviceaccount.jmx）====================
    # 注意：文件顶部已存在 get_service_account / create_service_account / delete_service_account
    # 该组是 serviceaccount.jmx 的 GET/POST/DELETE 三接口，直接复用已有方法，无需追加。
