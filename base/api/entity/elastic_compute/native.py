"""
Elastic Compute Native / K8s 原生资源实体模型。

承载：
- 基础复用组件：``PaasLabels``（12 字段 PaaS 标签集）、``K8sMetadata``、
  ``ContainerPort``、``ContainerSpec``、``PodTemplate``、``LabelSelector``。
- 通用 K8s Payload（对应 openapi / native 通用路径）：
  ``NamespacePayload`` / ``ResourceQuotaPayload`` / ``LimitRangePayload`` /
  ``PriorityClassPayload`` / ``IngressPayload`` / ``HpaPayload`` /
  ``PodPayload`` / ``WorkloadPayload`` 等，均提供 ``to_dict()`` 输出符合 K8s API
  契约的 JSON。
- ``tests/api/elastic_compute/native/`` 下测试文件对应的 ``*NativePublicParams``
  与 ``*Entity``（用于 create/update 请求体构造）。

命名约定：
- Python 侧统一 ``snake_case``；K8s 契约字段 ``camelCase``/``kebab-case`` 由本模块内
  ``to_dict()`` 或 service 层负责映射。
- 与 :mod:`base.api.entity.elastic_compute.extension`（磐基 extensions 专有）
  物理隔离；两处存在部分同名概念（如 ``ResourceQuotaEntity`` / ``LimitRangeEntity``）
  但语义不同，禁止跨模块 re-import。
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
    """K8s Namespace 资源 payload。"""

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
    """K8s ResourceQuota 资源 payload。"""

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
    """K8s LimitRange 资源 payload。"""

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
    """K8s PriorityClass（cluster-scoped）payload。"""

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
    """K8s Ingress 资源 payload。"""

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
    """K8s HorizontalPodAutoscaler 资源 payload。"""

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


# ==================== Pod / Workload ====================

@dataclass
class PodPayload(object):
    """K8s Pod 资源 payload。"""

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
