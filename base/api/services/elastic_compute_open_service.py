"""
弹性计算 OpenAPI 服务封装（Bearer 鉴权）

基于 auto_test_pro 的 auto-test/files/elastic-compute/openapi/*.jmx 转换：
- cluster.jmx：集群管理生命周期
- namespace-api.jmx：分区管理
- elastic-computer-resource-collection.jmx：资源采集/指标信息
- Node.jmx：Node 节点查询/更新
- pvc-pv.jmx：PVC/PV/StorageClass 生命周期
"""
import logging
from typing import Dict, Any

from base import BaseService
from core import DataCache


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头（走 Portal 登录得到的 Bearer Token）。"""
    cache = DataCache.get_instance()
    return {
        "Authorization": cache.get("token"),
    }


class PanJiElasticComputeOpenService(BaseService):
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
