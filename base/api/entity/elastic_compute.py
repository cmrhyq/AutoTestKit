"""
Elastic Compute（弹性计算）Native K8s 资源实体模型。

参照 Java MVC 分层设计，将 K8s 原生资源的 payload 构造从 test / service 层
解耦到独立的 Entity / DTO 层，便于跨 test / service 复用。

分为三类：
1. 基础复用组件：PaasLabels（12 字段 PaaS 标签）、K8sMetadata、
   ContainerPort、ContainerSpec、PodTemplate、LabelSelector
2. 具体资源 Payload：NamespacePayload / ResourceQuotaPayload / LimitRangePayload /
   PriorityClassPayload / IngressPayload / HpaPayload / PodPayload /
   DeploymentPayload / DaemonSetPayload / JobPayload
3. 每个 Payload 都提供 `to_dict()` 方法生成符合 K8s API 契约的 JSON 对象。

所有 Payload 字段名使用 camelCase 以对齐 K8s API 契约（不做二次转换）。
"""

from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional


# ==================== 基础复用组件 ====================


@dataclass
class PaasLabels(object):
    """
    磐基 PaaS 标准 12 字段标签集，跨 Deployment / DaemonSet / Job / Pod / Ingress /
    HPA 等资源复用。

    对应 K8s metadata.labels 中的 paas-* / operation-source / paas-resource-category
    等键值对。字段名使用 snake_case（Python 侧），序列化到 API 时会转换为 K8s 惯用的
    带连字符 kebab-case 键名（如 paas-app-code）。
    """

    paas_owner: str = "panji_probe"
    paas_cluster_code: str = ""
    paas_app_code: str = ""
    paas_env_code: str = "ENV1"
    paas_plane_code: str = "PLANE1"
    paas_tenant_code: str = "tenant-001"
    paas_unit_code: str = "TEST"
    paas_system_code: str = ""
    paas_workload_name: str = ""
    paas_app_service_version: str = "v1"
    paas_app_source: str = "baseImage"
    paas_resource_category: str = "tenant-app"
    operation_source: str = "api"

    # 键名映射：Python snake_case -> K8s label kebab-case
    _KEY_MAP: ClassVar[Dict[str, str]] = {
        "paas_owner": "paas-owner",
        "paas_cluster_code": "paas-cluster-code",
        "paas_app_code": "paas-app-code",
        "paas_env_code": "paas-env-code",
        "paas_plane_code": "paas-plane-code",
        "paas_tenant_code": "paas-tenant-code",
        "paas_unit_code": "paas-unit-code",
        "paas_system_code": "paas-system-code",
        "paas_workload_name": "paas-workload-name",
        "paas_app_service_version": "paas-app-service-version",
        "paas_app_source": "paas-app-source",
        "paas_resource_category": "paas-resource-category",
        "operation_source": "operation-source",
    }

    def to_dict(self) -> Dict[str, str]:
        """按 K8s 标签契约输出 kebab-case 键的字典（跳过空字符串字段）。"""
        result: Dict[str, str] = {}
        for py_key, k8s_key in self._KEY_MAP.items():
            value = getattr(self, py_key)
            if value == "" or value is None:
                continue
            result[k8s_key] = str(value)
        return result

    def merged_with(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """合并额外标签（如 name / test / kind 等自定义标签）。"""
        result = self.to_dict()
        if extra:
            result.update(extra)
        return result


@dataclass
class LabelSelector(object):
    """
    K8s LabelSelector 用于列表查询接口（labelSelector 查询参数）。

    使用 to_query_string() 生成形如 `key1=val1,key2=val2` 的字符串。
    """

    match_labels: Dict[str, str] = field(default_factory=dict)

    def to_query_string(self) -> str:
        """按 K8s labelSelector 查询参数格式输出（逗号分隔的 k=v 对）。"""
        return ",".join(f"{k}={v}" for k, v in self.match_labels.items())


@dataclass
class ContainerPort(object):
    """K8s 容器端口。"""

    containerPort: int
    name: str = "port0"
    protocol: str = "TCP"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "containerPort": self.containerPort,
            "name": self.name,
            "protocol": self.protocol,
        }


@dataclass
class ContainerSpec(object):
    """K8s 容器规格（image + name + ports）。"""

    image: str
    name: str = "container0"
    imagePullPolicy: Optional[str] = None
    ports: List[ContainerPort] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "image": self.image,
            "name": self.name,
        }
        if self.imagePullPolicy is not None:
            result["imagePullPolicy"] = self.imagePullPolicy
        if self.ports:
            result["ports"] = [p.to_dict() for p in self.ports]
        return result


@dataclass
class K8sMetadata(object):
    """K8s 通用元数据（name + labels）。"""

    name: str
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"name": self.name}
        if self.labels:
            result["labels"] = dict(self.labels)
        return result


@dataclass
class PodTemplate(object):
    """K8s Pod 模板（metadata.labels + spec.containers）。"""

    labels: Dict[str, str] = field(default_factory=dict)
    containers: List[ContainerSpec] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": {"labels": dict(self.labels)},
            "spec": {"containers": [c.to_dict() for c in self.containers]},
        }


# ==================== Namespace / ResourceQuota / LimitRange ====================


@dataclass
class NamespacePayload(object):
    """K8s Namespace 资源 payload（对应 namespace-api.jmx 中的 POST/PUT body）。"""

    name: str
    apiVersion: str = "v1"
    kind: str = "Namespace"
    spec: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "metadata": {"name": self.name},
            "spec": dict(self.spec),
        }


@dataclass
class ResourceQuotaPayload(object):
    """K8s ResourceQuota 资源 payload（对应 namespace-api.jmx 中的 POST/PUT body）。"""

    name: str
    hard: Dict[str, str] = field(default_factory=lambda: {"pods": "110"})
    apiVersion: str = "v1"
    kind: str = "ResourceQuota"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "metadata": {"name": self.name},
            "spec": {"hard": dict(self.hard)},
        }


@dataclass
class LimitRangeItem(object):
    """LimitRange spec.limits 中的单项（Container 级别 CPU 限制）。"""

    default_cpu: str = "50m"
    defaultRequest_cpu: str = "50m"
    max_cpu: str = "1"
    min_cpu: str = "10m"
    type: str = "Container"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "default": {"cpu": self.default_cpu},
            "defaultRequest": {"cpu": self.defaultRequest_cpu},
            "max": {"cpu": self.max_cpu},
            "min": {"cpu": self.min_cpu},
            "type": self.type,
        }


@dataclass
class LimitRangePayload(object):
    """K8s LimitRange 资源 payload（对应 namespace-api.jmx 中的 POST/PUT body）。"""

    name: str
    limits: List[LimitRangeItem] = field(default_factory=lambda: [LimitRangeItem()])
    apiVersion: str = "v1"
    kind: str = "LimitRange"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "metadata": {"name": self.name},
            "spec": {"limits": [item.to_dict() for item in self.limits]},
        }


# ==================== PriorityClass ====================


@dataclass
class PriorityClassPayload(object):
    """K8s PriorityClass（cluster-scoped）payload（对应 priorityclass.jmx）。"""

    name: str
    value: int = 100000000
    description: str = "this is a test"
    labels: Dict[str, str] = field(default_factory=dict)
    apiVersion: str = "scheduling.k8s.io/v1"
    kind: str = "PriorityClass"

    def to_dict(self) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {"name": self.name}
        if self.labels:
            metadata["labels"] = dict(self.labels)
        return {
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "metadata": metadata,
            "value": self.value,
            "description": self.description,
        }


# ==================== Ingress ====================


@dataclass
class IngressServiceBackend(object):
    """K8s Ingress backend.service 结构。"""

    name: str = "qwe"
    port_number: int = 4000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service": {
                "name": self.name,
                "port": {"number": self.port_number},
            }
        }


@dataclass
class IngressHttpPath(object):
    """K8s Ingress rules[].http.paths[] 单项。"""

    path: str = "/install"
    pathType: str = "Prefix"
    backend: IngressServiceBackend = field(default_factory=IngressServiceBackend)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "pathType": self.pathType,
            "backend": self.backend.to_dict(),
        }


@dataclass
class IngressPayload(object):
    """K8s Ingress 资源 payload（对应 ingress-api.jmx 中的 POST/PUT body）。"""

    name: str
    labels: Dict[str, str] = field(default_factory=dict)
    paths: List[IngressHttpPath] = field(default_factory=lambda: [IngressHttpPath()])
    apiVersion: str = "networking.k8s.io/v1"
    kind: str = "Ingress"

    def to_dict(self) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {"name": self.name}
        if self.labels:
            metadata["labels"] = dict(self.labels)
        return {
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "metadata": metadata,
            "spec": {
                "rules": [
                    {"http": {"paths": [p.to_dict() for p in self.paths]}}
                ]
            },
        }


# ==================== HPA ====================


@dataclass
class HpaScaleTargetRef(object):
    """K8s HPA spec.scaleTargetRef 结构。"""

    kind: str
    name: str
    apiVersion: str = "apps/v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "name": self.name,
        }


@dataclass
class HpaCpuUtilizationMetric(object):
    """K8s HPA CPU 利用率 metric（Resource 类型）。"""

    averageUtilization: int = 50

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Resource",
            "resource": {
                "name": "cpu",
                "target": {
                    "type": "Utilization",
                    "averageUtilization": self.averageUtilization,
                },
            },
        }


@dataclass
class HpaPayload(object):
    """K8s HorizontalPodAutoscaler 资源 payload（对应 hpa.jmx）。"""

    name: str
    scale_target: HpaScaleTargetRef
    labels: Dict[str, str] = field(default_factory=dict)
    minReplicas: int = 1
    maxReplicas: int = 3
    cpu_utilization: int = 50
    apiVersion: str = "autoscaling/v2"
    kind: str = "HorizontalPodAutoscaler"

    def to_dict(self) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {"name": self.name}
        if self.labels:
            metadata["labels"] = dict(self.labels)
        return {
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "metadata": metadata,
            "spec": {
                "maxReplicas": self.maxReplicas,
                "minReplicas": self.minReplicas,
                "metrics": [
                    HpaCpuUtilizationMetric(self.cpu_utilization).to_dict()
                ],
                "scaleTargetRef": self.scale_target.to_dict(),
            },
        }


# ==================== Pod / Workload（Deployment / DaemonSet / Job）====================


@dataclass
class PodPayload(object):
    """K8s Pod 资源 payload（对应 pod.jmx）。"""

    name: str
    containers: List[ContainerSpec]
    labels: Dict[str, str] = field(default_factory=dict)
    apiVersion: str = "v1"
    kind: str = "Pod"

    def to_dict(self) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {"name": self.name}
        if self.labels:
            metadata["labels"] = dict(self.labels)
        return {
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "metadata": metadata,
            "spec": {"containers": [c.to_dict() for c in self.containers]},
        }


@dataclass
class WorkloadPayload(object):
    """
    K8s 工作负载（Deployment / DaemonSet / Job / etc）通用 payload。

    通过设置不同的 apiVersion / kind / include_replicas 适配多种工作负载类型：
    - Deployment: apiVersion="apps/v1", kind="Deployment", include_replicas=True
    - DaemonSet:  apiVersion="apps/v1", kind="DaemonSet", include_replicas=False
    - Job:        apiVersion="batch/v1", kind="Job", include_replicas=False,
                  include_selector=False, template_include_matchlabels=False

    对应 JMX 中的 POST/PUT body。
    """

    name: str
    apiVersion: str
    kind: str
    template: PodTemplate
    labels: Dict[str, str] = field(default_factory=dict)
    match_labels: Dict[str, str] = field(default_factory=dict)
    replicas: Optional[int] = None
    include_selector: bool = True

    def to_dict(self) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {"name": self.name}
        if self.labels:
            metadata["labels"] = dict(self.labels)

        spec: Dict[str, Any] = {}
        if self.replicas is not None:
            spec["replicas"] = self.replicas
        if self.include_selector:
            spec["selector"] = {"matchLabels": dict(self.match_labels)}
        spec["template"] = self.template.to_dict()

        return {
            "apiVersion": self.apiVersion,
            "kind": self.kind,
            "metadata": metadata,
            "spec": spec,
        }

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


# ==================== Native K8s Resources: PublicParams ====================


@dataclass
class ServiceAccountNativePublicParams(object):
    """test_ec_serviceaccount.py 公参。"""

    cluster_id: str
    namespace: str
    name: str


@dataclass
class ClusterRoleBindingNativePublicParams(object):
    """test_ec_clusterrolebinding.py 公参。"""

    cluster_id: str
    namespace: str
    name: str
    cluster_role_name: str
    service_account_name: str


@dataclass
class RoleBindingNativePublicParams(object):
    """test_ec_rolebinding.py 公参。"""

    cluster_id: str
    namespace: str
    name: str
    role_name: str
    service_account_name: str


@dataclass
class PvcNativePublicParams(object):
    """test_ec_pvc.py 公参。"""

    cluster_id: str
    namespace: str
    pvc_name: str
    paas_owner: str


@dataclass
class CrdNativePublicParams(object):
    """test_ec_crd.py 公参。"""

    cluster_id: str
    name: str


@dataclass
class PodNativePublicParams(object):
    """test_ec_pod.py 公参（含完整 PaaS 标签集）。"""

    cluster_id: str
    namespace: str
    name: str
    paas_app_code: str
    paas_env_code: str
    paas_owner: str
    paas_plane_code: str
    paas_tenant_code: str
    paas_unit_code: str
    image: str


@dataclass
class JobNativePublicParams(object):
    """test_ec_job.py 公参。"""

    cluster_id: str
    namespace: str
    name: str
    paas_app_code: str
    paas_env_code: str
    paas_owner: str
    paas_plane_code: str
    paas_tenant_code: str
    paas_unit_code: str
    image: str
    completions: int
    parallelism: int


@dataclass
class NodeNativePublicParams(object):
    """test_ec_node.py 公参（native 模块，仅 cluster_id）。"""

    cluster_id: str


@dataclass
class SecretNativePublicParams(object):
    """test_ec_secret.py 公参。"""

    cluster_id: str
    namespace: str
    name: str
    paas_owner: str


@dataclass
class ConfigMapNativePublicParams(object):
    """test_ec_configmap_native.py 公参。"""

    cluster_id: str
    namespace: str
    name: str
    paas_owner: str


@dataclass
class ServiceNativePublicParams(object):
    """test_ec_service.py 公参。"""

    cluster_id: str
    namespace: str
    name: str
    paas_app_code: str
    paas_env_code: str
    paas_owner: str
    paas_plane_code: str
    paas_tenant_code: str
    paas_unit_code: str
    paas_workload_name: str


@dataclass
class IngressNativePublicParams(object):
    """test_ec_ingress.py 公参。"""

    cluster_id: str
    namespace: str
    name: str
    paas_owner: str


@dataclass
class PriorityClassNativePublicParams(object):
    """test_ec_priorityclass.py 公参。"""

    cluster_id: str
    name: str


@dataclass
class HpaNativePublicParams(object):
    """test_ec_hpa_native.py 公参。"""

    cluster_id: str
    namespace: str
    name: str
    paas_owner: str
    workload_kind: str
    workload_name: str
    min_replicas: int
    max_replicas: int


@dataclass
class NamespaceNativePublicParams(object):
    """test_ec_namespace.py 公参（含 rq/lr 名字）。"""

    cluster_id: str
    namespace: str
    rq_name: str
    lr_name: str


@dataclass
class StatefulSetNativePublicParams(object):
    """test_ec_statefulset.py 公参。"""

    cluster_id: str
    namespace: str
    name: str
    paas_app_code: str
    paas_env_code: str
    paas_owner: str
    paas_plane_code: str
    paas_tenant_code: str
    paas_unit_code: str
    image: str
    replicas: int


@dataclass
class DeploymentNativePublicParams(object):
    """test_ec_deployment.py 公参。"""

    cluster_id: str
    namespace: str
    name: str
    paas_app_code: str
    paas_env_code: str
    paas_owner: str
    paas_plane_code: str
    paas_tenant_code: str
    paas_unit_code: str
    image: str
    replicas: int


@dataclass
class DaemonSetNativePublicParams(object):
    """test_ec_daemonset.py 公参。"""

    cluster_id: str
    namespace: str
    name: str
    paas_app_code: str
    paas_env_code: str
    paas_owner: str
    paas_plane_code: str
    paas_tenant_code: str
    paas_unit_code: str
    image: str


# ==================== Native K8s Resources: Payload Entities ====================


@dataclass
class ServiceAccountEntity(object):
    """
    K8s ServiceAccount payload 实体（对应 create_service_account 的 body）。

    Attributes:
        name: ServiceAccount 名称
    """

    name: str


@dataclass
class ClusterRoleBindingEntity(object):
    """
    K8s ClusterRoleBinding payload 实体。

    Attributes:
        name: ClusterRoleBinding 名称
        cluster_role_name: 绑定的 ClusterRole 名称（roleRef.name）
        service_account_name: 绑定的 ServiceAccount 名称
        subject_namespace: 绑定的 ServiceAccount 所在 Namespace
    """

    name: str
    cluster_role_name: str
    service_account_name: str
    subject_namespace: str


@dataclass
class RoleBindingEntity(object):
    """
    K8s RoleBinding payload 实体。

    Attributes:
        name: RoleBinding 名称
        role_name: 绑定的 Role 名称
        service_account_name: 绑定的 ServiceAccount 名称
        namespace: RoleBinding 所在 Namespace
    """

    name: str
    role_name: str
    service_account_name: str
    namespace: str


@dataclass
class PvcEntity(object):
    """
    K8s PersistentVolumeClaim payload 实体。

    Attributes:
        name: PVC 名称
        paas_owner: PaaS owner 标签
        storage: 存储容量（如 "10Mi"）
        storage_class_name: StorageClass 名称
        access_modes: 访问模式列表
        volume_mode: 卷模式（Filesystem/Block）
    """

    name: str
    paas_owner: str
    storage: str = "10Mi"
    storage_class_name: str = "demo-sss-001"
    access_modes: List[str] = field(default_factory=lambda: ["ReadWriteOnce"])
    volume_mode: str = "Filesystem"


@dataclass
class CrdEntity(object):
    """
    K8s CustomResourceDefinition payload 实体。

    Attributes:
        name: CRD 名称
        group: API Group
        scope: Namespaced / Cluster
        plural: 复数形式
        singular: 单数形式
        kind: 资源 Kind
        short_names: 简写列表
        version_name: 版本号
        properties: OpenAPI v3 schema 的 spec.properties 内容
        extra_labels: 附加 labels（用于 update 场景）
    """

    name: str
    group: str
    scope: str
    plural: str
    singular: str
    kind: str
    short_names: List[str] = field(default_factory=list)
    version_name: str = "v1"
    properties: Dict[str, Any] = field(default_factory=dict)
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class PodNativeEntity(object):
    """
    K8s Pod native payload 实体（区别于 openapi 的 PodPayload，含完整 PaaS 标签）。

    Attributes:
        name: Pod 名称
        namespace: Namespace（用于 labels，非 URL）
        paas_app_code: PaaS 应用编码
        paas_env_code: PaaS 环境编码
        paas_owner: PaaS owner
        paas_plane_code: PaaS 平面
        paas_tenant_code: PaaS 租户
        paas_unit_code: PaaS 单元
        image: 容器镜像
        container_port: 容器端口
        extra_labels: 额外 labels
    """

    name: str
    namespace: str
    paas_app_code: str
    paas_env_code: str
    paas_owner: str
    paas_plane_code: str
    paas_tenant_code: str
    paas_unit_code: str
    image: str
    container_port: int = 8080
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class JobEntity(object):
    """
    K8s Job payload 实体。

    Attributes:
        name: Job 名称
        namespace: Namespace
        paas_app_code / paas_env_code / paas_owner / paas_plane_code / paas_tenant_code / paas_unit_code:
            PaaS 标签集
        image: 容器镜像
        completions: 完成数
        parallelism: 并行度
        backoff_limit: 失败重试上限
        command: 容器命令
        container_name: 容器名
        restart_policy: 重启策略
        extra_labels: 额外 labels
    """

    name: str
    namespace: str
    paas_app_code: str
    paas_env_code: str
    paas_owner: str
    paas_plane_code: str
    paas_tenant_code: str
    paas_unit_code: str
    image: str
    completions: int = 1
    parallelism: int = 1
    backoff_limit: int = 6
    command: List[str] = field(
        default_factory=lambda: ["/bin/sh", "-c", "date;echo 'Hello World'"]
    )
    container_name: str = "busyjob"
    restart_policy: str = "Never"
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class SecretEntity(object):
    """
    K8s Secret payload 实体。

    Attributes:
        name: Secret 名称
        paas_owner: PaaS owner 标签
        data: base64 编码的 secret 数据
        secret_type: Secret 类型（默认 Opaque）
        extra_labels: 额外 labels（用于 update 场景）
    """

    name: str
    paas_owner: str
    data: Dict[str, str] = field(default_factory=lambda: {"test": "Y3JlYXRl"})
    secret_type: str = "Opaque"
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class ConfigMapEntity(object):
    """
    K8s ConfigMap payload 实体。

    Attributes:
        name: ConfigMap 名称
        paas_owner: PaaS owner 标签
        data: ConfigMap key-value 数据
        extra_labels: 额外 labels（用于 update 场景）
    """

    name: str
    paas_owner: str
    data: Dict[str, str] = field(default_factory=lambda: {"test": "create"})
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class ServiceEntity(object):
    """
    K8s Service payload 实体。

    Attributes:
        name: Service 名称
        namespace: Namespace
        paas_app_code / paas_env_code / paas_owner / paas_plane_code / paas_tenant_code / paas_unit_code:
            PaaS 标签集
        paas_workload_name: 关联 workload 名（作为 selector）
        port: Service 端口
        target_port: Pod 端口
        protocol: 协议（TCP/UDP）
        port_name: 端口名
        service_type: Service 类型（ClusterIP/NodePort/LoadBalancer）
        extra_labels: 额外 labels（用于 update 场景）
    """

    name: str
    namespace: str
    paas_app_code: str
    paas_env_code: str
    paas_owner: str
    paas_plane_code: str
    paas_tenant_code: str
    paas_unit_code: str
    paas_workload_name: str
    port: int = 8080
    target_port: int = 8080
    protocol: str = "TCP"
    port_name: str = "nginx"
    service_type: str = "ClusterIP"
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class IngressNativeEntity(object):
    """
    K8s Ingress native payload 实体。

    Attributes:
        name: Ingress 名称
        paas_owner: PaaS owner 标签
        host: 主机名（None 表示不设置 host）
        path: URL 路径
        service_name: 后端 Service 名称
        service_port: 后端 Service 端口
        extra_labels: 额外 labels（用于 update 场景）
    """

    name: str
    paas_owner: str
    host: Optional[str] = None
    path: str = "/install"
    service_name: str = "qwe"
    service_port: int = 4000
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class PriorityClassNativeEntity(object):
    """
    K8s PriorityClass native payload 实体。

    Attributes:
        name: PriorityClass 名称
        value: 优先级值
        description: 描述
        extra_labels: 额外 labels（用于 update 场景）
    """

    name: str
    value: int = 100000000
    description: str = "this is a test"
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class HpaNativeEntity(object):
    """
    K8s HPA native payload 实体（区别于 openapi 的 HpaPayload，含 PaaS 标签）。

    Attributes:
        name: HPA 名称
        paas_owner: PaaS owner 标签
        workload_kind: 目标 workload Kind（Deployment/StatefulSet/DaemonSet）
        workload_name: 目标 workload 名称
        min_replicas: 最小副本数
        max_replicas: 最大副本数
        cpu_utilization: CPU 目标利用率
        extra_labels: 额外 labels（用于 update 场景）
    """

    name: str
    paas_owner: str
    workload_kind: str
    workload_name: str
    min_replicas: int
    max_replicas: int
    cpu_utilization: int = 50
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class NamespaceEntity(object):
    """
    K8s Namespace payload 实体。

    Attributes:
        name: Namespace 名称
        extra_labels: 额外 labels（用于 update 场景）
    """

    name: str
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class ResourceQuotaNativeEntity(object):
    """
    K8s ResourceQuota native payload 实体（区别于 extensions 的 ResourceQuotaEntity 用于 partitions-api）。

    Attributes:
        name: ResourceQuota 名称
        hard: hard 限制字典（如 {"pods": "110"}）
        extra_labels: 额外 labels（用于 update 场景）
    """

    name: str
    hard: Dict[str, str] = field(default_factory=lambda: {"pods": "110"})
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class LimitRangeNativeEntity(object):
    """
    K8s LimitRange native payload 实体（区别于 extensions 的 LimitRangeEntity）。

    Attributes:
        name: LimitRange 名称
        limits: LimitRange 限制项列表（默认包含 Container 默认限制）
        extra_labels: 额外 labels（用于 update 场景）
    """

    name: str
    limits: Optional[List[Dict[str, Any]]] = None
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class WorkloadNativeEntity(object):
    """
    K8s Workload native payload 实体（StatefulSet / Deployment / DaemonSet 共用）。

    Attributes:
        name: workload 名称
        namespace: Namespace
        kind: Workload 类型（StatefulSet / Deployment / DaemonSet）
        paas_app_code / paas_env_code / paas_owner / paas_plane_code / paas_tenant_code / paas_unit_code:
            PaaS 标签集
        image: 容器镜像
        replicas: 副本数（DaemonSet 忽略）
        container_port: 容器端口
        extra_labels: 额外 labels（用于 update 场景）
    """

    name: str
    namespace: str
    kind: str
    paas_app_code: str
    paas_env_code: str
    paas_owner: str
    paas_plane_code: str
    paas_tenant_code: str
    paas_unit_code: str
    image: str
    replicas: int = 1
    container_port: int = 8080
    extra_labels: Optional[Dict[str, str]] = None


__all__ = [
    "PaasLabels",
    "LabelSelector",
    "ContainerPort",
    "ContainerSpec",
    "K8sMetadata",
    "PodTemplate",
    "NamespacePayload",
    "ResourceQuotaPayload",
    "LimitRangeItem",
    "LimitRangePayload",
    "PriorityClassPayload",
    "IngressServiceBackend",
    "IngressHttpPath",
    "IngressPayload",
    "HpaScaleTargetRef",
    "HpaCpuUtilizationMetric",
    "HpaPayload",
    "PodPayload",
    "WorkloadPayload",
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
    # Native K8s Resources - PublicParams
    "ServiceAccountNativePublicParams",
    "ClusterRoleBindingNativePublicParams",
    "RoleBindingNativePublicParams",
    "PvcNativePublicParams",
    "CrdNativePublicParams",
    "PodNativePublicParams",
    "JobNativePublicParams",
    "NodeNativePublicParams",
    "SecretNativePublicParams",
    "ConfigMapNativePublicParams",
    "ServiceNativePublicParams",
    "IngressNativePublicParams",
    "PriorityClassNativePublicParams",
    "HpaNativePublicParams",
    "NamespaceNativePublicParams",
    "StatefulSetNativePublicParams",
    "DeploymentNativePublicParams",
    "DaemonSetNativePublicParams",
    # Native K8s Resources - Payload Entities
    "ServiceAccountEntity",
    "ClusterRoleBindingEntity",
    "RoleBindingEntity",
    "PvcEntity",
    "CrdEntity",
    "PodNativeEntity",
    "JobEntity",
    "SecretEntity",
    "ConfigMapEntity",
    "ServiceEntity",
    "IngressNativeEntity",
    "PriorityClassNativeEntity",
    "HpaNativeEntity",
    "NamespaceEntity",
    "ResourceQuotaNativeEntity",
    "LimitRangeNativeEntity",
    "WorkloadNativeEntity",
]
