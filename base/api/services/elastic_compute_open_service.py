"""
弹性计算 OpenAPI 服务封装（Bearer 鉴权）

基于 auto_test_pro 的 auto-test/files/elastic-compute/openapi/*.jmx 转换。

集群/命名空间/资源采集/节点：
- cluster.jmx：集群管理生命周期
- namespace-api.jmx：分区管理
- elastic-computer-resource-collection.jmx：资源采集/指标信息
- Node.jmx：Node 节点查询/更新

PVC/PV/StorageClass（简写路径 /pvc /pv /storageClass）：
- pvc-pv.jmx：PVC/PV/StorageClass 生命周期

K8s 标准资源（Namespaced）：
- ConfigMap.jmx        （8）
- SecretV2.jmx         （14）
- ServiceV2.jmx        （14）
- ServiceAccountV2.jmx （3）
- EndpointsV2.jmx      （2）

K8s 集群级资源 / 命名空间配额：
- LimitRange.jmx        （16）
- resourcequota.jmx     （16）
- PriorityClassesV2.jmx （12）
- RBAC_V2.jmx           （4）
- pvc-pv.jmx（标准 K8s 路径 /persistentvolumeclaims /persistentvolumes）（12）
"""
import logging
from typing import Any, Dict

from base import BaseService
from core import DataCache


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头（走 Portal 登录得到的 Bearer Token）。"""
    cache = DataCache.get_instance()
    return {
        "Authorization": cache.get("token"),
    }


class ElasticComputeOpenService(BaseService):
    """
    弹性计算 OpenAPI 服务

    - 走 Portal 的 Bearer Token（由 tests/api/conftest.py 的 get_token fixture 注入 cache["token"]）
    - base_url 由 api_env["api_base_url"] 提供
    """

    DEFAULT_BASE_URL = "http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030"

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        """
        初始化 PanJi 弹性计算 OpenAPI 服务

        Args:
            base_url: API 基础 URL
            logger: 日志记录器
        """
        super().__init__(
            base_url=base_url or self.DEFAULT_BASE_URL,
            logger=logger,
        )
        self.logger.info(
            f"Initializing PanJi ElasticCompute OpenAPI Service with base_url: {self.base_url}"
        )

    # ==================== cluster 集群管理接口 ====================

    def list_cluster_info_v1(self) -> Dict[str, Any]:
        """
        获取 paas 系统下集群列表信息（V1）。

        对应 JMX：弹性计算_openapi_cluster_获取paas系统下集群列表信息的接口
        GET /openapi/elastic-compute/v1/clusters/info
        """
        self.logger.info("List elastic-compute clusters info v1")
        url = "/openapi/elastic-compute/v1/clusters/info"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def list_cluster_info_v2(self) -> Dict[str, Any]:
        """
        获取运行面集群信息列表（V2）。

        对应 JMX：弹性计算_openapi_cluster_获取运行面集群信息列表V2
        GET /openapi/elastic-compute/v2/clusters/info
        """
        self.logger.info("List elastic-compute clusters info v2")
        url = "/openapi/elastic-compute/v2/clusters/info"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== namespace 分区管理接口 ====================

    def list_namespaces(self, cell_code: str) -> Dict[str, Any]:
        """
        查询指定单元下的 Namespace 列表。

        对应 JMX：弹性计算_openapi_namespace_查询NamespaceList
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems

        Args:
            cell_code: 单元编码
        """
        self.logger.info(f"List namespaces of cell: {cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_namespace_detail(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询指定单元下指定系统 Namespace 详情。

        对应 JMX：弹性计算_openapi_namespace_查询Namespace详情
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}

        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        self.logger.info(f"Get namespace detail: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== elastic-computer-resource-collection 资源采集接口 ====================

    def list_cluster_quota(self) -> Dict[str, Any]:
        """
        查询集群配额信息。

        对应 JMX：弹性计算_openapi_elastic-computer-resource-collection_查询集群配额信息
        GET /openapi/elastic-compute/v2/metrics/clusterQuota
        """
        self.logger.info("List elastic-compute cluster quota metrics")
        url = "/openapi/elastic-compute/v2/metrics/clusterQuota"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def list_tenant_quota(self) -> Dict[str, Any]:
        """
        查询租户配额信息。

        对应 JMX：弹性计算_openapi_elastic-computer-resource-collection_查询租户配额信息
        GET /openapi/elastic-compute/v2/metrics/tenantQuota
        """
        self.logger.info("List elastic-compute tenant quota metrics")
        url = "/openapi/elastic-compute/v2/metrics/tenantQuota"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def list_cluster_resource(self) -> Dict[str, Any]:
        """
        查询集群资源信息。

        对应 JMX：弹性计算_openapi_elastic-computer-resource-collection_查询集群资源信息
        GET /openapi/elastic-compute/v2/metrics/clusterResource
        """
        self.logger.info("List elastic-compute cluster resource metrics")
        url = "/openapi/elastic-compute/v2/metrics/clusterResource"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def list_middleware_info(self) -> Dict[str, Any]:
        """
        查询中间件信息。

        对应 JMX：弹性计算_openapi_elastic-computer-resource-collection_查询中间件信息
        GET /openapi/elastic-compute/v2/metrics/middlewareInfo
        """
        self.logger.info("List elastic-compute middleware info metrics")
        url = "/openapi/elastic-compute/v2/metrics/middlewareInfo"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def list_system_quota(self) -> Dict[str, Any]:
        """
        查询应用/组件系统配额信息。

        对应 JMX：弹性计算_openapi_elastic-computer-resource-collection_查询应用/组件系统配额信息
        GET /openapi/elastic-compute/v2/metrics/systemQuota
        """
        self.logger.info("List elastic-compute system quota metrics")
        url = "/openapi/elastic-compute/v2/metrics/systemQuota"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== Node 节点接口 ====================

    def get_node_detail(self, cell_code: str, name: str) -> Dict[str, Any]:
        """
        查询指定 Node。

        对应 JMX：弹性计算_openapi_Node_查询指定Node
        GET /openapi/elastic-compute/v2/cells/{cellCode}/nodes/{name}

        Args:
            cell_code: 单元编码
            name: Node 名（如 IP）
        """
        self.logger.info(f"Get node detail: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/nodes/{name}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def list_nodes(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群所有 Node 列表。

        对应 JMX：弹性计算_openapi_Node_查询全集群所有Node列表请求
        GET /openapi/elastic-compute/v2/cells/{cellCode}/nodes

        Args:
            cell_code: 单元编码
        """
        self.logger.info(f"List nodes of cell: {cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/nodes"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def patch_node(
        self,
        cell_code: str,
        name: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        增量更新指定 Node。

        对应 JMX：弹性计算_openapi_Node_增量更新指定Node
        PATCH /openapi/elastic-compute/v2/cells/{cellCode}/nodes/{name}

        Args:
            cell_code: 单元编码
            name: Node 名
            payload: patch body（strategic merge patch）
        """
        self.logger.info(f"Patch node: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/nodes/{name}"
        response = self.patch(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def update_node(
        self,
        cell_code: str,
        name: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        全量更新指定 Node。

        对应 JMX：弹性计算_openapi_Node_更新指定Node
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/nodes/{name}

        Args:
            cell_code: 单元编码
            name: Node 名
            payload: 完整 Node 对象
        """
        self.logger.info(f"Update node: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/nodes/{name}"
        response = self.put(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    # ==================== PVC (PersistentVolumeClaim) 接口 ====================

    def get_pvc(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        查询指定 PVC。

        对应 JMX：弹性计算_openapi_pvc-pv_查询指定pvc
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc/{name}

        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: PVC 名称
        """
        self.logger.info(f"Get PVC: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pvc/{name}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def create_pvc(
        self,
        cell_code: str,
        sys_code: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        创建 PVC。

        对应 JMX：弹性计算_openapi_pvc-pv_创建pvc请求
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc

        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            payload: PVC 资源定义（K8s PersistentVolumeClaim 对象）
        """
        self.logger.info(f"Create PVC: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pvc"
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def delete_pvc(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        删除指定 PVC。

        对应 JMX：弹性计算_openapi_pvc-pv_删除指定pvc
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc/{name}

        Args:
            cell_code: 单元编码
            sys_code: 系统编码
            name: PVC 名称
        """
        self.logger.info(f"Delete PVC: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pvc/{name}"
        response = self.delete(endpoint=url, headers=_get_default_headers())
        return response.json()

    def list_pvc(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询 PVC 列表。

        对应 JMX：弹性计算_openapi_pvc-pv_查询pvc列表请求
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/pvc

        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        self.logger.info(f"List PVC: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/pvc"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def list_all_cluster_pvc(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群所有 PVC 列表。

        对应 JMX：弹性计算_openapi_pvc-pv_查询全集群所有pvc列表请求
        GET /openapi/elastic-compute/v2/cells/{cellCode}/pvc

        Args:
            cell_code: 单元编码
        """
        self.logger.info(f"List all cluster PVC: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/pvc"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== PV (PersistentVolume) 接口 ====================

    def get_pv(self, cell_code: str, pv_name: str) -> Dict[str, Any]:
        """
        查询指定 PV。

        对应 JMX：弹性计算_openapi_pvc-pv_查询指定pv
        GET /openapi/elastic-compute/v2/cells/{cellCode}/pv/{pvName}

        Args:
            cell_code: 单元编码
            pv_name: PV 名称
        """
        self.logger.info(f"Get PV: cell={cell_code}, name={pv_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/pv/{pv_name}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== StorageClass 接口 ====================

    def get_storage_class(self, cell_code: str, storage_class_name: str) -> Dict[str, Any]:
        """
        查询指定 StorageClass。

        对应 JMX：弹性计算_openapi_pvc-pv_查询StorageClass
        GET /openapi/elastic-compute/v2/cells/{cellCode}/storageClass/{storageClassName}

        Args:
            cell_code: 单元编码
            storage_class_name: StorageClass 名称
        """
        self.logger.info(f"Get StorageClass: cell={cell_code}, name={storage_class_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/storageClass/{storage_class_name}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== ConfigMap.jmx ====================

    def get_configmap(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """查询指定 configmap。GET /openapi/elastic-compute/v2/cells/{c}/systems/{s}/configmaps/{name}"""
        self.logger.info(f"Get configmap: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def delete_configmap(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """删除指定 configmap。DELETE /.../configmaps/{name}"""
        self.logger.info(f"Delete configmap: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps/{name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    def create_configmap(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 configmap 请求。POST /.../configmaps"""
        self.logger.info(f"Create configmap: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def list_configmaps_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询 cm 列表请求。GET /.../configmaps"""
        self.logger.info(f"List configmaps by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_configmaps_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群所有 cm 列表请求。GET /openapi/elastic-compute/v2/cells/{c}/configmaps"""
        self.logger.info(f"List configmaps by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/configmaps"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def update_configmap(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新指定 configmap。PUT /.../configmaps/{name}"""
        self.logger.info(f"Update configmap: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps/{name}"
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_configmap(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新指定 configmap。PATCH /.../configmaps/{name}"""
        self.logger.info(f"Patch configmap: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/configmaps/{name}"
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    # ==================== SecretV2.jmx ====================

    def get_secret(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """查询 Secret。GET /.../secrets/{name}"""
        self.logger.info(f"Get secret: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def delete_secret(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """删除 Secret。DELETE /.../secrets/{name}"""
        self.logger.info(f"Delete secret: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets/{name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    def create_secret(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 Secret。POST /.../secrets"""
        self.logger.info(f"Create secret: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def list_secrets_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询指定命名空间下的 Secret 列表。GET /.../secrets"""
        self.logger.info(f"List secrets by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_secrets_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群 Secret 列表。GET /openapi/elastic-compute/v2/cells/{c}/secrets"""
        self.logger.info(f"List secrets by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/secrets"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def update_secret(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 Secret。PUT /.../secrets/{name}"""
        self.logger.info(f"Update secret: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets/{name}"
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_secret(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新 Secret。PATCH /.../secrets/{name}"""
        self.logger.info(f"Patch secret: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/secrets/{name}"
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    # ==================== ServiceV2.jmx ====================

    def get_service(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """查询 Service。GET /.../services/{name}"""
        self.logger.info(f"Get service: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def delete_service(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """删除 Service。DELETE /.../services/{name}"""
        self.logger.info(f"Delete service: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services/{name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    def create_service(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 Service。POST /.../services"""
        self.logger.info(f"Create service: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def list_services_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询指定命名空间下的 Service 列表。GET /.../services"""
        self.logger.info(f"List services by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_services_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群 Service 列表。GET /openapi/elastic-compute/v2/cells/{c}/services"""
        self.logger.info(f"List services by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/services"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def update_service(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 Service。PUT /.../services/{name}"""
        self.logger.info(f"Update service: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services/{name}"
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_service(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新 Service。PATCH /.../services/{name}"""
        self.logger.info(f"Patch service: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/services/{name}"
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    # ==================== ServiceAccountV2.jmx ====================

    def list_service_accounts_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群 ServiceAccount 列。GET /.../serviceaccounts"""
        self.logger.info(f"List service accounts by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/serviceaccounts"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_service_accounts_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询 ServiceAccount 列。GET /.../serviceaccounts"""
        self.logger.info(f"List service accounts by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/serviceaccounts"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def get_service_account(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """查询 ServiceAccount。GET /.../serviceaccounts/{name}"""
        self.logger.info(f"Get service account: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/serviceaccounts/{name}"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    # ==================== EndpointsV2.jmx ====================

    def list_endpoints(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询 Endpoints 列表。GET /.../endpoints"""
        self.logger.info(f"List endpoints: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/endpoints"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def get_endpoints(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """查询 Endpoints。GET /.../endpoints/{name}"""
        self.logger.info(f"Get endpoints: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/endpoints/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    # ==================== LimitRange.jmx ====================

    def list_limitranges_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群 LimitRange。GET /openapi/elastic-compute/v2/cells/{c}/limitranges"""
        self.logger.info(f"List limitranges by cell: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/limitranges",
            headers=_get_default_headers(),
        ).json()

    def list_limitranges_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询命名空间下 LimitRange。GET /.../limitranges"""
        self.logger.info(f"List limitranges by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/limitranges"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def get_limitrange(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """查询 LimitRange。GET /.../limitranges/{name}"""
        self.logger.info(f"Get limitrange: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitranges/{name}"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_limitrange(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 LimitRange。POST /.../limitranges"""
        self.logger.info(f"Create limitrange: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/limitranges"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def update_limitrange(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 LimitRange。PUT /.../limitranges/{name}"""
        self.logger.info(f"Update limitrange: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitranges/{name}"
        )
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_limitrange(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新 LimitRange。PATCH /.../limitranges/{name}"""
        self.logger.info(f"Patch limitrange: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitranges/{name}"
        )
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_limitrange(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """删除 LimitRange。DELETE /.../limitranges/{name}"""
        self.logger.info(f"Delete limitrange: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/limitranges/{name}"
        )
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    # ==================== resourcequota.jmx ====================

    def list_resource_quotas_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群 ResourceQuota。GET /.../resourcequotas"""
        self.logger.info(f"List resourcequotas by cell: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/resourcequotas",
            headers=_get_default_headers(),
        ).json()

    def list_resource_quotas_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询命名空间 ResourceQuota。GET /.../resourcequotas"""
        self.logger.info(f"List resourcequotas by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/resourcequotas"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def get_resource_quota(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """查询 ResourceQuota。GET /.../resourcequotas/{name}"""
        self.logger.info(f"Get resourcequota: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resourcequotas/{name}"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_resource_quota(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 ResourceQuota。POST /.../resourcequotas"""
        self.logger.info(f"Create resourcequota: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/resourcequotas"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def update_resource_quota(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 ResourceQuota。PUT /.../resourcequotas/{name}"""
        self.logger.info(f"Update resourcequota: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resourcequotas/{name}"
        )
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_resource_quota(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新 ResourceQuota。PATCH /.../resourcequotas/{name}"""
        self.logger.info(f"Patch resourcequota: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resourcequotas/{name}"
        )
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_resource_quota(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """删除 ResourceQuota。DELETE /.../resourcequotas/{name}"""
        self.logger.info(f"Delete resourcequota: cell={cell_code}, sys={sys_code}, name={name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/resourcequotas/{name}"
        )
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    # ==================== PriorityClassesV2.jmx ====================

    def list_priority_classes(self, cell_code: str) -> Dict[str, Any]:
        """查询 PriorityClass 列表。GET /.../priorityclasses"""
        self.logger.info(f"List priority classes: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses",
            headers=_get_default_headers(),
        ).json()

    def get_priority_class(self, cell_code: str, name: str) -> Dict[str, Any]:
        """查询 PriorityClass。GET /.../priorityclasses/{name}"""
        self.logger.info(f"Get priority class: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_priority_class(self, cell_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """创建 PriorityClass。POST /.../priorityclasses"""
        self.logger.info(f"Create priority class: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def update_priority_class(
        self, cell_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 PriorityClass。PUT /.../priorityclasses/{name}"""
        self.logger.info(f"Update priority class: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses/{name}"
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_priority_class(
        self, cell_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新 PriorityClass。PATCH /.../priorityclasses/{name}"""
        self.logger.info(f"Patch priority class: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses/{name}"
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_priority_class(self, cell_code: str, name: str) -> Dict[str, Any]:
        """删除 PriorityClass。DELETE /.../priorityclasses/{name}"""
        self.logger.info(f"Delete priority class: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/priorityclasses/{name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    # ==================== RBAC_V2.jmx ====================

    def list_rbac_roles(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询 Role 列表。GET /.../roles"""
        self.logger.info(f"List rbac roles: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/roles"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_rbac_role_bindings(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """查询 RoleBinding 列表。GET /.../rolebindings"""
        self.logger.info(f"List rbac rolebindings: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/rolebindings"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_rbac_cluster_roles(self, cell_code: str) -> Dict[str, Any]:
        """查询 ClusterRole 列表。GET /.../clusterroles"""
        self.logger.info(f"List rbac clusterroles: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/clusterroles",
            headers=_get_default_headers(),
        ).json()

    def list_rbac_cluster_role_bindings(self, cell_code: str) -> Dict[str, Any]:
        """查询 ClusterRoleBinding 列表。GET /.../clusterrolebindings"""
        self.logger.info(f"List rbac clusterrolebindings: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/clusterrolebindings",
            headers=_get_default_headers(),
        ).json()

    # ==================== cr-cluster.jmx（Cluster 级别 CustomResource） ====================

    def get_cluster_custom_resource(
        self, cell_code: str, group: str, version: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        查询指定 Cluster 级别 CR。

        对应 JMX：弹性计算_openapi_cr-cluster_查询指定CR
        GET /openapi/elastic-compute/v2/cells/{cellCode}/{group}/{version}/kind/{kind}/customResources/{name}

        Args:
            cell_code: 单元编码
            group: CR group（如 test.example.com）
            version: CR version（如 v1）
            kind: CR kind（如 Apple）
            name: CR 名称
        """
        self.logger.info(
            f"Get cluster CR: cell={cell_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/{group}/{version}"
            f"/kind/{kind}/customResources/{name}"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_cluster_custom_resource(
        self, cell_code: str, group: str, version: str, kind: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建 Cluster 级别 CR。

        对应 JMX：弹性计算_openapi_cr-cluster_创建CR请求
        POST /openapi/elastic-compute/v2/cells/{cellCode}/{group}/{version}/kind/{kind}/customResources

        Args:
            cell_code: 单元编码
            group: CR group
            version: CR version
            kind: CR kind
            payload: CR 资源定义
        """
        self.logger.info(
            f"Create cluster CR: cell={cell_code}, group={group}, version={version}, kind={kind}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/{group}/{version}"
            f"/kind/{kind}/customResources"
        )
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def list_cluster_custom_resources(
        self, cell_code: str, group: str, version: str, kind: str,
        label_selector: str = None,
    ) -> Dict[str, Any]:
        """
        查询 Cluster 级别 CR 列表。

        对应 JMX：弹性计算_openapi_cr-cluster_查询CR列表请求
        GET /openapi/elastic-compute/v2/cells/{cellCode}/{group}/{version}/kind/{kind}/customResources

        Args:
            cell_code: 单元编码
            group: CR group
            version: CR version
            kind: CR kind
            label_selector: labelSelector 过滤条件（可选）
        """
        self.logger.info(
            f"List cluster CRs: cell={cell_code}, group={group}, version={version}, kind={kind}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/{group}/{version}"
            f"/kind/{kind}/customResources"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        return self.get(endpoint=url, params=params, headers=_get_default_headers()).json()

    def update_cluster_custom_resource(
        self, cell_code: str, group: str, version: str, kind: str, name: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        全量更新指定 Cluster 级别 CR。

        对应 JMX：弹性计算_openapi_cr-cluster_更新指定CR
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/{group}/{version}/kind/{kind}/customResources/{name}

        Args:
            cell_code: 单元编码
            group: CR group
            version: CR version
            kind: CR kind
            name: CR 名称
            payload: 完整 CR 对象
        """
        self.logger.info(
            f"Update cluster CR: cell={cell_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/{group}/{version}"
            f"/kind/{kind}/customResources/{name}"
        )
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_cluster_custom_resource(
        self, cell_code: str, group: str, version: str, kind: str, name: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        增量更新指定 Cluster 级别 CR。

        对应 JMX：弹性计算_openapi_cr-cluster_增量更新指定CR
        PATCH /openapi/elastic-compute/v2/cells/{cellCode}/{group}/{version}/kind/{kind}/customResources/{name}

        Args:
            cell_code: 单元编码
            group: CR group
            version: CR version
            kind: CR kind
            name: CR 名称
            payload: 增量更新字段
        """
        self.logger.info(
            f"Patch cluster CR: cell={cell_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/{group}/{version}"
            f"/kind/{kind}/customResources/{name}"
        )
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_cluster_custom_resource(
        self, cell_code: str, group: str, version: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Cluster 级别 CR。

        对应 JMX：弹性计算_openapi_cr-cluster_删除指定CR
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/{group}/{version}/kind/{kind}/customResources/{name}

        Args:
            cell_code: 单元编码
            group: CR group
            version: CR version
            kind: CR kind
            name: CR 名称
        """
        self.logger.info(
            f"Delete cluster CR: cell={cell_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/{group}/{version}"
            f"/kind/{kind}/customResources/{name}"
        )
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    # ==================== pvc-pv.jmx（K8s 标准路径 /persistentvolumeclaims /persistentvolumes） ====================
    # 说明：与上方 PVC/PV 接口（简写路径 /pvc、/pv）为两套并存的 OpenAPI，
    # 此处方法名统一使用完整 K8s 资源名以示区分。

    def list_persistentvolumeclaims_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """查询全集群 PVC。GET /.../persistentvolumeclaims"""
        self.logger.info(f"List persistentvolumeclaims by cell: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumeclaims",
            headers=_get_default_headers(),
        ).json()

    def list_persistentvolumeclaims_by_ns(
        self, cell_code: str, sys_code: str
    ) -> Dict[str, Any]:
        """查询命名空间 PVC。GET /.../persistentvolumeclaims"""
        self.logger.info(
            f"List persistentvolumeclaims by ns: cell={cell_code}, sys={sys_code}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def get_persistentvolumeclaim(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """查询 PVC。GET /.../persistentvolumeclaims/{name}"""
        self.logger.info(
            f"Get persistentvolumeclaim: cell={cell_code}, sys={sys_code}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims/{name}"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_persistentvolumeclaim(
        self, cell_code: str, sys_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 PVC。POST /.../persistentvolumeclaims"""
        self.logger.info(f"Create persistentvolumeclaim: cell={cell_code}, sys={sys_code}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims"
        )
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def update_persistentvolumeclaim(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 PVC。PUT /.../persistentvolumeclaims/{name}"""
        self.logger.info(
            f"Update persistentvolumeclaim: cell={cell_code}, sys={sys_code}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims/{name}"
        )
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_persistentvolumeclaim(
        self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """增量更新 PVC。PATCH /.../persistentvolumeclaims/{name}"""
        self.logger.info(
            f"Patch persistentvolumeclaim: cell={cell_code}, sys={sys_code}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims/{name}"
        )
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_persistentvolumeclaim(
        self, cell_code: str, sys_code: str, name: str
    ) -> Dict[str, Any]:
        """删除 PVC。DELETE /.../persistentvolumeclaims/{name}"""
        self.logger.info(
            f"Delete persistentvolumeclaim: cell={cell_code}, sys={sys_code}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/persistentvolumeclaims/{name}"
        )
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    def list_persistentvolumes(self, cell_code: str) -> Dict[str, Any]:
        """查询 PV 列表。GET /.../persistentvolumes"""
        self.logger.info(f"List persistentvolumes: cell={cell_code}")
        return self.get(
            endpoint=f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes",
            headers=_get_default_headers(),
        ).json()

    def get_persistentvolume(self, cell_code: str, name: str) -> Dict[str, Any]:
        """查询 PV。GET /.../persistentvolumes/{name}"""
        self.logger.info(f"Get persistentvolume: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_persistentvolume(
        self, cell_code: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建 PV。POST /.../persistentvolumes"""
        self.logger.info(f"Create persistentvolume: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def update_persistentvolume(
        self, cell_code: str, name: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 PV。PUT /.../persistentvolumes/{name}"""
        self.logger.info(f"Update persistentvolume: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes/{name}"
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_persistentvolume(self, cell_code: str, name: str) -> Dict[str, Any]:
        """删除 PV。DELETE /.../persistentvolumes/{name}"""
        self.logger.info(f"Delete persistentvolume: cell={cell_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/persistentvolumes/{name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    # ==================== CustomResource-ns.jmx（Namespace 级别 CustomResource） ====================

    def get_ns_custom_resource(
        self, cell_code: str, sys_code: str, group: str, version: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        查询指定 Namespace 级别 CR。

        对应 JMX：弹性计算_openapi_CustomResource-ns_查询指定CR
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{group}/{version}/kind/{kind}/customResources/{name}
        """
        self.logger.info(
            f"Get ns CR: cell={cell_code}, sys={sys_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{group}/{version}/kind/{kind}/customResources/{name}"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_ns_custom_resource(
        self, cell_code: str, sys_code: str, group: str, version: str, kind: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        创建 Namespace 级别 CR。

        对应 JMX：弹性计算_openapi_CustomResource-ns_创建CR请求
        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{group}/{version}/kind/{kind}/customResources
        """
        self.logger.info(
            f"Create ns CR: cell={cell_code}, sys={sys_code}, group={group}, version={version}, kind={kind}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{group}/{version}/kind/{kind}/customResources"
        )
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def list_ns_custom_resources(
        self, cell_code: str, sys_code: str, group: str, version: str, kind: str,
        label_selector: str = None,
    ) -> Dict[str, Any]:
        """
        查询 Namespace 级别 CR 列表。

        对应 JMX：弹性计算_openapi_CustomResource-ns_查询CR列表请求
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{group}/{version}/kind/{kind}/customResources
        """
        self.logger.info(
            f"List ns CRs: cell={cell_code}, sys={sys_code}, group={group}, version={version}, kind={kind}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{group}/{version}/kind/{kind}/customResources"
        )
        params = {}
        if label_selector:
            params["labelSelector"] = label_selector
        return self.get(endpoint=url, params=params, headers=_get_default_headers()).json()

    def update_ns_custom_resource(
        self, cell_code: str, sys_code: str, group: str, version: str, kind: str, name: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        全量更新指定 Namespace 级别 CR。

        对应 JMX：弹性计算_openapi_CustomResource-ns_更新指定CR
        PUT /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{group}/{version}/kind/{kind}/customResources/{name}
        """
        self.logger.info(
            f"Update ns CR: cell={cell_code}, sys={sys_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{group}/{version}/kind/{kind}/customResources/{name}"
        )
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_ns_custom_resource(
        self, cell_code: str, sys_code: str, group: str, version: str, kind: str, name: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        增量更新指定 Namespace 级别 CR。

        对应 JMX：弹性计算_openapi_CustomResource-ns_增量更新指定CR
        PATCH /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{group}/{version}/kind/{kind}/customResources/{name}
        """
        self.logger.info(
            f"Patch ns CR: cell={cell_code}, sys={sys_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{group}/{version}/kind/{kind}/customResources/{name}"
        )
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_ns_custom_resource(
        self, cell_code: str, sys_code: str, group: str, version: str, kind: str, name: str
    ) -> Dict[str, Any]:
        """
        删除指定 Namespace 级别 CR。

        对应 JMX：弹性计算_openapi_CustomResource-ns_删除指定CR
        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/{group}/{version}/kind/{kind}/customResources/{name}
        """
        self.logger.info(
            f"Delete ns CR: cell={cell_code}, sys={sys_code}, group={group}, version={version}, kind={kind}, name={name}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/{group}/{version}/kind/{kind}/customResources/{name}"
        )
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    # ==================== helm-chart.jmx Helm Chart 接口 ====================

    def get_helm_chart(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        查询指定 Helm Chart。

        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helmCharts/{name}
        """
        self.logger.info(f"Get helm chart: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helmCharts/{name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_helm_chart(self, cell_code: str, sys_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建 Helm Chart。

        POST /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helmCharts
        """
        self.logger.info(f"Create helm chart: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helmCharts"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def list_helm_charts_by_ns(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询 Namespace 下 Helm Chart 列表。

        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helmCharts
        """
        self.logger.info(f"List helm charts by ns: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helmCharts"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def list_helm_charts_by_cell(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群 Helm Chart 列表。

        GET /openapi/elastic-compute/v2/cells/{cellCode}/helmCharts
        """
        self.logger.info(f"List helm charts by cell: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/helmCharts"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def update_helm_chart(self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        全量更新指定 Helm Chart。

        PUT /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helmCharts/{name}
        """
        self.logger.info(f"Update helm chart: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helmCharts/{name}"
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def patch_helm_chart(self, cell_code: str, sys_code: str, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        增量更新指定 Helm Chart。

        PATCH /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helmCharts/{name}
        """
        self.logger.info(f"Patch helm chart: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helmCharts/{name}"
        return self.patch(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_helm_chart(self, cell_code: str, sys_code: str, name: str) -> Dict[str, Any]:
        """
        删除指定 Helm Chart。

        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helmCharts/{name}
        """
        self.logger.info(f"Delete helm chart: cell={cell_code}, sys={sys_code}, name={name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helmCharts/{name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    # ==================== harbor.jmx / harbor-init.jmx Harbor 镜像仓库接口 ====================

    def get_harbor_project(self, cell_code: str, project_name: str) -> Dict[str, Any]:
        """
        查询指定 Harbor 项目。

        GET /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}
        """
        self.logger.info(f"Get harbor project: cell={cell_code}, project={project_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def create_harbor_project(self, cell_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建 Harbor 项目。

        POST /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects
        """
        self.logger.info(f"Create harbor project: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def list_harbor_projects(self, cell_code: str) -> Dict[str, Any]:
        """
        查询 Harbor 项目列表。

        GET /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects
        """
        self.logger.info(f"List harbor projects: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def update_harbor_project(self, cell_code: str, project_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新 Harbor 项目。

        PUT /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}
        """
        self.logger.info(f"Update harbor project: cell={cell_code}, project={project_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}"
        return self.put(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_harbor_project(self, cell_code: str, project_name: str) -> Dict[str, Any]:
        """
        删除 Harbor 项目。

        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}
        """
        self.logger.info(f"Delete harbor project: cell={cell_code}, project={project_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    def list_harbor_repositories(self, cell_code: str, project_name: str) -> Dict[str, Any]:
        """
        查询 Harbor 仓库列表。

        GET /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}/repositories
        """
        self.logger.info(f"List harbor repositories: cell={cell_code}, project={project_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}/repositories"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def delete_harbor_repository(self, cell_code: str, project_name: str, repo_name: str) -> Dict[str, Any]:
        """
        删除 Harbor 仓库。

        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}/repositories/{repoName}
        """
        self.logger.info(f"Delete harbor repository: cell={cell_code}, project={project_name}, repo={repo_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}/repositories/{repo_name}"
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    def list_harbor_artifacts(self, cell_code: str, project_name: str, repo_name: str) -> Dict[str, Any]:
        """
        查询 Harbor 制品列表。

        GET /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}/repositories/{repoName}/artifacts
        """
        self.logger.info(f"List harbor artifacts: cell={cell_code}, project={project_name}, repo={repo_name}")
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}"
            f"/repositories/{repo_name}/artifacts"
        )
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def delete_harbor_artifact(
        self, cell_code: str, project_name: str, repo_name: str, reference: str
    ) -> Dict[str, Any]:
        """
        删除 Harbor 制品。

        DELETE /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}/repositories/{repoName}/artifacts/{reference}
        """
        self.logger.info(
            f"Delete harbor artifact: cell={cell_code}, project={project_name}, repo={repo_name}, ref={reference}"
        )
        url = (
            f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}"
            f"/repositories/{repo_name}/artifacts/{reference}"
        )
        return self.delete(endpoint=url, headers=_get_default_headers()).json()

    def get_harbor_project_summary(self, cell_code: str, project_name: str) -> Dict[str, Any]:
        """
        查询 Harbor 项目概要。

        GET /openapi/elastic-compute/v2/cells/{cellCode}/harbor/projects/{projectName}/summary
        """
        self.logger.info(f"Get harbor project summary: cell={cell_code}, project={project_name}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/projects/{project_name}/summary"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def init_harbor(self, cell_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        初始化 Harbor（harbor-init）。

        POST /openapi/elastic-compute/v2/cells/{cellCode}/harbor/init
        """
        self.logger.info(f"Init harbor: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/init"
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def get_harbor_status(self, cell_code: str) -> Dict[str, Any]:
        """
        查询 Harbor 状态。

        GET /openapi/elastic-compute/v2/cells/{cellCode}/harbor/status
        """
        self.logger.info(f"Get harbor status: cell={cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/harbor/status"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

