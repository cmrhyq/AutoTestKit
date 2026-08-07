"""
API 实体模型模块（Entity / DTO 层）

参照 Java MVC 分层设计，将 API 请求/响应中使用的数据传输对象（DTO）
从 Service 层解耦出来，按业务模块组织：

- entity.portal:          Portal 门户相关实体（Inner + Open）
- entity.microservices:   微服务相关实体（Inner + Open）
- entity.observable:      可观测服务相关实体
- entity.operation:       运营运维相关实体
- entity.plugin:          插件中心相关实体
- entity.elastic_compute: 弹性计算 Native K8s 资源实体（Payload/DTO）

Service 层通过组合这些实体完成 API 请求参数构造，测试用例可直接
从 `base.api.entity.<模块>` 导入所需实体。
"""

from base.api.entity.elastic_compute import (
    ContainerPort,
    ContainerSpec,
    HpaCpuUtilizationMetric,
    HpaPayload,
    HpaScaleTargetRef,
    IngressHttpPath,
    IngressPayload,
    IngressServiceBackend,
    K8sMetadata,
    LabelSelector,
    LimitRangeItem,
    LimitRangePayload,
    NamespacePayload,
    PaasLabels,
    PodPayload,
    PodTemplate,
    PriorityClassPayload,
    ResourceQuotaPayload,
    WorkloadPayload,
)
from base.api.entity.microservices import (
    GatewayInstance,
    Ingress,
    IngressConfig,
    IngressIns,
    Kem,
    MeshNode,
    MeshVS,
    NginxParam,
    NginxParamStatus,
)
from base.api.entity.observable import (
    Log,
    LogContext,
    QueryModelConf,
)
from base.api.entity.operation import (
    MetricQuery,
)
from base.api.entity.portal import (
    ApplicationEntity,
    BasicCodeEntity,
    ClusterPlaneEntity,
    InnerSystemEntity,
    InnerUserEntity,
    MenuEntity,
    OpenSystemEntity,
    PortalUserEntity,
    RoleEntity,
    TenantEntity,
)

__all__ = [
    # portal
    "InnerSystemEntity",
    "ApplicationEntity",
    "MenuEntity",
    "RoleEntity",
    "TenantEntity",
    "InnerUserEntity",
    "PortalUserEntity",
    "ClusterPlaneEntity",
    "OpenSystemEntity",
    "BasicCodeEntity",
    # microservices
    "Ingress",
    "IngressConfig",
    "NginxParam",
    "NginxParamStatus",
    "IngressIns",
    "GatewayInstance",
    "Kem",
    "MeshVS",
    "MeshNode",
    # observable
    "Log",
    "LogContext",
    "QueryModelConf",
    # operation
    "MetricQuery",
    # plugin
    "McpValidatePayload",
    # elastic_compute
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
