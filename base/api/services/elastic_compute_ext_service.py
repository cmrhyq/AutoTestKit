"""
弹性计算 Extensions 服务封装（apikey 鉴权）

基于 auto_test_pro 的 auto-test/files/elastic-compute/extensions/*.jmx 转换：
- applications.jmx：查询应用服务列表
- helm-chart.jmx：Helm/Chart 完整生命周期
- nginx-rbac.jmx：Nginx RBAC 模板管理
- Node.jmx：节点污点查询
- partitions-api.jmx：ResourceQuota / LimitRange 分区 API
- physical-host.jmx：裸金属主机绑定/查询
- tenant-quota.jmx：租户资源配额相关接口
- workload.jmx：Workload 单实例 & 批量生命周期
- system-bind.jmx：系统 - 用户绑定接口

Extensions 类接口使用 apikey/username/tenantCode 三件头鉴权，
不需要走 Portal 登录、也不需要 Bearer Token。
所有敏感值均从 core.config.env_manager 的 yaml 配置读取，杜绝硬编码。
"""

import os
from typing import Any, Dict, List, Optional

from base import BaseService
from base.api.entity.elastic_compute import (
    WorkloadEntity,
    WorkloadPatchEntity,
    WorkloadServiceEntity,
)
from core import get_logger
from core.config import env_manager

logger = get_logger(__name__)


def _get_ext_headers() -> Dict[str, str]:
    """获取 Extensions 类接口的默认请求头。

    从 env yaml 中读取：
    - ec_apikey：apikey
    - basicAuthUsername：username
    - tenantCode：tenantCode
    """
    env = env_manager.get_config()
    return {
        "username": env.get("basicAuthUsername"),
        "tenantCode": env.get("tenantCode"),
    }


def _get_admin_headers() -> Dict[str, str]:
    """获取以管理员身份访问 Extensions 接口所用请求头。

    在默认 headers 基础上，用 adminUsername / adminTenantCode 覆盖 username / tenantCode，
    对齐 JMX 中局部 HeaderManager 使用 admin 身份的场景。
    """
    env = env_manager.get_config()
    headers = _get_ext_headers()
    admin_username = env.get("adminUsername")
    admin_tenant_code = env.get("adminTenantCode")
    if admin_username:
        headers["username"] = admin_username
    if admin_tenant_code:
        headers["tenantCode"] = admin_tenant_code
    return headers


def _get_workload_headers() -> Dict[str, str]:
    """获取 Workload 类接口专用请求头（在默认 headers 基础上追加 rolecode）。"""
    env = env_manager.get_config()
    headers = _get_ext_headers()
    role_code = env.get("roleCode") or "tenant"
    headers["rolecode"] = role_code
    return headers


class ElasticComputeExtService(BaseService):
    """
    弹性计算 Extensions 服务（apikey 鉴权）

    与 openapi 类接口的区别：
    - 无需 Portal 登录 / Bearer Token
    - 通过 apikey + username + tenantCode 头进行鉴权
    - URL 前缀通常为 /elastic-compute/... 而非 /openapi/elastic-compute/...
    """

    def __init__(self, base_url: str):
        """
        初始化 PanJi 弹性计算 Extensions 服务

        Args:
            base_url: API 基础 URL（必传，来自 config/env_*.yaml 的 apiBaseUrl）

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
            auth_credentials={"api_key": "186cc9f603c4fed3742ff4160f2beec2", "header_name": "apikey"},
        )
        logger.info(f"Initializing PanJi ElasticCompute Extensions Service with base_url: {self.base_url}")

    # ==================== applications 应用服务查询 ====================

    def search_app(self, kinds: str) -> Dict[str, Any]:
        """
        查询当前租户的所有应用服务信息。

        对应 JMX：弹性计算_extensions_applications_查询应用服务列表
        GET /elastic-compute/v2/searchApp?kinds=Deployment

        Args:
            kinds: 应用类型，如 "Deployment"、"StatefulSet" 等
        """
        logger.info(f"Search app with kinds: {kinds}")
        url = "/elastic-compute/server/v2/searchApp"
        params = {"kinds": kinds}
        response = self.get(endpoint=url, params=params, headers=_get_ext_headers())
        return response.json()

    # ==================== Dashboard 资源面板 ====================

    def get_resource_dashboard(self, tenant_code: str) -> Dict[str, Any]:
        """
        资源信息统计接口，对接门户页面上的集群、主机、namespace、CPU、内存和PVC。

        对应 JMX：弹性计算_extentions_Dashboard_资源信息统计接口
        GET /elastic-compute/v1/resource/dashboard?tenantCode={tenantCode}

        Args:
            tenant_code: 租户编码
        """
        logger.info(f"Get resource dashboard: tenantCode={tenant_code}")
        url = "/elastic-compute/v1/resource/dashboard"
        params = {"tenantCode": tenant_code}
        response = self.get(endpoint=url, params=params, headers=_get_ext_headers())
        return response.json()

    def get_app_dashboard(self, tenant_code: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """
        工作负载和应用服务统计接口，对接门户 dashboard 页面上的工作负载和应用服务。

        对应 JMX：弹性计算_extentions_Dashboard_工作负载和应用服务
        GET /elastic-compute/v1/app/dashboard?startTime=&endTime=&tenantCode=

        Args:
            tenant_code: 租户编码
            start_time: 统计起始时间戳（毫秒）
            end_time: 统计结束时间戳（毫秒）
        """
        logger.info(f"Get app dashboard: tenantCode={tenant_code}, startTime={start_time}, endTime={end_time}")
        url = "/elastic-compute/v1/app/dashboard"
        params = {
            "tenantCode": tenant_code,
            "startTime": start_time,
            "endTime": end_time,
        }
        response = self.get(endpoint=url, params=params, headers=_get_ext_headers())
        return response.json()

    # ==================== app-grant 应用授权 ====================

    def grant_app(self, app_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用授权，调用 extendapi 进行应用授权。

        对应 JMX：弹性计算_extentions_app-grant_应用授权
        POST /elastic-compute/v1/applications/{appCode}/grant

        Args:
            app_code: 应用编码
            payload: 授权请求体，包含 users 列表和 endTime
        """
        logger.info(f"Grant app: appCode={app_code}")
        url = f"/elastic-compute/v1/applications/{app_code}/grant"
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def remove_grant_app(self, app_code: str, payload: Any) -> Dict[str, Any]:
        """
        解除应用授权，调用 extendapi 解除应用授权。

        对应 JMX：弹性计算_extentions_app-grant_解除应用授权
        POST /elastic-compute/v1/applications/{appCode}/removeGrant

        Args:
            app_code: 应用编码
            payload: 解除授权请求体，用户名列表
        """
        logger.info(f"Remove grant app: appCode={app_code}")
        url = f"/elastic-compute/v1/applications/{app_code}/removeGrant"
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    # ==================== cluster-manager 集群管理 ====================

    def list_clusters(self) -> Dict[str, Any]:
        """
        获取集群列表信息。

        对应 JMX：弹性计算_extentions_cluster-manager_获取集群l信息
        GET /elastic-compute/v1/clusters
        """
        logger.info("List clusters")
        url = "/elastic-compute/v1/clusters"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_cluster_info(self, cluster_id: str) -> Dict[str, Any]:
        """
        查询指定集群的详情接口。

        对应 JMX：弹性计算_extentions_cluster-manager_查询指定集群的详情接口
        GET /elastic-compute/v1/clusters/{clusterId}/info

        Args:
            cluster_id: 集群 ID
        """
        logger.info(f"Get cluster info: clusterId={cluster_id}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/info"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_cluster_status(self, cluster_id: str) -> Dict[str, Any]:
        """
        查询集群状态。

        对应 JMX：弹性计算_extentions_cluster-manager_查询集群状态
        GET /elastic-compute/v1/clusters/{clusterId}/status

        Args:
            cluster_id: 集群 ID
        """
        logger.info(f"Get cluster status: clusterId={cluster_id}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/status"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_controller_cluster(self) -> Dict[str, Any]:
        """
        获取控制面集群信息。

        对应 JMX：弹性计算_extentions_cluster-manager_获取控制面集群信息
        GET /elastic-compute/v2/clusters/controller
        """
        logger.info("Get controller cluster info")
        url = "/elastic-compute/v2/clusters/controller"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    # ==================== CustomResourceV1 自定义资源 ====================

    def get_custom_resource(
        self,
        cluster_id: str,
        group: str,
        version: str,
        namespace: str,
        kind: str,
        name: str,
    ) -> Any:
        """
        查询 CR 资源。

        对应 JMX：弹性计算_extentions_CustomResourceV1_查询CR资源
        GET /elastic-compute/v1/clusters/{clusterId}/{group}/{version}/namespaces/{namespace}/kind/{kind}/customResources/{name}

        Args:
            cluster_id: 集群 ID
            group: CR group（如 test.example.com）
            version: CR version（如 v1）
            namespace: 命名空间
            kind: CR kind（如 Apple）
            name: CR 实例名称
        """
        logger.info(
            f"Get custom resource: cluster={cluster_id}, "
            f"group={group}, version={version}, ns={namespace}, kind={kind}, name={name}"
        )
        url = (
            f"/elastic-compute/v1/clusters/{cluster_id}/{group}/{version}"
            f"/namespaces/{namespace}/kind/{kind}/customResources/{name}"
        )
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.status_code, response.json()

    def create_custom_resource(
        self,
        cluster_id: str,
        group: str,
        version: str,
        namespace: str,
        kind: str,
        payload: Dict[str, Any],
    ) -> Any:
        """
        创建 CR 实例。

        对应 JMX：弹性计算_extentions_CustomResourceV1_创建CR实例
        POST /elastic-compute/v1/clusters/{clusterId}/{group}/{version}/namespaces/{namespace}/kind/{kind}/customResources

        Args:
            cluster_id: 集群 ID
            group: CR group
            version: CR version
            namespace: 命名空间
            kind: CR kind
            payload: CR 资源定义
        """
        logger.info(
            f"Create custom resource: cluster={cluster_id}, "
            f"group={group}, version={version}, ns={namespace}, kind={kind}"
        )
        url = (
            f"/elastic-compute/v1/clusters/{cluster_id}/{group}/{version}"
            f"/namespaces/{namespace}/kind/{kind}/customResources"
        )
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.status_code, response.json()

    def update_custom_resource(
        self,
        cluster_id: str,
        group: str,
        version: str,
        namespace: str,
        kind: str,
        payload: Dict[str, Any],
    ) -> Any:
        """
        更新 CR 实例。

        对应 JMX：弹性计算_extentions_CustomResourceV1_更新CR实例
        PUT /elastic-compute/v1/clusters/{clusterId}/{group}/{version}/namespaces/{namespace}/kind/{kind}/customResources

        Args:
            cluster_id: 集群 ID
            group: CR group
            version: CR version
            namespace: 命名空间
            kind: CR kind
            payload: 更新后的 CR 资源定义
        """
        logger.info(
            f"Update custom resource: cluster={cluster_id}, "
            f"group={group}, version={version}, ns={namespace}, kind={kind}"
        )
        url = (
            f"/elastic-compute/v1/clusters/{cluster_id}/{group}/{version}"
            f"/namespaces/{namespace}/kind/{kind}/customResources"
        )
        response = self.put(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.status_code, response.json()

    def delete_custom_resource(
        self,
        cluster_id: str,
        group: str,
        version: str,
        namespace: str,
        kind: str,
        name: str,
    ) -> Any:
        """
        删除 CR 实例。

        对应 JMX：弹性计算_extentions_CustomResourceV1_删除CR实例
        DELETE /elastic-compute/v1/clusters/{clusterId}/{group}/{version}/namespaces/{namespace}/kind/{kind}/customResources/{name}

        Args:
            cluster_id: 集群 ID
            group: CR group
            version: CR version
            namespace: 命名空间
            kind: CR kind
            name: CR 实例名称
        """
        logger.info(
            f"Delete custom resource: cluster={cluster_id}, "
            f"group={group}, version={version}, ns={namespace}, kind={kind}, name={name}"
        )
        url = (
            f"/elastic-compute/v1/clusters/{cluster_id}/{group}/{version}"
            f"/namespaces/{namespace}/kind/{kind}/customResources/{name}"
        )
        response = self.delete(endpoint=url, headers=_get_ext_headers())
        return response.status_code, response.json()

    def list_custom_resources(
        self,
        cluster_id: str,
        group: str,
        version: str,
        namespace: str,
        kind: str,
    ) -> Any:
        """
        查询 CR 列表。

        对应 JMX：弹性计算_extentions_CustomResourceV1_查询CR列表
        GET /elastic-compute/v1/clusters/{clusterId}/{group}/{version}/namespaces/{namespace}/kind/{kind}/customResources

        Args:
            cluster_id: 集群 ID
            group: CR group
            version: CR version
            namespace: 命名空间
            kind: CR kind
        """
        logger.info(
            f"List custom resources: cluster={cluster_id}, "
            f"group={group}, version={version}, ns={namespace}, kind={kind}"
        )
        url = (
            f"/elastic-compute/v1/clusters/{cluster_id}/{group}/{version}"
            f"/namespaces/{namespace}/kind/{kind}/customResources"
        )
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.status_code, response.json()

    # ==================== harbor 仓库绑定 ====================

    def harbor_bind_cluster(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Harbor 仓库绑定集群。

        对应 JMX：弹性计算_extentions_harbor-bindcluster_harbor仓库绑定
        POST /elastic-compute/v2/harbor/bindCluster

        Args:
            payload: 绑定请求体，包含 clusterId 和 harborName
        """
        logger.info(f"Harbor bind cluster: {payload}")
        url = "/elastic-compute/v2/harbor/bindCluster"
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    # ==================== 资源采集类接口 ====================

    def get_metrics_nodes(self) -> Dict[str, Any]:
        """
        获取全量集群节点列表信息。

        对应 JMX：弹性计算_extentions_ElasticComputeResourceCollectorAPI_全量集群节点列表信息
        GET /elastic-compute/v2/metrics/nodes
        """
        logger.info("Get metrics nodes")
        url = "/elastic-compute/v2/metrics/nodes"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_metrics_workloads(self) -> Dict[str, Any]:
        """
        获取全量应用服务列表信息。

        对应 JMX：弹性计算_extentions_ElasticComputeResourceCollectorAPI_全量应用服务列表信息
        GET /elastic-compute/v2/metrics/workloads
        """
        logger.info("Get metrics workloads")
        url = "/elastic-compute/v2/metrics/workloads"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_metrics_physical_hosts(self) -> Dict[str, Any]:
        """
        查询裸金属主机列表。

        对应 JMX：弹性计算_extentions_ElasticComputeResourceCollectorAPI_查询裸金属主机列表
        GET /elastic-compute/v2/metrics/physicalHosts
        """
        logger.info("Get metrics physical hosts")
        url = "/elastic-compute/v2/metrics/physicalHosts"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_metrics_physical_host_number(self) -> Dict[str, Any]:
        """
        查询裸金属主机数量。

        对应 JMX：弹性计算_extentions_ElasticComputeResourceCollectorAPI_查询裸金属主机数量
        GET /elastic-compute/v2/metrics/physicalHostNumber
        """
        logger.info("Get metrics physical host number")
        url = "/elastic-compute/v2/metrics/physicalHostNumber"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_metrics_cluster_resource(self) -> Dict[str, Any]:
        """
        查询集群资源信息。

        对应 JMX：弹性计算_extentions_ElasticComputeResourceCollectorAPI_查询集群资源信息
        GET /elastic-compute/v2/metrics/clusterResource
        """
        logger.info("Get metrics cluster resource")
        url = "/elastic-compute/v2/metrics/clusterResource"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_metrics_cluster_quota(self) -> Dict[str, Any]:
        """
        查询集群配额信息。

        对应 JMX：弹性计算_extentions_ElasticComputeResourceCollectorAPI_查询集群配额信息
        GET /elastic-compute/v2/metrics/clusterQuota
        """
        logger.info("Get metrics cluster quota")
        url = "/elastic-compute/v2/metrics/clusterQuota"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_metrics_tenant_quota(self) -> Dict[str, Any]:
        """
        查询租户配额信息。

        对应 JMX：弹性计算_extentions_ElasticComputeResourceCollectorAPI_查询租户配额信息
        GET /elastic-compute/v2/metrics/tenantQuota
        """
        logger.info("Get metrics tenant quota")
        url = "/elastic-compute/v2/metrics/tenantQuota"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_metrics_system_quota(self) -> Dict[str, Any]:
        """
        查询应用/组件系统配额信息。

        对应 JMX：弹性计算_extentions_ElasticComputeResourceCollectorAPI_查询应用/组件系统配额信息
        GET /elastic-compute/v2/metrics/systemQuota
        """
        logger.info("Get metrics system quota")
        url = "/elastic-compute/v2/metrics/systemQuota"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_metrics_container_storage_software(self) -> Dict[str, Any]:
        """
        查询容器存储软件信息。

        对应 JMX：弹性计算_extentions_ElasticComputeResourceCollectorAPI_查询容器存储软件信息
        GET /elastic-compute/v2/metrics/containerStorageSoftware
        """
        logger.info("Get metrics container storage software")
        url = "/elastic-compute/v2/metrics/containerStorageSoftware"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_metrics_container_orchestration_software(self) -> Dict[str, Any]:
        """
        查询容器编排软件信息。

        对应 JMX：弹性计算_extentions_ElasticComputeResourceCollectorAPI_查询容器编排软件信息
        GET /elastic-compute/v2/metrics/containerOrchestrationSoftware
        """
        logger.info("Get metrics container orchestration software")
        url = "/elastic-compute/v2/metrics/containerOrchestrationSoftware"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    # ==================== Endpoints 管理 ====================

    def list_endpoints(self, cell_code: str) -> Dict[str, Any]:
        """
        查询全集群的 Endpoints 列表。

        对应 JMX：弹性计算_extentions_Endpoints_查询全集群的Endpoints列表
        GET /elastic-compute/v2/cells/{cellCode}/endpoints

        Args:
            cell_code: 单元编码
        """
        logger.info(f"List endpoints: cellCode={cell_code}")
        url = f"/elastic-compute/v2/cells/{cell_code}/endpoints"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    # ==================== 模糊查询（持续交付定制接口）====================

    def search_helm_app(self) -> Dict[str, Any]:
        """
        Helm 应用模糊查询服务接口。

        对应 JMX：弹性计算_extentions_fuzzy-query_Helm应用模糊查询服务接口
        GET /elastic-compute/v2/searchHelmApp
        """
        logger.info("Search helm app")
        url = "/elastic-compute/v2/searchHelmApp"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def search_app_fuzzy(self) -> Dict[str, Any]:
        """
        应用模糊查询。

        对应 JMX：弹性计算_extentions_fuzzy-query_应用模糊查询
        GET /elastic-compute/v2/searchApp
        """
        logger.info("Search app fuzzy")
        url = "/elastic-compute/v2/searchApp"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    # ==================== namespace-quota 系统配额管理 ====================

    def get_namespace_quota_overview(self, tenant_code: str, namespace: str) -> Dict[str, Any]:
        """
        系统资源配额各集群概览。

        对应 JMX：弹性计算_extentions_namespace-quota_系统资源配额各集群概览
        GET /elastic-compute/v1/tenants/{tenantCode}/namespaces/{namespace}/quota
        """
        logger.info(f"Get namespace quota overview: tenant={tenant_code}, ns={namespace}")
        url = f"/elastic-compute/v1/tenants/{tenant_code}/namespaces/{namespace}/quota"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_namespace_quota_detail(self, cluster_id: str, tenant_code: str, namespace: str) -> Dict[str, Any]:
        """
        系统资源配额详情。

        对应 JMX：弹性计算_extentions_namespace-quota_系统资源配额详情
        GET /elastic-compute/v1/clusters/{clusterId}/tenants/{tenantCode}/namespaces/{namespace}/quota/detail
        """
        logger.info(f"Get namespace quota detail: cluster={cluster_id}, tenant={tenant_code}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/tenants/{tenant_code}/namespaces/{namespace}/quota/detail"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_namespace_quota_scale(self, cluster_id: str, tenant_code: str, namespace: str) -> Dict[str, Any]:
        """
        系统可调整资源配额查询。

        对应 JMX：弹性计算_extentions_namespace-quota_系统可调整资源配额查询
        GET /elastic-compute/v1/clusters/{clusterId}/tenants/{tenantCode}/namespaces/{namespace}/quota/scale
        """
        logger.info(f"Get namespace quota scale: cluster={cluster_id}, tenant={tenant_code}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/tenants/{tenant_code}/namespaces/{namespace}/quota/scale"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def update_namespace_quota_scale(
        self, cluster_id: str, tenant_code: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        系统资源配额调整(扩容缩容)。

        对应 JMX：弹性计算_extentions_namespace-quota_系统资源配额调整(扩容缩容)
        PUT /elastic-compute/v1/clusters/{clusterId}/tenants/{tenantCode}/namespaces/{namespace}/quota/scale
        """
        logger.info(f"Update namespace quota scale: cluster={cluster_id}, tenant={tenant_code}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/tenants/{tenant_code}/namespaces/{namespace}/quota/scale"
        response = self.put(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def allocate_namespace_quota(
        self, cluster_id: str, tenant_code: str, namespace: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        系统资源配额分配。

        对应 JMX：弹性计算_extentions_namespace-quota_系统资源配额分配
        POST /elastic-compute/v1/clusters/{clusterId}/tenants/{tenantCode}/namespaces/{namespace}/quota/allocate
        """
        logger.info(f"Allocate namespace quota: cluster={cluster_id}, tenant={tenant_code}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/tenants/{tenant_code}/namespaces/{namespace}/quota/allocate"
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    # ==================== host-bind 主机绑定 ====================

    def list_hosts(self, cell_code: str) -> Dict[str, Any]:
        """
        集群下的主机列表查询接口。

        对应 JMX：弹性计算_extentions_host-bind_集群下的主机列表查询接口
        GET /elastic-compute/v2/cells/{cellCode}/hosts
        """
        logger.info(f"List hosts: cellCode={cell_code}")
        url = f"/elastic-compute/v2/cells/{cell_code}/hosts"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    # ==================== image-api 镜像接口 ====================

    def get_image_tags(self, repo_name: str, project_name: str) -> Dict[str, Any]:
        """
        获取镜像 tag 列表。

        对应 JMX：弹性计算_extentions_image-api_获取镜像tag列表
        GET /elastic-compute/v1/images/getRepositoriesTags?repo_name=&projectName=

        Args:
            repo_name: 镜像仓库名（如 kube_system/nfs/provisioner/v1）
            project_name: 项目名（如 kube_system）
        """
        logger.info(f"Get image tags: repo={repo_name}, project={project_name}")
        url = "/elastic-compute/v1/images/getRepositoriesTags"
        params = {"repo_name": repo_name, "projectName": project_name}
        response = self.get(endpoint=url, params=params, headers=_get_ext_headers())
        return response.json()

    # ==================== helm-chart Helm/Chart 管理 ====================

    def list_helm_charts(self, cluster_id: str, keyword: Optional[str] = None) -> Dict[str, Any]:
        """
        查询 Chart 列表。

        对应 JMX：弹性计算_extentions_helm-chart_查询Chart列表
        GET /elastic-compute/v1/clusters/{clusterId}/helm/charts?keyword={keyword}

        Args:
            cluster_id: 集群 ID
            keyword: 关键字过滤（可选，通常传 chartName 用于精准匹配）
        """
        logger.info(f"List helm charts: clusterId={cluster_id}, keyword={keyword}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/helm/charts"
        params = {"keyword": keyword} if keyword else None
        response = self.get(endpoint=url, params=params, headers=_get_ext_headers())
        return response.json()

    def download_helm_chart(self, cluster_id: str, chart_name: str, chart_version: str) -> Any:
        """
        下载 Chart。

        对应 JMX：弹性计算_extentions_helm-chart_下载Chart
        GET /elastic-compute/v1/clusters/{clusterId}/helm/charts/{chartName}/versions/{chartVersion}/download
        """
        logger.info(f"Download helm chart: cluster={cluster_id}, chart={chart_name}, version={chart_version}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/helm/charts/{chart_name}/versions/{chart_version}/download"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.status_code, response.content

    def delete_helm_chart(
        self, cluster_id: str, chart_name: str, chart_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        删除 Chart。

        对应 JMX：弹性计算_extentions_helm-chart_删除Chart
        DELETE /elastic-compute/v1/clusters/{clusterId}/helm/charts/{chartName}?version={chartVersion}

        Args:
            cluster_id: 集群 ID
            chart_name: Chart 名称
            chart_version: Chart 版本（可选，指定则仅删除该版本）
        """
        logger.info(f"Delete helm chart: cluster={cluster_id}, chart={chart_name}, version={chart_version}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/helm/charts/{chart_name}"
        params = {"version": chart_version} if chart_version else None
        response = self.delete(endpoint=url, params=params, headers=_get_ext_headers())
        return response.json()

    def helm_install(self, cluster_id: str, namespace: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helm Install 请求。

        对应 JMX：弹性计算_extentions_helm-chart_Helm Install请求
        POST /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/helm/install
        """
        logger.info(f"Helm install: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/helm/install"
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def helm_uninstall(self, cluster_id: str, namespace: str, name: str) -> Dict[str, Any]:
        """
        Helm Uninstall 请求。

        对应 JMX：弹性计算_extentions_helm-chart_Helm Uninstall请求
        DELETE /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/helm/release/{name}/uninstall
        """
        logger.info(f"Helm uninstall: cluster={cluster_id}, ns={namespace}, name={name}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/helm/release/{name}/uninstall"
        response = self.delete(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def helm_list_releases(self, cluster_id: str, namespace: str) -> Dict[str, Any]:
        """
        查询 Helm Release 列表。

        对应 JMX：弹性计算_extentions_helm-chart_Helm list请求
        GET /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/helm/release
        """
        logger.info(f"Helm list releases: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/helm/release"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def helm_manifest(self, cluster_id: str, namespace: str, name: str) -> Dict[str, Any]:
        """
        查询 Helm Release Manifest。

        对应 JMX：弹性计算_extentions_helm-chart_Helm Manifest请求
        GET /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/helm/release/{name}/manifest
        """
        logger.info(f"Helm manifest: cluster={cluster_id}, ns={namespace}, name={name}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/helm/release/{name}/manifest"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def helm_upgrade(self, cluster_id: str, namespace: str, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helm Upgrade 请求。

        对应 JMX：弹性计算_extentions_helm-chart_Helm Upgrade请求
        POST /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/helm/release/{name}/upgrade
        """
        logger.info(f"Helm upgrade: cluster={cluster_id}, ns={namespace}, name={name}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/helm/release/{name}/upgrade"
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def helm_history(self, cluster_id: str, namespace: str, name: str) -> Dict[str, Any]:
        """
        查询 Helm Release 历史版本。

        对应 JMX：弹性计算_extentions_helm-chart_Helm History请求
        GET /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/helm/release/{name}/history
        """
        logger.info(f"Helm history: cluster={cluster_id}, ns={namespace}, name={name}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/helm/release/{name}/history"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def helm_rollback(self, cluster_id: str, namespace: str, name: str, revision: int = 1) -> Dict[str, Any]:
        """
        Helm Rollback 请求。

        对应 JMX：弹性计算_extentions_helm-chart_Helm Rollback请求
        POST /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/helm/release/{name}/rollback?revision={revision}

        Args:
            cluster_id: 集群 ID
            namespace: 命名空间
            name: Helm Release 名称
            revision: 目标回滚版本号
        """
        logger.info(f"Helm rollback: cluster={cluster_id}, ns={namespace}, name={name}, revision={revision}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/helm/release/{name}/rollback"
        params = {"revision": revision}
        response = self.post(endpoint=url, params=params, headers=_get_ext_headers())
        return response.json()

    def upload_helm_chart(self, cluster_id: str, file_path: str) -> Dict[str, Any]:
        """
        上传 Chart 包。

        对应 JMX：弹性计算_extentions_helm-chart_上传Chart请求
        POST /elastic-compute/v1/clusters/{clusterId}/helm/charts/upload (multipart/form-data)

        Args:
            cluster_id: 集群 ID
            file_path: 本地 Chart 包文件路径
        """
        logger.info(f"Upload helm chart: cluster={cluster_id}, file={file_path}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/helm/charts/upload"
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, "application/octet-stream")}
            response = self.post(endpoint=url, files=files, headers=_get_ext_headers())
        return response.json()

    def helm_batch_install(self, cluster_id: str, namespace: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helm 批量 Install 请求（v1）。

        对应 JMX：弹性计算_extentions_helm-chart_Helm Batch Install请求
        POST /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/helm/install/batch
        """
        logger.info(f"Helm batch install v1: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/helm/install/batch"
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def helm_batch_uninstall(self, cluster_id: str, namespace: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helm 批量 Uninstall 请求（v1）。

        对应 JMX：弹性计算_extentions_helm-chart_Helm Batch Uninstall请求
        DELETE /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/helm/uninstall/batch
        """
        logger.info(f"Helm batch uninstall v1: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/helm/uninstall/batch"
        response = self.delete(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def helm_batch_upgrade(self, cluster_id: str, namespace: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helm 批量 Upgrade 请求（v1）。

        对应 JMX：弹性计算_extentions_helm-chart_Helm Batch Upgrade请求
        POST /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/helm/upgrade/batch
        """
        logger.info(f"Helm batch upgrade v1: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/helm/upgrade/batch"
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def helm_batch_install_v2(self, cell_code: str, sys_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helm 批量 Install 请求（v2）。

        对应 JMX：弹性计算_extentions_helm-chart_Helm Batch Install请求 v2
        POST /elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helm/install/batch
        """
        logger.info(f"Helm batch install v2: cell={cell_code}, sys={sys_code}")
        url = f"/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helm/install/batch"
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def helm_batch_uninstall_v2(self, cell_code: str, sys_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helm 批量 Uninstall 请求（v2）。

        对应 JMX：弹性计算_extentions_helm-chart_Helm Batch Uninstall请求 v2
        DELETE /elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helm/uninstall/batch
        """
        logger.info(f"Helm batch uninstall v2: cell={cell_code}, sys={sys_code}")
        url = f"/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helm/uninstall/batch"
        response = self.delete(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def helm_batch_upgrade_v2(self, cell_code: str, sys_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helm 批量 Upgrade 请求（v2）。

        对应 JMX：弹性计算_extentions_helm-chart_Helm Batch Upgrade请求 v2
        POST /elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/helm/upgrade/batch
        """
        logger.info(f"Helm batch upgrade v2: cell={cell_code}, sys={sys_code}")
        url = f"/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/helm/upgrade/batch"
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    # ==================== nginx-rbac Nginx RBAC 模板管理 ====================

    def get_nginx_rbac(self, cluster_id: str, namespace: str, code: str) -> Dict[str, Any]:
        """
        查询 Nginx RBAC 模板。

        对应 JMX：弹性计算_extentions_nginx-rbac_查询RBAC接口
        GET /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/rbac/nginx/{code}
        """
        logger.info(f"Get nginx rbac: cluster={cluster_id}, ns={namespace}, code={code}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/rbac/nginx/{code}"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def create_nginx_rbac(self, cluster_id: str, namespace: str, code: str) -> Dict[str, Any]:
        """
        创建 Nginx RBAC 模板。

        对应 JMX：弹性计算_extentions_nginx-rbac_创建RBAC接口
        POST /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/rbac/nginx/{code}
        """
        logger.info(f"Create nginx rbac: cluster={cluster_id}, ns={namespace}, code={code}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/rbac/nginx/{code}"
        response = self.post(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def delete_nginx_rbac(self, cluster_id: str, namespace: str, code: str) -> Dict[str, Any]:
        """
        删除 Nginx RBAC 模板。

        对应 JMX：弹性计算_extentions_nginx-rbac_删除RBAC接口
        DELETE /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/rbac/nginx/{code}
        """
        logger.info(f"Delete nginx rbac: cluster={cluster_id}, ns={namespace}, code={code}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/rbac/nginx/{code}"
        response = self.delete(endpoint=url, headers=_get_ext_headers())
        return response.json()

    # ==================== Node 节点污点查询 ====================

    def list_node_taints(self, cell_code: str, node_name: str) -> Dict[str, Any]:
        """
        查询节点污点列表。

        对应 JMX：弹性计算_extentions_Node_查询节点污点列表
        GET /elastic-compute/v2/cells/{cellCode}/nodes/taints?nodeName={nodeName}
        """
        logger.info(f"List node taints: cell={cell_code}, nodeName={node_name}")
        url = f"/elastic-compute/v2/cells/{cell_code}/nodes/taints"
        params = {"nodeName": node_name}
        response = self.get(endpoint=url, params=params, headers=_get_ext_headers())
        return response.json()

    # ==================== partitions-api ResourceQuota / LimitRange ====================

    def create_resource_quota(self, cluster_id: str, namespace: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建资源配额。

        对应 JMX：弹性计算_extentions_partitions-api_创建资源配额
        POST /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/resourceQuota
        """
        logger.info(f"Create resource quota: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/resourceQuota"
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def get_resource_quota(self, cluster_id: str, namespace: str) -> Dict[str, Any]:
        """
        获取资源配额。

        对应 JMX：弹性计算_extentions_partitions-api_获取资源配额
        GET /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/resourceQuota
        """
        logger.info(f"Get resource quota: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/resourceQuota"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def update_resource_quota(self, cluster_id: str, namespace: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新资源配额。

        对应 JMX：弹性计算_extentions_partitions-api_更新资源配额
        PUT /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/resourceQuota
        """
        logger.info(f"Update resource quota: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/resourceQuota"
        response = self.put(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def delete_resource_quota(self, cluster_id: str, namespace: str) -> Dict[str, Any]:
        """
        删除资源配额。

        DELETE /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/resourceQuota
        """
        logger.info(f"Delete resource quota: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/resourceQuota"
        response = self.delete(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def create_limit_range(self, cluster_id: str, namespace: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建资源限额。

        对应 JMX：弹性计算_extentions_partitions-api_创建资源限额
        POST /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/limitRange
        """
        logger.info(f"Create limit range: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/limitRange"
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def get_limit_range(self, cluster_id: str, namespace: str) -> Dict[str, Any]:
        """
        获取资源限额。

        对应 JMX：弹性计算_extentions_partitions-api_获取资源限额
        GET /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/limitRange
        """
        logger.info(f"Get limit range: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/limitRange"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def update_limit_range(self, cluster_id: str, namespace: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新资源限额。

        对应 JMX：弹性计算_extentions_partitions-api_更新资源限额
        PUT /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/limitRange
        """
        logger.info(f"Update limit range: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/limitRange"
        response = self.put(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def delete_limit_range(self, cluster_id: str, namespace: str) -> Dict[str, Any]:
        """
        删除资源限额。

        对应 JMX：弹性计算_extentions_partitions-api_删除资源限额
        DELETE /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/limitRange
        """
        logger.info(f"Delete limit range: cluster={cluster_id}, ns={namespace}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/limitRange"
        response = self.delete(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def list_partition_nodes(self, cluster_id: str, admin: bool = False) -> Dict[str, Any]:
        """
        获取节点信息（partitions-api 场景下用于节点资源查询）。

        对应 JMX：弹性计算_extentions_partitions-api_获取节点信息
        GET /elastic-compute/v1/clusters/{clusterId}/nodes

        Args:
            cluster_id: 集群 ID
            admin: 是否使用 adminUsername / adminTenantCode 请求（对齐 JMX 中局部 HeaderManager）
        """
        logger.info(f"List partition nodes: cluster={cluster_id}, admin={admin}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/nodes"
        headers = _get_admin_headers() if admin else _get_ext_headers()
        response = self.get(endpoint=url, headers=headers)
        return response.json()

    # ==================== physical-host 裸金属主机 ====================

    def search_physical_host_for_authorization(self) -> Dict[str, Any]:
        """
        获取主机列表（门户视图，供租户授权查询）。

        对应 JMX：弹性计算_extentions_physical-host_获取主机列表(门户)
        GET /elastic-compute/v2/physicalHost/searchPhysicalHostListForTenantAuthorization
        """
        logger.info("Search physical host list for tenant authorization")
        url = "/elastic-compute/v2/physicalHost/searchPhysicalHostListForTenantAuthorization"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def bind_physical_host_tenant(self, host_id: Any, tenant_code: str) -> Dict[str, Any]:
        """
        主机绑定租户（门户）。

        对应 JMX：弹性计算_extentions_physical-host_主机绑定租户(门户)
        POST /elastic-compute/v2/physicalHost/bindTenant
        """
        logger.info(f"Bind physical host tenant: hostId={host_id}, tenantCode={tenant_code}")
        url = "/elastic-compute/v2/physicalHost/bindTenant"
        payload = {"hostId": str(host_id), "tenantCode": tenant_code}
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    def list_current_tenant_hosts(self) -> Dict[str, Any]:
        """
        获取当前租户的裸金属主机列表。

        对应 JMX：弹性计算_extentions_physical-host_获取当前租户的裸金属主机列表
        GET /elastic-compute/v2/hosts
        """
        logger.info("List current tenant hosts")
        url = "/elastic-compute/v2/hosts"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_host_resource(self, host_id: Any, admin: bool = False) -> Dict[str, Any]:
        """
        获取指定裸金属主机信息。

        对应 JMX：弹性计算_extentions_physical-host_获取指定裸金属主机信息
        GET /elastic-compute/v2/hostResource/{hostId}

        Args:
            host_id: 主机 ID
            admin: 是否使用 adminUsername / adminTenantCode 请求（对齐 JMX 中局部 HeaderManager）
        """
        logger.info(f"Get host resource: hostId={host_id}, admin={admin}")
        url = f"/elastic-compute/v2/hostResource/{host_id}"
        headers = _get_admin_headers() if admin else _get_ext_headers()
        response = self.get(endpoint=url, headers=headers)
        return response.json()

    def get_host_connect_info(self, host_id: Any) -> Dict[str, Any]:
        """
        获取指定裸金属主机连接信息。

        对应 JMX：弹性计算_extentions_physical-host_获取指定裸金属主机连接信息
        GET /elastic-compute/v2/hostConnectInfo/{hostId}
        """
        logger.info(f"Get host connect info: hostId={host_id}")
        url = f"/elastic-compute/v2/hostConnectInfo/{host_id}"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def unbind_physical_host_tenant(self, host_id: Any, tenant_code: str) -> Dict[str, Any]:
        """
        主机解绑租户（门户）。

        对应 JMX：弹性计算_extentions_physical-host_主机解绑租户(门户)
        POST /elastic-compute/v2/physicalHost/unbindTenant
        """
        logger.info(f"Unbind physical host tenant: hostId={host_id}, tenantCode={tenant_code}")
        url = "/elastic-compute/v2/physicalHost/unbindTenant"
        payload = {"hostId": str(host_id), "tenantCode": tenant_code}
        response = self.post(endpoint=url, json=payload, headers=_get_ext_headers())
        return response.json()

    # ==================== tenant-quota 租户配额管理 ====================

    def get_cluster_quota(self, cluster_id: str) -> Dict[str, Any]:
        """
        集群配额概览查询。

        对应 JMX：弹性计算_extentions_tenant-quota_集群配额概览查询
        GET /elastic-compute/v1/clusters/{clusterId}/quota
        """
        logger.info(f"Get cluster quota: cluster={cluster_id}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/quota"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_tenant_quota_overview(self, tenant_code: str) -> Dict[str, Any]:
        """
        租户资源配额总览。

        对应 JMX：弹性计算_extentions_tenant-quota_租户资源配额总览
        GET /elastic-compute/v1/tenants/{tenantCode}/quota
        """
        logger.info(f"Get tenant quota overview: tenant={tenant_code}")
        url = f"/elastic-compute/v1/tenants/{tenant_code}/quota"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_tenant_quota_detail(self, cluster_id: str, tenant_code: str) -> Dict[str, Any]:
        """
        租户资源配额详情。

        对应 JMX：弹性计算_extentions_tenant-quota_租户资源配额详情
        GET /elastic-compute/v1/clusters/{clusterId}/tenants/{tenantCode}/quota/detail
        """
        logger.info(f"Get tenant quota detail: cluster={cluster_id}, tenant={tenant_code}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/tenants/{tenant_code}/quota/detail"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_tenant_cluster_quota(self, cluster_id: str, tenant_code: str) -> Dict[str, Any]:
        """
        租户资源配额单集群总览。

        对应 JMX：弹性计算_extentions_tenant-quota_租户资源配额单集群总览
        GET /elastic-compute/v1/clusters/{clusterId}/tenants/{tenantCode}/quota
        """
        logger.info(f"Get tenant cluster quota: cluster={cluster_id}, tenant={tenant_code}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/tenants/{tenant_code}/quota"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def get_tenant_quota_scale(self, cluster_id: str, tenant_code: str) -> Dict[str, Any]:
        """
        租户可调整资源配额查询。

        对应 JMX：弹性计算_extentions_tenant-quota_租户可调整资源配额查询
        GET /elastic-compute/v1/clusters/{clusterId}/tenants/{tenantCode}/quota/scale
        """
        logger.info(f"Get tenant quota scale: cluster={cluster_id}, tenant={tenant_code}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/tenants/{tenant_code}/quota/scale"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def allocate_tenant_quota(
        self, cluster_id: str, tenant_code: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        租户资源配额分配。

        对应 JMX：弹性计算_extentions_tenant-quota_租户资源配额分配
        POST /elastic-compute/v1/clusters/{clusterId}/tenants/{tenantCode}/quota/allocate
        """
        logger.info(f"Allocate tenant quota: cluster={cluster_id}, tenant={tenant_code}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/tenants/{tenant_code}/quota/allocate"
        response = self.post(endpoint=url, json=payload or {}, headers=_get_ext_headers())
        return response.json()

    def update_tenant_quota_scale(
        self, cluster_id: str, tenant_code: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        租户资源配额调整（扩容缩容）。

        对应 JMX：弹性计算_extentions_tenant-quota_租户资源配额调整(扩容缩容)
        PUT /elastic-compute/v1/clusters/{clusterId}/tenants/{tenantCode}/quota/scale
        """
        logger.info(f"Update tenant quota scale: cluster={cluster_id}, tenant={tenant_code}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/tenants/{tenant_code}/quota/scale"
        response = self.put(endpoint=url, json=payload or {}, headers=_get_ext_headers())
        return response.json()

    def batch_query_tenant_quota(self, payload: Dict[str, Any], admin: bool = False) -> Dict[str, Any]:
        """
        批量查询租户资源配额概览。

        对应 JMX：弹性计算_extentions_tenant-quota_批量查询租户资源配额概览
        POST /elastic-compute/v1/tenants/quota/batch

        Args:
            payload: 请求体，形如 {"tenantCodeList": ["tenantCode1", ...]}
            admin: 是否使用 adminUsername / adminTenantCode 请求（对齐 JMX 中局部 HeaderManager）
        """
        logger.info(f"Batch query tenant quota: admin={admin}, tenants={payload.get('tenantCodeList')}")
        url = "/elastic-compute/v1/tenants/quota/batch"
        headers = _get_admin_headers() if admin else _get_ext_headers()
        response = self.post(endpoint=url, json=payload, headers=headers)
        return response.json()

    # ==================== workload Workload 生命周期 ====================

    def get_workload_status(self, cell_code: str, sys_code: str, kind: str, name: str) -> Dict[str, Any]:
        """
        查询指定 Workload 状态。

        对应 JMX：弹性计算_extentions_workload_查询指定Deployment
        GET /elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/kinds/{kind}/workloads/{name}/status
        """
        logger.info(f"Get workload status: cell={cell_code}, sys={sys_code}, kind={kind}, name={name}")
        url = f"/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/kinds/{kind}/workloads/{name}/status"
        response = self.get(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def create_workload(
        self, cluster_id: str, namespace: str, kind: str, workload: WorkloadEntity
    ) -> Dict[str, Any]:
        """
        创建 Workload。

        对应 JMX：弹性计算_extentions_workload_创建Deployment请求
        POST /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/kinds/{kind}/applications

        Args:
            cluster_id: 集群 ID
            namespace: K8s Namespace
            kind: Workload 类型（路径参数，通常等于 workload.kind）
            workload: Workload 实体
        """
        logger.info(f"Create workload: cluster={cluster_id}, ns={namespace}, kind={kind}, name={workload.name}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/kinds/{kind}/applications"
        payload: Dict[str, Any] = {
            "name": workload.name,
            "kind": workload.kind,
            "image": workload.image,
            "appCode": workload.app_code,
            "labels": dict(workload.labels),
        }
        if workload.replicas is not None:
            payload["replicas"] = workload.replicas
        response = self.post(endpoint=url, json=payload, headers=_get_workload_headers())
        return response.json()

    def update_workload(
        self, cluster_id: str, namespace: str, kind: str, name: str, workload: WorkloadEntity
    ) -> Dict[str, Any]:
        """
        更新指定 Workload（PUT，全量更新）。

        对应 JMX：弹性计算_extentions_workload_更新指定Deployment
        PUT /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/kinds/{kind}/applications/{name}
        """
        logger.info(f"Update workload: cluster={cluster_id}, ns={namespace}, kind={kind}, name={name}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/kinds/{kind}/applications/{name}"
        payload: Dict[str, Any] = {
            "name": workload.name,
            "kind": workload.kind,
            "image": workload.image,
            "appCode": workload.app_code,
            "labels": dict(workload.labels),
        }
        if workload.replicas is not None:
            payload["replicas"] = workload.replicas
        response = self.put(endpoint=url, json=payload, headers=_get_workload_headers())
        return response.json()

    def patch_workload(
        self, cluster_id: str, namespace: str, kind: str, name: str, patch: WorkloadPatchEntity
    ) -> Dict[str, Any]:
        """
        增量更新指定 Workload。

        对应 JMX：弹性计算_extentions_workload_增量更新指定Deployment
        PATCH /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/kinds/{kind}/applications/{name}
        """
        logger.info(f"Patch workload: cluster={cluster_id}, ns={namespace}, kind={kind}, name={name}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/kinds/{kind}/applications/{name}"
        payload: Dict[str, Any] = {}
        if patch.labels:
            payload["labels"] = dict(patch.labels)
        response = self.patch(endpoint=url, json=payload, headers=_get_workload_headers())
        return response.json()

    def delete_workload(self, cluster_id: str, namespace: str, kind: str, name: str) -> Dict[str, Any]:
        """
        删除指定 Workload。

        对应 JMX：弹性计算_extentions_workload_删除Deployment
        DELETE /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/kinds/{kind}/applications/{name}
        """
        logger.info(f"Delete workload: cluster={cluster_id}, ns={namespace}, kind={kind}, name={name}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/kinds/{kind}/applications/{name}"
        response = self.delete(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def list_workload_pods(self, cell_code: str, sys_code: str, kind: str, name: str) -> Dict[str, Any]:
        """
        查询 Workload 关联的 Pod 实例列表。

        对应 JMX：弹性计算_extentions_workload_查询应用服务的Pod实例列表
        GET /elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/kinds/{kind}/workloads/{name}/pods
        """
        logger.info(f"List workload pods: cell={cell_code}, sys={sys_code}, kind={kind}, name={name}")
        url = f"/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}/kinds/{kind}/workloads/{name}/pods"
        response = self.get(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def get_workload_pod_events(
        self, cell_code: str, sys_code: str, kind: str, name: str, pod_name: str
    ) -> Dict[str, Any]:
        """
        查询 Workload Pod 的事件列表。

        对应 JMX：弹性计算_extentions_workload_查询应用服务的Pod事件列表
        GET /elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/kinds/{kind}/workloads/{name}/pods/{podName}/events
        """
        logger.info(f"Get workload pod events: kind={kind}, name={name}, pod={pod_name}")
        url = (
            f"/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads/{name}/pods/{pod_name}/events"
        )
        response = self.get(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def get_workload_pod_logs(
        self,
        cell_code: str,
        sys_code: str,
        kind: str,
        name: str,
        pod_name: str,
        container_name: str = "container0",
    ) -> Dict[str, Any]:
        """
        查询 Workload Pod 容器日志。

        对应 JMX：弹性计算_extentions_workload_查询应用服务的Pod容器日志
        GET /elastic-compute/v2/cells/{cellCode}/systems/{sysCode}/kinds/{kind}/workloads/{name}/pods/{podName}/containers/{containerName}/logs
        """
        logger.info(f"Get workload pod logs: kind={kind}, name={name}, pod={pod_name}, container={container_name}")
        url = (
            f"/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
            f"/kinds/{kind}/workloads/{name}/pods/{pod_name}"
            f"/containers/{container_name}/logs"
        )
        response = self.get(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def get_workload_volume_mounts(self, cluster_id: str, namespace: str, kind: str, name: str) -> Dict[str, Any]:
        """
        查询 Workload 的挂载存储列表。

        对应 JMX：弹性计算_extentions_workload_查询应用服务的挂载存储列表
        GET /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/kinds/{kind}/applications/{name}/volumeMounts
        """
        logger.info(f"Get workload volume mounts: kind={kind}, name={name}")
        url = (
            f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}"
            f"/kinds/{kind}/applications/{name}/volumeMounts"
        )
        response = self.get(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def get_workload_hpa(self, cluster_id: str, namespace: str, kind: str, name: str) -> Dict[str, Any]:
        """
        查询 Workload 的 HPA。

        对应 JMX：弹性计算_extentions_workload_查询应用服务的HPA
        GET /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/kinds/{kind}/applications/{name}/hpa
        """
        logger.info(f"Get workload hpa: kind={kind}, name={name}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/kinds/{kind}/applications/{name}/hpa"
        response = self.get(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def update_workload_replicas(
        self, cluster_id: str, namespace: str, kind: str, name: str, replicas: int
    ) -> Dict[str, Any]:
        """
        更新 Workload 副本数。

        对应 JMX：弹性计算_extentions_workload_更新Deployment副本数
        POST /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/kinds/{kind}/applications/{name}/replicas/{replicas}
        """
        logger.info(f"Update workload replicas: kind={kind}, name={name}, replicas={replicas}")
        url = (
            f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}"
            f"/kinds/{kind}/applications/{name}/replicas/{replicas}"
        )
        response = self.post(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def stop_workload(self, cluster_id: str, namespace: str, kind: str, name: str) -> Dict[str, Any]:
        """停止 Workload。POST /kinds/{kind}/applications/{name}/stop"""
        logger.info(f"Stop workload: kind={kind}, name={name}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/kinds/{kind}/applications/{name}/stop"
        response = self.post(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def start_workload(self, cluster_id: str, namespace: str, kind: str, name: str) -> Dict[str, Any]:
        """启动 Workload。POST /kinds/{kind}/applications/{name}/start"""
        logger.info(f"Start workload: kind={kind}, name={name}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/kinds/{kind}/applications/{name}/start"
        response = self.post(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def restart_workload(self, cluster_id: str, namespace: str, kind: str, name: str) -> Dict[str, Any]:
        """重启 Workload。POST /kinds/{kind}/applications/{name}/restart"""
        logger.info(f"Restart workload: kind={kind}, name={name}")
        url = (
            f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/kinds/{kind}/applications/{name}/restart"
        )
        response = self.post(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def get_workload_services(self, cluster_id: str, namespace: str, kind: str, name: str) -> Dict[str, Any]:
        """
        查询 Workload 关联的 Service。

        对应 JMX：弹性计算_extentions_workload_查询应用服务关联的Service
        GET /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/kinds/{kind}/applications/{name}/services
        """
        logger.info(f"Get workload services: kind={kind}, name={name}")
        url = (
            f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}"
            f"/kinds/{kind}/applications/{name}/services"
        )
        response = self.get(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def update_workload_services(
        self,
        cluster_id: str,
        namespace: str,
        kind: str,
        name: str,
        services: List[WorkloadServiceEntity],
    ) -> Dict[str, Any]:
        """
        更新 Workload 关联的 Service。

        对应 JMX：弹性计算_extentions_workload_更新应用服务Service
        PUT /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/kinds/{kind}/applications/{name}/services
        """
        logger.info(f"Update workload services: kind={kind}, name={name}, count={len(services)}")
        url = (
            f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}"
            f"/kinds/{kind}/applications/{name}/services"
        )
        payload = {
            "services": [
                {
                    "name": s.name,
                    "type": s.type,
                    "ports": [
                        {"port": p.port, "targetPort": p.target_port, "protocol": p.protocol}
                        for p in s.ports
                    ],
                }
                for s in services
            ]
        }
        response = self.put(endpoint=url, json=payload, headers=_get_workload_headers())
        return response.json()

    def get_services_workloads(self, cluster_id: str, namespace: str, name: str) -> Dict[str, Any]:
        """
        通过 Service 反查关联的 Workload。

        对应 JMX：弹性计算_extentions_workload_通过Service查询关联的应用服务
        GET /elastic-compute/v1/clusters/{clusterId}/namespaces/{namespace}/services/{name}/workloads
        """
        logger.info(f"Get services workloads: name={name}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/services/{name}/workloads"
        response = self.get(endpoint=url, headers=_get_workload_headers())
        return response.json()

    def batch_create_workloads(
        self, cluster_id: str, namespace: str, workloads: List[WorkloadEntity]
    ) -> Dict[str, Any]:
        """批量创建 Workload。POST /applications/batch"""
        logger.info(f"Batch create workloads: cluster={cluster_id}, ns={namespace}, count={len(workloads)}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/applications/batch"
        workload_list: List[Dict[str, Any]] = []
        for w in workloads:
            item: Dict[str, Any] = {
                "name": w.name,
                "kind": w.kind,
                "image": w.image,
                "appCode": w.app_code,
                "labels": dict(w.labels),
            }
            if w.replicas is not None:
                item["replicas"] = w.replicas
            workload_list.append(item)
        payload = {"workloadList": workload_list}
        response = self.post(endpoint=url, json=payload, headers=_get_workload_headers())
        return response.json()

    def batch_update_workloads(
        self, cluster_id: str, namespace: str, workloads: List[WorkloadEntity]
    ) -> Dict[str, Any]:
        """批量更新 Workload。PUT /applications/batch"""
        logger.info(f"Batch update workloads: cluster={cluster_id}, ns={namespace}, count={len(workloads)}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/applications/batch"
        workload_list: List[Dict[str, Any]] = []
        for w in workloads:
            item: Dict[str, Any] = {
                "name": w.name,
                "kind": w.kind,
                "image": w.image,
                "appCode": w.app_code,
                "labels": dict(w.labels),
            }
            if w.replicas is not None:
                item["replicas"] = w.replicas
            workload_list.append(item)
        payload = {"workloadList": workload_list}
        response = self.put(endpoint=url, json=payload, headers=_get_workload_headers())
        return response.json()

    def batch_delete_workloads(
        self, cluster_id: str, namespace: str, workloads: List[WorkloadEntity]
    ) -> Dict[str, Any]:
        """批量删除 Workload。DELETE /applications/batch（body 仅 kind+name）"""
        logger.info(f"Batch delete workloads: cluster={cluster_id}, ns={namespace}, count={len(workloads)}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/applications/batch"
        payload = {"workloadList": [{"kind": w.kind, "name": w.name} for w in workloads]}
        response = self.delete(endpoint=url, json=payload, headers=_get_workload_headers())
        return response.json()

    def batch_stop_workloads(
        self, cluster_id: str, namespace: str, workloads: List[WorkloadEntity]
    ) -> Dict[str, Any]:
        """批量停止 Workload。POST /applications/stop/batch（body 仅 kind+name）"""
        logger.info(f"Batch stop workloads: cluster={cluster_id}, ns={namespace}, count={len(workloads)}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/applications/stop/batch"
        payload = {"workloadList": [{"kind": w.kind, "name": w.name} for w in workloads]}
        response = self.post(endpoint=url, json=payload, headers=_get_workload_headers())
        return response.json()

    def batch_start_workloads(
        self, cluster_id: str, namespace: str, workloads: List[WorkloadEntity]
    ) -> Dict[str, Any]:
        """批量启动 Workload。POST /applications/start/batch（body 仅 kind+name）"""
        logger.info(f"Batch start workloads: cluster={cluster_id}, ns={namespace}, count={len(workloads)}")
        url = f"/elastic-compute/v1/clusters/{cluster_id}/namespaces/{namespace}/applications/start/batch"
        payload = {"workloadList": [{"kind": w.kind, "name": w.name} for w in workloads]}
        response = self.post(endpoint=url, json=payload, headers=_get_workload_headers())
        return response.json()

    # ==================== system-bind 系统绑定 ====================

    def check_system_quota(self, tenant_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询系统是否有配额信息。

        对应 JMX：弹性计算_extentions_system-bind_查询系统是否有配额信息
        GET /elastic-compute/v2/tenants/{tenantCode}/sysCode/{sysCode}/ns/quota
        """
        logger.info(f"Check system quota: tenant={tenant_code}, sysCode={sys_code}")
        url = f"/elastic-compute/v2/tenants/{tenant_code}/sysCode/{sys_code}/ns/quota"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def bind_system_user(self, sys_code: str, username: str) -> Dict[str, Any]:
        """
        用户与系统绑定。

        对应 JMX：弹性计算_extentions_system-bind_用户与系统绑定接口
        GET /elastic-compute/v2/sysCode/{sysCode}/username/{username}/bindUser
        """
        logger.info(f"Bind system user: sysCode={sys_code}, username={username}")
        url = f"/elastic-compute/v2/sysCode/{sys_code}/username/{username}/bindUser"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()

    def unbind_system_user(self, sys_code: str, username: str) -> Dict[str, Any]:
        """
        解除用户与系统绑定。

        对应 JMX：弹性计算_extentions_system-bind_解除用户与系统绑定接口
        GET /elastic-compute/v2/sysCode/{sysCode}/username/{username}/unbindUser
        """
        logger.info(f"Unbind system user: sysCode={sys_code}, username={username}")
        url = f"/elastic-compute/v2/sysCode/{sys_code}/username/{username}/unbindUser"
        response = self.get(endpoint=url, headers=_get_ext_headers())
        return response.json()
