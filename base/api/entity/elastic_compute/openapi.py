"""
弹性计算 OpenAPI 测试的公共参数与实体模型（Entity / DTO 层）。

与 :mod:`base.api.entity.elastic_compute`（Native / Extensions 通用组件）**物理隔离**，
本模块专门承载 ``tests/api/elastic_compute/openapi/`` 下测试文件所需的：

- ``XxxPublicParams``：每个测试类 ``public_params`` fixture 的强类型返回体。
- ``K8sXxxEntity`` / ``XxxEntity``：openapi 侧的请求实体。openapi 系接口 payload 采用
  **K8s 原生 spec 风格**（``apiVersion / metadata / spec / data / ...``），故命名统一带
  ``K8s`` 前缀以与 extensions 侧的磐基自定义扁平结构区分。

字段命名约定：
- Python 侧：``snake_case``
- payload 序列化到 API 时的 ``camelCase``/``kebab-case`` 转换点位于 service 层方法体内联的
  payload 构造中；本模块的 dataclass 不做任何字段名映射。

新增 Entity 请：
1. 严格遵循 dataclass 语法（必填字段在前、可选字段带默认值在后、可变默认值使用
   ``field(default_factory=...)``）。
2. 在类顶部写一行 docstring 说明对应哪条 API 路径 / JMX sampler。
3. 追加到本模块末尾的 ``__all__``。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# ==================== ConfigMap（ConfigMap.jmx）====================


@dataclass
class ConfigMapPublicParams(object):
    """
    ConfigMap 测试公共参数。对应 [test_ec_configmap.py](tests/api/elastic_compute/openapi/test_ec_configmap.py)。

    Attributes:
        cell_code: 集群 code（对应 URL 中的 cellCode）
        sys_code: 系统 code（对应 URL 中的 sysCode）
        cm_name: 目标 ConfigMap 名称
    """

    cell_code: str
    sys_code: str
    cm_name: str = "auto-test-probe-cm-test-0001"


@dataclass
class K8sConfigMapEntity(object):
    """
    ConfigMap 的 K8s 原生 payload 实体，用于 create / put update。

    对应 JMX ``ConfigMap.jmx`` 中"创建cm请求" / "更新指定 configmap" sampler 的 body。
    序列化后的 payload 形如::

        {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": <name>},
            "data": {...}
        }
    """

    name: str
    data: Dict[str, str] = field(default_factory=lambda: {"test": "test"})
    api_version: str = "v1"
    kind: str = "ConfigMap"


@dataclass
class K8sConfigMapPatchEntity(object):
    """
    ConfigMap 的 K8s strategic merge patch payload 实体。

    对应 JMX ``ConfigMap.jmx`` 中"增量更新指定 configmap" sampler 的 body。
    序列化后的 payload 形如::

        {
            "metadata": {"labels": {...}},
            "data": {...}
        }
    """

    labels: Dict[str, str] = field(default_factory=lambda: {"test": "test2"})
    data: Dict[str, str] = field(default_factory=lambda: {"test": "test2"})


# ==================== ServiceAccount（ServiceAccountV2.jmx）====================


@dataclass
class ServiceAccountPublicParams(object):
    """
    ServiceAccount 测试公共参数。对应 [test_ec_service_account.py](tests/api/elastic_compute/openapi/test_ec_service_account.py)。

    ServiceAccountV2 接口只做查询，无 payload。
    """

    cell_code: str
    sys_code: str


# ==================== ReplicaSet（ReplicaSetV2.jmx）====================


@dataclass
class ReplicaSetPublicParams(object):
    """
    ReplicaSet 测试公共参数。对应 [test_ec_replicaset.py](tests/api/elastic_compute/openapi/test_ec_replicaset.py)。

    ReplicaSetV2 接口只做查询，无 payload。
    """

    cell_code: str
    sys_code: str


# ==================== RBAC（RBAC_V2.jmx）====================


@dataclass
class RbacPublicParams(object):
    """
    RBAC 测试公共参数。对应 [test_ec_rbac.py](tests/api/elastic_compute/openapi/test_ec_rbac.py)。

    RBAC_V2 接口只做查询，无 payload。
    """

    cell_code: str
    sys_code: str


# ==================== Port / NodePort（port-nodeport.jmx）====================


@dataclass
class PortNodePortPublicParams(object):
    """
    Port/NodePort 测试公共参数。对应 [test_ec_port_nodeport.py](tests/api/elastic_compute/openapi/test_ec_port_nodeport.py)。

    Attributes:
        cell_code: 集群 code
        node_port: 单个 NodePort 端口（用于可用性查询）
        tenant_code: 目标租户 code
        ports: 待分配端口范围（如 "30011-30030"）
    """

    cell_code: str
    node_port: str = "10001"
    tenant_code: str = "monitor-group"
    ports: str = "30011-30030"


@dataclass
class PortAllocationEntity(object):
    """
    NodePort 端口范围分配请求实体。对应 JMX ``port-nodeport.jmx``
    "租户 nodeport 端口范围分配" sampler 的 body::

        {"kind": "ALLOCATE", "tenantCode": <t>, "ports": [<range>]}
    """

    tenant_code: str
    ports: str
    kind: str = "ALLOCATE"


# ==================== ResourceQuota（resourcequota.jmx）====================


@dataclass
class ResourceQuotaPublicParams(object):
    """
    ResourceQuota 测试公共参数。对应 [test_ec_resourcequota.py](tests/api/elastic_compute/openapi/test_ec_resourcequota.py)。
    """

    cell_code: str
    sys_code: str


@dataclass
class K8sResourceQuotaEntity(object):
    """
    ResourceQuota PUT 全量更新实体。对应 JMX ``resourcequota.jmx`` 中
    PUT 更新 sampler 的 body::

        {"spec": {"hard": {"limits.cpu": "100", "limits.memory": "200Gi"}}}
    """

    hard: Dict[str, str] = field(
        default_factory=lambda: {"limits.cpu": "100", "limits.memory": "200Gi"}
    )


@dataclass
class K8sResourceQuotaPatchEntity(object):
    """
    ResourceQuota PATCH 增量更新实体。对应 JMX ``resourcequota.jmx`` 中
    PATCH 更新 sampler 的 body::

        {"spec": {"hard": {"limits.cpu": "50"}}}
    """

    hard: Dict[str, str] = field(default_factory=lambda: {"limits.cpu": "50"})


# ==================== ScaledObject（ScaledObject.jmx）====================


@dataclass
class ScaledObjectPublicParams(object):
    """
    ScaledObject 测试公共参数。对应 [test_ec_scaled_object.py](tests/api/elastic_compute/openapi/test_ec_scaled_object.py)。
    """

    cell_code: str
    sys_code: str
    so_name: str = "test-scaled-object-001"
    workload_kind: str = "Deployment"
    workload_name: str = "auto-test-deploy-probe-ns-test-0002"


@dataclass
class ScaledObjectEntity(object):
    """
    ScaledObject 创建实体。对应 JMX ``ScaledObject.jmx`` 中"创建 ScaledObject" sampler。
    """

    name: str
    workload_kind: str
    workload_name: str
    polling_interval: int = 30
    cooldown_period: int = 300
    min_replica_count: int = 1
    max_replica_count: int = 5
    restore_to_original_replica_count: bool = False
    timezone: str = "Asia/Shanghai"
    start: str = "30 * * * *"
    end: str = "45 * * * *"
    desired_replicas: int = 3


@dataclass
class ScaledObjectPatchEntity(object):
    """
    ScaledObject 更新实体。对应 JMX ``ScaledObject.jmx`` 中"更新 ScaledObject" sampler
    的 body::

        {"start": "35 * * * *", "end": "45 * * * *"}
    """

    start: str = "35 * * * *"
    end: str = "45 * * * *"


# ==================== 容灾组件资源（recovery-resource.jmx）====================


@dataclass
class RecoveryResourcePublicParams(object):
    """
    容灾组件资源测试公共参数。对应
    [test_ec_recovery_resource.py](tests/api/elastic_compute/openapi/test_ec_recovery_resource.py)。
    """

    cell_code: str
    sys_code: str
    resource_name: str = "test-resource-deploy-001"
    app_name: str = "app-nginx-test"
    kind: str = "Deployment"
    image: str = "hpe_containers/nginx:latest"
    tenant_code: str = "monitor-group"
    app_code: str = "probe-deploy"
    plane_code: str = "PLANE"
    unit_code: str = "test"
    env_code: str = "PROD"
    user: str = "PROD"


@dataclass
class RecoveryResourceEntity(object):
    """
    容灾组件单条资源实体。对应 JMX ``recovery-resource.jmx`` 中"创建资源" /
    "Apply 资源" sampler body 数组元素。字段与 K8s payload 的 camelCase 对齐：
    ``name / appName / kind / image / tenantCode / appCode / planeCode / unitCode /
    envCode / username``。
    """

    name: str
    app_name: str
    kind: str
    image: str
    tenant_code: str
    app_code: str
    plane_code: str
    unit_code: str
    env_code: str
    username: str


# ==================== PVC / PV / StorageClass（pvc-pv.jmx）====================


@dataclass
class PvcPvPublicParams(object):
    """
    PVC / PV / StorageClass 测试公共参数。对应
    [test_ec_pvc_pv.py](tests/api/elastic_compute/openapi/test_ec_pvc_pv.py)。
    """

    cell_code: str
    sys_code: str
    pvc_name: str = "test-hpa-001"
    pv_name: str = "test-pv-001"
    storage_class_name: str = "test-sc-001"


@dataclass
class K8sPvcEntity(object):
    """
    K8s PersistentVolumeClaim 创建实体。对应 JMX ``pvc-pv.jmx`` 中"创建 pvc 请求"
    sampler 的 body::

        {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": <name>},
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": "1Gi"}},
                "storageClassName": <sc>
            }
        }
    """

    name: str
    storage_class_name: str
    storage: str = "1Gi"
    access_mode: str = "ReadWriteOnce"
    api_version: str = "v1"
    kind: str = "PersistentVolumeClaim"


# ==================== PriorityClass（PriorityClassesV2.jmx）====================


@dataclass
class PriorityClassPublicParams(object):
    """
    PriorityClass 测试公共参数。对应
    [test_ec_priorityclasses.py](tests/api/elastic_compute/openapi/test_ec_priorityclasses.py)。
    """

    cell_code: str
    pc_name: str = "pc-test"


@dataclass
class K8sPriorityClassEntity(object):
    """
    K8s PriorityClass 创建 / PUT 更新实体。对应 JMX ``PriorityClassesV2.jmx``
    中"创建/更新 PriorityClass" sampler 的 body::

        {
            "apiVersion": "scheduling.k8s.io/v1",
            "description": "this is a test",
            "kind": "PriorityClass",
            "metadata": {"name": <name>},
            "value": 100000000
        }
    """

    name: str
    value: int = 100000000
    description: str = "this is a test"
    api_version: str = "scheduling.k8s.io/v1"
    kind: str = "PriorityClass"


@dataclass
class K8sPriorityClassPatchEntity(object):
    """
    K8s PriorityClass strategic merge patch 实体。对应 JMX
    ``PriorityClassesV2.jmx`` 中 PATCH sampler 的 body。
    """

    description: str = "this is a patched description"
    global_default: bool = True
    labels: Dict[str, str] = field(
        default_factory=lambda: {"environment": "production", "app": "critical-service"}
    )
    annotations: Dict[str, str] = field(
        default_factory=lambda: {"update-reason": "configuration change", "updated-by": "system-admin"}
    )


# ==================== Secret（SecretV2.jmx）====================


@dataclass
class SecretPublicParams(object):
    """
    Secret 测试公共参数。对应 [test_ec_secret.py](tests/api/elastic_compute/openapi/test_ec_secret.py)。
    """

    cell_code: str
    sys_code: str
    secret_name: str = "auto-test-probe-secret-test-0001"


@dataclass
class K8sSecretEntity(object):
    """
    K8s Secret 创建 / PUT 更新实体。对应 JMX ``SecretV2.jmx`` 中"创建/更新 secret"
    sampler 的 body。
    """

    name: str
    data: Dict[str, str] = field(
        default_factory=lambda: {"username": "YWRtaW4=", "password": "MWYyZDFlMmU2N2Rm"}
    )
    secret_type: str = "Opaque"
    api_version: str = "v1"
    kind: str = "Secret"


@dataclass
class K8sSecretPatchEntity(object):
    """
    K8s Secret strategic merge patch 实体。对应 JMX ``SecretV2.jmx`` 中 PATCH sampler 的 body。
    """

    labels: Dict[str, str] = field(default_factory=lambda: {"test": "patch-test"})
    data: Dict[str, str] = field(default_factory=lambda: {"extra": "cGF0Y2hlZA=="})


# ==================== Service（ServiceV2.jmx）====================


@dataclass
class ServiceV2PublicParams(object):
    """
    Service (V2) 测试公共参数。对应
    [test_ec_service_v2.py](tests/api/elastic_compute/openapi/test_ec_service_v2.py)。
    """

    cell_code: str
    sys_code: str
    svc_name: str = "auto-test-probe-svc-test-0001"


@dataclass
class K8sServicePortSpec(object):
    """K8s Service.spec.ports[] 单个端口条目。"""

    port: int
    target_port: int
    name: str = "http"
    protocol: str = "TCP"


@dataclass
class K8sServiceEntity(object):
    """
    K8s Service 创建 / PUT 更新实体。对应 JMX ``ServiceV2.jmx`` 中"创建/更新 service"
    sampler 的 body。
    """

    name: str
    ports: list = field(
        default_factory=lambda: [K8sServicePortSpec(port=80, target_port=8080, name="http")]
    )
    selector: Dict[str, str] = field(default_factory=lambda: {"app": "auto-test-probe"})
    service_type: str = "ClusterIP"
    api_version: str = "v1"
    kind: str = "Service"


@dataclass
class K8sServicePatchEntity(object):
    """
    K8s Service strategic merge patch 实体。对应 JMX ``ServiceV2.jmx`` 中 PATCH sampler 的 body。
    """

    labels: Dict[str, str] = field(default_factory=lambda: {"test": "patch-test"})


# ==================== Quota Manager (Admin)（quota-manager-admin.jmx）====================


@dataclass
class QuotaManagerAdminPublicParams(object):
    """
    配额管理（管理员视角）测试公共参数。对应
    [test_ec_quota_manager_admin.py](tests/api/elastic_compute/openapi/test_ec_quota_manager_admin.py)。
    """

    cell_code: str
    sys_code: str
    tenant_code: str
    username: str


@dataclass
class TenantQuotaAllocationEntity(object):
    """
    租户资源配额分配 / 调整实体。对应 JMX ``quota-manager-admin.jmx`` 中
    "租户资源配额分配" 与 "租户资源配额调整（扩缩容）" 两个 sampler 的 body。

    实际请求体可为空对象 ``{}`` 或包含具体的配额字段（如 ``cpu / memory``），
    这里将两种能力字段声明为 ``Optional``，未提供时不会写入 payload。
    """

    cpu: Optional[str] = None
    memory: Optional[str] = None
    extras: Optional[Dict[str, Any]] = None


# ==================== HPA（HPA.jmx）====================


@dataclass
class HpaPublicParams(object):
    """
    HPA 测试公共参数。对应 [test_ec_hpa.py](tests/api/elastic_compute/openapi/test_ec_hpa.py)。

    注：``api_version`` 是 HPA autoscaling group 的版本部分（如 ``v1`` / ``v2``），
    最终 K8s payload 的 ``apiVersion`` 会拼成 ``autoscaling/{api_version}``。
    """

    cell_code: str
    sys_code: str
    api_version: str = "v1"
    hpa_name: str = "auto-test-hpa-test-0001"


@dataclass
class K8sHpaEntity(object):
    """
    K8s HorizontalPodAutoscaler 创建 / PUT / PATCH 实体。对应 JMX ``HPA.jmx``
    中"创建/更新 hpa"sampler 的 body。默认绑定到 StatefulSet ``web``。
    """

    name: str
    api_version: str
    max_replicas: int
    min_replicas: int = 1
    target_cpu_utilization_percentage: int = 50
    scale_target_kind: str = "StatefulSet"
    scale_target_name: str = "web"
    scale_target_api_version: str = "apps/v1"
    kind: str = "HorizontalPodAutoscaler"


# ==================== LimitRange（LimitRange.jmx）====================


@dataclass
class LimitrangeStandardParams(object):
    """
    LimitRange 测试的"标准集群"公共参数。对应 JMX 顶层 ``testHostCluster=0`` 分支。
    使用 ``cellCode / sysCode``。``test_host_cluster`` 字段保存的是原始 yaml
    中的 ``hostCellCode`` 值，用于分支判断。
    """

    cell_code: str
    sys_code: str
    test_host_cluster: str


@dataclass
class LimitrangeHostParams(object):
    """
    LimitRange 测试的"托管集群"公共参数。对应 JMX 顶层 ``testHostCluster=1`` 分支。
    使用 ``hostCellCode / hostSysCode``。
    """

    cell_code: str
    sys_code: str
    test_host_cluster: str


@dataclass
class K8sLimitRangeEntity(object):
    """
    K8s LimitRange 创建 / PUT 实体。对应 JMX ``LimitRange.jmx`` 中"创建/更新
    LimitRange"sampler 的 body。``name`` 通常取当前命名空间的 sysCode。
    """

    name: str
    default_cpu: str = "1m"
    default_memory: str = "1"
    default_request_cpu: str = "1m"
    default_request_memory: str = "1"
    limit_type: str = "Container"
    api_version: str = "v1"
    kind: str = "LimitRange"


# ==================== CustomResource - Namespace 级别（CustomResource-ns.jmx）====================


@dataclass
class CrNsPublicParams(object):
    """
    Namespace 级 CustomResource 测试公共参数。对应 [test_ec_cr_ns.py](tests/api/elastic_compute/openapi/test_ec_cr_ns.py)。
    """

    cell_code: str
    sys_code: str
    cr_group: str = "test.example.com"
    cr_version: str = "v1"
    cr_kind: str = "Apple"
    cr_name: str = "auto-test-probe-cr-ns-test-0001"


@dataclass
class NsCustomResourceEntity(object):
    """
    Namespace 级 CustomResource 创建 / PUT 实体。对应 JMX ``CustomResource-ns.jmx``
    中"创建/更新指定 CR"sampler 的 body。默认使用 ``Apple`` 演示 CRD 的
    ``spec.color`` 字段。
    """

    name: str
    group: str
    version: str
    kind: str
    color: str = "red"


@dataclass
class NsCustomResourcePatchEntity(object):
    """
    Namespace 级 CustomResource PATCH 实体。对应 JMX ``CustomResource-ns.jmx``
    中"增量更新指定 CR"sampler 的 body。仅覆盖 ``metadata.labels`` 与
    ``spec.color`` 两个字段（增量补丁）。
    """

    color: str = "blue"
    labels: Optional[Dict[str, str]] = None


# ==================== CustomResource - Cluster 级别（cr-cluster.jmx）====================


@dataclass
class CrClusterPublicParams(object):
    """
    Cluster 级 CustomResource 测试公共参数。对应 [test_ec_cr_cluster.py](tests/api/elastic_compute/openapi/test_ec_cr_cluster.py)。
    """

    cell_code: str
    cr_group: str = "test.example.com"
    cr_version: str = "v1"
    cr_kind: str = "Apple"
    cr_name: str = "test-apple"


@dataclass
class ClusterCustomResourceEntity(object):
    """
    Cluster 级 CustomResource 创建 / PUT 实体。对应 JMX ``cr-cluster.jmx``
    中"创建/更新指定 CR"sampler 的 body。CRD ``Apple`` 通过 ``spec.message``
    与 ``spec.replicas`` 两个字段承载业务数据；``metadata.labels`` 中会写入
    ``name / kind``（默认）以及可选的自定义标签。
    """

    name: str
    group: str
    version: str
    kind: str
    message: str = "I have an apple!"
    replicas: int = 1
    extra_labels: Optional[Dict[str, str]] = None


@dataclass
class ClusterCustomResourcePatchEntity(object):
    """
    Cluster 级 CustomResource PATCH 实体。对应 JMX ``cr-cluster.jmx`` 中
    "增量更新指定 CR"sampler 的 body。仅覆盖 ``metadata.labels`` 与
    ``spec.replicas`` 两个字段（增量补丁）。
    """

    replicas: int = 3
    labels: Optional[Dict[str, str]] = None


# ==================== Pod（pod.jmx）====================


@dataclass
class PodPublicParams(object):
    """
    Pod 测试公共参数。对应 [test_ec_pod.py](tests/api/elastic_compute/openapi/test_ec_pod.py)。
    """

    cell_code: str
    sys_code: str
    pod_name: str
    pod_image: str
    container_name: str = "container0"


@dataclass
class K8sPodEntity(object):
    """
    K8s Pod 创建实体。对应 JMX ``pod.jmx`` 中"创建 Pod"sampler 的 body。
    默认为单容器 + 单端口（``containerPort=8080 / TCP``）。
    """

    name: str
    image: str
    container_name: str = "container0"
    container_port: int = 8080
    port_name: str = "port0"
    port_protocol: str = "TCP"
    kind: str = "Pod"
    api_version: str = "v1"


@dataclass
class K8sPodPatchEntity(object):
    """
    K8s Pod PATCH 实体。对应 JMX ``pod.jmx`` 中"增量更新指定 Pod"sampler 的 body。
    仅覆盖 ``metadata.labels`` 字段（增量补丁）。
    """

    labels: Dict[str, str]


@dataclass
class K8sPodRawEntity(object):
    """
    Pod PUT 全量更新实体。JMX 中该 sampler 的 body 是从 GET Pod 返回的
    完整 K8s Pod 对象（含 ``resourceVersion / uid / status`` 等运行时字段），
    并对 ``metadata.labels`` 做局部修改后回传。用透传的 dict 承载。
    """

    body: Dict[str, Any]


# ==================== Helm Chart（helm-chart.jmx）====================


@dataclass
class HelmOpenapiPublicParams(object):
    """
    Helm Chart 测试公共参数。对应 [test_ec_helm_chart.py](tests/api/elastic_compute/openapi/test_ec_helm_chart.py)。
    """

    cell_code: str
    sys_code: str
    release_name: str
    chart_name: str
    chart_version: str
    chart_file_path: Optional[str]
    image: str
    image_tag: str
    interval_seconds: int = 3


@dataclass
class HelmInstallEntity(object):
    """
    Helm Install 请求体实体。对应 JMX ``helm-chart.jmx`` 中"Helm Install"
    sampler 的 body。注意：``values`` 字段最终以 **JSON string** 形式提交
    （对齐 JMX 原生行为），因此内联 payload 构造时需 ``json.dumps``。
    """

    release_name: str
    chart_name: str
    chart_version: str
    image_repository: str
    image_tag: str
    replica_count: int = 1


@dataclass
class HelmUpgradeEntity(object):
    """
    Helm Upgrade 请求体实体。对应 JMX ``helm-chart.jmx`` 中"Helm Upgrade"
    sampler 的 body。``values`` 序列化规则同 :class:`HelmInstallEntity`。
    """

    chart_name: str
    chart_version: str
    image_repository: str
    image_tag: str
    replica_count: int = 2


# ==================== Workload Query（workload-query.jmx，全 GET）====================


@dataclass
class WorkloadQueryPublicParams(object):
    """
    Workload Query 测试公共参数。对应 [test_ec_workload_query.py](tests/api/elastic_compute/openapi/test_ec_workload_query.py)。
    该模块所有 sampler 均为 GET 类查询，无需 payload Entity。
    """

    cell_code: str
    sys_code: str
    kind: str
    app_code: str
    workload_name: str


# ==================== Harbor（harbor.jmx，4 子域）====================


@dataclass
class HarborPublicParams(object):
    """
    Harbor 测试公共参数。对应 [test_ec_harbor.py](tests/api/elastic_compute/openapi/test_ec_harbor.py)。
    覆盖 harbor 项目 / 项目成员 / 仓库 / 复制策略四个子域的通用输入。
    """

    harbor_id: int
    project_name: str
    project_member_name: str
    replication_policy_name: str
    copy_harbor_access_id: str
    copy_harbor_access_secret: str
    rep_name: str


@dataclass
class HarborProjectEntity(object):
    """
    Harbor 项目创建实体。对应 JMX ``harbor.jmx`` 中"创建 harbor 项目"sampler 的 body。
    默认建为公共项目（``metadata.public='true'``）。
    """

    project_name: str
    public: bool = True


@dataclass
class HarborMemberEntity(object):
    """
    Harbor 项目成员创建实体。对应 JMX ``harbor.jmx`` 中"创建 harbor 项目成员关系"
    sampler 的 body。``role_id`` 默认为 1（项目管理员）。
    """

    username: str
    role_id: int = 1


@dataclass
class HarborReplicationPolicyEntity(object):
    """
    Harbor 复制策略创建 / 更新实体。对应 JMX ``harbor.jmx`` 中"添加/更新 harbor 复制策略"
    sampler 的 body。默认使用手动触发、``speed=-1``（不限速）、启用+覆盖模式。
    """

    name: str
    project_name: str
    target_id: int
    description: Optional[str] = None
    trigger_type: str = "manual"
    trigger_cron: str = ""
    deletion: bool = False
    override: bool = True
    enabled: bool = True
    speed: str = "-1"


# ==================== Helm Chart（helm-chart.jmx）====================


@dataclass
class HelmOpenapiPublicParams(object):
    """
    Helm Chart 测试公共参数。对应 [test_ec_helm_chart.py](tests/api/elastic_compute/openapi/test_ec_helm_chart.py)。
    """

    cell_code: str
    sys_code: str
    release_name: str
    chart_name: str
    chart_version: str
    chart_file_path: Optional[str]
    image: str
    image_tag: str
    interval_seconds: int = 3


@dataclass
class HelmInstallEntity(object):
    """
    Helm Install 请求实体。对应 JMX ``helm-chart.jmx`` "Helm Install"sampler
    的 body。``values`` 字段以 JSON 字符串形式提交（保留 JMX 原生格式）。
    """

    release_name: str
    chart_name: str
    chart_version: str
    image_repo: str
    image_tag: str
    replica_count: int = 1


@dataclass
class HelmUpgradeEntity(object):
    """
    Helm Upgrade 请求实体。对应 JMX ``helm-chart.jmx`` "Helm Upgrade"sampler
    的 body。相比 :class:`HelmInstallEntity` 无 ``release_name``（release 名走
    路径参数），且 ``replica_count`` 默认改为 ``2``。
    """

    chart_name: str
    chart_version: str
    image_repo: str
    image_tag: str
    replica_count: int = 2


# ==================== Small / no-op params (batch 4) ====================


@dataclass
class HarborInitPublicParams(object):
    """
    Harbor-Init 测试公共参数。对应
    [test_ec_harbor_init.py](tests/api/elastic_compute/openapi/test_ec_harbor_init.py)。

    Attributes:
        harbor_id: 目标 Harbor ID
    """

    harbor_id: str


@dataclass
class EndpointsV2PublicParams(object):
    """
    Endpoints 查询测试公共参数。对应
    [test_ec_endpoints_v2.py](tests/api/elastic_compute/openapi/test_ec_endpoints_v2.py)。

    Attributes:
        cell_code: 集群 code
        sys_code: 系统 code
    """

    cell_code: str
    sys_code: str


@dataclass
class ImagePullSecretPublicParams(object):
    """
    ImagePullSecret 测试公共参数。对应
    [test_ec_image_pull_secret.py](tests/api/elastic_compute/openapi/test_ec_image_pull_secret.py)。

    Attributes:
        cell_code: 集群 code
        sys_code: 系统 code
    """

    cell_code: str
    sys_code: str


@dataclass
class ImagePublicParams(object):
    """
    Image 查询测试公共参数。对应
    [test_ec_image.py](tests/api/elastic_compute/openapi/test_ec_image.py)。

    Attributes:
        cluster_id: 集群 ID
        namespace: 命名空间
        project_name: Harbor 项目名
        image_name: 镜像名
        image_version: 镜像版本 tag
    """

    cluster_id: str
    namespace: str
    project_name: str
    image_name: str
    image_version: str


@dataclass
class NodePublicParams(object):
    """
    Node 测试公共参数。对应
    [test_ec_node.py](tests/api/elastic_compute/openapi/test_ec_node.py)。

    Attributes:
        cell_code: 集群 code
        node_ip: Node 名称（IP）
    """

    cell_code: str
    node_ip: str


@dataclass
class QuotaManagerTenantPublicParams(object):
    """
    Quota-Manager 租户视角测试公共参数。对应
    [test_ec_quota_manager_tenant.py](tests/api/elastic_compute/openapi/test_ec_quota_manager_tenant.py)。

    Attributes:
        cell_code: 集群 code
        sys_code: 系统 code
        tenant_code: 租户 code
        username: 用户名
    """

    cell_code: str
    sys_code: str
    tenant_code: str
    username: str


@dataclass
class ClusterPublicParams(object):
    """
    Cluster 查询测试公共参数（无入参，仅作 SOP 契约占位）。对应
    [test_ec_cluster.py](tests/api/elastic_compute/openapi/test_ec_cluster.py)。
    """


@dataclass
class NamespacePublicParams(object):
    """
    Namespace 查询测试公共参数（无入参，仅作 SOP 契约占位）。对应
    [test_ec_namespace.py](tests/api/elastic_compute/openapi/test_ec_namespace.py)。
    """


@dataclass
class OidcHarborInitPublicParams(object):
    """
    OIDC/Harbor-Init 测试公共参数（无入参，仅作 SOP 契约占位）。对应
    [test_ec_oidc_harborinit.py](tests/api/elastic_compute/openapi/test_ec_oidc_harborinit.py)。
    """


@dataclass
class ResourceCollectionPublicParams(object):
    """
    资源采集测试公共参数（无入参，仅作 SOP 契约占位）。对应
    [test_ec_resource_collection.py](tests/api/elastic_compute/openapi/test_ec_resource_collection.py)。
    """


# ==================== Workload (openapi/workload.jmx) ====================

@dataclass
class WorkloadPublicParams(object):
    """
    Workload 生命周期测试公共参数。对应
    [test_ec_workload.py](tests/api/elastic_compute/openapi/test_ec_workload.py)。

    Attributes:
        cell_code: 集群 code
        sys_code: 系统 code
        app_code: 应用 code
        kind: workload kind（Deployment / StatefulSet 等）
        name: workload 名称
        image: 容器镜像
        replicas: 副本数
        file_path_in_pod: Pod 内文件路径（copy 用）
    """

    cell_code: str
    sys_code: str
    app_code: str
    kind: str
    name: str
    image: str
    replicas: int
    file_path_in_pod: str


@dataclass
class WorkloadCreateEntity(object):
    """
    创建 Deployment Workload 的实体。对应 JMX: 创建Deployment 请求。

    仅暴露最常用字段；其余固定值（apiVersion/containerName/containerPort/protocol）
    由 service 层内联填入。

    Attributes:
        kind: workload kind
        name: workload 名称
        image: 容器镜像
        replicas: 副本数
    """

    kind: str
    name: str
    image: str
    replicas: int


@dataclass
class WorkloadUpdateEntity(object):
    """
    PUT 全量更新 Deployment Workload 的实体。对应 JMX: 更新指定Deployment。

    在 service 层 payload 中会自动应用 JMX 原始规则：
    ``replicas += 1``、``containerPort = 8090``、新增 ``imagePullPolicy=Always``、
    labels 追加 ``test=update``。

    Attributes:
        kind: workload kind
        name: workload 名称
        image: 容器镜像
        replicas: 原 replicas（service 内部会 +1）
    """

    kind: str
    name: str
    image: str
    replicas: int


@dataclass
class WorkloadPatchEntity(object):
    """
    PATCH 增量更新 Workload 的实体。对应 JMX: 增量更新指定Deployment。

    Attributes:
        replicas: 目标副本数
    """

    replicas: int


@dataclass
class WorkloadBatchTargetEntity(object):
    """
    批量查询/滚动/生命周期操作的单个目标（applications 数组条目）。
    对应 JMX: 批量查询Deployment状态列表 / 批量滚动 / 批量停止启动重启。

    Attributes:
        name: workload 名称（会序列化为 ``appName``）
        kind: workload kind
    """

    name: str
    kind: str


@dataclass
class WorkloadBatchPatchTargetEntity(object):
    """
    批量增量更新 Workload 的单个目标。对应 JMX: 批量增量更新Deployment。

    payload 中固定使用 labels ``test=batch-patch-update``、``containerPort=8020``、
    ``containerName=container0``，由 service 层内联填入。

    Attributes:
        name: workload 名称
        kind: workload kind
    """

    name: str
    kind: str


@dataclass
class WorkloadExecEntity(object):
    """
    Pod exec 请求实体。对应 JMX: 应用服务Pod exec请求。

    Attributes:
        pod_name: Pod 名称
        container_name: 容器名（默认 container0，与 JMX 一致）
        command: 命令（默认 ``ls``）
        timeout: 超时秒数
    """

    pod_name: str
    container_name: str = "container0"
    command: str = "ls"
    timeout: int = 10


@dataclass
class WorkloadPodDeleteEntity(object):
    """
    批量删除应用服务 Pod 实例（作用于单个应用）。对应 JMX: 批量删除应用服务Pod实例。

    Attributes:
        pod_name: Pod 名称
        app_code: 应用 code
    """

    pod_name: str
    app_code: str


@dataclass
class WorkloadAppPodDeleteEntity(object):
    """
    批量删除 Pod 实例（跨应用，全局接口）。对应 JMX: 批量删除Pod实例。

    Attributes:
        pod_name: Pod 名称
        app_code: 应用 code
        cell_code: 集群 code
        sys_code: 系统 code
    """

    pod_name: str
    app_code: str
    cell_code: str
    sys_code: str


__all__ = [
    # ConfigMap
    "ConfigMapPublicParams",
    "K8sConfigMapEntity",
    "K8sConfigMapPatchEntity",
    # ServiceAccount
    "ServiceAccountPublicParams",
    # ReplicaSet
    "ReplicaSetPublicParams",
    # RBAC
    "RbacPublicParams",
    # Port / NodePort
    "PortNodePortPublicParams",
    "PortAllocationEntity",
    # ResourceQuota
    "ResourceQuotaPublicParams",
    "K8sResourceQuotaEntity",
    "K8sResourceQuotaPatchEntity",
    # ScaledObject
    "ScaledObjectPublicParams",
    "ScaledObjectEntity",
    "ScaledObjectPatchEntity",
    # Recovery Resource
    "RecoveryResourcePublicParams",
    "RecoveryResourceEntity",
    # PVC / PV / StorageClass
    "PvcPvPublicParams",
    "K8sPvcEntity",
    # PriorityClass
    "PriorityClassPublicParams",
    "K8sPriorityClassEntity",
    "K8sPriorityClassPatchEntity",
    # Secret
    "SecretPublicParams",
    "K8sSecretEntity",
    "K8sSecretPatchEntity",
    # Service
    "ServiceV2PublicParams",
    "K8sServicePortSpec",
    "K8sServiceEntity",
    "K8sServicePatchEntity",
    # Quota Manager (Admin)
    "QuotaManagerAdminPublicParams",
    "TenantQuotaAllocationEntity",
    # HPA
    "HpaPublicParams",
    "K8sHpaEntity",
    # LimitRange
    "LimitrangeStandardParams",
    "LimitrangeHostParams",
    "K8sLimitRangeEntity",
    # Custom Resource (ns / cluster)
    "CrNsPublicParams",
    "CrClusterPublicParams",
    "NsCustomResourceEntity",
    "NsCustomResourcePatchEntity",
    "ClusterCustomResourceEntity",
    "ClusterCustomResourcePatchEntity",
    # Pod
    "PodPublicParams",
    "K8sPodEntity",
    "K8sPodPatchEntity",
    "K8sPodRawEntity",
    # Helm Chart (openapi)
    "HelmOpenapiPublicParams",
    "HelmInstallEntity",
    "HelmUpgradeEntity",
    # Workload Query (query-only)
    "WorkloadQueryPublicParams",
    # Harbor (harbor.jmx)
    "HarborPublicParams",
    "HarborProjectEntity",
    "HarborMemberEntity",
    "HarborReplicationPolicyEntity",
    # Small / query-only params (batch 4)
    "HarborInitPublicParams",
    "EndpointsV2PublicParams",
    "ImagePullSecretPublicParams",
    "ImagePublicParams",
    "NodePublicParams",
    "QuotaManagerTenantPublicParams",
    "ClusterPublicParams",
    "NamespacePublicParams",
    "OidcHarborInitPublicParams",
    "ResourceCollectionPublicParams",
    # Workload (workload.jmx)
    "WorkloadPublicParams",
    "WorkloadCreateEntity",
    "WorkloadUpdateEntity",
    "WorkloadPatchEntity",
    "WorkloadBatchTargetEntity",
    "WorkloadBatchPatchTargetEntity",
    "WorkloadExecEntity",
    "WorkloadPodDeleteEntity",
    "WorkloadAppPodDeleteEntity",
]
