"""
Elastic Compute Extensions（磐基自定义扩展）实体模型。

承载 ``tests/api/elastic_compute/extensions/`` 下测试文件对应的 ``*PublicParams``
与请求体 Entity。包括：Workload 生命周期、Helm Chart 生命周期、Partitions API
（磐基自定义 ResourceQuota/LimitRange）、CustomResource V1、TenantQuota、
PhysicalHost、NamespaceQuota、NginxRbac、SystemBind、ClusterManager、AppGrant、
Dashboard、Node（节点污点）、HarborBindCluster、ImageApi、Endpoints、HostBind。

与 :mod:`base.api.entity.elastic_compute.native` 物理隔离：
- native 侧偏 K8s 原生 spec；extensions 侧为磐基自定义扁平 payload。
- 存在部分同名概念（如 ``ResourceQuotaEntity`` / ``LimitRangeEntity``），语义
  分别对应两条独立的 API，请按目录路径引用正确的一份。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from base.api.entity.elastic_compute.native import PaasLabels



# ==================== Workload 生命周期 ====================

@dataclass
class WorkloadPublicParams(object):
    """
    Workload 生命周期测试的公共参数集合（对齐 workload.jmx 中的默认变量）。

    集中承载 cluster / namespace / kind / name / image / labels 等常用字段，
    供测试用例传给 service 层构造具体 Entity。字段名与 JMX 变量一一对应。

    Attributes:
        cluster_id: 集群 ID
        namespace: K8s Namespace
        cell_code: PaaS Cell 编码（查询接口用）
        sys_code: PaaS System 编码（查询接口用）
        name: Workload 名称
        kind: Workload 类型（Deployment / StatefulSet / CloneSet / DaemonSet / CronJob / Job）
        image: 容器镜像
        replicas: 初始副本数
        app_code: 应用编码
        paas_env_code / paas_plane_code / paas_tenant_code / paas_owner / paas_unit_code:
            PaaS 标签集所需字段
    """

    cluster_id: str
    namespace: str
    cell_code: str
    sys_code: str
    name: str
    kind: str
    image: str
    replicas: int = 1
    app_code: str = "test-app"
    paas_env_code: str = "PROD"
    paas_plane_code: str = "test"
    paas_tenant_code: str = "monitor-group"
    paas_owner: str = "panji_probe"
    paas_unit_code: str = "test"

@dataclass
class WorkloadEntity(object):
    """
    Workload create / update / batch payload 的实体表示（对应 workload.jmx create body）。

    字段命名使用 snake_case（Python 侧），service 层负责映射到 API 契约的字段名
    （name / kind / replicas / image / appCode / labels）。

    Attributes:
        name: Workload 名称
        kind: Workload 类型
        image: 容器镜像
        app_code: 应用编码
        replicas: 副本数（Deployment / StatefulSet 用；DaemonSet / Job 可为 None 由 service 决定是否携带）
        labels: 完整 labels 字典（key 使用 K8s kebab-case）
    """

    name: str
    kind: str
    image: str
    app_code: str
    replicas: Optional[int] = 1
    labels: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_public_params(cls, params: "WorkloadPublicParams") -> "WorkloadEntity":
        """
        从 WorkloadPublicParams 快捷构造 WorkloadEntity，并附加对齐 JMX 的 12 项 PaaS 标签。
        """
        labels = PaasLabels(
            paas_owner=params.paas_owner,
            paas_cluster_code=params.cluster_id,
            paas_app_code=params.app_code,
            paas_env_code=params.paas_env_code,
            paas_plane_code=params.paas_plane_code,
            paas_tenant_code=params.paas_tenant_code,
            paas_unit_code=params.paas_unit_code,
            paas_system_code=params.namespace,
            paas_workload_name=params.name,
            paas_app_source="workload",
        ).to_dict()
        labels["paas-workload-kind"] = params.kind
        return cls(
            name=params.name,
            kind=params.kind,
            image=params.image,
            app_code=params.app_code,
            replicas=params.replicas,
            labels=labels,
        )

@dataclass
class WorkloadServicePortEntity(object):
    """K8s Service 端口定义（Workload 关联 Service 的 ports[] 单项）。"""

    port: int = 80
    target_port: int = 80
    protocol: str = "TCP"

@dataclass
class WorkloadServiceEntity(object):
    """
    Workload 关联的 Service payload 单项（对应 workload.jmx update-services body）。

    Attributes:
        name: Service 名称（一般等于 Workload 名称）
        type: Service 类型，默认 ClusterIP
        ports: 端口列表
    """

    name: str
    type: str = "ClusterIP"
    ports: List[WorkloadServicePortEntity] = field(
        default_factory=lambda: [WorkloadServicePortEntity()]
    )

@dataclass
class WorkloadPatchEntity(object):
    """
    Workload PATCH（增量更新）payload 实体（对应 workload.jmx patch body）。

    PATCH 场景为局部字段更新，目前 JMX 场景只使用 labels 字段。
    如后续需要 patch 其他字段，可在此扩展。
    """

    labels: Dict[str, str] = field(default_factory=dict)


# ==================== Helm Chart 生命周期 ====================

@dataclass
class HelmChartPublicParams(object):
    """
    Helm/Chart 生命周期测试的公共参数集合（对齐 helm-chart.jmx 用户参数默认值）。

    Attributes:
        cluster_id: 集群 ID
        namespace: K8s Namespace
        cell_code: PaaS Cell 编码（v2 批量接口路径参数）
        sys_code: PaaS System 编码（v2 批量接口路径参数）
        chart_name: Chart 名称
        chart_version: Chart 版本
        release_name: Helm Release 名称（发布实例名）
        image: 容器镜像仓库地址
        image_tag: 镜像 tag
        paas_app_code: PaaS 应用编码
        paas_owner: PaaS 应用负责人
        paas_tenant_code: PaaS 租户编码
        paas_env_code: PaaS 环境编码
        paas_plane_code: PaaS 平面编码
    """

    cluster_id: str
    namespace: str
    cell_code: str
    sys_code: str
    chart_name: str
    chart_version: str
    release_name: str
    image: str
    image_tag: str
    paas_app_code: str
    paas_owner: str
    paas_tenant_code: str
    paas_env_code: str
    paas_plane_code: str

@dataclass
class HelmReleaseEntity(object):
    """
    Helm Install / Upgrade / 批量安装 / 批量升级 的单条 Release 实体。

    对应 helm-chart.jmx 中 install/upgrade body 的核心字段。
    Python 侧字段为 snake_case，service 层负责组装成 API 契约要求的
    带点 flat key（image.repository / labels.paas-* / service.labels.paas-*）。

    Attributes:
        name: Helm Release 名称
        chart_name: Chart 名称
        chart_version: Chart 版本
        image: 容器镜像仓库地址
        image_tag: 镜像 tag
        cluster_id: 集群编码（写入 labels.paas-cluster-code）
        namespace: K8s Namespace（写入 labels.paas-system-code）
        cell_code: PaaS Cell 编码（写入 labels.paas-unit-code）
        paas_app_code / paas_owner / paas_tenant_code / paas_env_code /
            paas_plane_code: PaaS 标签字段
        extra_label_test: True 时额外追加 labels.test=update / service.labels.test=update
            （对齐 JMX upgrade 场景），默认 False（install 场景）
    """

    name: str
    chart_name: str
    chart_version: str
    image: str
    image_tag: str
    cluster_id: str
    namespace: str
    cell_code: str
    paas_app_code: str
    paas_owner: str
    paas_tenant_code: str
    paas_env_code: str
    paas_plane_code: str
    extra_label_test: bool = False

    @classmethod
    def from_public_params(
        cls, params: "HelmChartPublicParams", *, extra_label_test: bool = False
    ) -> "HelmReleaseEntity":
        """从 HelmChartPublicParams 快捷构造 HelmReleaseEntity。"""
        return cls(
            name=params.release_name,
            chart_name=params.chart_name,
            chart_version=params.chart_version,
            image=params.image,
            image_tag=params.image_tag,
            cluster_id=params.cluster_id,
            namespace=params.namespace,
            cell_code=params.cell_code,
            paas_app_code=params.paas_app_code,
            paas_owner=params.paas_owner,
            paas_tenant_code=params.paas_tenant_code,
            paas_env_code=params.paas_env_code,
            paas_plane_code=params.paas_plane_code,
            extra_label_test=extra_label_test,
        )

@dataclass
class HelmBatchUninstallEntity(object):
    """
    Helm 批量卸载 payload 实体（对应 helm-chart.jmx 批量卸载 body）。

    Attributes:
        release_names: 待卸载的 Helm Release 名称列表
    """

    release_names: List[str] = field(default_factory=list)


# ==================== Partitions API - ResourceQuota / LimitRange ====================

@dataclass
class PartitionsPublicParams(object):
    """
    Partitions API 测试公共参数（对齐 partitions-api.jmx 用户参数默认值）。

    Attributes:
        cluster_id: 集群 ID
        namespace: K8s Namespace
        is_host_cluster: 是否托管集群（"1"=托管集群，"0"=标准集群）
    """

    cluster_id: str
    namespace: str
    is_host_cluster: str = "0"

@dataclass
class ResourceQuotaEntity(object):
    """
    ResourceQuota 创建 / 更新 payload 实体（对应 partitions-api.jmx create body）。

    Attributes:
        limits_cpu: CPU 上限（核）
        limits_memory: 内存上限（Gi）
        requests_cpu: CPU 请求量（核）
        requests_memory: 内存请求量（Gi）
    """

    limits_cpu: int = 1
    limits_memory: int = 1
    requests_cpu: int = 1
    requests_memory: int = 1

@dataclass
class LimitRangeEntity(object):
    """
    LimitRange 创建 / 更新 payload 实体（对应 partitions-api.jmx create body）。

    Attributes:
        max_cpu: 最大 CPU 限额
        max_memory: 最大内存限额（Mi）
        min_cpu: 最小 CPU 限额
        min_memory: 最小内存限额（Mi）
    """

    max_cpu: int = 2
    max_memory: int = 1024
    min_cpu: int = 1
    min_memory: int = 256


# ==================== CustomResource V1 自定义资源 ====================

@dataclass
class CustomResourcePublicParams(object):
    """
    CustomResource V1 测试公共参数（对齐 CustomResourceV1.jmx 用户参数默认值）。

    Attributes:
        cluster_id: 集群 ID
        group: CRD API group（如 test.example.com）
        version: CRD API version（如 v1）
        namespace: K8s Namespace
        kind: CRD Kind（如 Banana）
        name: CR 实例名称
    """

    cluster_id: str
    group: str
    version: str
    namespace: str
    kind: str
    name: str

@dataclass
class CustomResourceCreateEntity(object):
    """
    CustomResource 创建 payload 实体（对应 CustomResourceV1.jmx create body）。

    Attributes:
        group: CRD API group
        version: CRD API version
        kind: CRD Kind
        name: CR 实例名称
        message: spec.message 字段值
        replicas: spec.replicas 字段值
    """

    group: str
    version: str
    kind: str
    name: str
    message: str = "I have an apple!"
    replicas: int = 1

    @classmethod
    def from_public_params(
        cls, params: "CustomResourcePublicParams"
    ) -> "CustomResourceCreateEntity":
        """从 CustomResourcePublicParams 快捷构造 CustomResourceCreateEntity。"""
        return cls(
            group=params.group,
            version=params.version,
            kind=params.kind,
            name=params.name,
        )

@dataclass
class CustomResourceUpdateEntity(object):
    """
    CustomResource 更新 payload 实体（对应 CustomResourceV1.jmx update body）。

    Attributes:
        group: CRD API group
        version: CRD API version
        kind: CRD Kind
        name: CR 实例名称
        namespace: K8s Namespace（更新场景 metadata.namespace 必填）
        display_name: spec.name 字段值（用户可见展示名）
        description: spec.description 字段值
    """

    group: str
    version: str
    kind: str
    name: str
    namespace: str
    display_name: str = "Test Resource 001"
    description: str = "Updated description for test resource."

    @classmethod
    def from_public_params(
        cls, params: "CustomResourcePublicParams"
    ) -> "CustomResourceUpdateEntity":
        """从 CustomResourcePublicParams 快捷构造 CustomResourceUpdateEntity。"""
        return cls(
            group=params.group,
            version=params.version,
            kind=params.kind,
            name=params.name,
            namespace=params.namespace,
        )


# ==================== Tenant Quota 租户配额 ====================

@dataclass
class TenantQuotaPublicParams(object):
    """
    Tenant Quota 测试公共参数（对齐 tenant-quota.jmx 用户参数默认值）。

    Attributes:
        cluster_id: 集群 ID
        tenant_code: 租户编码（对齐 JMX 中 adminTenantCode 变量）
    """

    cluster_id: str
    tenant_code: str

@dataclass
class TenantQuotaBatchEntity(object):
    """
    批量查询租户资源配额概览的 payload 实体
    （对应 tenant-quota.jmx 中 POST /v1/tenants/quota/batch 的 body）。

    Attributes:
        tenant_codes: 待查询的租户编码列表
    """

    tenant_codes: List[str] = field(default_factory=list)


# ==================== Physical Host 裸金属主机 ====================

@dataclass
class PhysicalHostPublicParams(object):
    """
    Physical Host 测试公共参数（对齐 physical-host.jmx 用户参数默认值）。

    Attributes:
        fallback_host_id: 当动态查询未获取到 hostId 时的回退值（env physicalHostId）
        admin_tenant_code: 绑定用租户编码（管理员场景，写入 bind 接口）
        bind_tenant_code: 解绑用租户编码（对齐 JMX 中两个可能不同的变量）
    """

    fallback_host_id: str
    admin_tenant_code: str
    bind_tenant_code: str


# ==================== Namespace Quota 系统配额 ====================

@dataclass
class NamespaceQuotaPublicParams(object):
    """
    Namespace Quota 测试公共参数（对齐 namespace-quota.jmx 用户参数默认值）。

    Attributes:
        cluster_id: 集群 ID
        tenant_code: 租户编码
        namespace: K8s Namespace
    """

    cluster_id: str
    tenant_code: str
    namespace: str


# ==================== Nginx RBAC 模板 ====================

@dataclass
class NginxRbacPublicParams(object):
    """
    Nginx RBAC 模板测试公共参数（对齐 nginx-rbac.jmx 用户参数默认值）。

    Attributes:
        cluster_id: 集群 ID
        namespace: K8s Namespace
        code: RBAC 模板编码
    """

    cluster_id: str
    namespace: str
    code: str


# ==================== System Bind 系统绑定 ====================

@dataclass
class SystemBindPublicParams(object):
    """
    System Bind 测试公共参数（对齐 system-bind.jmx 用户参数默认值）。

    Attributes:
        tenant_code: 租户编码
        sys_code: 系统编码
        username: 待绑定的用户名
    """

    tenant_code: str
    sys_code: str
    username: str


# ==================== Cluster Manager 集群管理 ====================

@dataclass
class ClusterManagerPublicParams(object):
    """
    Cluster Manager 测试公共参数（对齐 cluster-manager.jmx 用户参数默认值）。

    Attributes:
        cluster_id: 集群 ID（fallback 值，实际优先使用 api_cache 中动态提取的 ext_cluster_id）
    """

    cluster_id: str


# ==================== App Grant 应用授权 ====================

@dataclass
class AppGrantPublicParams(object):
    """
    App Grant 测试公共参数（对齐 app-grant.jmx 用户参数默认值）。

    Attributes:
        app_code: 应用编码
        grant_user: 待授权/解除授权的用户名
        end_time: 授权到期时间字符串（yyyy-MM-dd HH:mm:ss）
    """

    app_code: str
    grant_user: str
    end_time: str

@dataclass
class AppGrantEntity(object):
    """
    应用授权请求体实体
    （对应 app-grant.jmx 中 POST /elastic-compute/v1/applications/{appCode}/grantUsers 的 body）。

    Attributes:
        users: 待授权的用户名列表
        end_time: 授权到期时间字符串（yyyy-MM-dd HH:mm:ss）
    """

    users: List[str] = field(default_factory=list)
    end_time: str = ""

@dataclass
class AppRemoveGrantEntity(object):
    """
    解除应用授权请求体实体
    （对应 app-grant.jmx 中 DELETE /elastic-compute/v1/applications/{appCode}/grantUsers 的 body，
    JMX 中为纯 JSON 数组形态）。

    Attributes:
        users: 待解除授权的用户名列表（序列化为 JSON 数组，非对象）
    """

    users: List[str] = field(default_factory=list)


# ==================== Dashboard 资源面板 ====================

@dataclass
class DashboardPublicParams(object):
    """
    Dashboard 测试公共参数（对齐 Dashboard.jmx 用户参数默认值）。

    Attributes:
        tenant_code: 租户编码
        start_time: 查询起始时间戳（毫秒，字符串形态对齐 JMX 用户参数）
        end_time: 查询结束时间戳（毫秒，字符串形态对齐 JMX 用户参数）
    """

    tenant_code: str
    start_time: str
    end_time: str


# ==================== Node 节点污点 ====================

@dataclass
class NodePublicParams(object):
    """
    Node 节点污点查询测试公共参数（对齐 Node.jmx 用户参数默认值）。

    Attributes:
        cell_code: 单元编码
        node_name: 节点名（对齐 JMX 中 nodeIp 变量）
    """

    cell_code: str
    node_name: str


# ==================== Harbor Bind Cluster ====================

@dataclass
class HarborBindPublicParams(object):
    """
    Harbor 绑定集群测试公共参数（对齐 harbor-bindcluster.jmx 用户参数默认值）。

    Attributes:
        cluster_id: 集群 ID（JMX 中为数值类型）
        harbor_name: Harbor 仓库名称
    """

    cluster_id: int
    harbor_name: str

@dataclass
class HarborBindClusterEntity(object):
    """
    Harbor 绑定集群请求体实体
    （对应 harbor-bindcluster.jmx 中 POST /elastic-compute/v1/harbor/bindCluster 的 body）。

    Attributes:
        cluster_id: 集群 ID（数值）
        harbor_name: Harbor 仓库名称
    """

    cluster_id: int
    harbor_name: str


# ==================== Image API 镜像 ====================

@dataclass
class ImageApiPublicParams(object):
    """
    Image API 测试公共参数（对齐 image-api.jmx 用户参数默认值）。

    Attributes:
        repo_name: 镜像仓库名（对齐 JMX 中 nginxRepoName 变量）
        project_name: 项目名（对齐 JMX 中 nginxProjectName 变量）
    """

    repo_name: str
    project_name: str


# ==================== Endpoints ====================

@dataclass
class EndpointsPublicParams(object):
    """
    Endpoints 测试公共参数（对齐 Endpoints.jmx 用户参数默认值）。

    Attributes:
        cell_code: 单元编码
    """

    cell_code: str


# ==================== Host Bind ====================

@dataclass
class HostBindPublicParams(object):
    """
    Host Bind 测试公共参数（对齐 host-bind.jmx 用户参数默认值）。

    Attributes:
        cell_code: 单元编码
    """

    cell_code: str


__all__ = [
    "WorkloadPublicParams",
    "WorkloadEntity",
    "WorkloadServicePortEntity",
    "WorkloadServiceEntity",
    "WorkloadPatchEntity",
    "HelmChartPublicParams",
    "HelmReleaseEntity",
    "HelmBatchUninstallEntity",
    "PartitionsPublicParams",
    "ResourceQuotaEntity",
    "LimitRangeEntity",
    "CustomResourcePublicParams",
    "CustomResourceCreateEntity",
    "CustomResourceUpdateEntity",
    "TenantQuotaPublicParams",
    "TenantQuotaBatchEntity",
    "PhysicalHostPublicParams",
    "NamespaceQuotaPublicParams",
    "NginxRbacPublicParams",
    "SystemBindPublicParams",
    "ClusterManagerPublicParams",
    "AppGrantPublicParams",
    "AppGrantEntity",
    "AppRemoveGrantEntity",
    "DashboardPublicParams",
    "NodePublicParams",
    "HarborBindPublicParams",
    "HarborBindClusterEntity",
    "ImageApiPublicParams",
    "EndpointsPublicParams",
    "HostBindPublicParams",
]
