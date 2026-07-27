"""
API 实体模型模块（Entity / DTO 层）

参照 Java MVC 分层设计，将 API 请求/响应中使用的数据传输对象（DTO）
从 Service 层解耦出来，按业务模块组织：

- entity.portal:        Portal 门户相关实体（Inner + Open）
- entity.microservices: 微服务相关实体（Inner + Open）
- entity.observable:    可观测服务相关实体

Service 层通过组合这些实体完成 API 请求参数构造，测试用例可直接
从 `base.api.entity.<模块>` 导入所需实体。
"""

from base.api.entity.portal import (
    InnerSystemEntity,
    ApplicationEntity,
    MenuEntity,
    RoleEntity,
    TenantEntity,
    InnerUserEntity,
    PortalUserEntity,
    ClusterPlaneEntity,
    OpenSystemEntity,
    BasicCodeEntity,
)
from base.api.entity.microservices import (
    Ingress,
    IngressConfig,
    NginxParam,
    NginxParamStatus,
    IngressIns,
    GatewayInstance,
    Kem,
    MeshVS,
    MeshNode,
)
from base.api.entity.observable import (
    Log,
    LogContext,
    QueryModelConf,
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
]
