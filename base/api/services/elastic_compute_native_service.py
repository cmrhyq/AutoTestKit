"""
弹性计算 Native K8s API 服务封装（特权接口 - Bearer + X-API-KEY + apikey 三重鉴权）

面向磐基（PanJi）弹性计算平台的 **K8s 原生代理接口** 客户端，直接透传 K8s API Server
资源模型（apiVersion/metadata/spec），与 `openapi` / `extensions` 系统的扁平化契约互补。

业务域覆盖（elastic-compute/native）：
- 工作负载：Deployment / StatefulSet / DaemonSet / Job / Pod
- K8s 标准资源：ConfigMap / Secret / Service / ServiceAccount / Endpoints / Ingress
- 权限与调度：Role / RoleBinding / ClusterRole / ClusterRoleBinding / PriorityClass
- 存储与配额：PVC / PV / StorageClass / ResourceQuota / LimitRange
- 集群级：Namespace / Node / HPA / CRD / CustomResource
- 弹性伸缩：Scaled Object / Recovery Resource

鉴权：Bearer Token + `X-API-KEY` + `apikey` 三重头。
- Bearer 由 `BaseService(auth_type='bearer')` 挂到 `session.headers`（测试层 `service_factory`
  通过 `TokenManager` 注入）
- `X-API-KEY` + `apikey` 为静态特权头，由 `_get_native_headers()` 每次请求补充
URL 前缀：`/elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/...`
        或 `/elastic-compute/v2/k8s/clusters/{clusterId}/apis/{group}/{version}/...`。

**特权接口**：不经磐基业务层扁平化包装，直接返回 K8s 原生 JSON（含 `code=0` 表示无 `{code, data}`
封装），成功语义由 HTTP 状态码判断（200 OK / 201 Created / 404 NotFound）。
"""
from typing import Any, Dict, List, Optional, Tuple

from base import BaseService
from base.api.entity.elastic_compute import (
    ClusterRoleBindingEntity,
    ConfigMapEntity,
    CrdEntity,
    HpaNativeEntity,
    IngressNativeEntity,
    JobEntity,
    LimitRangeNativeEntity,
    NamespaceEntity,
    PodNativeEntity,
    PriorityClassNativeEntity,
    PvcEntity,
    ResourceQuotaNativeEntity,
    RoleBindingEntity,
    SecretEntity,
    ServiceAccountEntity,
    ServiceEntity,
    WorkloadNativeEntity,
)
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
    弹性计算 Native K8s API 服务接口（特权接口）。

    - 鉴权：Bearer Token + `X-API-KEY` + `apikey` 三重头
      （Bearer 由 `TokenManager` 注入；后两者由 `_get_native_headers()` 每次请求补充）
    - URL 前缀：`/elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/...`
              或 `/elastic-compute/v2/k8s/clusters/{clusterId}/apis/{group}/{version}/...`
    - 响应模型：K8s 原生 JSON（apiVersion/metadata/spec/status），无 `{code, data}` 封装
    - 成功判定：HTTP 状态码（200 / 201 / 404 语义 direct passthrough）
    - base_url：由 fixture `api_env["apiBaseUrl"]` 提供，必传
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

    # ==================== ServiceAccount ====================

    def get_service_account(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 ServiceAccount。
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
        self, cluster_id: str, namespace: str, sa: ServiceAccountEntity
    ) -> Dict[str, Any]:
        """
        创建 ServiceAccount。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/serviceaccounts
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            sa: ServiceAccount 实体（仅包含 name）

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
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"name": sa.name},
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_service_account(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 ServiceAccount。
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

    # ==================== DaemonSet ====================

    def get_daemonset(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 DaemonSet。
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
        self, cluster_id: str, namespace: str, workload: WorkloadNativeEntity
    ) -> Dict[str, Any]:
        """
        创建 DaemonSet。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/daemonsets
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            workload: Workload 实体（kind 应为 "DaemonSet"，replicas 忽略）

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create DaemonSet: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/daemonsets"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-code": workload.paas_app_code,
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": workload.paas_env_code,
            "paas-owner": workload.paas_owner,
            "paas-plane-code": workload.paas_plane_code,
            "paas-resource-category": "tenant-app",
            "paas-system-code": workload.namespace,
            "paas-tenant-code": workload.paas_tenant_code,
            "paas-unit-code": workload.paas_unit_code,
            "paas-workload-name": workload.name,
        }
        if workload.extra_labels:
            labels.update(workload.extra_labels)
        template_labels = {"name": workload.name, "test": "deploy"}
        payload: Dict[str, Any] = {
            "apiVersion": "apps/v1",
            "kind": workload.kind,
            "metadata": {"name": workload.name, "labels": labels},
            "spec": {
                "selector": {"matchLabels": dict(template_labels)},
                "template": {
                    "metadata": {"labels": dict(template_labels)},
                    "spec": {
                        "containers": [
                            {
                                "image": workload.image,
                                "imagePullPolicy": "Always",
                                "name": "container0",
                                "ports": [
                                    {
                                        "containerPort": workload.container_port,
                                        "name": "port0",
                                        "protocol": "TCP",
                                    }
                                ],
                            }
                        ],
                    },
                },
            },
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_daemonset(
        self,
        cluster_id: str,
        namespace: str,
        name: str,
        workload: WorkloadNativeEntity,
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 DaemonSet。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/daemonsets/{name}
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: DaemonSet 名称
            workload: Workload 实体（kind 应为 "DaemonSet"，replicas 忽略）

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
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-code": workload.paas_app_code,
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": workload.paas_env_code,
            "paas-owner": workload.paas_owner,
            "paas-plane-code": workload.paas_plane_code,
            "paas-resource-category": "tenant-app",
            "paas-system-code": workload.namespace,
            "paas-tenant-code": workload.paas_tenant_code,
            "paas-unit-code": workload.paas_unit_code,
            "paas-workload-name": workload.name,
        }
        if workload.extra_labels:
            labels.update(workload.extra_labels)
        template_labels = {"name": workload.name, "test": "deploy"}
        payload: Dict[str, Any] = {
            "apiVersion": "apps/v1",
            "kind": workload.kind,
            "metadata": {"name": workload.name, "labels": labels},
            "spec": {
                "selector": {"matchLabels": dict(template_labels)},
                "template": {
                    "metadata": {"labels": dict(template_labels)},
                    "spec": {
                        "containers": [
                            {
                                "image": workload.image,
                                "imagePullPolicy": "Always",
                                "name": "container0",
                                "ports": [
                                    {
                                        "containerPort": workload.container_port,
                                        "name": "port0",
                                        "protocol": "TCP",
                                    }
                                ],
                            }
                        ],
                    },
                },
            },
        }
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_daemonset(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 DaemonSet。
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

    # ==================== ClusterRoleBinding ====================

    def get_cluster_role_binding(
        self, cluster_id: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 ClusterRoleBinding。
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
        self, cluster_id: str, crb: ClusterRoleBindingEntity
    ) -> Dict[str, Any]:
        """
        创建 ClusterRoleBinding。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/rbac.authorization.k8s.io/v1/clusterrolebindings
        Args:
            cluster_id: 集群 ID
            crb: ClusterRoleBinding 实体（包含 name / cluster_role_name / service_account_name / subject_namespace）

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create ClusterRoleBinding: cluster={cluster_id}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/rbac.authorization.k8s.io/v1/clusterrolebindings"
        )
        payload: Dict[str, Any] = {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "ClusterRoleBinding",
            "metadata": {"name": crb.name},
            "roleRef": {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "ClusterRole",
                "name": crb.cluster_role_name,
            },
            "subjects": [
                {
                    "kind": "ServiceAccount",
                    "name": crb.service_account_name,
                    "namespace": crb.subject_namespace,
                }
            ],
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_cluster_role_binding(
        self, cluster_id: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 ClusterRoleBinding。
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

    # ==================== ConfigMap - Native ====================

    def get_native_configmap(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 ConfigMap（Native 接口）。
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
        self, cluster_id: str, namespace: str, cm: ConfigMapEntity
    ) -> Dict[str, Any]:
        """
        创建 ConfigMap（Native 接口）。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/configmaps
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            cm: ConfigMap 实体（name / paas_owner / data / extra_labels）

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create Native ConfigMap: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/configmaps"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-cluster-code": cluster_id,
            "paas-owner": cm.paas_owner,
            "paas-resource-category": "tenant-app",
            "name": cm.name,
        }
        if cm.extra_labels:
            labels.update(cm.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": cm.name, "labels": labels},
            "data": dict(cm.data),
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_native_configmap(
        self, cluster_id: str, namespace: str, name: str, cm: ConfigMapEntity
    ) -> Dict[str, Any]:
        """
        PUT 全量更新 ConfigMap（Native 接口）。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/configmaps/{name}
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: ConfigMap 名称
            cm: ConfigMap 实体（完整）

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
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-cluster-code": cluster_id,
            "paas-owner": cm.paas_owner,
            "paas-resource-category": "tenant-app",
            "name": cm.name,
        }
        if cm.extra_labels:
            labels.update(cm.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": cm.name, "labels": labels},
            "data": dict(cm.data),
        }
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_native_configmap(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 ConfigMap（Native 接口）。
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

    # ==================== CRD ====================

    def get_crd(
        self, cluster_id: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 CustomResourceDefinition。
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
        self, cluster_id: str, crd: CrdEntity
    ) -> Dict[str, Any]:
        """
        创建 CustomResourceDefinition。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apiextensions.k8s.io/v1/customresourcedefinitions
        Args:
            cluster_id: 集群 ID
            crd: CRD 实体（name / group / scope / plural / singular / kind / short_names / version_name / properties / extra_labels）

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create CRD: cluster={cluster_id}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apiextensions.k8s.io/v1/customresourcedefinitions"
        )
        labels: Dict[str, str] = {"name": crd.name, "test": "crd"}
        if crd.extra_labels:
            labels.update(crd.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "apiextensions.k8s.io/v1",
            "kind": "CustomResourceDefinition",
            "metadata": {"name": crd.name, "labels": labels},
            "spec": {
                "group": crd.group,
                "scope": crd.scope,
                "names": {
                    "plural": crd.plural,
                    "singular": crd.singular,
                    "kind": crd.kind,
                    "shortNames": list(crd.short_names),
                },
                "versions": [
                    {
                        "name": crd.version_name,
                        "served": True,
                        "storage": True,
                        "schema": {
                            "openAPIV3Schema": {
                                "type": "object",
                                "properties": {
                                    "spec": {
                                        "type": "object",
                                        "properties": dict(crd.properties),
                                    }
                                },
                            },
                        },
                    }
                ],
            },
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_crd(
        self, cluster_id: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 CustomResourceDefinition。
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

    # ==================== Job ====================

    def get_job(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Job。
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
        self, cluster_id: str, namespace: str, job: JobEntity
    ) -> Dict[str, Any]:
        """
        创建 Job。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/batch/v1/namespaces/{namespace}/jobs
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            job: Job 实体

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create Job: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/batch/v1/namespaces/{namespace}/jobs"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-code": job.paas_app_code,
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": job.paas_env_code,
            "paas-owner": job.paas_owner,
            "paas-plane-code": job.paas_plane_code,
            "paas-resource-category": "tenant-app",
            "paas-system-code": job.namespace,
            "paas-tenant-code": job.paas_tenant_code,
            "paas-unit-code": job.paas_unit_code,
            "paas-workload-name": job.name,
        }
        if job.extra_labels:
            labels.update(job.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": job.name, "labels": labels},
            "spec": {
                "backoffLimit": job.backoff_limit,
                "completions": job.completions,
                "parallelism": job.parallelism,
                "template": {
                    "spec": {
                        "restartPolicy": job.restart_policy,
                        "containers": [
                            {
                                "name": job.container_name,
                                "image": job.image,
                                "command": list(job.command),
                            }
                        ],
                    },
                },
            },
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_job(
        self, cluster_id: str, namespace: str, name: str, job: JobEntity
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Job。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/batch/v1/namespaces/{namespace}/jobs/{name}
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Job 名称
            job: Job 实体（完整）

        Returns:
            响应 JSON（HTTP 200=更新成功）
        """
        logger.info(f"Update Job: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/batch/v1/namespaces/{namespace}/jobs/{name}"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-code": job.paas_app_code,
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": job.paas_env_code,
            "paas-owner": job.paas_owner,
            "paas-plane-code": job.paas_plane_code,
            "paas-resource-category": "tenant-app",
            "paas-system-code": job.namespace,
            "paas-tenant-code": job.paas_tenant_code,
            "paas-unit-code": job.paas_unit_code,
            "paas-workload-name": job.name,
        }
        if job.extra_labels:
            labels.update(job.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": job.name, "labels": labels},
            "spec": {
                "backoffLimit": job.backoff_limit,
                "completions": job.completions,
                "parallelism": job.parallelism,
                "template": {
                    "spec": {
                        "restartPolicy": job.restart_policy,
                        "containers": [
                            {
                                "name": job.container_name,
                                "image": job.image,
                                "command": list(job.command),
                            }
                        ],
                    },
                },
            },
        }
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
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/batch/v1/namespaces/{namespace}/jobs/{name}


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

    # ==================== Deployment ====================

    def get_deployment(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Deployment。
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
        self, cluster_id: str, namespace: str, workload: WorkloadNativeEntity
    ) -> Dict[str, Any]:
        """
        创建 Deployment。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/deployments
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            workload: Workload 实体（kind 应为 "Deployment"）

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create Deployment: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/deployments"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-code": workload.paas_app_code,
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": workload.paas_env_code,
            "paas-owner": workload.paas_owner,
            "paas-plane-code": workload.paas_plane_code,
            "paas-resource-category": "tenant-app",
            "paas-system-code": workload.namespace,
            "paas-tenant-code": workload.paas_tenant_code,
            "paas-unit-code": workload.paas_unit_code,
            "paas-workload-name": workload.name,
        }
        if workload.extra_labels:
            labels.update(workload.extra_labels)
        template_labels = {"name": workload.name, "test": "deploy"}
        payload: Dict[str, Any] = {
            "apiVersion": "apps/v1",
            "kind": workload.kind,
            "metadata": {"name": workload.name, "labels": labels},
            "spec": {
                "replicas": workload.replicas,
                "selector": {"matchLabels": dict(template_labels)},
                "template": {
                    "metadata": {"labels": dict(template_labels)},
                    "spec": {
                        "containers": [
                            {
                                "image": workload.image,
                                "imagePullPolicy": "Always",
                                "name": "container0",
                                "ports": [
                                    {
                                        "containerPort": workload.container_port,
                                        "name": "port0",
                                        "protocol": "TCP",
                                    }
                                ],
                            }
                        ],
                    },
                },
            },
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_deployment(
        self,
        cluster_id: str,
        namespace: str,
        name: str,
        workload: WorkloadNativeEntity,
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Deployment。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/deployments/{name}
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Deployment 名称
            workload: Workload 实体（kind 应为 "Deployment"）

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
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-code": workload.paas_app_code,
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": workload.paas_env_code,
            "paas-owner": workload.paas_owner,
            "paas-plane-code": workload.paas_plane_code,
            "paas-resource-category": "tenant-app",
            "paas-system-code": workload.namespace,
            "paas-tenant-code": workload.paas_tenant_code,
            "paas-unit-code": workload.paas_unit_code,
            "paas-workload-name": workload.name,
        }
        if workload.extra_labels:
            labels.update(workload.extra_labels)
        template_labels = {"name": workload.name, "test": "deploy"}
        payload: Dict[str, Any] = {
            "apiVersion": "apps/v1",
            "kind": workload.kind,
            "metadata": {"name": workload.name, "labels": labels},
            "spec": {
                "replicas": workload.replicas,
                "selector": {"matchLabels": dict(template_labels)},
                "template": {
                    "metadata": {"labels": dict(template_labels)},
                    "spec": {
                        "containers": [
                            {
                                "image": workload.image,
                                "imagePullPolicy": "Always",
                                "name": "container0",
                                "ports": [
                                    {
                                        "containerPort": workload.container_port,
                                        "name": "port0",
                                        "protocol": "TCP",
                                    }
                                ],
                            }
                        ],
                    },
                },
            },
        }
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_deployment(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Deployment。
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

    # ==================== HorizontalPodAutoscaler ====================

    def get_native_hpa(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 HorizontalPodAutoscaler（Native 接口）。
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
        self, cluster_id: str, namespace: str, hpa: HpaNativeEntity
    ) -> Dict[str, Any]:
        """
        创建 HorizontalPodAutoscaler（Native 接口）。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            hpa: HPA 实体

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create Native HPA: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": "ENV1",
            "paas-owner": hpa.paas_owner,
            "paas-plane-code": "PLANE1",
            "paas-resource-category": "tenant-app",
            "paas-tenant-code": "tenant-001",
            "paas-unit-code": "TEST",
            "name": hpa.name,
        }
        if hpa.extra_labels:
            labels.update(hpa.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {"name": hpa.name, "labels": labels},
            "spec": {
                "maxReplicas": hpa.max_replicas,
                "minReplicas": hpa.min_replicas,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": hpa.cpu_utilization,
                            },
                        },
                    }
                ],
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": hpa.workload_kind,
                    "name": hpa.workload_name,
                },
            },
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_native_hpa(
        self, cluster_id: str, namespace: str, name: str, hpa: HpaNativeEntity
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 HorizontalPodAutoscaler（Native 接口）。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/autoscaling/v2/namespaces/{namespace}/horizontalpodautoscalers/{name}
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: HPA 名称
            hpa: HPA 实体（完整）

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
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": "ENV1",
            "paas-owner": hpa.paas_owner,
            "paas-plane-code": "PLANE1",
            "paas-resource-category": "tenant-app",
            "paas-tenant-code": "tenant-001",
            "paas-unit-code": "TEST",
            "name": hpa.name,
        }
        if hpa.extra_labels:
            labels.update(hpa.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {"name": hpa.name, "labels": labels},
            "spec": {
                "maxReplicas": hpa.max_replicas,
                "minReplicas": hpa.min_replicas,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": hpa.cpu_utilization,
                            },
                        },
                    }
                ],
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": hpa.workload_kind,
                    "name": hpa.workload_name,
                },
            },
        }
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_native_hpa(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 HorizontalPodAutoscaler（Native 接口）。
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

    # ==================== Ingress ====================

    def get_ingress(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Ingress。
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
        self, cluster_id: str, namespace: str, ingress: IngressNativeEntity
    ) -> Dict[str, Any]:
        """
        创建 Ingress。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            ingress: Ingress 实体

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create Ingress: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": "ENV1",
            "paas-owner": ingress.paas_owner,
            "paas-plane-code": "PLANE1",
            "paas-resource-category": "tenant-app",
            "paas-tenant-code": "tenant-001",
            "paas-unit-code": "TEST",
        }
        if ingress.extra_labels:
            labels.update(ingress.extra_labels)
        rule: Dict[str, Any] = {
            "http": {
                "paths": [
                    {
                        "path": ingress.path,
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": ingress.service_name,
                                "port": {"number": ingress.service_port},
                            }
                        },
                    }
                ]
            }
        }
        if ingress.host:
            rule["host"] = ingress.host
        payload: Dict[str, Any] = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {"name": ingress.name, "labels": labels},
            "spec": {"rules": [rule]},
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_ingress(
        self,
        cluster_id: str,
        namespace: str,
        name: str,
        ingress: IngressNativeEntity,
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Ingress。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses/{name}
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Ingress 名称
            ingress: Ingress 实体（完整）

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
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": "ENV1",
            "paas-owner": ingress.paas_owner,
            "paas-plane-code": "PLANE1",
            "paas-resource-category": "tenant-app",
            "paas-tenant-code": "tenant-001",
            "paas-unit-code": "TEST",
        }
        if ingress.extra_labels:
            labels.update(ingress.extra_labels)
        rule: Dict[str, Any] = {
            "http": {
                "paths": [
                    {
                        "path": ingress.path,
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": ingress.service_name,
                                "port": {"number": ingress.service_port},
                            }
                        },
                    }
                ]
            }
        }
        if ingress.host:
            rule["host"] = ingress.host
        payload: Dict[str, Any] = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {"name": ingress.name, "labels": labels},
            "spec": {"rules": [rule]},
        }
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_ingress(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Ingress。
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

    # ==================== PriorityClass ====================

    def get_priority_class(
        self, cluster_id: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 PriorityClass（cluster-scoped）。
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
        self, cluster_id: str, pc: PriorityClassNativeEntity
    ) -> Dict[str, Any]:
        """
        创建 PriorityClass。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/scheduling.k8s.io/v1/priorityclasses
        Args:
            cluster_id: 集群 ID
            pc: PriorityClass 实体

        Returns:
            响应 JSON（HTTP 201=创建成功）
        """
        logger.info(f"Create PriorityClass: cluster={cluster_id}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/scheduling.k8s.io/v1/priorityclasses"
        )
        metadata: Dict[str, Any] = {"name": pc.name}
        if pc.extra_labels:
            metadata["labels"] = dict(pc.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "scheduling.k8s.io/v1",
            "kind": "PriorityClass",
            "metadata": metadata,
            "value": pc.value,
            "description": pc.description,
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_priority_class(
        self, cluster_id: str, name: str, pc: PriorityClassNativeEntity
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 PriorityClass。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/scheduling.k8s.io/v1/priorityclasses/{name}
        Args:
            cluster_id: 集群 ID
            name: PriorityClass 名称
            pc: PriorityClass 实体（完整）

        Returns:
            响应 JSON（HTTP 200=更新成功）
        """
        logger.info(f"Update PriorityClass: cluster={cluster_id}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/scheduling.k8s.io/v1/priorityclasses/{name}"
        )
        metadata: Dict[str, Any] = {"name": pc.name}
        if pc.extra_labels:
            metadata["labels"] = dict(pc.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "scheduling.k8s.io/v1",
            "kind": "PriorityClass",
            "metadata": metadata,
            "value": pc.value,
            "description": pc.description,
        }
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_priority_class(
        self, cluster_id: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 PriorityClass。
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

    # ==================== Namespace ====================

    def get_namespace(
        self, cluster_id: str, namespace: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Namespace。
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
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
        self, cluster_id: str, ns: NamespaceEntity
    ) -> Dict[str, Any]:
        """
        创建 Namespace。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces
        Args:
            cluster_id: 集群 ID
            ns: Namespace 实体
        """
        logger.info(f"Create Namespace: cluster={cluster_id}")
        url = f"/elastic-compute/v2/k8s/clusters/{cluster_id}/api/v1/namespaces"
        metadata: Dict[str, Any] = {"name": ns.name}
        if ns.extra_labels:
            metadata["labels"] = dict(ns.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": metadata,
            "spec": {},
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_namespace(
        self, cluster_id: str, namespace: str, ns: NamespaceEntity
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Namespace。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            ns: Namespace 实体（完整）
        """
        logger.info(f"Update Namespace: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}"
        )
        metadata: Dict[str, Any] = {"name": ns.name}
        if ns.extra_labels:
            metadata["labels"] = dict(ns.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": metadata,
            "spec": {},
        }
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_namespace(
        self, cluster_id: str, namespace: str
    ) -> Dict[str, Any]:
        """
        删除指定 Namespace。
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
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
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces
        Args:
            cluster_id: 集群 ID
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
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/events
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
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

    # ==================== ResourceQuota ====================

    def get_resource_quota(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        查询指定 ResourceQuota。
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/resourcequotas/{name}
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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
        self, cluster_id: str, namespace: str, rq: ResourceQuotaNativeEntity
    ) -> Dict[str, Any]:
        """
        创建 ResourceQuota。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/resourcequotas
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            rq: ResourceQuota 实体
        """
        logger.info(f"Create ResourceQuota: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/resourcequotas"
        )
        metadata: Dict[str, Any] = {"name": rq.name}
        if rq.extra_labels:
            metadata["labels"] = dict(rq.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "ResourceQuota",
            "metadata": metadata,
            "spec": {"hard": dict(rq.hard)},
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_resource_quota(
        self,
        cluster_id: str,
        namespace: str,
        name: str,
        rq: ResourceQuotaNativeEntity,
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 ResourceQuota。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/resourcequotas/{name}
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: ResourceQuota 名称
            rq: ResourceQuota 实体（完整）
        """
        logger.info(
            f"Update ResourceQuota: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/resourcequotas/{name}"
        )
        metadata: Dict[str, Any] = {"name": rq.name}
        if rq.extra_labels:
            metadata["labels"] = dict(rq.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "ResourceQuota",
            "metadata": metadata,
            "spec": {"hard": dict(rq.hard)},
        }
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    # ==================== LimitRange ====================

    def get_limit_range(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        查询指定 LimitRange。
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/limitranges/{name}
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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
        self, cluster_id: str, namespace: str, lr: LimitRangeNativeEntity
    ) -> Dict[str, Any]:
        """
        创建 LimitRange。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/limitranges
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            lr: LimitRange 实体
        """
        logger.info(f"Create LimitRange: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/limitranges"
        )
        metadata: Dict[str, Any] = {"name": lr.name}
        if lr.extra_labels:
            metadata["labels"] = dict(lr.extra_labels)
        limits: List[Dict[str, Any]] = (
            [dict(item) for item in lr.limits]
            if lr.limits is not None
            else [
                {
                    "type": "Container",
                    "default": {"cpu": "500m", "memory": "512Mi"},
                    "defaultRequest": {"cpu": "100m", "memory": "128Mi"},
                }
            ]
        )
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "LimitRange",
            "metadata": metadata,
            "spec": {"limits": limits},
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_limit_range(
        self,
        cluster_id: str,
        namespace: str,
        name: str,
        lr: LimitRangeNativeEntity,
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 LimitRange。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/limitranges/{name}
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: LimitRange 名称
            lr: LimitRange 实体（完整）
        """
        logger.info(
            f"Update LimitRange: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/limitranges/{name}"
        )
        metadata: Dict[str, Any] = {"name": lr.name}
        if lr.extra_labels:
            metadata["labels"] = dict(lr.extra_labels)
        limits: List[Dict[str, Any]] = (
            [dict(item) for item in lr.limits]
            if lr.limits is not None
            else [
                {
                    "type": "Container",
                    "default": {"cpu": "500m", "memory": "512Mi"},
                    "defaultRequest": {"cpu": "100m", "memory": "128Mi"},
                }
            ]
        )
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "LimitRange",
            "metadata": metadata,
            "spec": {"limits": limits},
        }
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    # ==================== Node ====================

    def list_nodes(self, cluster_id: str) -> Dict[str, Any]:
        """
        查询 Node 列表。
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/nodes
        Args:
            cluster_id: 集群 ID
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
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/nodes/{name}
        Args:
            cluster_id: 集群 ID
            name: 资源名称
        """
        logger.info(f"Get Node: cluster={cluster_id}, name={name}")
        url = f"/elastic-compute/v2/k8s/clusters/{cluster_id}/api/v1/nodes/{name}"
        resp = self.get(endpoint=url, headers=_get_native_headers())
        return resp.json()

    # ==================== Pod ====================

    def get_pod(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Pod。
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/pods/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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
        self, cluster_id: str, namespace: str, pod: PodNativeEntity
    ) -> Dict[str, Any]:
        """
        创建 Pod。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/pods
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            pod: Pod 实体
        """
        logger.info(f"Create Pod: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/pods"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-code": pod.paas_app_code,
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": pod.paas_env_code,
            "paas-owner": pod.paas_owner,
            "paas-plane-code": pod.paas_plane_code,
            "paas-resource-category": "tenant-app",
            "paas-system-code": pod.namespace,
            "paas-tenant-code": pod.paas_tenant_code,
            "paas-unit-code": pod.paas_unit_code,
            "paas-workload-name": pod.name,
            "kind": "Pod",
        }
        if pod.extra_labels:
            labels.update(pod.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": pod.name, "labels": labels},
            "spec": {
                "containers": [
                    {
                        "image": pod.image,
                        "name": "container0",
                        "ports": [{"containerPort": pod.container_port}],
                    }
                ]
            },
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_pod(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Pod。
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/pods/{name}
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/pods
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            label_selector: 标签选择器
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
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/pods/{name}/log

        注意：响应为纯文本日志（非 JSON），返回字符串。
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
            container: 容器名
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

    # ==================== StatefulSet ====================

    def get_statefulset(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 StatefulSet。
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/statefulsets/{name}

        注意：此方法允许 404 返回（表示资源不存在），不抛出异常。
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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
        self, cluster_id: str, namespace: str, workload: WorkloadNativeEntity
    ) -> Dict[str, Any]:
        """
        创建 StatefulSet。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/statefulsets
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            workload: Workload 实体（kind="StatefulSet"）
        """
        logger.info(f"Create StatefulSet: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/statefulsets"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-code": workload.paas_app_code,
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": workload.paas_env_code,
            "paas-owner": workload.paas_owner,
            "paas-plane-code": workload.paas_plane_code,
            "paas-resource-category": "tenant-app",
            "paas-system-code": workload.namespace,
            "paas-tenant-code": workload.paas_tenant_code,
            "paas-unit-code": workload.paas_unit_code,
            "paas-workload-name": workload.name,
        }
        if workload.extra_labels:
            labels.update(workload.extra_labels)
        template_labels = {"name": workload.name, "test": "deploy"}
        payload: Dict[str, Any] = {
            "apiVersion": "apps/v1",
            "kind": workload.kind,
            "metadata": {"name": workload.name, "labels": labels},
            "spec": {
                "replicas": workload.replicas,
                "selector": {"matchLabels": dict(template_labels)},
                "template": {
                    "metadata": {"labels": dict(template_labels)},
                    "spec": {
                        "containers": [
                            {
                                "image": workload.image,
                                "imagePullPolicy": "Always",
                                "name": "container0",
                                "ports": [
                                    {
                                        "containerPort": workload.container_port,
                                        "name": "port0",
                                        "protocol": "TCP",
                                    }
                                ],
                            }
                        ],
                    },
                },
            },
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_statefulset(
        self,
        cluster_id: str,
        namespace: str,
        name: str,
        workload: WorkloadNativeEntity,
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 StatefulSet。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/statefulsets/{name}
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: StatefulSet 名称
            workload: Workload 实体（完整）
        """
        logger.info(
            f"Update StatefulSet: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/apps/v1/namespaces/{namespace}/statefulsets/{name}"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-code": workload.paas_app_code,
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": workload.paas_env_code,
            "paas-owner": workload.paas_owner,
            "paas-plane-code": workload.paas_plane_code,
            "paas-resource-category": "tenant-app",
            "paas-system-code": workload.namespace,
            "paas-tenant-code": workload.paas_tenant_code,
            "paas-unit-code": workload.paas_unit_code,
            "paas-workload-name": workload.name,
        }
        if workload.extra_labels:
            labels.update(workload.extra_labels)
        template_labels = {"name": workload.name, "test": "deploy"}
        payload: Dict[str, Any] = {
            "apiVersion": "apps/v1",
            "kind": workload.kind,
            "metadata": {"name": workload.name, "labels": labels},
            "spec": {
                "replicas": workload.replicas,
                "selector": {"matchLabels": dict(template_labels)},
                "template": {
                    "metadata": {"labels": dict(template_labels)},
                    "spec": {
                        "containers": [
                            {
                                "image": workload.image,
                                "imagePullPolicy": "Always",
                                "name": "container0",
                                "ports": [
                                    {
                                        "containerPort": workload.container_port,
                                        "name": "port0",
                                        "protocol": "TCP",
                                    }
                                ],
                            }
                        ],
                    },
                },
            },
        }
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_statefulset(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 StatefulSet。
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/statefulsets/{name}
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/apps/v1/namespaces/{namespace}/statefulsets
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            label_selector: 标签选择器
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

    # ==================== PVC ====================

    def get_pvc(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 PersistentVolumeClaim。
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/persistentvolumeclaims/{name}

        注意：此方法允许 404 返回，不抛出异常。
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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
        self, cluster_id: str, namespace: str, pvc: PvcEntity
    ) -> Dict[str, Any]:
        """
        创建 PersistentVolumeClaim。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/persistentvolumeclaims
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            pvc: PVC 实体
        """
        logger.info(f"Create PVC: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/persistentvolumeclaims"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-resource-category": "tenant-app",
            "paas-owner": pvc.paas_owner,
            "paas-cluster-code": cluster_id,
        }
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": pvc.name, "labels": labels},
            "spec": {
                "accessModes": list(pvc.access_modes),
                "resources": {"requests": {"storage": pvc.storage}},
                "storageClassName": pvc.storage_class_name,
                "volumeMode": pvc.volume_mode,
            },
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_pvc(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 PersistentVolumeClaim。
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/persistentvolumeclaims/{name}
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
        """
        logger.info(f"Delete PVC: cluster={cluster_id}, ns={namespace}, name={name}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/persistentvolumeclaims/{name}"
        )
        resp = self.delete(endpoint=url, headers=_get_native_headers())
        return resp.json()

    # ==================== RoleBinding ====================

    def get_role_binding(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 RoleBinding。
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/rolebindings/{name}

        注意：此方法允许 404 返回，不抛出异常。
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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
        self, cluster_id: str, namespace: str, rb: RoleBindingEntity
    ) -> Dict[str, Any]:
        """
        创建 RoleBinding。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/rolebindings
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            rb: RoleBinding 实体（name / role_name / service_account_name / namespace）
        """
        logger.info(f"Create RoleBinding: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/rolebindings"
        )
        payload: Dict[str, Any] = {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "RoleBinding",
            "metadata": {"name": rb.name},
            "roleRef": {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "Role",
                "name": rb.role_name,
            },
            "subjects": [
                {
                    "kind": "ServiceAccount",
                    "name": rb.service_account_name,
                    "namespace": rb.namespace,
                }
            ],
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_role_binding(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 RoleBinding。
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/rolebindings/{name}
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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

    # ==================== Secret ====================

    def get_secret(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Secret。
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/secrets/{name}

        注意：此方法允许 404 返回，不抛出异常。
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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
        self, cluster_id: str, namespace: str, secret: SecretEntity
    ) -> Dict[str, Any]:
        """
        创建 Secret。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/secrets
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            secret: Secret 实体
        """
        logger.info(f"Create Secret: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/secrets"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-cluster-code": cluster_id,
            "paas-owner": secret.paas_owner,
            "paas-resource-category": "tenant-app",
            "name": secret.name,
        }
        if secret.extra_labels:
            labels.update(secret.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": secret.name, "labels": labels},
            "data": dict(secret.data),
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_secret(
        self, cluster_id: str, namespace: str, name: str, secret: SecretEntity
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Secret。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/secrets/{name}
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Secret 名称
            secret: Secret 实体（完整）
        """
        logger.info(
            f"Update Secret: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/secrets/{name}"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-cluster-code": cluster_id,
            "paas-owner": secret.paas_owner,
            "paas-resource-category": "tenant-app",
            "name": secret.name,
        }
        if secret.extra_labels:
            labels.update(secret.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": secret.name, "labels": labels},
            "data": dict(secret.data),
        }
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_secret(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Secret。
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/secrets/{name}
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/secrets
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            label_selector: 标签选择器
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

    # ==================== Service ====================

    def get_service_resource(
        self, cluster_id: str, namespace: str, name: str
    ) -> Tuple[int, Dict[str, Any]]:
        """
        查询指定 Service（K8s Service 资源，非本项目服务层的 service）。
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/services/{name}

        注意：此方法允许 404 返回，不抛出异常。
        方法名末尾附 `_resource` 后缀以避免与 BaseService 潜在同名冲突。
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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
        self, cluster_id: str, namespace: str, svc: ServiceEntity
    ) -> Dict[str, Any]:
        """
        创建 Service。
        POST /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/services
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            svc: Service 实体
        """
        logger.info(f"Create Service: cluster={cluster_id}, ns={namespace}")
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/services"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-code": svc.paas_app_code,
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": svc.paas_env_code,
            "paas-owner": svc.paas_owner,
            "paas-plane-code": svc.paas_plane_code,
            "paas-resource-category": "tenant-app",
            "paas-system-code": svc.namespace,
            "paas-tenant-code": svc.paas_tenant_code,
            "paas-unit-code": svc.paas_unit_code,
            "paas-workload-name": svc.paas_workload_name,
        }
        if svc.extra_labels:
            labels.update(svc.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": svc.name, "labels": labels},
            "spec": {
                "ports": [
                    {
                        "name": svc.port_name,
                        "port": svc.port,
                        "protocol": svc.protocol,
                        "targetPort": svc.target_port,
                    }
                ],
                "selector": {"name": svc.paas_workload_name},
            },
        }
        resp = self.post(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def update_service_resource(
        self, cluster_id: str, namespace: str, name: str, svc: ServiceEntity
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Service。
        PUT /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/services/{name}
        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Service 名称
            svc: Service 实体（完整）
        """
        logger.info(
            f"Update Service: cluster={cluster_id}, ns={namespace}, name={name}"
        )
        url = (
            f"/elastic-compute/v2/k8s/clusters/{cluster_id}"
            f"/api/v1/namespaces/{namespace}/services/{name}"
        )
        labels: Dict[str, str] = {
            "operation-source": "api",
            "paas-app-code": svc.paas_app_code,
            "paas-app-service-version": "v1",
            "paas-app-source": "baseImage",
            "paas-cluster-code": cluster_id,
            "paas-env-code": svc.paas_env_code,
            "paas-owner": svc.paas_owner,
            "paas-plane-code": svc.paas_plane_code,
            "paas-resource-category": "tenant-app",
            "paas-system-code": svc.namespace,
            "paas-tenant-code": svc.paas_tenant_code,
            "paas-unit-code": svc.paas_unit_code,
            "paas-workload-name": svc.paas_workload_name,
        }
        if svc.extra_labels:
            labels.update(svc.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": svc.name, "labels": labels},
            "spec": {
                "ports": [
                    {
                        "name": svc.port_name,
                        "port": svc.port,
                        "protocol": svc.protocol,
                        "targetPort": svc.target_port,
                    }
                ],
                "selector": {"name": svc.paas_workload_name},
            },
        }
        resp = self.put(endpoint=url, json=payload, headers=_get_native_headers())
        return resp.json()

    def delete_service_resource(
        self, cluster_id: str, namespace: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Service。
        DELETE /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/services/{name}
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            name: 资源名称
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
        GET /elastic-compute/v2/k8s/clusters/{clusterId}/api/v1/namespaces/{namespace}/services
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            label_selector: 标签选择器
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

    # ==================== ServiceAccount：新增查询/创建/删除 ====================
    # 注意：文件顶部已存在 get_service_account / create_service_account / delete_service_account
    # 说明：文件顶部已存在 get_service_account / create_service_account / delete_service_account
