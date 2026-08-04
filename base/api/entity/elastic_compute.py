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
]
