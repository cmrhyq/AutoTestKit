"""
弹性计算 OpenAPI 服务封装（Bearer 鉴权）

面向磐基（PanJi）弹性计算平台的 **对外开放接口** 客户端，与 `native`（K8s 原生透传）
和 `extensions`（内部扩展） 系统互补：路径统一以 `/openapi/elastic-compute/...` 开头，
使用 Portal Bearer Token 鉴权。

业务域覆盖（elastic-compute/openapi）：
- 集群 / 命名空间 / 节点 / 资源采集：
  cluster、namespace-api、Node、elastic-computer-resource-collection
- K8s 标准资源（Namespaced）：
  ConfigMap、SecretV2、ServiceV2、ServiceAccountV2、EndpointsV2
- K8s 集群级资源 / 命名空间配额：
  LimitRange、resourcequota、PriorityClassesV2、RBAC_V2
- 存储：
  pvc-pv（简写路径 `/pvc /pv /storageClass` + 标准 K8s 路径
  `/persistentvolumeclaims /persistentvolumes`）
- 弹性伸缩 / 工作负载 / 端口 / 资源回收 / 租户配额分配 / Helm / Harbor / CustomResource

鉴权：`Authorization: Bearer <token>`（由测试层 `service_factory` 从 `TokenManager` 注入）。
URL 前缀：`/openapi/elastic-compute/v1/...` 与 `/openapi/elastic-compute/v2/...`。

**注意**：本服务的实体对象位于 `base.api.entity.elastic_compute.openapi`，
与 `extensions` 系统的实体（磐基自定义扁平结构）物理隔离；本服务的 K8s 原生 spec 类实体
统一以 `K8s` 前缀命名（如 `K8sConfigMapEntity`），避免与 `extensions` 同名类冲突。
"""
from typing import Any, Dict, List, Optional
import json

from base import BaseService
from base.api.entity.elastic_compute.openapi import (
    ClusterCustomResourceEntity,
    ClusterCustomResourcePatchEntity,
    HarborMemberEntity,
    HarborProjectEntity,
    HarborReplicationPolicyEntity,
    HelmInstallEntity,
    HelmUpgradeEntity,
    K8sConfigMapEntity,
    K8sConfigMapPatchEntity,
    K8sHpaEntity,
    K8sLimitRangeEntity,
    K8sPodEntity,
    K8sPodPatchEntity,
    K8sPodRawEntity,
    K8sPriorityClassEntity,
    K8sPriorityClassPatchEntity,
    K8sPvcEntity,
    K8sResourceQuotaEntity,
    K8sResourceQuotaPatchEntity,
    K8sSecretEntity,
    K8sSecretPatchEntity,
    K8sServiceEntity,
    K8sServicePatchEntity,
    NsCustomResourceEntity,
    NsCustomResourcePatchEntity,
    PortAllocationEntity,
    RecoveryResourceEntity,
    ScaledObjectEntity,
    ScaledObjectPatchEntity,
    TenantQuotaAllocationEntity,
    WorkloadAppPodDeleteEntity,
    WorkloadBatchPatchTargetEntity,
    WorkloadBatchTargetEntity,
    WorkloadCreateEntity,
    WorkloadExecEntity,
    WorkloadPatchEntity,
    WorkloadPodDeleteEntity,
    WorkloadUpdateEntity,
)
from core import get_logger

logger = get_logger(__name__)


class ElasticComputeOpenService(BaseService):
    """
    弹性计算 OpenAPI 服务接口（对外开放接口）。

    - 鉴权：`Authorization: Bearer <token>`
      （由测试层 `service_factory` 从 `TokenManager` 注入）
    - URL 前缀：`/openapi/elastic-compute/v1/...`、`/openapi/elastic-compute/v2/...`
      （与 `extensions` 系统的 `/elastic-compute/...` 前缀相区分）
    - 响应模型：磐基业务层扁平化包装（`{code, data, message}`），
      **K8s 原生 spec 类接口** 除外（直接返回 apiVersion/metadata/spec 结构）
    - base_url：由 fixture `test_env["apiBaseUrl"]` 提供，必传
    """

    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        初始化 PanJi 弹性计算 OpenAPI 服务

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
                "and pass via fixture: test_env.get('apiBaseUrl')"
            )
        super().__init__(
            base_url=base_url,
            auth_type="bearer" if token else None,
            auth_credentials={"token": token} if token else None,
        )
        logger.info(
            f"Initializing PanJi ElasticCompute OpenAPI Service with base_url: {self.base_url}"
        )

    # ==================== cluster 集群管理接口 ====================

    def list_cluster_info_v1(self) -> Dict[str, Any]:
        """
        获取 paas 系统下集群列表信息（V1）。
        GET /openapi/elastic-compute/v1/clusters/info
        """
        logger.info("List elastic-compute clusters info v1")
        url = "/openapi/elastic-compute/v1/clusters/info"
        response = self.get(endpoint=url)
        return response.json()

    def list_cluster_info_v2(self) -> Dict[str, Any]:
        """
        获取运行面集群信息列表（V2）。
        GET /openapi/elastic-compute/v2/clusters/info
        """
        logger.info("List elastic-compute clusters info v2")
        url = "/openapi/elastic-compute/v2/clusters/info"
        response = self.get(endpoint=url)
        return response.json()

    # ==================== namespace 分区管理接口 ====================

    def list_namespaces(self, cell_code: str) -> Dict[str, Any]:
        """
        查询指定单元下的 Namespace 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List namespaces of cell: {cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems"
        response = self.get(endpoint=url)
        return response.json()

    def get_namespace_detail(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询指定单元下指定系统 Namespace 详情。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"Get namespace detail: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
        response = self.get(endpoint=url)
        return response.json()

    # ==================== elastic-computer-resource-collection 资源采集接口 ====================

    def list_cluster_quota(self) -> Dict[str, Any]:
        """
        查询集群配额信息。
        GET /openapi/elastic-compute/v2/metrics/clusterQuota
        """
        logger.info("List elastic-compute cluster quota metrics")
        url = "/openapi/elastic-compute/v2/metrics/clusterQuota"
        response = self.get(endpoint=url)
        return response.json()

    def list_tenant_quota(self) -> Dict[str, Any]:
        """
        查询租户配额信息。
        GET /openapi/elastic-compute/v2/metrics/tenantQuota
        """
        logger.info("List elastic-compute tenant quota metrics")
        url = "/openapi/elastic-compute/v2/metrics/tenantQuota"
        response = self.get(endpoint=url)
        return response.json()

    def list_cluster_resource(self) -> Dict[str, Any]:
        """
        查询集群资源信息。
        GET /openapi/elastic-compute/v2/metrics/clusterResource
        """
        logger.info("List elastic-compute cluster resource metrics")
        url = "/openapi/elastic-compute/v2/metrics/clusterResource"
        response = self.get(endpoint=url)
        return response.json()

    def list_middleware_info(self) -> Dict[str, Any]:
        """
        查询中间件信息。
        GET /openapi/elastic-compute/v2/metrics/middlewareInfo
        """
        logger.info("List elastic-compute middleware info metrics")
        url = "/openapi/elastic-compute/v2/metrics/middlewareInfo"
        response = self.get(endpoint=url)
        return response.json()

    def list_system_quota(self) -> Dict[str, Any]:
        """
        查询应用/组件系统配额信息。
        GET /openapi/elastic-compute/v2/metrics/systemQuota
        """
        logger.info("List elastic-compute system quota metrics")
        url = "/openapi/elastic-compute/v2/metrics/systemQuota"
        response = self.get(endpoint=url)
        return response.json()

    # ==================== Node 节点接口 ====================

    def get_node_detail(self, cell_code: str, name: str) -> Dict[str, Any]:
        """
        查询指定 Node。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/nodes/{name}
        Args:
            cell_code: 单元编码
            name: Node 名（如 IP）
        """
        logger.info(f"Get node detail: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/nodes/{name}"
        response = self.get(endpoint=url)
        return response.json()

    def list_nodes(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群所有 Node 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/nodes
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List nodes of cell: {cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/nodes"
        response = self.get(endpoint=url)
        return response.json()

    def patch_node(
        self,
        cell_code: str,
        name: str,
        labels: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        增量更新指定 Node。
        PATCH /openapi/elastic-compute/v2/cells/{cellCode}/nodes/{name}
        Args:
            cell_code: 单元编码
            name: Node 名
            labels: 需要合并的 labels（strategic merge patch）
        """
        logger.info(f"Patch node: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/nodes/{name}"
        payload: Dict[str, Any] = {"metadata": {"labels": labels}}
        response = self.patch(endpoint=url, json=payload)
        return response.json()

    def update_node(
        self,
        cell_code: str,
        name: str,
        unschedulable: bool = False,
    ) -> Dict[str, Any]:
        """
        全量更新指定 Node（构造最小 Node 对象）。
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/nodes/{name}
        Args:
            cell_code: 单元编码
            name: Node 名
            unschedulable: 是否禁止调度
        """
        logger.info(f"Update node: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/nodes/{name}"
        payload: Dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "Node",
            "metadata": {"name": name},
            "spec": {"unschedulable": unschedulable},
        }
        response = self.put(endpoint=url, json=payload)
        return response.json()

    # ==================== PVC (PersistentVolumeClaim) 接口 ====================

    def get_pvc(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        查询指定 PVC。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: PVC 名称
        """
        logger.info(f"Get PVC: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pvc/{name}"
        response = self.get(endpoint=url)
        return response.json()

    def create_pvc(
        self,
        cell_code: str,
        sys_code: str,
        pvc: K8sPvcEntity,
    ) -> Dict[str, Any]:
        """
        创建 PVC。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc

        接收 :class:`K8sPvcEntity`，内联构造 K8s 原生 PVC payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            pvc: PVC 实体
        """
        logger.info(f"Create PVC: cell={cell_code}, sys={sys_code}, name={pvc.name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pvc"
        payload: Dict[str, Any] = {
            "apiVersion": pvc.api_version,
            "kind": pvc.kind,
            "metadata": {"name": pvc.name},
            "spec": {
                "accessModes": [pvc.access_mode],
                "resources": {"requests": {"storage": pvc.storage}},
                "storageClassName": pvc.storage_class_name,
            },
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def delete_pvc(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        删除指定 PVC。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: PVC 名称
        """
        logger.info(f"Delete PVC: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pvc/{name}"
        response = self.delete(endpoint=url)
        return response.json()

    def list_pvc(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询 PVC 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List PVC: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pvc"
        response = self.get(endpoint=url)
        return response.json()

    def list_all_cluster_pvc(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群所有 PVC 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/pvc
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List all cluster PVC: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/pvc"
        response = self.get(endpoint=url)
        return response.json()

    # ==================== PV (PersistentVolume) 接口 ====================

    def get_pv(self, cell_code: str, pv_name: str) -> Dict[str, Any]:
        """
        查询指定 PV。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/pv/{pvName}
        Args:
            cell_code: 单元编码
            pv_name: PV 名称
        """
        logger.info(f"Get PV: cell={cell_code}, name={pv_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/pv/{pv_name}"
        response = self.get(endpoint=url)
        return response.json()

    # ==================== StorageClass 接口 ====================

    def get_storage_class(self, cell_code: str, storage_class_name: str) -> Dict[str, Any]:
        """
        查询指定 StorageClass。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/storageClass/{storageClassName}
        Args:
            cell_code: 单元编码
            storage_class_name: StorageClass 名称
        """
        logger.info(f"Get StorageClass: cell={cell_code}, name={storage_class_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/storageClass/{storage_class_name}"
        response = self.get(endpoint=url)
        return response.json()


    def get_configmap(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        查询指定 configmap。
        GET /openapi/elastic-compute/v2/cells/{c}/systems/{s}/configmaps/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Get configmap: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps/{name}"
        return self.get(endpoint=url).json()

    def delete_configmap(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        删除指定 configmap。
        DELETE /.../configmaps/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Delete configmap: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps/{name}"
        return self.delete(endpoint=url).json()

    def create_configmap(
        self, cell_code: str, sys_code: str, configmap: K8sConfigMapEntity
    ) -> Dict[str, Any]:
        """创建 configmap 请求。POST /.../configmaps

        接收 :class:`K8sConfigMapEntity`，内联构造 K8s 原生 ConfigMap payload。
        中"创建cm请求" sampler。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            configmap: ConfigMap 实体
        """
        logger.info(f"Create configmap: cell={cell_code}, sys={sys_code}, name={configmap.name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps"
        payload: Dict[str, Any] = {
            "apiVersion": configmap.api_version,
            "kind": configmap.kind,
            "metadata": {"name": configmap.name},
            "data": dict(configmap.data),
        }
        return self.post(endpoint=url, json=payload).json()

    def list_configmaps_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询 cm 列表请求。
        GET /.../configmaps
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List configmaps by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps"
        return self.get(endpoint=url).json()

    def list_configmaps_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群所有 cm 列表请求。
        GET /openapi/elastic-compute/v2/cells/{c}/configmaps
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List configmaps by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/configmaps"
        return self.get(endpoint=url).json()

    def update_configmap(
        self, cell_code: str, sys_code: str, name: str, configmap: K8sConfigMapEntity
    ) -> Dict[str, Any]:
        """更新指定 configmap。PUT /.../configmaps/{name}

        接收 :class:`K8sConfigMapEntity`，内联构造 K8s 原生 ConfigMap payload。
        中"更新指定 configmap" sampler。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            configmap: ConfigMap 实体
        """
        logger.info(f"Update configmap: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps/{name}"
        payload: Dict[str, Any] = {
            "apiVersion": configmap.api_version,
            "kind": configmap.kind,
            "metadata": {"name": configmap.name},
            "data": dict(configmap.data),
        }
        return self.put(endpoint=url, json=payload).json()

    def patch_configmap(
        self, cell_code: str, sys_code: str, name: str, patch: K8sConfigMapPatchEntity
    ) -> Dict[str, Any]:
        """增量更新指定 configmap。PATCH /.../configmaps/{name}

        接收 :class:`K8sConfigMapPatchEntity`，内联构造 strategic merge patch payload。
        中"增量更新指定 configmap" sampler。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            patch: PATCH 增量更新实体
        """
        logger.info(f"Patch configmap: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps/{name}"
        payload: Dict[str, Any] = {
            "metadata": {"labels": dict(patch.labels)},
            "data": dict(patch.data),
        }
        return self.patch(endpoint=url, json=payload).json()


    def get_secret(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        查询 Secret。
        GET /.../secrets/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Get secret: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets/{name}"
        return self.get(endpoint=url).json()

    def delete_secret(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        删除 Secret。
        DELETE /.../secrets/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Delete secret: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets/{name}"
        return self.delete(endpoint=url).json()

    def create_secret(
        self, cell_code: str, sys_code: str, secret: K8sSecretEntity
    ) -> Dict[str, Any]:
        """创建 Secret。POST /.../secrets

        接收 :class:`K8sSecretEntity`，内联构造 K8s 原生 Secret payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            secret: Secret 实体
        """
        logger.info(f"Create secret: cell={cell_code}, sys={sys_code}, name={secret.name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets"
        payload: Dict[str, Any] = {
            "apiVersion": secret.api_version,
            "kind": secret.kind,
            "metadata": {"name": secret.name},
            "type": secret.secret_type,
            "data": dict(secret.data),
        }
        return self.post(endpoint=url, json=payload).json()

    def list_secrets_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询指定命名空间下的 Secret 列表。
        GET /.../secrets
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List secrets by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets"
        return self.get(endpoint=url).json()

    def list_secrets_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群 Secret 列表。
        GET /openapi/elastic-compute/v2/cells/{c}/secrets
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List secrets by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/secrets"
        return self.get(endpoint=url).json()

    def update_secret(
        self, cell_code: str, sys_code: str, name: str, secret: K8sSecretEntity
    ) -> Dict[str, Any]:
        """更新 Secret。PUT /.../secrets/{name}

        接收 :class:`K8sSecretEntity`，内联构造 K8s 原生 Secret payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            secret: Secret 实体
        """
        logger.info(f"Update secret: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets/{name}"
        payload: Dict[str, Any] = {
            "apiVersion": secret.api_version,
            "kind": secret.kind,
            "metadata": {"name": secret.name},
            "type": secret.secret_type,
            "data": dict(secret.data),
        }
        return self.put(endpoint=url, json=payload).json()

    def patch_secret(
        self, cell_code: str, sys_code: str, name: str, patch: K8sSecretPatchEntity
    ) -> Dict[str, Any]:
        """增量更新 Secret。PATCH /.../secrets/{name}

        接收 :class:`K8sSecretPatchEntity`，内联构造 strategic merge patch payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            patch: PATCH 增量更新实体
        """
        logger.info(f"Patch secret: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets/{name}"
        payload: Dict[str, Any] = {
            "metadata": {"labels": dict(patch.labels)},
            "data": dict(patch.data),
        }
        return self.patch(endpoint=url, json=payload).json()


    def get_service(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        查询 Service。
        GET /.../services/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Get service: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services/{name}"
        return self.get(endpoint=url).json()

    def delete_service(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        删除 Service。
        DELETE /.../services/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Delete service: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services/{name}"
        return self.delete(endpoint=url).json()

    def create_service(
        self, cell_code: str, sys_code: str, service: K8sServiceEntity
    ) -> Dict[str, Any]:
        """创建 Service。POST /.../services

        接收 :class:`K8sServiceEntity`，内联构造 K8s 原生 Service payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            service: Service 实体
        """
        logger.info(f"Create service: cell={cell_code}, sys={sys_code}, name={service.name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services"
        payload: Dict[str, Any] = {
            "apiVersion": service.api_version,
            "kind": service.kind,
            "metadata": {"name": service.name},
            "spec": {
                "type": service.service_type,
                "ports": [
                    {
                        "port": p.port,
                        "targetPort": p.target_port,
                        "protocol": p.protocol,
                        "name": p.name,
                    }
                    for p in service.ports
                ],
                "selector": dict(service.selector),
            },
        }
        return self.post(endpoint=url, json=payload).json()

    def list_services_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询指定命名空间下的 Service 列表。
        GET /.../services
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List services by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services"
        return self.get(endpoint=url).json()

    def list_services_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群 Service 列表。
        GET /openapi/elastic-compute/v2/cells/{c}/services
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List services by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/services"
        return self.get(endpoint=url).json()

    def update_service(
        self, cell_code: str, sys_code: str, name: str, service: K8sServiceEntity
    ) -> Dict[str, Any]:
        """更新 Service。PUT /.../services/{name}

        接收 :class:`K8sServiceEntity`，内联构造 K8s 原生 Service payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            service: Service 实体
        """
        logger.info(f"Update service: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services/{name}"
        payload: Dict[str, Any] = {
            "apiVersion": service.api_version,
            "kind": service.kind,
            "metadata": {"name": service.name},
            "spec": {
                "type": service.service_type,
                "ports": [
                    {
                        "port": p.port,
                        "targetPort": p.target_port,
                        "protocol": p.protocol,
                        "name": p.name,
                    }
                    for p in service.ports
                ],
                "selector": dict(service.selector),
            },
        }
        return self.put(endpoint=url, json=payload).json()

    def patch_service(
        self, cell_code: str, sys_code: str, name: str, patch: K8sServicePatchEntity
    ) -> Dict[str, Any]:
        """增量更新 Service。PATCH /.../services/{name}

        接收 :class:`K8sServicePatchEntity`，内联构造 strategic merge patch payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            patch: PATCH 增量更新实体
        """
        logger.info(f"Patch service: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services/{name}"
        payload: Dict[str, Any] = {"metadata": {"labels": dict(patch.labels)}}
        return self.patch(endpoint=url, json=payload).json()


    def list_service_accounts_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群 ServiceAccount 列。
        GET /.../serviceaccounts
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List service accounts by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/serviceaccounts"
        return self.get(endpoint=url).json()

    def list_service_accounts_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询 ServiceAccount 列。
        GET /.../serviceaccounts
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List service accounts by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/serviceaccounts"
        return self.get(endpoint=url).json()

    def get_service_account(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """
        查询 ServiceAccount。
        GET /.../serviceaccounts/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Get service account: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/serviceaccounts/{name}"
        )
        return self.get(endpoint=url).json()


    def list_endpoints(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询 Endpoints 列表。
        GET /.../endpoints
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List endpoints: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/endpoints"
        return self.get(endpoint=url).json()

    def get_endpoints(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """
        查询 Endpoints。
        GET /.../endpoints/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Get endpoints: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/endpoints/{name}"
        return self.get(endpoint=url).json()


    def list_limitranges_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群 LimitRange。
        GET /openapi/elastic-compute/v2/cells/{c}/limitranges
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List limitranges by cell: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/limitranges",
        ).json()

    def list_limitranges_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询命名空间下 LimitRange。
        GET /.../limitranges
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List limitranges by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/limitranges"
        return self.get(endpoint=url).json()

    def get_limitrange(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        查询 LimitRange。
        GET /.../limitranges/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Get limitrange: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitranges/{name}"
        )
        return self.get(endpoint=url).json()

    def create_limitrange(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 LimitRange。
        POST /.../limitranges
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            payload: 请求体 payload
        """
        logger.info(f"Create limitrange: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/limitranges"
        return self.post(endpoint=url, json=payload).json()

    def update_limitrange(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新 LimitRange。
        PUT /.../limitranges/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            payload: 请求体 payload
        """
        logger.info(f"Update limitrange: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitranges/{name}"
        )
        return self.put(endpoint=url, json=payload).json()

    def patch_limitrange(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        增量更新 LimitRange。
        PATCH /.../limitranges/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            payload: 请求体 payload
        """
        logger.info(f"Patch limitrange: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitranges/{name}"
        )
        return self.patch(endpoint=url, json=payload).json()

    def delete_limitrange(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        删除 LimitRange。
        DELETE /.../limitranges/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Delete limitrange: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitranges/{name}"
        )
        return self.delete(endpoint=url).json()


    def list_resource_quotas_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群 ResourceQuota。
        GET /.../resourcequotas
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List resourcequotas by cell: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/resourcequotas",
        ).json()

    def list_resource_quotas_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询命名空间 ResourceQuota。
        GET /.../resourcequotas
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List resourcequotas by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/resourcequotas"
        return self.get(endpoint=url).json()

    def get_resource_quota(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """
        查询 ResourceQuota。
        GET /.../resourcequotas/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Get resourcequota: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resourcequotas/{name}"
        )
        return self.get(endpoint=url).json()

    def create_resource_quota(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 ResourceQuota。
        POST /.../resourcequotas
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            payload: 请求体 payload
        """
        logger.info(f"Create resourcequota: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/resourcequotas"
        return self.post(endpoint=url, json=payload).json()

    def update_resource_quota(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新 ResourceQuota。
        PUT /.../resourcequotas/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            payload: 请求体 payload
        """
        logger.info(f"Update resourcequota: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resourcequotas/{name}"
        )
        return self.put(endpoint=url, json=payload).json()

    def patch_resource_quota(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        增量更新 ResourceQuota。
        PATCH /.../resourcequotas/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            payload: 请求体 payload
        """
        logger.info(f"Patch resourcequota: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resourcequotas/{name}"
        )
        return self.patch(endpoint=url, json=payload).json()

    def delete_resource_quota(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """
        删除 ResourceQuota。
        DELETE /.../resourcequotas/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Delete resourcequota: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resourcequotas/{name}"
        )
        return self.delete(endpoint=url).json()


    def list_priority_classes(self, cell_code: str) -> Dict[str, Any]:
        """
        查询 PriorityClass 列表。
        GET /.../priorityclasses
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List priority classes: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses",
        ).json()

    def get_priority_class(self, cell_code: str, name: str) -> Dict[str, Any]:
        """
        查询 PriorityClass。
        GET /.../priorityclasses/{name}
        Args:
            cell_code: 单元编码
            name: 资源名称
        """
        logger.info(f"Get priority class: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses/{name}"
        return self.get(endpoint=url).json()

    def create_priority_class(self, cell_code: str, priority_class: K8sPriorityClassEntity) -> Dict[str, Any]:
        """创建 PriorityClass。POST /.../priorityclasses

        接收 :class:`K8sPriorityClassEntity`，内联构造 K8s PriorityClass payload。
        Args:
            cell_code: 单元编码
            priority_class: PriorityClass 实体
        """
        logger.info(f"Create priority class: cell={cell_code}, name={priority_class.name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses"
        payload: Dict[str, Any] = {
            "apiVersion": priority_class.api_version,
            "description": priority_class.description,
            "kind": priority_class.kind,
            "metadata": {"name": priority_class.name},
            "value": priority_class.value,
        }
        return self.post(endpoint=url, json=payload).json()

    def update_priority_class(
        self, cell_code: str, name: str, priority_class: K8sPriorityClassEntity
    ) -> Dict[str, Any]:
        """更新 PriorityClass。PUT /.../priorityclasses/{name}

        接收 :class:`K8sPriorityClassEntity`，内联构造 K8s PriorityClass payload。
        Args:
            cell_code: 单元编码
            name: 资源名称
            priority_class: PriorityClass 实体
        """
        logger.info(f"Update priority class: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses/{name}"
        payload: Dict[str, Any] = {
            "apiVersion": priority_class.api_version,
            "description": priority_class.description,
            "kind": priority_class.kind,
            "metadata": {"name": priority_class.name},
            "value": priority_class.value,
        }
        return self.put(endpoint=url, json=payload).json()

    def patch_priority_class(
        self, cell_code: str, name: str, patch: K8sPriorityClassPatchEntity
    ) -> Dict[str, Any]:
        """增量更新 PriorityClass。PATCH /.../priorityclasses/{name}

        接收 :class:`K8sPriorityClassPatchEntity`，内联构造 strategic merge patch payload。
        Args:
            cell_code: 单元编码
            name: 资源名称
            patch: PATCH 增量更新实体
        """
        logger.info(f"Patch priority class: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses/{name}"
        payload: Dict[str, Any] = {
            "description": patch.description,
            "globalDefault": patch.global_default,
            "metadata": {
                "labels": dict(patch.labels),
                "annotations": dict(patch.annotations),
            },
        }
        return self.patch(endpoint=url, json=payload).json()

    def delete_priority_class(self, cell_code: str, name: str) -> Dict[str, Any]:
        """
        删除 PriorityClass。
        DELETE /.../priorityclasses/{name}
        Args:
            cell_code: 单元编码
            name: 资源名称
        """
        logger.info(f"Delete priority class: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses/{name}"
        return self.delete(endpoint=url).json()


    def list_rbac_roles(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询 Role 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/rbac/roles
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List rbac roles: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/rbac/roles"
        return self.get(endpoint=url).json()

    def get_rbac_role(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        查询指定 Role。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/rbac/roles/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: Role 名称
        """
        logger.info(f"Get rbac role: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/rbac/roles/{name}"
        return self.get(endpoint=url).json()

    def list_rbac_role_bindings(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询 RoleBinding 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/rbac/rolebindings
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List rbac rolebindings: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/rbac/rolebindings"
        return self.get(endpoint=url).json()

    def get_rbac_role_binding(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        查询指定 RoleBinding。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/rbac/rolebindings/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: RoleBinding 名称
        """
        logger.info(f"Get rbac rolebinding: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/rbac/rolebindings/{name}"
        return self.get(endpoint=url).json()

    def list_rbac_cluster_roles(self, cell_code: str) -> Dict[str, Any]:
        """
        查询 ClusterRole 列表。
        GET /.../clusterroles
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List rbac clusterroles: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/clusterroles",
        ).json()

    def list_rbac_cluster_role_bindings(self, cell_code: str) -> Dict[str, Any]:
        """
        查询 ClusterRoleBinding 列表。
        GET /.../clusterrolebindings
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List rbac clusterrolebindings: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/clusterrolebindings",
        ).json()

    # ==================== cr-cluster（Cluster 级别 CustomResource） ====================

    def get_cluster_custom_resource(
        self, cell_code: str, group: str, version: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        查询指定 Cluster 级别 CR。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/{group}/{version}/kind/{kind}/customResources/{name}
        Args:
            cell_code: 单元编码
            group: CR group（如 test.example.com）
            version: CR version（如 v1）
            kind: CR kind（如 Apple）
            name: CR 名称
        """
        logger.info(
            f"Get cluster CR: cell={cell_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/{group}/{version}"
            f"/kind/{kind}/customResources/{name}"
        )
        return self.get(endpoint=url).json()

    def create_cluster_custom_resource(
        self, cell_code: str, group: str, version: str, kind: str,
        custom_resource: ClusterCustomResourceEntity,
    ) -> Dict[str, Any]:
        """
        创建 Cluster 级别 CR。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/{group}/{version}/kind/{kind}/customResources

        接收 :class:`ClusterCustomResourceEntity`，内联构造 K8s CR payload。
        Args:
            cell_code: 单元编码
            group: CR API group
            version: CR API version
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            custom_resource: 参数
        """
        logger.info(
            f"Create cluster CR: cell={cell_code}, group={group}, version={version}, "
            f"kind={kind}, name={custom_resource.name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/{group}/{version}"
            f"/kind/{kind}/customResources"
        )
        labels: Dict[str, str] = {
            "name": custom_resource.name,
            "kind": custom_resource.kind,
        }
        if custom_resource.extra_labels:
            labels.update(custom_resource.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": f"{custom_resource.group}/{custom_resource.version}",
            "kind": custom_resource.kind,
            "metadata": {
                "name": custom_resource.name,
                "labels": labels,
            },
            "spec": {
                "message": custom_resource.message,
                "replicas": custom_resource.replicas,
            },
        }
        return self.post(endpoint=url, json=payload).json()

    def list_cluster_custom_resources(
        self, cell_code: str, group: str, version: str, kind: str,
        label_selector: str = None,
    ) -> Dict[str, Any]:
        """
        查询 Cluster 级别 CR 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/{group}/{version}/kind/{kind}/customResources
        Args:
            cell_code: 单元编码
            group: CR group
            version: CR version
            kind: CR kind
            label_selector: labelSelector 过滤条件（可选）
        """
        logger.info(
            f"List cluster CRs: cell={cell_code}, group={group}, version={version}, kind={kind}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/{group}/{version}"
            f"/kind/{kind}/customResources"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        return self.get(endpoint=url, params=params).json()

    def update_cluster_custom_resource(
        self, cell_code: str, group: str, version: str, kind: str, name: str,
        custom_resource: ClusterCustomResourceEntity,
    ) -> Dict[str, Any]:
        """
        全量更新指定 Cluster 级别 CR。
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/{group}/{version}/kind/{kind}/customResources/{name}

        接收 :class:`ClusterCustomResourceEntity`，内联构造 K8s CR payload。
        Args:
            cell_code: 单元编码
            group: CR API group
            version: CR API version
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
            custom_resource: 参数
        """
        logger.info(
            f"Update cluster CR: cell={cell_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/{group}/{version}"
            f"/kind/{kind}/customResources/{name}"
        )
        labels: Dict[str, str] = {
            "name": custom_resource.name,
            "kind": custom_resource.kind,
        }
        if custom_resource.extra_labels:
            labels.update(custom_resource.extra_labels)
        payload: Dict[str, Any] = {
            "apiVersion": f"{custom_resource.group}/{custom_resource.version}",
            "kind": custom_resource.kind,
            "metadata": {
                "name": custom_resource.name,
                "labels": labels,
            },
            "spec": {
                "message": custom_resource.message,
                "replicas": custom_resource.replicas,
            },
        }
        return self.put(endpoint=url, json=payload).json()

    def patch_cluster_custom_resource(
        self, cell_code: str, group: str, version: str, kind: str, name: str,
        custom_resource: ClusterCustomResourcePatchEntity,
    ) -> Dict[str, Any]:
        """
        增量更新指定 Cluster 级别 CR。
        PATCH /openapi/elastic-compute/v2/cells/{cellCode}/{group}/{version}/kind/{kind}/customResources/{name}

        接收 :class:`ClusterCustomResourcePatchEntity`，内联构造 K8s CR patch payload；
        当 ``labels`` 为 ``None`` 时不写入 ``metadata`` 字段。
        Args:
            cell_code: 单元编码
            group: CR API group
            version: CR API version
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
            custom_resource: 参数
        """
        logger.info(
            f"Patch cluster CR: cell={cell_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/{group}/{version}"
            f"/kind/{kind}/customResources/{name}"
        )
        payload: Dict[str, Any] = {"spec": {"replicas": custom_resource.replicas}}
        if custom_resource.labels is not None:
            payload["metadata"] = {"labels": custom_resource.labels}
        return self.patch(endpoint=url, json=payload).json()

    def delete_cluster_custom_resource(
        self, cell_code: str, group: str, version: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Cluster 级别 CR。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/{group}/{version}/kind/{kind}/customResources/{name}
        Args:
            cell_code: 单元编码
            group: CR group
            version: CR version
            kind: CR kind
            name: CR 名称
        """
        logger.info(
            f"Delete cluster CR: cell={cell_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/{group}/{version}"
            f"/kind/{kind}/customResources/{name}"
        )
        return self.delete(endpoint=url).json()

    # ==================== pvc-pv（K8s 标准路径 /persistentvolumeclaims /persistentvolumes） ====================
    # 说明：与上方 PVC/PV 接口（简写路径 /pvc、/pv）为两套并存的 OpenAPI，
    # 此处方法名统一使用完整 K8s 资源名以示区分。

    def list_persistentvolumeclaims_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群 PVC。
        GET /.../persistentvolumeclaims
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List persistentvolumeclaims by cell: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumeclaims",
        ).json()

    def list_persistentvolumeclaims_by_ns(
        self, cell_code: str, sys_code: str
    ) -> Dict[str, Any]:
        """
        查询命名空间 PVC。
        GET /.../persistentvolumeclaims
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(
            f"List persistentvolumeclaims by ns: cell={cell_code}, sys={sys_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims"
        )
        return self.get(endpoint=url).json()

    def get_persistentvolumeclaim(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """
        查询 PVC。
        GET /.../persistentvolumeclaims/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(
            f"Get persistentvolumeclaim: cell={cell_code}, sys={sys_code}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims/{name}"
        )
        return self.get(endpoint=url).json()

    def create_persistentvolumeclaim(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 PVC。
        POST /.../persistentvolumeclaims
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            payload: 请求体 payload
        """
        logger.info(f"Create persistentvolumeclaim: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims"
        )
        return self.post(endpoint=url, json=payload).json()

    def update_persistentvolumeclaim(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新 PVC。
        PUT /.../persistentvolumeclaims/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            payload: 请求体 payload
        """
        logger.info(
            f"Update persistentvolumeclaim: cell={cell_code}, sys={sys_code}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims/{name}"
        )
        return self.put(endpoint=url, json=payload).json()

    def patch_persistentvolumeclaim(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        增量更新 PVC。
        PATCH /.../persistentvolumeclaims/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            payload: 请求体 payload
        """
        logger.info(
            f"Patch persistentvolumeclaim: cell={cell_code}, sys={sys_code}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims/{name}"
        )
        return self.patch(endpoint=url, json=payload).json()

    def delete_persistentvolumeclaim(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """
        删除 PVC。
        DELETE /.../persistentvolumeclaims/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(
            f"Delete persistentvolumeclaim: cell={cell_code}, sys={sys_code}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims/{name}"
        )
        return self.delete(endpoint=url).json()

    def list_persistentvolumes(self, cell_code: str) -> Dict[str, Any]:
        """
        查询 PV 列表。
        GET /.../persistentvolumes
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List persistentvolumes: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes",
        ).json()

    def get_persistentvolume(self, cell_code: str, name: str) -> Dict[str, Any]:
        """
        查询 PV。
        GET /.../persistentvolumes/{name}
        Args:
            cell_code: 单元编码
            name: 资源名称
        """
        logger.info(f"Get persistentvolume: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes/{name}"
        return self.get(endpoint=url).json()

    def create_persistentvolume(
        self, cell_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 PV。
        POST /.../persistentvolumes
        Args:
            cell_code: 单元编码
            payload: 请求体 payload
        """
        logger.info(f"Create persistentvolume: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes"
        return self.post(endpoint=url, json=payload).json()

    def update_persistentvolume(
        self, cell_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新 PV。
        PUT /.../persistentvolumes/{name}
        Args:
            cell_code: 单元编码
            name: 资源名称
            payload: 请求体 payload
        """
        logger.info(f"Update persistentvolume: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes/{name}"
        return self.put(endpoint=url, json=payload).json()

    def delete_persistentvolume(self, cell_code: str, name: str) -> Dict[str, Any]:
        """
        删除 PV。
        DELETE /.../persistentvolumes/{name}
        Args:
            cell_code: 单元编码
            name: 资源名称
        """
        logger.info(f"Delete persistentvolume: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes/{name}"
        return self.delete(endpoint=url).json()

    # ==================== CustomResource-ns（Namespace 级别 CustomResource） ====================

    def get_ns_custom_resource(
        self, cell_code: str, sys_code: str, group: str, version: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        查询指定 Namespace 级别 CR。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{group}/{version}/kind/{kind}/customResources/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            group: CR API group
            version: CR API version
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
        """
        logger.info(
            f"Get ns CR: cell={cell_code}, sys={sys_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{group}/{version}/kind/{kind}/customResources/{name}"
        )
        return self.get(endpoint=url).json()

    def create_ns_custom_resource(
        self, cell_code: str, sys_code: str, group: str, version: str, kind: str,
        custom_resource: NsCustomResourceEntity,
    ) -> Dict[str, Any]:
        """
        创建 Namespace 级别 CR。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{group}/{version}/kind/{kind}/customResources

        接收 :class:`NsCustomResourceEntity`，内联构造 K8s CR payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            group: CR API group
            version: CR API version
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            custom_resource: 参数
        """
        logger.info(
            f"Create ns CR: cell={cell_code}, sys={sys_code}, group={group}, "
            f"version={version}, kind={kind}, name={custom_resource.name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{group}/{version}/kind/{kind}/customResources"
        )
        payload: Dict[str, Any] = {
            "apiVersion": f"{custom_resource.group}/{custom_resource.version}",
            "kind": custom_resource.kind,
            "metadata": {"name": custom_resource.name},
            "spec": {"color": custom_resource.color},
        }
        return self.post(endpoint=url, json=payload).json()

    def list_ns_custom_resources(
        self, cell_code: str, sys_code: str, group: str, version: str, kind: str,
        label_selector: str = None,
    ) -> Dict[str, Any]:
        """
        查询 Namespace 级别 CR 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{group}/{version}/kind/{kind}/customResources
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            group: CR API group
            version: CR API version
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            label_selector: 标签选择器
        """
        logger.info(
            f"List ns CRs: cell={cell_code}, sys={sys_code}, group={group}, version={version}, kind={kind}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{group}/{version}/kind/{kind}/customResources"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        return self.get(endpoint=url, params=params).json()

    def update_ns_custom_resource(
        self, cell_code: str, sys_code: str, group: str, version: str, kind: str, name: str,
        custom_resource: NsCustomResourceEntity,
    ) -> Dict[str, Any]:
        """
        全量更新指定 Namespace 级别 CR。
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{group}/{version}/kind/{kind}/customResources/{name}

        接收 :class:`NsCustomResourceEntity`，内联构造 K8s CR payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            group: CR API group
            version: CR API version
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
            custom_resource: 参数
        """
        logger.info(
            f"Update ns CR: cell={cell_code}, sys={sys_code}, group={group}, "
            f"version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{group}/{version}/kind/{kind}/customResources/{name}"
        )
        payload: Dict[str, Any] = {
            "apiVersion": f"{custom_resource.group}/{custom_resource.version}",
            "kind": custom_resource.kind,
            "metadata": {"name": custom_resource.name},
            "spec": {"color": custom_resource.color},
        }
        return self.put(endpoint=url, json=payload).json()

    def patch_ns_custom_resource(
        self, cell_code: str, sys_code: str, group: str, version: str, kind: str, name: str,
        custom_resource: NsCustomResourcePatchEntity,
    ) -> Dict[str, Any]:
        """
        增量更新指定 Namespace 级别 CR。
        PATCH /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{group}/{version}/kind/{kind}/customResources/{name}

        接收 :class:`NsCustomResourcePatchEntity`，内联构造 K8s CR patch payload；
        当 ``labels`` 为 ``None`` 时不写入 ``metadata`` 字段。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            group: CR API group
            version: CR API version
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
            custom_resource: 参数
        """
        logger.info(
            f"Patch ns CR: cell={cell_code}, sys={sys_code}, group={group}, "
            f"version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{group}/{version}/kind/{kind}/customResources/{name}"
        )
        payload: Dict[str, Any] = {"spec": {"color": custom_resource.color}}
        if custom_resource.labels is not None:
            payload["metadata"] = {"labels": custom_resource.labels}
        return self.patch(endpoint=url, json=payload).json()

    def delete_ns_custom_resource(
        self, cell_code: str, sys_code: str, group: str, version: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Namespace 级别 CR。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{group}/{version}/kind/{kind}/customResources/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            group: CR API group
            version: CR API version
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
        """
        logger.info(
            f"Delete ns CR: cell={cell_code}, sys={sys_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{group}/{version}/kind/{kind}/customResources/{name}"
        )
        return self.delete(endpoint=url).json()

    # ==================== Helm Chart 接口 ====================

    def get_helm_chart(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        查询指定 Helm Chart。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helmCharts/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Get helm chart: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helmCharts/{name}"
        return self.get(endpoint=url).json()

    def create_helm_chart(self, cell_code: str, sys_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建 Helm Chart。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helmCharts
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            payload: 请求体 payload
        """
        logger.info(f"Create helm chart: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helmCharts"
        return self.post(endpoint=url, json=payload).json()

    def list_helm_charts_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询 Namespace 下 Helm Chart 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helmCharts
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List helm charts by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helmCharts"
        return self.get(endpoint=url).json()

    def list_helm_charts_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群 Helm Chart 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/helmCharts
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List helm charts by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/helmCharts"
        return self.get(endpoint=url).json()

    def update_helm_chart(self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        全量更新指定 Helm Chart。
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helmCharts/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            payload: 请求体 payload
        """
        logger.info(f"Update helm chart: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helmCharts/{name}"
        return self.put(endpoint=url, json=payload).json()

    def patch_helm_chart(self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        增量更新指定 Helm Chart。
        PATCH /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helmCharts/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            payload: 请求体 payload
        """
        logger.info(f"Patch helm chart: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helmCharts/{name}"
        return self.patch(endpoint=url, json=payload).json()

    def delete_helm_chart(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        删除指定 Helm Chart。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helmCharts/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Delete helm chart: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helmCharts/{name}"
        return self.delete(endpoint=url).json()

    # ==================== Harbor 镜像仓库接口 ====================

    def get_harbor_project(self, cell_code: str, project_name: str) -> Dict[str, Any]:
        """
        查询指定 Harbor 项目。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}
        Args:
            cell_code: 单元编码
            project_name: Harbor 项目名称
        """
        logger.info(f"Get harbor project: cell={cell_code}, project={project_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}"
        return self.get(endpoint=url).json()

    def create_harbor_project(self, cell_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建 Harbor 项目。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects
        Args:
            cell_code: 单元编码
            payload: 请求体 payload
        """
        logger.info(f"Create harbor project: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects"
        return self.post(endpoint=url, json=payload).json()

    def list_harbor_projects(self, cell_code: str) -> Dict[str, Any]:
        """
        查询 Harbor 项目列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List harbor projects: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects"
        return self.get(endpoint=url).json()

    def update_harbor_project(self, cell_code: str, project_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新 Harbor 项目。
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}
        Args:
            cell_code: 单元编码
            project_name: Harbor 项目名称
            payload: 请求体 payload
        """
        logger.info(f"Update harbor project: cell={cell_code}, project={project_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}"
        return self.put(endpoint=url, json=payload).json()

    def delete_harbor_project(self, cell_code: str, project_name: str) -> Dict[str, Any]:
        """
        删除 Harbor 项目。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}
        Args:
            cell_code: 单元编码
            project_name: Harbor 项目名称
        """
        logger.info(f"Delete harbor project: cell={cell_code}, project={project_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}"
        return self.delete(endpoint=url).json()

    def list_harbor_repositories(self, cell_code: str, project_name: str) -> Dict[str, Any]:
        """
        查询 Harbor 仓库列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}/repositories
        Args:
            cell_code: 单元编码
            project_name: Harbor 项目名称
        """
        logger.info(f"List harbor repositories: cell={cell_code}, project={project_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}/repositories"
        return self.get(endpoint=url).json()

    def delete_harbor_repository(self, cell_code: str, project_name: str, repo_name: str) -> Dict[str, Any]:
        """
        删除 Harbor 仓库。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}/repositories/{repoName}
        Args:
            cell_code: 单元编码
            project_name: Harbor 项目名称
            repo_name: 镜像仓库名
        """
        logger.info(f"Delete harbor repository: cell={cell_code}, project={project_name}, repo={repo_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}/repositories/{repo_name}"
        return self.delete(endpoint=url).json()

    def list_harbor_artifacts(self, cell_code: str, project_name: str, repo_name: str) -> Dict[str, Any]:
        """
        查询 Harbor 制品列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}/repositories/{repoName}/artifacts
        Args:
            cell_code: 单元编码
            project_name: Harbor 项目名称
            repo_name: 镜像仓库名
        """
        logger.info(f"List harbor artifacts: cell={cell_code}, project={project_name}, repo={repo_name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}"
            f"/repositories/{repo_name}/artifacts"
        )
        return self.get(endpoint=url).json()

    def delete_harbor_artifact(
        self, cell_code: str, project_name: str, repo_name: str, reference: str
    ) -> Dict[str, Any]:
        """
        删除 Harbor 制品。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}/repositories/{repoName}/artifacts/{reference}
        Args:
            cell_code: 单元编码
            project_name: Harbor 项目名称
            repo_name: 镜像仓库名
            reference: 参数
        """
        logger.info(
            f"Delete harbor artifact: cell={cell_code}, project={project_name}, repo={repo_name}, ref={reference}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}"
            f"/repositories/{repo_name}/artifacts/{reference}"
        )
        return self.delete(endpoint=url).json()

    def get_harbor_project_summary(self, cell_code: str, project_name: str) -> Dict[str, Any]:
        """
        查询 Harbor 项目概要。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}/summary
        Args:
            cell_code: 单元编码
            project_name: Harbor 项目名称
        """
        logger.info(f"Get harbor project summary: cell={cell_code}, project={project_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}/summary"
        return self.get(endpoint=url).json()

    def init_harbor(self, cell_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        初始化 Harbor（harbor-init）。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/harbor/init
        Args:
            cell_code: 单元编码
            payload: 请求体 payload
        """
        logger.info(f"Init harbor: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/init"
        return self.post(endpoint=url, json=payload).json()

    def get_harbor_status(self, cell_code: str) -> Dict[str, Any]:
        """
        查询 Harbor 状态。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/harbor/status
        Args:
            cell_code: 单元编码
        """
        logger.info(f"Get harbor status: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/status"
        return self.get(endpoint=url).json()

    # ==================== HorizontalPodAutoscaler 接口 ====================

    def get_hpa(
        self, cell_code: str, sys_code: str, api_version: str, name: str
    ) -> Dict[str, Any]:
        """
        查询指定 HPA。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{apiVersion}/hpas/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            api_version: 参数
            name: 资源名称
        """
        logger.info(
            f"Get HPA: cell={cell_code}, sys={sys_code}, apiVer={api_version}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{api_version}/hpas/{name}"
        )
        return self.get(endpoint=url).json()

    def create_hpa(
        self, cell_code: str, sys_code: str, api_version: str, hpa: K8sHpaEntity
    ) -> Dict[str, Any]:
        """
        创建 HPA。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{apiVersion}/hpas

        接收 :class:`K8sHpaEntity`，内联构造 K8s HPA payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            api_version: 参数
            hpa: HPA 实体
        """
        logger.info(
            f"Create HPA: cell={cell_code}, sys={sys_code}, apiVer={api_version}, name={hpa.name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{api_version}/hpas"
        )
        payload: Dict[str, Any] = {
            "apiVersion": f"autoscaling/{hpa.api_version}",
            "kind": hpa.kind,
            "metadata": {"name": hpa.name},
            "spec": {
                "scaleTargetRef": {
                    "kind": hpa.scale_target_kind,
                    "name": hpa.scale_target_name,
                    "apiVersion": hpa.scale_target_api_version,
                },
                "minReplicas": hpa.min_replicas,
                "maxReplicas": hpa.max_replicas,
                "targetCPUUtilizationPercentage": hpa.target_cpu_utilization_percentage,
            },
        }
        return self.post(endpoint=url, json=payload).json()

    def list_hpas_by_ns(
        self, cell_code: str, sys_code: str, api_version: str
    ) -> Dict[str, Any]:
        """
        查询 Namespace 下 HPA 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{apiVersion}/hpas
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            api_version: 参数
        """
        logger.info(
            f"List HPAs by ns: cell={cell_code}, sys={sys_code}, apiVer={api_version}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{api_version}/hpas"
        )
        return self.get(endpoint=url).json()

    def list_hpas_by_cell(self, cell_code: str, api_version: str) -> Dict[str, Any]:
        """
        查询全集群 HPA 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/{apiVersion}/hpas
        Args:
            cell_code: 单元编码
            api_version: 参数
        """
        logger.info(f"List HPAs by cell: cell={cell_code}, apiVer={api_version}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/{api_version}/hpas"
        return self.get(endpoint=url).json()

    def update_hpa(
        self, cell_code: str, sys_code: str, api_version: str, name: str,
        hpa: K8sHpaEntity,
    ) -> Dict[str, Any]:
        """
        全量更新指定 HPA。
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{apiVersion}/hpas/{name}

        接收 :class:`K8sHpaEntity`，内联构造 K8s HPA payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            api_version: 参数
            name: 资源名称
            hpa: HPA 实体
        """
        logger.info(
            f"Update HPA: cell={cell_code}, sys={sys_code}, apiVer={api_version}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{api_version}/hpas/{name}"
        )
        payload: Dict[str, Any] = {
            "apiVersion": f"autoscaling/{hpa.api_version}",
            "kind": hpa.kind,
            "metadata": {"name": hpa.name},
            "spec": {
                "scaleTargetRef": {
                    "kind": hpa.scale_target_kind,
                    "name": hpa.scale_target_name,
                    "apiVersion": hpa.scale_target_api_version,
                },
                "minReplicas": hpa.min_replicas,
                "maxReplicas": hpa.max_replicas,
                "targetCPUUtilizationPercentage": hpa.target_cpu_utilization_percentage,
            },
        }
        return self.put(endpoint=url, json=payload).json()

    def patch_hpa(
        self, cell_code: str, sys_code: str, api_version: str, name: str,
        hpa: K8sHpaEntity,
    ) -> Dict[str, Any]:
        """
        增量更新指定 HPA。
        PATCH /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{apiVersion}/hpas/{name}

        接收 :class:`K8sHpaEntity`，内联构造 K8s HPA patch payload（结构等同于全量更新）。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            api_version: 参数
            name: 资源名称
            hpa: HPA 实体
        """
        logger.info(
            f"Patch HPA: cell={cell_code}, sys={sys_code}, apiVer={api_version}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{api_version}/hpas/{name}"
        )
        payload: Dict[str, Any] = {
            "apiVersion": f"autoscaling/{hpa.api_version}",
            "kind": hpa.kind,
            "metadata": {"name": hpa.name},
            "spec": {
                "scaleTargetRef": {
                    "kind": hpa.scale_target_kind,
                    "name": hpa.scale_target_name,
                    "apiVersion": hpa.scale_target_api_version,
                },
                "minReplicas": hpa.min_replicas,
                "maxReplicas": hpa.max_replicas,
                "targetCPUUtilizationPercentage": hpa.target_cpu_utilization_percentage,
            },
        }
        return self.patch(endpoint=url, json=payload).json()

    def delete_hpa(
        self, cell_code: str, sys_code: str, api_version: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 HPA。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{apiVersion}/hpas/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            api_version: 参数
            name: 资源名称
        """
        logger.info(
            f"Delete HPA: cell={cell_code}, sys={sys_code}, apiVer={api_version}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{api_version}/hpas/{name}"
        )
        return self.delete(endpoint=url).json()

    # ==================== Harbor 版本刷新 ====================

    def refresh_harbor_version(self, harbor_id: int) -> Dict[str, Any]:
        """
        更新 harbor 版本信息（harbor-init）。
        POST /openapi/elastic-compute/v2/harbor/refreshHarborVersion?clusterId={harborId}
        Args:
            harbor_id: 参数
        """
        logger.info(f"Refresh harbor version: harborId={harbor_id}")
        url = "/openapi/elastic-compute/v2/harbor/refreshHarborVersion"
        params = {"clusterId": harbor_id}
        return self.post(endpoint=url, params=params).json()

    # ==================== Harbor 完整生命周期接口（新路径 /harbors/{harborId}/...） ====================

    def list_harbors(self) -> Dict[str, Any]:
        """
        查询 harbor 列表。
        GET /openapi/elastic-compute/v2/harbors
        """
        logger.info("List harbors")
        return self.get(
            endpoint="/openapi/elastic-compute/v2/harbors",
        ).json()

    def list_all_cluster_harbor_addresses(self) -> Dict[str, Any]:
        """
        查询所有集群 harbor 地址。
        GET /openapi/elastic-compute/v2/harbor/list
        """
        logger.info("List all cluster harbor addresses")
        return self.get(
            endpoint="/openapi/elastic-compute/v2/harbor/list",
        ).json()

    def get_harbor_project_by_id(
        self, harbor_id: int, project_name: str
    ) -> Dict[str, Any]:
        """
        查询指定 harbor 项目信息。
        GET /openapi/elastic-compute/v2/harbors/{harborId}/projects/{projectName}
        Args:
            harbor_id: 参数
            project_name: Harbor 项目名称
        """
        logger.info(f"Get harbor project: harborId={harbor_id}, project={project_name}")
        url = f"/openapi/elastic-compute/v2/harbors/{harbor_id}/projects/{project_name}"
        return self.get(endpoint=url).json()

    def delete_harbor_project_by_id(
        self, harbor_id: int, project_name: str
    ) -> Dict[str, Any]:
        """
        删除指定 harbor 项目。
        DELETE /openapi/elastic-compute/v2/harbors/{harborId}/projects/{projectName}
        Args:
            harbor_id: 参数
            project_name: Harbor 项目名称
        """
        logger.info(
            f"Delete harbor project: harborId={harbor_id}, project={project_name}"
        )
        url = f"/openapi/elastic-compute/v2/harbors/{harbor_id}/projects/{project_name}"
        return self.delete(endpoint=url).json()

    def create_harbor_project_by_id(
        self, harbor_id: int, project: HarborProjectEntity,
    ) -> Dict[str, Any]:
        """
        创建 harbor 项目。
        POST /openapi/elastic-compute/v2/harbors/{harborId}/projects

        接收 :class:`HarborProjectEntity`，内联构造 payload。``public`` 字段以
        字符串 ``'true'``/``'false'`` 形式提交（Harbor 原生 API 契约）。
        Args:
            harbor_id: 参数
            project: 参数
        """
        logger.info(
            f"Create harbor project: harborId={harbor_id}, project={project.project_name}"
        )
        url = f"/openapi/elastic-compute/v2/harbors/{harbor_id}/projects"
        payload: Dict[str, Any] = {
            "project_name": project.project_name,
            "metadata": {"public": "true" if project.public else "false"},
        }
        return self.post(endpoint=url, json=payload).json()

    def list_harbor_projects_by_id(
        self, harbor_id: int, page: int = 1, page_size: int = 10
    ) -> Dict[str, Any]:
        """
        分页查询 harbor 项目列表。
        GET /openapi/elastic-compute/v2/harbors/{harborId}/projects
        Args:
            harbor_id: 参数
            page: 页码
            page_size: 每页数量
        """
        logger.info(
            f"List harbor projects: harborId={harbor_id}, page={page}, size={page_size}"
        )
        url = f"/openapi/elastic-compute/v2/harbors/{harbor_id}/projects"
        params = {"page": page, "page_size": page_size}
        return self.get(endpoint=url, params=params).json()

    def create_harbor_project_member(
        self, harbor_id: int, project_id: int, member: HarborMemberEntity,
    ) -> Dict[str, Any]:
        """
        创建 harbor 项目成员关系。
        POST /openapi/elastic-compute/v2/harbors/{harborId}/projects/{projectId}/members

        接收 :class:`HarborMemberEntity`，内联构造 payload。
        Args:
            harbor_id: 参数
            project_id: Harbor 项目 ID
            member: 成员实体
        """
        logger.info(
            f"Create harbor project member: harborId={harbor_id}, "
            f"projectId={project_id}, username={member.username}"
        )
        url = (
            f"/openapi/elastic-compute/v2/harbors/{harbor_id}/projects/{project_id}/members"
        )
        payload: Dict[str, Any] = {
            "role_id": member.role_id,
            "member_user": {"username": member.username},
        }
        return self.post(endpoint=url, json=payload).json()

    def delete_harbor_project_member(
        self, harbor_id: int, project_id: int, member_id: int
    ) -> Dict[str, Any]:
        """
        删除 harbor 项目成员。
        DELETE /openapi/elastic-compute/v2/harbors/{harborId}/projects/{projectId}/members/{memberId}
        Args:
            harbor_id: 参数
            project_id: Harbor 项目 ID
            member_id: 成员 ID
        """
        logger.info(
            f"Delete harbor project member: harborId={harbor_id}, "
            f"projectId={project_id}, memberId={member_id}"
        )
        url = (
            f"/openapi/elastic-compute/v2/harbors/{harbor_id}/projects/{project_id}"
            f"/members/{member_id}"
        )
        return self.delete(endpoint=url).json()

    def get_harbor_registry(self, harbor_id: int, target_id: int) -> Dict[str, Any]:
        """
        查询 harbor 新注册中心/新仓库。
        GET /openapi/elastic-compute/v2/harbors/{harborId}/registries/{targetId}
        Args:
            harbor_id: 参数
            target_id: 参数
        """
        logger.info(f"Get harbor registry: harborId={harbor_id}, targetId={target_id}")
        url = f"/openapi/elastic-compute/v2/harbors/{harbor_id}/registries/{target_id}"
        return self.get(endpoint=url).json()

    def create_harbor_replication_policy(
        self, harbor_id: int, policy: HarborReplicationPolicyEntity,
    ) -> Dict[str, Any]:
        """
        添加 harbor 复制策略。
        POST /openapi/elastic-compute/v2/harbors/{harborId}/replication/policies

        接收 :class:`HarborReplicationPolicyEntity`，内联构造 payload。``src_registry``
        固定为 ``None``（默认从当前 harbor 出站），``filters`` 按 ``{project}/**`` 通配匹配。
        Args:
            harbor_id: 参数
            policy: 策略实体
        """
        logger.info(
            f"Create harbor replication policy: harborId={harbor_id}, name={policy.name}"
        )
        url = f"/openapi/elastic-compute/v2/harbors/{harbor_id}/replication/policies"
        payload: Dict[str, Any] = {
            "name": policy.name,
            "description": policy.description if policy.description is not None else policy.name,
            "src_registry": None,
            "dest_registry": {"id": policy.target_id},
            "dest_namespace": policy.project_name,
            "trigger": {
                "type": policy.trigger_type,
                "trigger_settings": {"cron": policy.trigger_cron},
            },
            "filters": [
                {"type": "name", "value": f"{policy.project_name}/**"},
            ],
            "deletion": policy.deletion,
            "override": policy.override,
            "enabled": policy.enabled,
            "speed": policy.speed,
        }
        return self.post(endpoint=url, json=payload).json()

    def list_harbor_replication_policies(
        self, harbor_id: int, name: str = None, page: int = 1, page_size: int = 10
    ) -> Dict[str, Any]:
        """
        查询 harbor 复制/备份策略列表。
        GET /openapi/elastic-compute/v2/harbors/{harborId}/replication/policies
        Args:
            harbor_id: 参数
            name: 资源名称
            page: 页码
            page_size: 每页数量
        """
        logger.info(
            f"List harbor replication policies: harborId={harbor_id}, name={name}"
        )
        url = f"/openapi/elastic-compute/v2/harbors/{harbor_id}/replication/policies"
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if name is not None:
            params["name"] = name
        return self.get(endpoint=url, params=params).json()

    def get_harbor_replication_policy(
        self, harbor_id: int, policy_id: int
    ) -> Dict[str, Any]:
        """
        查询 harbor 复制策略详情。
        GET /openapi/elastic-compute/v2/harbors/{harborId}/replication/policies/{policyId}
        Args:
            harbor_id: 参数
            policy_id: 策略 ID
        """
        logger.info(
            f"Get harbor replication policy: harborId={harbor_id}, policyId={policy_id}"
        )
        url = (
            f"/openapi/elastic-compute/v2/harbors/{harbor_id}/replication/policies/{policy_id}"
        )
        return self.get(endpoint=url).json()

    def update_harbor_replication_policy(
        self, harbor_id: int, policy_id: int,
        policy: HarborReplicationPolicyEntity,
    ) -> Dict[str, Any]:
        """
        更新 harbor 复制/备份策略。
        PUT /openapi/elastic-compute/v2/harbors/{harborId}/replication/policies/{policyId}

        接收 :class:`HarborReplicationPolicyEntity`，内联构造 payload（等同 create）。
        Args:
            harbor_id: 参数
            policy_id: 策略 ID
            policy: 策略实体
        """
        logger.info(
            f"Update harbor replication policy: harborId={harbor_id}, policyId={policy_id}"
        )
        url = (
            f"/openapi/elastic-compute/v2/harbors/{harbor_id}/replication/policies/{policy_id}"
        )
        payload: Dict[str, Any] = {
            "name": policy.name,
            "description": policy.description if policy.description is not None else policy.name,
            "src_registry": None,
            "dest_registry": {"id": policy.target_id},
            "dest_namespace": policy.project_name,
            "trigger": {
                "type": policy.trigger_type,
                "trigger_settings": {"cron": policy.trigger_cron},
            },
            "filters": [
                {"type": "name", "value": f"{policy.project_name}/**"},
            ],
            "deletion": policy.deletion,
            "override": policy.override,
            "enabled": policy.enabled,
            "speed": policy.speed,
        }
        return self.put(endpoint=url, json=payload).json()

    def delete_harbor_replication_policy(
        self, harbor_id: int, policy_id: int
    ) -> Dict[str, Any]:
        """
        删除 harbor 策略详情。
        DELETE /openapi/elastic-compute/v2/harbors/{harborId}/replication/policies/{policyId}
        Args:
            harbor_id: 参数
            policy_id: 策略 ID
        """
        logger.info(
            f"Delete harbor replication policy: harborId={harbor_id}, policyId={policy_id}"
        )
        url = (
            f"/openapi/elastic-compute/v2/harbors/{harbor_id}/replication/policies/{policy_id}"
        )
        return self.delete(endpoint=url).json()

    def start_harbor_replication_execution(
        self, harbor_id: int, policy_id: int
    ) -> Dict[str, Any]:
        """
        启动 harbor 复制策略执行。
        POST /openapi/elastic-compute/v2/harbors/{harborId}/replication/executions
        Args:
            harbor_id: 参数
            policy_id: 策略 ID
        """
        logger.info(
            f"Start harbor replication execution: harborId={harbor_id}, policyId={policy_id}"
        )
        url = f"/openapi/elastic-compute/v2/harbors/{harbor_id}/replication/executions"
        payload = {"policy_id": policy_id}
        return self.post(endpoint=url, json=payload).json()

    def list_harbor_replication_executions(
        self, harbor_id: int, policy_id: int, page: int = 1, page_size: int = 10
    ) -> Dict[str, Any]:
        """
        查询 harbor 策略执行列表。
        GET /openapi/elastic-compute/v2/harbors/{harborId}/replication/executions
        Args:
            harbor_id: 参数
            policy_id: 策略 ID
            page: 页码
            page_size: 每页数量
        """
        logger.info(
            f"List harbor replication executions: harborId={harbor_id}, policyId={policy_id}"
        )
        url = f"/openapi/elastic-compute/v2/harbors/{harbor_id}/replication/executions"
        params = {"page": page, "page_size": page_size, "policy_id": policy_id}
        return self.get(endpoint=url, params=params).json()

    def list_harbor_replication_tasks(
        self, harbor_id: int, execution_id: int
    ) -> Dict[str, Any]:
        """
        查询 harbor 复制执行任务列表。
        GET /openapi/elastic-compute/v2/harbors/{harborId}/replication/executions/{executionId}/tasks
        Args:
            harbor_id: 参数
            execution_id: 参数
        """
        logger.info(
            f"List harbor replication tasks: harborId={harbor_id}, executionId={execution_id}"
        )
        url = (
            f"/openapi/elastic-compute/v2/harbors/{harbor_id}"
            f"/replication/executions/{execution_id}/tasks"
        )
        return self.get(endpoint=url).json()

    def get_harbor_replication_task_log(
        self, harbor_id: int, execution_id: int, task_id: int
    ) -> Dict[str, Any]:
        """
        查询 harbor 复制执行任务日志。
        GET /openapi/elastic-compute/v2/harbors/{harborId}/replication/executions/{executionId}/tasks/{taskId}/log
        Args:
            harbor_id: 参数
            execution_id: 参数
            task_id: 参数
        """
        logger.info(
            f"Get harbor replication task log: harborId={harbor_id}, "
            f"executionId={execution_id}, taskId={task_id}"
        )
        url = (
            f"/openapi/elastic-compute/v2/harbors/{harbor_id}"
            f"/replication/executions/{execution_id}/tasks/{task_id}/log"
        )
        return self.get(endpoint=url).json()

    def list_harbor_repositories_by_id(
        self, harbor_id: int, project_name: str, page: int = 1, page_size: int = 10
    ) -> Dict[str, Any]:
        """
        查询 harbor 镜像仓库列表。
        GET /openapi/elastic-compute/v2/harbors/{harborId}/projects/{projectName}/repositories
        Args:
            harbor_id: 参数
            project_name: Harbor 项目名称
            page: 页码
            page_size: 每页数量
        """
        logger.info(
            f"List harbor repositories: harborId={harbor_id}, project={project_name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/harbors/{harbor_id}"
            f"/projects/{project_name}/repositories"
        )
        params = {"page": page, "page_size": page_size}
        return self.get(endpoint=url, params=params).json()

    def list_harbor_artifacts_by_id(
        self, harbor_id: int, project_name: str, rep_name: str,
        page: int = 1, page_size: int = 10,
    ) -> Dict[str, Any]:
        """
        查询 harbor 镜像库 artifacts。
        GET /openapi/elastic-compute/v2/harbors/{harborId}/projects/{projectName}/repositories/{repName}/artifacts
        Args:
            harbor_id: 参数
            project_name: Harbor 项目名称
            rep_name: 参数
            page: 页码
            page_size: 每页数量
        """
        logger.info(
            f"List harbor artifacts: harborId={harbor_id}, project={project_name}, repo={rep_name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/harbors/{harbor_id}"
            f"/projects/{project_name}/repositories/{rep_name}/artifacts"
        )
        params = {"page": page, "page_size": page_size}
        return self.get(endpoint=url, params=params).json()

    def get_harbor_repository_by_id(
        self, harbor_id: int, project_name: str, rep_name: str
    ) -> Dict[str, Any]:
        """
        获取指定的 harbor 镜像仓库。
        GET /openapi/elastic-compute/v2/harbors/{harborId}/projects/{projectName}/repositories/{repName}
        Args:
            harbor_id: 参数
            project_name: Harbor 项目名称
            rep_name: 参数
        """
        logger.info(
            f"Get harbor repository: harborId={harbor_id}, project={project_name}, repo={rep_name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/harbors/{harbor_id}"
            f"/projects/{project_name}/repositories/{rep_name}"
        )
        return self.get(endpoint=url).json()

    def delete_harbor_artifact_tag(
        self, harbor_id: int, project_name: str, rep_name: str,
        artifact: str, tag: str,
    ) -> Dict[str, Any]:
        """
        从 harbor 镜像指定 artifacts 中删除标签。
        DELETE /openapi/elastic-compute/v2/harbors/{harborId}/projects/{projectName}/repositories/{repName}/artifacts/{artifact}/tags/{tag}
        Args:
            harbor_id: 参数
            project_name: Harbor 项目名称
            rep_name: 参数
            artifact: 参数
            tag: 参数
        """
        logger.info(
            f"Delete harbor artifact tag: harborId={harbor_id}, project={project_name}, "
            f"repo={rep_name}, artifact={artifact}, tag={tag}"
        )
        url = (
            f"/openapi/elastic-compute/v2/harbors/{harbor_id}"
            f"/projects/{project_name}/repositories/{rep_name}"
            f"/artifacts/{artifact}/tags/{tag}"
        )
        return self.delete(endpoint=url).json()

    def delete_harbor_repository_by_id(
        self, harbor_id: int, project_name: str, rep_name: str
    ) -> Dict[str, Any]:
        """
        根据 harbor 镜像名删除。
        DELETE /openapi/elastic-compute/v2/harbors/{harborId}/projects/{projectName}/repositories/{repName}
        Args:
            harbor_id: 参数
            project_name: Harbor 项目名称
            rep_name: 参数
        """
        logger.info(
            f"Delete harbor repository: harborId={harbor_id}, project={project_name}, repo={rep_name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/harbors/{harbor_id}"
            f"/projects/{project_name}/repositories/{rep_name}"
        )
        return self.delete(endpoint=url).json()

    # ==================== Helm Chart 上传/下载/生命周期接口 ====================

    def upload_helm_chart(
        self, cell_code: str, chart_file_path: str
    ) -> Dict[str, Any]:
        """
        上传 Chart。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/helm/charts/upload (multipart)
        Args:
            cell_code: 单元编码
            chart_file_path: 本地 chart 包文件路径
        """
        logger.info(f"Upload helm chart: cell={cell_code}, path={chart_file_path}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/helm/charts/upload"
        with open(chart_file_path, "rb") as fh:
            files = {"file": (chart_file_path, fh, "application/octet-stream")}
            return self.post(
                endpoint=url, files=files
            ).json()

    def list_helm_charts(
        self, cell_code: str, keyword: str = None
    ) -> Dict[str, Any]:
        """
        查询 Chart 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/helm/charts?keyword=xxx
        Args:
            cell_code: 单元编码
            keyword: 搜索关键字
        """
        logger.info(f"List helm charts: cell={cell_code}, keyword={keyword}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/helm/charts"
        params = {}
        if keyword is not None:
            params["keyword"] = keyword
        return self.get(endpoint=url, params=params).json()

    def download_helm_chart(
        self, cell_code: str, chart_name: str, chart_version: str
    ):
        """
        下载 Chart。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/helm/charts/{chartName}/versions/{chartVersion}/download

        返回原始 Response 对象，调用方自行处理 status_code / content。
        Args:
            cell_code: 单元编码
            chart_name: Helm Chart 名称
            chart_version: Helm Chart 版本
        """
        logger.info(
            f"Download helm chart: cell={cell_code}, name={chart_name}, version={chart_version}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/helm/charts/{chart_name}"
            f"/versions/{chart_version}/download"
        )
        return self.get(endpoint=url)

    def helm_install(
        self, cell_code: str, sys_code: str, install: HelmInstallEntity,
    ) -> Dict[str, Any]:
        """
        Helm Install。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helm/install

        接收 :class:`HelmInstallEntity`，内联构造 payload。``values`` 字段以
        JSON 字符串形式提交。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            install: 参数
        """
        logger.info(
            f"Helm install: cell={cell_code}, sys={sys_code}, release={install.release_name}"
        )
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helm/install"
        values: Dict[str, Any] = {
            "image": {"repository": install.image_repository, "tag": install.image_tag},
            "replicaCount": install.replica_count,
        }
        payload: Dict[str, Any] = {
            "name": install.release_name,
            "chart": install.chart_name,
            "version": install.chart_version,
            "values": json.dumps(values, ensure_ascii=False),
        }
        return self.post(endpoint=url, json=payload).json()

    def helm_uninstall(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """
        Helm Uninstall。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helm/release/{name}/uninstall
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Helm uninstall: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/helm/release/{name}/uninstall"
        )
        return self.delete(endpoint=url).json()

    def get_helm_manifest(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """
        查询指定 Helm 服务详情。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helm/release/{name}/manifest
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Get helm manifest: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/helm/release/{name}/manifest"
        )
        return self.get(endpoint=url).json()

    def list_helm_releases(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询 Helm 服务列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helm/release
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List helm releases: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helm/release"
        return self.get(endpoint=url).json()

    def list_helm_release_apps(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """
        查询 Helm 服务关联应用服务状态列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helm/release/{name}/apps
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(
            f"List helm release apps: cell={cell_code}, sys={sys_code}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/helm/release/{name}/apps"
        )
        return self.get(endpoint=url).json()

    def helm_upgrade(
        self, cell_code: str, sys_code: str, name: str, upgrade: HelmUpgradeEntity,
    ) -> Dict[str, Any]:
        """
        Helm Upgrade。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helm/release/{name}/upgrade

        接收 :class:`HelmUpgradeEntity`，内联构造 payload。``values`` 字段以
        JSON 字符串形式提交。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            upgrade: 参数
        """
        logger.info(f"Helm upgrade: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/helm/release/{name}/upgrade"
        )
        values: Dict[str, Any] = {
            "image": {"repository": upgrade.image_repository, "tag": upgrade.image_tag},
            "replicaCount": upgrade.replica_count,
        }
        payload: Dict[str, Any] = {
            "chart": upgrade.chart_name,
            "version": upgrade.chart_version,
            "values": json.dumps(values, ensure_ascii=False),
        }
        return self.post(endpoint=url, json=payload).json()

    def list_helm_history(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """
        查询 Helm 服务历史版本列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helm/release/{name}/history
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"List helm history: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/helm/release/{name}/history"
        )
        return self.get(endpoint=url).json()

    def helm_rollback(
        self, cell_code: str, sys_code: str, name: str, revision: int
    ) -> Dict[str, Any]:
        """
        Helm Rollback。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helm/release/{name}/rollback?revision=X
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            revision: 版本号
        """
        logger.info(
            f"Helm rollback: cell={cell_code}, sys={sys_code}, name={name}, revision={revision}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/helm/release/{name}/rollback"
        )
        params = {"revision": revision}
        return self.post(endpoint=url, params=params).json()

    def delete_helm_chart_by_name(
        self, cell_code: str, chart_name: str, version: str
    ) -> Dict[str, Any]:
        """
        删除 Chart。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/helm/charts/{chartName}?version=X
        Args:
            cell_code: 单元编码
            chart_name: Helm Chart 名称
            version: CR API version
        """
        logger.info(
            f"Delete helm chart by name: cell={cell_code}, chart={chart_name}, version={version}"
        )
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/helm/charts/{chart_name}"
        params = {"version": version}
        return self.delete(endpoint=url, params=params).json()

    # ==================== 镜像查询接口 ====================

    def list_images(self) -> Dict[str, Any]:
        """
        获取镜像列表。
        GET /openapi/elastic-compute/v1/images
        """
        logger.info("List images")
        return self.get(
            endpoint="/openapi/elastic-compute/v1/images",
        ).json()

    def list_image_apps(
        self, cluster_id: int, namespace: str,
        project_name: str, image_name: str, version: str,
    ) -> Dict[str, Any]:
        """
        获取镜像已部署应用服务列表。
        GET /openapi/elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/images/apps
        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            project_name: Harbor 项目名称
            image_name: 参数
            version: CR API version
        """
        logger.info(
            f"List image apps: clusterId={cluster_id}, namespace={namespace}, "
            f"project={project_name}, image={image_name}, version={version}"
        )
        url = (
            f"/openapi/elastic-compute/v1/clusters/{cluster_id}"
            f"/namespaces/{namespace}/images/apps"
        )
        params = {
            "projectName": project_name,
            "imageName": image_name,
            "version": version,
        }
        return self.get(endpoint=url, params=params).json()

    # ==================== ImagePullSecret 接口 ====================

    def create_image_pull_secret(
        self, cell_code: str, sys_code: str,
    ) -> Dict[str, Any]:
        """
        创建 ImagePullSecret。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/imagePullSecrets

        备注：不指定请求体（postBodyRaw=false），依赖服务端根据 cell/sys 自动生成。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(
            f"Create imagePullSecret: cell={cell_code}, sys={sys_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/imagePullSecrets"
        )
        return self.post(endpoint=url).json()

    def delete_secret_by_name(
        self, cell_code: str, sys_code: str, secret_name: str,
    ) -> Dict[str, Any]:
        """
        删除指定 Secret（含 ImagePullSecret）。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/secrets/{secretName}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            secret_name: Secret 名称
        """
        logger.info(
            f"Delete secret: cell={cell_code}, sys={sys_code}, name={secret_name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/secrets/{secret_name}"
        )
        return self.delete(endpoint=url).json()

    # ==================== v2 无 name 版本（namespace 级别唯一） ====================

    def create_limitrange_ns(
        self, cell_code: str, sys_code: str, limit_range: K8sLimitRangeEntity,
    ) -> Dict[str, Any]:
        """
        创建 LimitRange（namespace 级唯一，路径无 name）。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/limitRanges

        接收 :class:`K8sLimitRangeEntity`，内联构造 K8s LimitRange payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            limit_range: LimitRange 实体
        """
        logger.info(
            f"Create limitRange (ns): cell={cell_code}, sys={sys_code}, name={limit_range.name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitRanges"
        )
        payload: Dict[str, Any] = {
            "apiVersion": limit_range.api_version,
            "kind": limit_range.kind,
            "metadata": {"name": limit_range.name},
            "spec": {
                "limits": [
                    {
                        "default": {
                            "cpu": limit_range.default_cpu,
                            "memory": limit_range.default_memory,
                        },
                        "defaultRequest": {
                            "cpu": limit_range.default_request_cpu,
                            "memory": limit_range.default_request_memory,
                        },
                        "type": limit_range.limit_type,
                    }
                ]
            },
        }
        return self.post(endpoint=url, json=payload).json()

    def update_limitrange_ns(
        self, cell_code: str, sys_code: str, limit_range: K8sLimitRangeEntity,
    ) -> Dict[str, Any]:
        """
        全量更新 LimitRange（namespace 级唯一，路径无 name）。
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/limitRanges

        接收 :class:`K8sLimitRangeEntity`，内联构造 K8s LimitRange payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            limit_range: LimitRange 实体
        """
        logger.info(
            f"Update limitRange (ns): cell={cell_code}, sys={sys_code}, name={limit_range.name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitRanges"
        )
        payload: Dict[str, Any] = {
            "apiVersion": limit_range.api_version,
            "kind": limit_range.kind,
            "metadata": {"name": limit_range.name},
            "spec": {
                "limits": [
                    {
                        "default": {
                            "cpu": limit_range.default_cpu,
                            "memory": limit_range.default_memory,
                        },
                        "defaultRequest": {
                            "cpu": limit_range.default_request_cpu,
                            "memory": limit_range.default_request_memory,
                        },
                        "type": limit_range.limit_type,
                    }
                ]
            },
        }
        return self.put(endpoint=url, json=payload).json()

    def patch_limitrange_ns(
        self, cell_code: str, sys_code: str,
        limit_range: Optional[K8sLimitRangeEntity] = None,
    ) -> Dict[str, Any]:
        """
        增量更新 LimitRange（namespace 级唯一，路径无 name）。
        PATCH /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/limitRanges

        接收可选的 :class:`K8sLimitRangeEntity`。当 ``limit_range`` 为 ``None`` 时，
        提交空对象 ``{}``；否则内联
        构造 K8s LimitRange payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            limit_range: LimitRange 实体
        """
        logger.info(
            f"Patch limitRange (ns): cell={cell_code}, sys={sys_code}, "
            f"has_body={limit_range is not None}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitRanges"
        )
        if limit_range is None:
            payload: Dict[str, Any] = {}
        else:
            payload = {
                "apiVersion": limit_range.api_version,
                "kind": limit_range.kind,
                "metadata": {"name": limit_range.name},
                "spec": {
                    "limits": [
                        {
                            "default": {
                                "cpu": limit_range.default_cpu,
                                "memory": limit_range.default_memory,
                            },
                            "defaultRequest": {
                                "cpu": limit_range.default_request_cpu,
                                "memory": limit_range.default_request_memory,
                            },
                            "type": limit_range.limit_type,
                        }
                    ]
                },
            }
        return self.patch(endpoint=url, json=payload).json()

    def delete_limitrange_ns(
        self, cell_code: str, sys_code: str,
    ) -> Dict[str, Any]:
        """
        删除 LimitRange（namespace 级唯一，路径无 name）。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/limitRanges
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(
            f"Delete limitRange (ns): cell={cell_code}, sys={sys_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitRanges"
        )
        return self.delete(endpoint=url).json()

    def list_limitranges_by_cell_v2(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群 LimitRange 列表（大写 R 版本）。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/limitRanges
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List limitRanges by cell (v2): cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/limitRanges",
        ).json()

    def list_limitranges_by_ns_v2(
        self, cell_code: str, sys_code: str,
    ) -> Dict[str, Any]:
        """
        查询命名空间下 LimitRange（大写 R 版本）。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/limitRanges
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(
            f"List limitRanges by ns (v2): cell={cell_code}, sys={sys_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitRanges"
        )
        return self.get(endpoint=url).json()

    # ==================== oidc-harborinit OIDC 接口 ====================

    def get_oidc_info(self) -> Dict[str, Any]:
        """
        获取 OIDC 信息。
        GET /openapi/elastic-compute/v2/oidc/info
        """
        logger.info("Get OIDC info")
        url = "/openapi/elastic-compute/v2/oidc/info"
        return self.get(endpoint=url).json()

    # ==================== pod Pod 接口 ====================

    def get_pod(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        查询指定 Pod。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pods/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: Pod 名称
        """
        logger.info(f"Get Pod: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pods/{name}"
        return self.get(endpoint=url).json()

    def create_pod(
        self, cell_code: str, sys_code: str, pod: K8sPodEntity,
    ) -> Dict[str, Any]:
        """
        创建 Pod。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pods

        接收 :class:`K8sPodEntity`，内联构造 K8s Pod payload（单容器 + 单端口）。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            pod: Pod 实体
        """
        logger.info(f"Create Pod: cell={cell_code}, sys={sys_code}, name={pod.name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pods"
        payload: Dict[str, Any] = {
            "apiVersion": pod.api_version,
            "kind": pod.kind,
            "metadata": {
                "name": pod.name,
                "labels": {"name": pod.name, "kind": pod.kind},
            },
            "spec": {
                "containers": [
                    {
                        "image": pod.image,
                        "name": pod.container_name,
                        "ports": [
                            {
                                "containerPort": pod.container_port,
                                "name": pod.port_name,
                                "protocol": pod.port_protocol,
                            }
                        ],
                    }
                ]
            },
        }
        return self.post(endpoint=url, json=payload).json()

    def delete_pod(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        删除指定 Pod。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pods/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: Pod 名称
        """
        logger.info(f"Delete Pod: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pods/{name}"
        return self.delete(endpoint=url).json()

    def list_pods_by_ns(
        self, cell_code: str, sys_code: str, label_selector: str = None,
    ) -> Dict[str, Any]:
        """
        查询 Namespace 下 Pod 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pods
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            label_selector: 标签选择器（可选）
        """
        logger.info(f"List Pods by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pods"
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        return self.get(endpoint=url, params=params).json()

    def list_pods_by_cell(
        self, cell_code: str, label_selector: str = None,
    ) -> Dict[str, Any]:
        """
        查询全集群 Pod 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/pods
        Args:
            cell_code: 单元编码
            label_selector: 标签选择器（可选）
        """
        logger.info(f"List Pods by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/pods"
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        return self.get(endpoint=url, params=params).json()

    def list_pod_events(
        self, cell_code: str, sys_code: str, name: str,
    ) -> Dict[str, Any]:
        """
        查询 Pod 事件列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pods/{name}/events
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: Pod 名称
        """
        logger.info(f"List Pod events: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/pods/{name}/events"
        )
        return self.get(endpoint=url).json()

    def get_pod_logs(
        self, cell_code: str, sys_code: str, name: str, container: str,
    ) -> Dict[str, Any]:
        """
        查询 Pod 容器日志。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pods/{name}/containers/{container}/logs
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: Pod 名称
            container: 容器名称
        """
        logger.info(
            f"Get Pod logs: cell={cell_code}, sys={sys_code}, name={name}, container={container}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/pods/{name}/containers/{container}/logs"
        )
        return self.get(endpoint=url).json()

    def update_pod(
        self, cell_code: str, sys_code: str, name: str, pod: K8sPodRawEntity,
    ) -> Dict[str, Any]:
        """
        PUT 全量更新指定 Pod。
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pods/{name}

        接收 :class:`K8sPodRawEntity`，其 ``body`` 字段即完整的 K8s Pod 对象
        （由前置 GET 请求获得并局部修改后回传）。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            pod: Pod 实体
        """
        logger.info(f"Update Pod: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pods/{name}"
        return self.put(endpoint=url, json=pod.body).json()

    def patch_pod(
        self, cell_code: str, sys_code: str, name: str, pod: K8sPodPatchEntity,
    ) -> Dict[str, Any]:
        """
        PATCH 增量更新指定 Pod。
        PATCH /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pods/{name}

        接收 :class:`K8sPodPatchEntity`，内联构造 ``metadata.labels`` patch payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            pod: Pod 实体
        """
        logger.info(f"Patch Pod: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pods/{name}"
        payload: Dict[str, Any] = {"metadata": {"labels": pod.labels}}
        return self.patch(endpoint=url, json=payload).json()

    # ==================== port-nodeport Port/NodePort 接口 ====================

    def list_nodeports(self, cell_code: str) -> Dict[str, Any]:
        """
        查询租户指定集群实际使用 NodePort 端口列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/nodeports
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List nodeports: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/nodeports"
        return self.get(endpoint=url).json()

    def get_nodeport(self, cell_code: str, nodeport: str) -> Dict[str, Any]:
        """
        查询指定 NodePort 是否可以使用。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/nodeports/{nodeport}
        Args:
            cell_code: 单元编码
            nodeport: NodePort 端口号
        """
        logger.info(f"Get nodeport: cell={cell_code}, nodeport={nodeport}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/nodeports/{nodeport}"
        return self.get(endpoint=url).json()

    def allocate_ports(self, cell_code: str, allocation: PortAllocationEntity) -> Dict[str, Any]:
        """
        租户 NodePort 端口范围分配 (Admin)。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/ports
        Args:
            cell_code: 单元编码
            allocation: :class:`PortAllocationEntity` 端口分配实体
        """
        logger.info(f"Allocate ports: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/ports"
        payload: Dict[str, Any] = {
            "kind": allocation.kind,
            "tenantCode": allocation.tenant_code,
            "ports": [allocation.ports],
        }
        return self.post(endpoint=url, json=payload).json()

    def list_ports_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询租户指定集群 NodePort 端口范围。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/ports
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List ports by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/ports"
        return self.get(endpoint=url).json()

    def list_all_ports(self) -> Dict[str, Any]:
        """
        查询租户全部 NodePort 端口范围。
        GET /openapi/elastic-compute/v2/ports
        """
        logger.info("List all ports")
        url = "/openapi/elastic-compute/v2/ports"
        return self.get(endpoint=url).json()

    # ==================== quota-manager-admin 配额管理（管理员）接口 ====================

    def get_cluster_quota_overview(self, cell_code: str) -> Dict[str, Any]:
        """
        查询集群资源配额概览。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/quota
        Args:
            cell_code: 单元编码
        """
        logger.info(f"Get cluster quota overview: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/quota"
        return self.get(endpoint=url).json()

    def batch_query_tenant_quotas(self, tenant_codes: List[str]) -> Dict[str, Any]:
        """
        批量查询多租户资源配额总览列表。
        POST /openapi/elastic-compute/v2/tenants/quota/batch
        Args:
            tenant_codes: 待批量查询的租户 code 列表
        """
        logger.info(f"Batch query tenant quotas, tenants={tenant_codes}")
        url = "/openapi/elastic-compute/v2/tenants/quota/batch"
        payload: Dict[str, Any] = {"tenantCodeList": list(tenant_codes)}
        return self.post(endpoint=url, json=payload).json()

    def allocate_tenant_quota(
        self, cell_code: str, tenant_code: str, allocation: TenantQuotaAllocationEntity,
    ) -> Dict[str, Any]:
        """
        租户资源配额分配。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/tenants/{tenantCode}/quota/allocate

        接收 :class:`TenantQuotaAllocationEntity`，未设置的字段不会写入 payload
        。
        Args:
            cell_code: 单元编码
            tenant_code: 租户编码
            allocation: 参数
        """
        logger.info(f"Allocate tenant quota: cell={cell_code}, tenant={tenant_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/tenants/{tenant_code}/quota/allocate"
        payload: Dict[str, Any] = {}
        if allocation.cpu is not None:
            payload["cpu"] = allocation.cpu
        if allocation.memory is not None:
            payload["memory"] = allocation.memory
        if allocation.extras is not None:
            payload.update(allocation.extras)
        return self.post(endpoint=url, json=payload).json()

    def scale_tenant_quota(
        self, cell_code: str, tenant_code: str, allocation: TenantQuotaAllocationEntity,
    ) -> Dict[str, Any]:
        """
        租户资源配额调整（扩缩容）。
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/tenants/{tenantCode}/quota/scale

        接收 :class:`TenantQuotaAllocationEntity`，未设置的字段不会写入 payload。
        Args:
            cell_code: 单元编码
            tenant_code: 租户编码
            allocation: 参数
        """
        logger.info(f"Scale tenant quota: cell={cell_code}, tenant={tenant_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/tenants/{tenant_code}/quota/scale"
        payload: Dict[str, Any] = {}
        if allocation.cpu is not None:
            payload["cpu"] = allocation.cpu
        if allocation.memory is not None:
            payload["memory"] = allocation.memory
        if allocation.extras is not None:
            payload.update(allocation.extras)
        return self.put(endpoint=url, json=payload).json()

    def get_system_quota_overview(self, tenant_code: str, sys_code: str) -> Dict[str, Any]:
        """
        系统资源配额各集群概览。
        GET /openapi/elastic-compute/v2/tenants/{tenantCode}/systems/{sysCode}/quota
        Args:
            tenant_code: 租户编码
            sys_code: 系统编码
        """
        logger.info(f"Get system quota overview: tenant={tenant_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/tenants/{tenant_code}/systems/{sys_code}/quota"
        return self.get(endpoint=url).json()

    def get_system_quota_detail(
        self, cell_code: str, tenant_code: str, sys_code: str,
    ) -> Dict[str, Any]:
        """
        系统资源配额详情。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/tenants/{tenantCode}/systems/{sysCode}/quota/detail
        Args:
            cell_code: 单元编码
            tenant_code: 租户编码
            sys_code: 系统编码
        """
        logger.info(
            f"Get system quota detail: cell={cell_code}, tenant={tenant_code}, sys={sys_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/tenants/{tenant_code}"
            f"/systems/{sys_code}/quota/detail"
        )
        return self.get(endpoint=url).json()

    def get_system_quota_scalable(
        self, cell_code: str, tenant_code: str, sys_code: str,
    ) -> Dict[str, Any]:
        """
        系统可调整资源配额查询。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/tenants/{tenantCode}/systems/{sysCode}/quota/scale
        Args:
            cell_code: 单元编码
            tenant_code: 租户编码
            sys_code: 系统编码
        """
        logger.info(
            f"Get system quota scalable: cell={cell_code}, tenant={tenant_code}, sys={sys_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/tenants/{tenant_code}"
            f"/systems/{sys_code}/quota/scale"
        )
        return self.get(endpoint=url).json()

    def get_tenant_quota_detail(self, cell_code: str, tenant_code: str) -> Dict[str, Any]:
        """
        查询租户资源配额详情。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/tenants/{tenantCode}/quota/detail
        Args:
            cell_code: 单元编码
            tenant_code: 租户编码
        """
        logger.info(f"Get tenant quota detail: cell={cell_code}, tenant={tenant_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/tenants/{tenant_code}/quota/detail"
        return self.get(endpoint=url).json()

    def list_tenant_quotas_by_cell(self, cell_code: str, tenant_code: str) -> Dict[str, Any]:
        """
        查询租户资源配额列表（按单元区分）。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/tenants/{tenantCode}/quotas
        Args:
            cell_code: 单元编码
            tenant_code: 租户编码
        """
        logger.info(f"List tenant quotas by cell: cell={cell_code}, tenant={tenant_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/tenants/{tenant_code}/quotas"
        return self.get(endpoint=url).json()

    def list_tenant_quotas(self, tenant_code: str) -> Dict[str, Any]:
        """
        查询租户资源配额列表。
        GET /openapi/elastic-compute/v2/tenants/{tenantCode}/quotas
        Args:
            tenant_code: 租户编码
        """
        logger.info(f"List tenant quotas: tenant={tenant_code}")
        url = f"/openapi/elastic-compute/v2/tenants/{tenant_code}/quotas"
        return self.get(endpoint=url).json()

    def get_tenant_quota_overview(self, tenant_code: str) -> Dict[str, Any]:
        """
        租户资源配额总览。
        GET /openapi/elastic-compute/v2/tenants/{tenantCode}/quota
        Args:
            tenant_code: 租户编码
        """
        logger.info(f"Get tenant quota overview: tenant={tenant_code}")
        url = f"/openapi/elastic-compute/v2/tenants/{tenant_code}/quota"
        return self.get(endpoint=url).json()

    def get_tenant_cell_quota_overview(self, cell_code: str, tenant_code: str) -> Dict[str, Any]:
        """
        单租户资源配额单集群下总览信息。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/tenants/{tenantCode}/quota
        Args:
            cell_code: 单元编码
            tenant_code: 租户编码
        """
        logger.info(f"Get tenant cell quota overview: cell={cell_code}, tenant={tenant_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/tenants/{tenant_code}/quota"
        return self.get(endpoint=url).json()

    def get_tenant_quota_scalable(self, cell_code: str, tenant_code: str) -> Dict[str, Any]:
        """
        租户可调整资源配额查询。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/tenants/{tenantCode}/quota/scale
        Args:
            cell_code: 单元编码
            tenant_code: 租户编码
        """
        logger.info(f"Get tenant quota scalable: cell={cell_code}, tenant={tenant_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/tenants/{tenant_code}/quota/scale"
        return self.get(endpoint=url).json()

    # ==================== quota-manager-tenant 配额管理（租户管理员）接口 ====================

    def allocate_system_quota(
        self, cell_code: str, tenant_code: str, sys_code: str,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        租户管理员审批通过系统资源申请时调用。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/tenants/{tenantCode}/systems/{sysCode}/quota/allocate
        Args:
            cell_code: 单元编码
            tenant_code: 租户编码
            sys_code: 系统编码
            username: 用户名
        """
        logger.info(
            f"Allocate system quota: cell={cell_code}, tenant={tenant_code}, sys={sys_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/tenants/{tenant_code}"
            f"/systems/{sys_code}/quota/allocate"
        )
        payload: Dict[str, Any] = {}
        if username is not None:
            payload["username"] = username
        return self.post(endpoint=url, json=payload).json()

    def scale_system_quota(
        self, cell_code: str, tenant_code: str, sys_code: str,
    ) -> Dict[str, Any]:
        """
        针对系统资源配额进行扩缩容。
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/tenants/{tenantCode}/systems/{sysCode}/quota/scale
        Args:
            cell_code: 单元编码
            tenant_code: 租户编码
            sys_code: 系统编码
        """
        logger.info(
            f"Scale system quota: cell={cell_code}, tenant={tenant_code}, sys={sys_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/tenants/{tenant_code}"
            f"/systems/{sys_code}/quota/scale"
        )
        return self.put(endpoint=url, json={}).json()


    def get_scaled_object(
        self, cell_code: str, sys_code: str, name: str,
    ) -> Dict[str, Any]:
        """
        查询指定 ScaledObject。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/scaledObject/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Get ScaledObject: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/scaledObject/{name}"
        )
        return self.get(endpoint=url).json()

    def create_scaled_object(
        self, cell_code: str, sys_code: str, scaled_object: ScaledObjectEntity,
    ) -> Dict[str, Any]:
        """
        创建 ScaledObject。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/scaledObject

        接收 :class:`ScaledObjectEntity`，内联构造 payload（snake_case → camelCase 转换）。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            scaled_object: 参数
        """
        logger.info(f"Create ScaledObject: cell={cell_code}, sys={sys_code}, name={scaled_object.name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/scaledObject"
        payload: Dict[str, Any] = {
            "name": scaled_object.name,
            "workloadKind": scaled_object.workload_kind,
            "workloadName": scaled_object.workload_name,
            "pollingInterval": scaled_object.polling_interval,
            "cooldownPeriod": scaled_object.cooldown_period,
            "minReplicaCount": scaled_object.min_replica_count,
            "maxReplicaCount": scaled_object.max_replica_count,
            "restoreToOriginalReplicaCount": scaled_object.restore_to_original_replica_count,
            "timezone": scaled_object.timezone,
            "start": scaled_object.start,
            "end": scaled_object.end,
            "desiredReplicas": scaled_object.desired_replicas,
        }
        return self.post(endpoint=url, json=payload).json()

    def update_scaled_object(
        self, cell_code: str, sys_code: str, name: str, patch: ScaledObjectPatchEntity,
    ) -> Dict[str, Any]:
        """
        更新 ScaledObject。


        接收 :class:`ScaledObjectPatchEntity`，内联构造 payload。
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/scaledObject/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
            patch: PATCH 增量更新实体
        """
        logger.info(f"Update ScaledObject: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/scaledObject/{name}"
        )
        payload: Dict[str, Any] = {"start": patch.start, "end": patch.end}
        return self.put(endpoint=url, json=payload).json()

    def delete_scaled_object(
        self, cell_code: str, sys_code: str, name: str,
    ) -> Dict[str, Any]:
        """
        删除 ScaledObject。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/scaledObject/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Delete ScaledObject: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/scaledObject/{name}"
        )
        return self.delete(endpoint=url).json()


    def list_recovery_resources(
        self, sys_code: str, cell_code: str,
    ) -> Dict[str, Any]:
        """
        查询容灾组件资源列表。
        GET /openapi/elastic-compute/v2/systems/{sysCode}/resources?cells={cellCode}
        Args:
            sys_code: 系统编码
            cell_code: 单元编码
        """
        logger.info(f"List recovery resources: sys={sys_code}, cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/systems/{sys_code}/resources"
        return self.get(
            endpoint=url, params={"cells": cell_code},
        ).json()

    def create_recovery_resources(
        self, cell_code: str, sys_code: str, resources: List[RecoveryResourceEntity],
    ) -> Dict[str, Any]:
        """
        创建容灾组件资源（批量，body 为数组）。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/resources

        接收 :class:`RecoveryResourceEntity` 列表，内联构造数组 payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            resources: 参数
        """
        logger.info(f"Create recovery resources: cell={cell_code}, sys={sys_code}, count={len(resources)}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/resources"
        )
        payload: List[Dict[str, Any]] = [
            {
                "name": r.name,
                "appName": r.app_name,
                "kind": r.kind,
                "image": r.image,
                "tenantCode": r.tenant_code,
                "appCode": r.app_code,
                "planeCode": r.plane_code,
                "unitCode": r.unit_code,
                "envCode": r.env_code,
                "username": r.username,
            }
            for r in resources
        ]
        return self.post(endpoint=url, json=payload).json()

    def delete_recovery_resources(
        self, cell_code: str, sys_code: str, resource_names: List[str],
    ) -> Dict[str, Any]:
        """
        删除容灾组件资源（批量，body 为名称数组）。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/resources/delete
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            resource_names: 参数
        """
        logger.info(f"Delete recovery resources: cell={cell_code}, sys={sys_code}, names={resource_names}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resources/delete"
        )
        return self.delete(endpoint=url, json=list(resource_names)).json()

    def apply_recovery_resources(
        self, cell_code: str, sys_code: str, resources: List[RecoveryResourceEntity],
    ) -> Dict[str, Any]:
        """
        Apply 容灾组件资源。
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/resources/apply

        接收 :class:`RecoveryResourceEntity` 列表，内联构造数组 payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            resources: 参数
        """
        logger.info(f"Apply recovery resources: cell={cell_code}, sys={sys_code}, count={len(resources)}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resources/apply"
        )
        payload: List[Dict[str, Any]] = [
            {
                "name": r.name,
                "appName": r.app_name,
                "kind": r.kind,
                "image": r.image,
                "tenantCode": r.tenant_code,
                "appCode": r.app_code,
                "planeCode": r.plane_code,
                "unitCode": r.unit_code,
                "envCode": r.env_code,
                "username": r.username,
            }
            for r in resources
        ]
        return self.post(endpoint=url, json=payload).json()


    def list_replica_sets_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群 ReplicaSet 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/replicaSets
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List replicaSets by cell: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/replicaSets",
        ).json()

    def list_replica_sets_by_ns(
        self, cell_code: str, sys_code: str,
    ) -> Dict[str, Any]:
        """
        查询命名空间下 ReplicaSet 列表。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/replicaSets
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List replicaSets by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/replicaSets"
        return self.get(endpoint=url).json()

    def get_replica_set(
        self, cell_code: str, sys_code: str, name: str,
    ) -> Dict[str, Any]:
        """
        查询指定 ReplicaSet。
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/replicaSets/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(f"Get replicaSet: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/replicaSets/{name}"
        )
        return self.get(endpoint=url).json()

    # ==================== (NS-level, no name) ====================

    def update_resource_quotas_ns(
        self, cell_code: str, sys_code: str, quota: K8sResourceQuotaEntity,
    ) -> Dict[str, Any]:
        """
        PUT 全量更新命名空间级 ResourceQuota（无 name 参数）。
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/resourceQuotas

        接收 :class:`K8sResourceQuotaEntity`，内联构造 K8s spec.hard payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            quota: ResourceQuota 实体
        """
        logger.info(f"Update resourceQuotas (ns-level): cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/resourceQuotas"
        payload: Dict[str, Any] = {"spec": {"hard": dict(quota.hard)}}
        return self.put(endpoint=url, json=payload).json()

    def patch_resource_quotas_ns(
        self, cell_code: str, sys_code: str, patch: K8sResourceQuotaPatchEntity,
    ) -> Dict[str, Any]:
        """
        PATCH 增量更新命名空间级 ResourceQuota（无 name 参数）。
        PATCH /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/resourceQuotas

        接收 :class:`K8sResourceQuotaPatchEntity`，内联构造 strategic merge patch payload。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            patch: PATCH 增量更新实体
        """
        logger.info(f"Patch resourceQuotas (ns-level): cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/resourceQuotas"
        payload: Dict[str, Any] = {"spec": {"hard": dict(patch.hard)}}
        return self.patch(endpoint=url, json=payload).json()

    def delete_resource_quotas_ns(
        self, cell_code: str, sys_code: str,
    ) -> Dict[str, Any]:
        """
        删除命名空间级 ResourceQuota（无 name 参数）。
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/resourceQuotas
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"Delete resourceQuotas (ns-level): cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/resourceQuotas"
        return self.delete(endpoint=url).json()


    def list_workloads_by_ns_kind(
        self, cell_code: str, sys_code: str, kind: str
    ) -> Dict[str, Any]:
        """
        按命名空间+Kind 查询工作负载列表。
        GET /.../kinds/{kind}/workloads
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
        """
        logger.info(
            f"List workloads by ns+kind: cell={cell_code}, sys={sys_code}, kind={kind}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads"
        )
        return self.get(endpoint=url).json()

    def list_workloads_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        按命名空间查询工作负载列表。
        GET /.../workloads
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List workloads by ns: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/workloads"
        )
        return self.get(endpoint=url).json()

    def list_workloads_by_cell_kind(
        self, cell_code: str, kind: str
    ) -> Dict[str, Any]:
        """
        按集群+Kind 查询工作负载列表。
        GET /.../kinds/{kind}/workloads
        Args:
            cell_code: 单元编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
        """
        logger.info(f"List workloads by cell+kind: cell={cell_code}, kind={kind}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/kinds/{kind}/workloads"
        )
        return self.get(endpoint=url).json()

    def list_workloads_by_sys_kind(
        self, sys_code: str, kind: str
    ) -> Dict[str, Any]:
        """
        按系统+Kind 查询工作负载列表。
        GET /.../systems/{sysCode}/kinds/{kind}/workloads
        Args:
            sys_code: 系统编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
        """
        logger.info(f"List workloads by sys+kind: sys={sys_code}, kind={kind}")
        url = (
            f"/openapi/elastic-compute/v2/systems/{sys_code}/kinds/{kind}/workloads"
        )
        return self.get(endpoint=url).json()

    def list_workloads_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        按集群查询工作负载列表。
        GET /.../cells/{cellCode}/workloads
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List workloads by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/workloads"
        return self.get(endpoint=url).json()

    def list_workloads_by_sys(self, sys_code: str) -> Dict[str, Any]:
        """
        按系统查询工作负载列表。
        GET /.../systems/{sysCode}/workloads
        Args:
            sys_code: 系统编码
        """
        logger.info(f"List workloads by sys: sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/systems/{sys_code}/workloads"
        return self.get(endpoint=url).json()

    def list_workloads_by_kind(self, kind: str) -> Dict[str, Any]:
        """
        按 Kind 查询工作负载列表。
        GET /.../kinds/{kind}/workloads
        Args:
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
        """
        logger.info(f"List workloads by kind: kind={kind}")
        url = f"/openapi/elastic-compute/v2/kinds/{kind}/workloads"
        return self.get(endpoint=url).json()

    def list_all_workloads(self) -> Dict[str, Any]:
        """
        查询所有工作负载列表。
        GET /.../workloads
        """
        logger.info("List all workloads")
        url = "/openapi/elastic-compute/v2/workloads"
        return self.get(endpoint=url).json()

    def get_workload_topology_with_app(
        self, cell_code: str, sys_code: str, app_code: str, name: str
    ) -> Dict[str, Any]:
        """
        查询工作负载拓扑信息（含 appCode）。
        GET /.../appcode/{appCode}/workloads/{name}/topologyinfo
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            app_code: 应用编码
            name: 资源名称
        """
        logger.info(
            f"Get workload topology with app: cell={cell_code}, sys={sys_code}, "
            f"app={app_code}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/appcode/{app_code}/workloads/{name}/topologyinfo"
        )
        return self.get(endpoint=url).json()

    def get_workload_topology(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """
        查询工作负载拓扑信息。
        GET /.../workloads/{name}/topologyinfo
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: 资源名称
        """
        logger.info(
            f"Get workload topology: cell={cell_code}, sys={sys_code}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/workloads/{name}/topologyinfo"
        )
        return self.get(endpoint=url).json()

    def get_ns_topology_with_app(
        self, cell_code: str, sys_code: str, app_code: str
    ) -> Dict[str, Any]:
        """
        查询命名空间拓扑信息（含 appCode）。
        GET /.../appcode/{appCode}/topologyinfo
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            app_code: 应用编码
        """
        logger.info(
            f"Get ns topology with app: cell={cell_code}, sys={sys_code}, app={app_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/appcode/{app_code}/topologyinfo"
        )
        return self.get(endpoint=url).json()

    def get_ns_topology(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询命名空间拓扑信息。
        GET /.../topologyinfo
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"Get ns topology: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/topologyinfo"
        )
        return self.get(endpoint=url).json()

    def list_deployments_by_ns(
        self, cell_code: str, sys_code: str
    ) -> Dict[str, Any]:
        """
        查询命名空间下 Deployment 列表。
        GET /.../deployments
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List deployments by ns: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/deployments"
        )
        return self.get(endpoint=url).json()

    def list_deployments_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询集群下 Deployment 列表。
        GET /.../deployments
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List deployments by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/deployments"
        return self.get(endpoint=url).json()

    def list_statefulsets_by_ns(
        self, cell_code: str, sys_code: str
    ) -> Dict[str, Any]:
        """
        查询命名空间下 StatefulSet 列表。
        GET /.../statefulsets
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List statefulsets by ns: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/statefulsets"
        )
        return self.get(endpoint=url).json()

    def list_statefulsets_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询集群下 StatefulSet 列表。
        GET /.../statefulsets
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List statefulsets by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/statefulsets"
        return self.get(endpoint=url).json()

    def list_daemonsets_by_ns(
        self, cell_code: str, sys_code: str
    ) -> Dict[str, Any]:
        """
        查询命名空间下 DaemonSet 列表。
        GET /.../daemonsets
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        logger.info(f"List daemonsets by ns: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/daemonsets"
        )
        return self.get(endpoint=url).json()

    def list_daemonsets_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询集群下 DaemonSet 列表。
        GET /.../daemonsets
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List daemonsets by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/daemonsets"
        return self.get(endpoint=url).json()

    def list_workload_events(self, cell_code: str) -> Dict[str, Any]:
        """
        查询集群工作负载事件。
        GET /.../workloads/events
        Args:
            cell_code: 单元编码
        """
        logger.info(f"List workload events: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/workloads/events"
        return self.get(endpoint=url).json()

    # ==================== (CRUD + Lifecycle) ====================

    def get_workload_status(
        self, cell_code: str, sys_code: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        查询工作负载状态。
        GET /.../kinds/{kind}/workloads/{name}/status
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
        """
        logger.info(
            f"Get workload status: cell={cell_code}, sys={sys_code}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads/{name}/status"
        )
        return self.get(endpoint=url).json()

    def create_workload(
        self, cell_code: str, sys_code: str, app_code: str,
        workload: WorkloadCreateEntity,
    ) -> Dict[str, Any]:
        """
        创建工作负载。
        POST /.../apps/{appCode}/workloads?paas-app-service-version=v1
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            app_code: 应用编码
            workload: Workload 实体
        """
        logger.info(
            f"Create workload: cell={cell_code}, sys={sys_code}, app={app_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/apps/{app_code}/workloads?paas-app-service-version=v1"
        )
        payload: Dict[str, Any] = {
            "workload": {
                "apiVersion": "apps/v1",
                "kind": workload.kind,
                "metadata": {
                    "name": workload.name,
                    "labels": {
                        "name": workload.name,
                        "kind": workload.kind,
                    },
                },
                "spec": {
                    "replicas": workload.replicas,
                    "selector": {
                        "matchLabels": {
                            "name": workload.name,
                            "kind": workload.kind,
                        },
                    },
                    "template": {
                        "metadata": {
                            "labels": {
                                "name": workload.name,
                                "kind": workload.kind,
                            },
                        },
                        "spec": {
                            "containers": [
                                {
                                    "image": workload.image,
                                    "name": "container0",
                                    "ports": [
                                        {
                                            "containerPort": 8080,
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
        }
        return self.post(endpoint=url, json=payload).json()

    def update_workload(
        self, cell_code: str, sys_code: str, kind: str, name: str,
        workload: WorkloadUpdateEntity,
    ) -> Dict[str, Any]:
        """全量更新工作负载。PUT /.../kinds/{kind}/workloads/{name}

        更新规则：replicas += 1、containerPort=8090、containers 增加 imagePullPolicy=Always、
        labels 追加 test=update。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
            workload: Workload 实体
        """
        logger.info(
            f"Update workload: cell={cell_code}, sys={sys_code}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads/{name}"
        )
        payload: Dict[str, Any] = {
            "workload": {
                "apiVersion": "apps/v1",
                "kind": workload.kind,
                "metadata": {
                    "name": workload.name,
                    "labels": {
                        "name": workload.name,
                        "kind": workload.kind,
                        "test": "update",
                    },
                },
                "spec": {
                    "replicas": workload.replicas + 1,
                    "selector": {
                        "matchLabels": {
                            "name": workload.name,
                            "kind": workload.kind,
                        },
                    },
                    "template": {
                        "metadata": {
                            "labels": {
                                "name": workload.name,
                                "kind": workload.kind,
                            },
                        },
                        "spec": {
                            "containers": [
                                {
                                    "image": workload.image,
                                    "imagePullPolicy": "Always",
                                    "name": "container0",
                                    "ports": [
                                        {
                                            "containerPort": 8090,
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
        }
        return self.put(endpoint=url, json=payload).json()

    def patch_workload(
        self, cell_code: str, sys_code: str, kind: str, name: str,
        workload: WorkloadPatchEntity,
    ) -> Dict[str, Any]:
        """增量更新工作负载。PATCH /.../kinds/{kind}/workloads/{name}

        更新规则：labels 追加 test=patch-update，容器 container0 增加 port1(8010)。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
            workload: Workload 实体
        """
        logger.info(
            f"Patch workload: cell={cell_code}, sys={sys_code}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads/{name}"
        )
        payload: Dict[str, Any] = {
            "metadata": {
                "labels": {
                    "test": "patch-update",
                },
            },
            "spec": {
                "replicas": workload.replicas,
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "container0",
                                "ports": [
                                    {
                                        "containerPort": 8010,
                                        "name": "port1",
                                    }
                                ],
                            }
                        ],
                    },
                },
            },
        }
        return self.patch(
            endpoint=url, json=payload
        ).json()

    def delete_workload(
        self, cell_code: str, sys_code: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        删除工作负载。
        DELETE /.../kinds/{kind}/workloads/{name}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
        """
        logger.info(
            f"Delete workload: cell={cell_code}, sys={sys_code}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads/{name}"
        )
        return self.delete(endpoint=url).json()

    def delete_workload_by_labels(
        self, cell_code: str, sys_code: str, kind: str, labels: str
    ) -> Dict[str, Any]:
        """
        按标签删除工作负载。
        DELETE /.../kinds/{kind}/workloads?labels={labels}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            labels: labels 字典
        """
        logger.info(
            f"Delete workload by labels: cell={cell_code}, sys={sys_code}, "
            f"kind={kind}, labels={labels}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads?labels={labels}"
        )
        return self.delete(endpoint=url).json()

    def batch_query_workload_status(
        self, cell_code: str, sys_code: str,
        applications: List[WorkloadBatchTargetEntity],
    ) -> Dict[str, Any]:
        """
        批量查询工作负载状态。
        POST /.../workloads/status/batch
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            applications: 参数
        """
        logger.info(
            f"Batch query workload status: cell={cell_code}, sys={sys_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/workloads/status/batch"
        )
        payload: Dict[str, Any] = {
            "applications": [
                {"appName": app.name, "kind": app.kind}
                for app in applications
            ]
        }
        return self.post(endpoint=url, json=payload).json()

    def batch_patch_workloads(
        self, cell_code: str, sys_code: str,
        applications: List[WorkloadBatchPatchTargetEntity],
    ) -> Dict[str, Any]:
        """批量增量更新工作负载。PATCH /.../workloads/batch

        更新规则：labels 追加 test=batch-patch-update，容器 container0 增加 port2(8020)。
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            applications: 参数
        """
        logger.info(f"Batch patch workloads: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/workloads/batch"
        )
        payload: Dict[str, Any] = {
            "applications": [
                {
                    "appName": app.name,
                    "kind": app.kind,
                    "patch": {
                        "metadata": {
                            "labels": {
                                "test": "batch-patch-update",
                            },
                        },
                        "spec": {
                            "template": {
                                "spec": {
                                    "containers": [
                                        {
                                            "name": "container0",
                                            "ports": [
                                                {
                                                    "containerPort": 8020,
                                                    "name": "port2",
                                                }
                                            ],
                                        }
                                    ],
                                },
                            },
                        },
                    },
                }
                for app in applications
            ]
        }
        return self.patch(
            endpoint=url, json=payload
        ).json()

    def workload_rolling(
        self, cell_code: str, sys_code: str, kind: str, name: str,
        action: str, payload: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        工作负载滚动操作。
        POST /.../workloads/{name}/rolling?action={action}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
            action: 参数
            payload: 请求体 payload
        """
        logger.info(
            f"Workload rolling: cell={cell_code}, sys={sys_code}, "
            f"kind={kind}, name={name}, action={action}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads/{name}/rolling?action={action}"
        )
        return self.post(
            endpoint=url, json=payload or {}
        ).json()

    def batch_workload_rolling(
        self, cell_code: str, sys_code: str, action: str,
        applications: List[WorkloadBatchTargetEntity],
    ) -> Dict[str, Any]:
        """
        批量工作负载滚动操作。
        POST /.../workloads/rolling/batch?action={action}
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            action: 参数
            applications: 参数
        """
        logger.info(
            f"Batch workload rolling: cell={cell_code}, sys={sys_code}, action={action}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/workloads/rolling/batch?action={action}"
        )
        payload: Dict[str, Any] = {
            "applications": [
                {"appName": app.name, "kind": app.kind}
                for app in applications
            ],
            "action": action,
        }
        return self.post(
            endpoint=url, json=payload
        ).json()

    def stop_workload(
        self, cell_code: str, sys_code: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        停止工作负载。
        POST /.../workloads/{name}/stop
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
        """
        logger.info(
            f"Stop workload: cell={cell_code}, sys={sys_code}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads/{name}/stop"
        )
        return self.post(
            endpoint=url, json={}
        ).json()

    def start_workload(
        self, cell_code: str, sys_code: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        启动工作负载。
        POST /.../workloads/{name}/start
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
        """
        logger.info(
            f"Start workload: cell={cell_code}, sys={sys_code}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads/{name}/start"
        )
        return self.post(
            endpoint=url, json={}
        ).json()

    def restart_workload(
        self, cell_code: str, sys_code: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        重启工作负载。
        POST /.../workloads/{name}/restart
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
        """
        logger.info(
            f"Restart workload: cell={cell_code}, sys={sys_code}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads/{name}/restart"
        )
        return self.post(
            endpoint=url, json={}
        ).json()

    def batch_stop_workloads(
        self, cell_code: str, sys_code: str,
        applications: List[WorkloadBatchTargetEntity],
    ) -> Dict[str, Any]:
        """
        批量停止工作负载。
        POST /.../workloads/stop/batch
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            applications: 参数
        """
        logger.info(f"Batch stop workloads: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/workloads/stop/batch"
        )
        payload: Dict[str, Any] = {
            "applications": [
                {"appName": app.name, "kind": app.kind}
                for app in applications
            ]
        }
        return self.post(
            endpoint=url, json=payload
        ).json()

    def batch_start_workloads(
        self, cell_code: str, sys_code: str,
        applications: List[WorkloadBatchTargetEntity],
    ) -> Dict[str, Any]:
        """
        批量启动工作负载。
        POST /.../workloads/start/batch
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            applications: 参数
        """
        logger.info(f"Batch start workloads: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/workloads/start/batch"
        )
        payload: Dict[str, Any] = {
            "applications": [
                {"appName": app.name, "kind": app.kind}
                for app in applications
            ]
        }
        return self.post(
            endpoint=url, json=payload
        ).json()

    def batch_restart_workloads(
        self, cell_code: str, sys_code: str,
        applications: List[WorkloadBatchTargetEntity],
    ) -> Dict[str, Any]:
        """
        批量重启工作负载。
        POST /.../workloads/restart/batch
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            applications: 参数
        """
        logger.info(f"Batch restart workloads: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/workloads/restart/batch"
        )
        payload: Dict[str, Any] = {
            "applications": [
                {"appName": app.name, "kind": app.kind}
                for app in applications
            ]
        }
        return self.post(
            endpoint=url, json=payload
        ).json()

    def workload_exec(
        self, cell_code: str, sys_code: str, app_code: str,
        exec_entity: WorkloadExecEntity,
    ) -> Dict[str, Any]:
        """
        工作负载 Pod 执行命令。
        POST /.../apps/{appCode}/exec
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            app_code: 应用编码
            exec_entity: 参数
        """
        logger.info(
            f"Workload exec: cell={cell_code}, sys={sys_code}, app={app_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/apps/{app_code}/exec"
        )
        payload: Dict[str, Any] = {
            "podName": exec_entity.pod_name,
            "containerName": exec_entity.container_name,
            "timeout": exec_entity.timeout,
            "command": exec_entity.command,
        }
        return self.post(
            endpoint=url, json=payload
        ).json()

    def workload_copy_file(
        self, cell_code: str, sys_code: str, kind: str, name: str,
        pod_name: str, container_name: str, file_path: str,
    ) -> Dict[str, Any]:
        """
        工作负载 Pod 拷贝文件。
        GET /.../pods/{podName}/copy?containerName=...&filePathInPod=...
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            kind: Workload 类型（Deployment / StatefulSet / DaemonSet / Job / CloneSet 等）
            name: 资源名称
            pod_name: Pod 名称
            container_name: 容器名
            file_path: 参数
        """
        logger.info(
            f"Workload copy file: cell={cell_code}, sys={sys_code}, "
            f"kind={kind}, name={name}, pod={pod_name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads/{name}/pods/{pod_name}/copy"
            f"?containerName={container_name}&filePathInPod={file_path}"
        )
        return self.get(endpoint=url).json()

    def batch_delete_workload_pods(
        self, cell_code: str, sys_code: str,
        pod_delete: WorkloadPodDeleteEntity,
    ) -> Dict[str, Any]:
        """
        批量删除工作负载 Pod。
        POST /.../workloads/pods/delete/batch
        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            pod_delete: 参数
        """
        logger.info(
            f"Batch delete workload pods: cell={cell_code}, sys={sys_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/workloads/pods/delete/batch"
        )
        payload: Dict[str, Any] = {
            "pods": [pod_delete.pod_name],
            "appCode": pod_delete.app_code,
        }
        return self.post(
            endpoint=url, json=payload
        ).json()

    def batch_delete_app_pods(
        self, pods: List[WorkloadAppPodDeleteEntity]
    ) -> Dict[str, Any]:
        """
        批量删除应用 Pod。
        POST /.../applications/pods/delete/batch
        Args:
            pods: 参数
        """
        logger.info("Batch delete app pods")
        url = "/openapi/elastic-compute/v2/applications/pods/delete/batch"
        payload: Dict[str, Any] = {
            "pods": [
                {
                    "podName": pod.pod_name,
                    "appCode": pod.app_code,
                    "cellCode": pod.cell_code,
                    "sysCode": pod.sys_code,
                }
                for pod in pods
            ]
        }
        return self.post(
            endpoint=url, json=payload
        ).json()


