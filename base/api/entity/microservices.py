"""
Microservices（微服务）相关实体模型。

- Open API 使用：Ingress / IngressConfig / NginxParam / NginxParamStatus /
  IngressIns / GatewayInstance
- Inner API 使用：Kem / MeshVS / MeshNode
- 测试公共参数：UbmPublicParams / CmfPublicParams / IngressPublicParams /
  InnerIstioPublicParams / IstioPublicParams
- 场景 Entity：GatewayMeta / GatewayInstanceQuery / GatewayRuleEntity /
  VirtualServiceEntity / CmfServiceMeta / CmfDegradeEntity /
  CmfCircuitBreakingEntity / FuncserEntity / StrategyRuleEntity /
  StrategyEntity / StrategyStatusEntity / ClusterInfoEntity /
  BatchStrategyStatusEntity
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ==================== Microservices Open API 实体 ====================


@dataclass
class Ingress(object):
    """
    name: ingress网关名称
    code: ingress网关编码
    sysCode: 系统编码
    sysName: 系统名称
    unitCode: 单元编码
    unitName: 单元名称
    planeCode: 平面编码
    planeName: 平面名称
    remark: 备注（更新场景使用）
    """
    name: str = None
    code: str = None
    sysCode: str = None
    sysName: str = None
    unitCode: str = None
    unitName: str = None
    planeCode: str = None
    planeName: str = None
    remark: Optional[str] = None

    @classmethod
    def from_public_params(
        cls, params: "IngressPublicParams", *, remark: Optional[str] = None
    ) -> "Ingress":
        """从 IngressPublicParams 构造 Ingress（name/code 均取 mesh_gateway_name）。"""
        return cls(
            name=params.mesh_gateway_name,
            code=params.mesh_gateway_name,
            sysCode=params.sys_code,
            unitCode=params.unit_code,
            planeCode=params.plane_code,
            remark=remark,
        )


@dataclass
class IngressConfig(object):
    """
    name: ingress网关名称
    code: ingress网关编码
    sysCode: 系统编码
    unitCode: 单元编码
    planeCode: 平面编码
    softLoadCode:
    softControllerId:
    """
    name: str = None
    code: str = None
    sysCode: str = None
    unitCode: str = None
    planeCode: str = None
    serviceName: str = None
    softLoadCode: str = None
    softControllerId: str = None

    @classmethod
    def from_public_params(
        cls, params: "IngressPublicParams", *, soft_load_code: Optional[str] = None
    ) -> "IngressConfig":
        """从 IngressPublicParams 构造 IngressConfig（默认 softLoadCode 与 name 一致）。"""
        return cls(
            name=params.mesh_gateway_name,
            code=params.mesh_gateway_name,
            sysCode=params.sys_code,
            unitCode=params.unit_code,
            planeCode=params.plane_code,
            serviceName=params.mesh_gateway_name,
            softLoadCode=soft_load_code or params.mesh_gateway_name,
        )


@dataclass
class NginxParam(object):
    """
    id: 参数模板编号
    code: 参数模板编码
    name: 参数模板名称
    type: 参数模板类型
    desc: 参数模板描述
    status: 状态
    loadType: 加载类型
    defaultValue: 默认值启用
    """
    id: int = 1
    code: str = None
    name: str = None
    type: str = "App"
    desc: str = None
    status: str = "online"
    loadType: str = "nginx"
    defaultValue: str = "false"


@dataclass
class NginxParamStatus(object):
    """
    id: 参数模板编号
    page:
    type: 参数模板类型
    keyword:
    rows:
    status: 需要更新成的状态
    """
    id: int
    keyword: str
    page: int = 1
    type: str = "App"
    rows: int = 1
    status: str = "online"


@dataclass
class IngressIns(object):
    """
    keyword: 查询关键字
    systemCode: 系统编码
    unitCode: 单元编码
    planeCode: 平面编码
    page: 页数
    rows: 行数
    """
    keyword: str
    systemCode: str
    unitCode: str
    planeCode: str
    page: int = 1
    rows: int = 1


@dataclass
class GatewayInstance(object):
    """
    name: 网关名称
    sysCode: 系统编码
    cellCode: 单元编码
    planeCode: 平面编码
    clusterId: 集群编号
    channel: 频道
    dualStack:
    exposeType: 服务曝光类型
    maxBodySize:
    nodes: 节点相关配置
    numTrustedProxies:
    portMaps: 端口映射配置, [{"nodePort":"${nodePort}","port":8080,"protocol":"http"}]
    replicas: 分片数
    """
    name: str = None
    sysCode: str = None
    cellCode: str = None
    planeCode: str = None
    clusterId: str = ""
    channel: str = ""
    dualStack: str = "N"
    exposeType: str = "NODEPORT"
    maxBodySize: int = 1
    nodes: list = field(default_factory=list)
    numTrustedProxies: int = 0
    portMaps: list = field(default_factory=list)
    replicas: int = 1


# ==================== Microservices Inner API 实体 ====================


@dataclass
class Kem(object):
    """
    sysCode: 系统编码
    cellCode: 单元编码
    planeCode: 平面编码
    tenantCode: 租户编码
    username: 用户名
    gatewayInsName: 网关实例名称
    gatewayName: 网关名称
    gatewayNodePort: 网关节点端口
    vsName: 虚拟服务名称
    """
    sysCode: str = None
    cellCode: str = None
    planeCode: str = None
    tenantCode: str = None
    username: str = None
    gatewayInsName: str = None
    gatewayName: str = None
    gatewayNodePort: str = None
    vsName: str = None

    @classmethod
    def from_public_params(
        cls,
        params: "InnerIstioPublicParams",
        *,
        gateway_node_port: Optional[str] = None,
    ) -> "Kem":
        """从 InnerIstioPublicParams 构造 Kem。"""
        return cls(
            sysCode=params.sys_code,
            cellCode=params.cell_code,
            planeCode=params.plane_code,
            tenantCode=params.tenant_code,
            username=params.basic_auth_username,
            gatewayInsName=params.mesh_gateway_name,
            gatewayName=params.mesh_gateway_name,
            gatewayNodePort=gateway_node_port,
            vsName=params.mesh_vs_name,
        )


@dataclass
class MeshVS(object):
    """
    sysCode: 系统编码
    cellCode: 单元编码
    planeCode: 平面编码
    clusterId: 集群编号
    """
    vsName: str = None
    gatewayName: str = None
    sysCode: str = None
    cellCode: str = None
    planeCode: str = None
    clusterId: str = None

    @classmethod
    def from_public_params(cls, params: "InnerIstioPublicParams") -> "MeshVS":
        """从 InnerIstioPublicParams 构造 MeshVS。"""
        return cls(
            vsName=params.mesh_vs_name,
            gatewayName=params.mesh_gateway_name,
            sysCode=params.sys_code,
            cellCode=params.cell_code,
            planeCode=params.plane_code,
            clusterId=params.cluster_id,
        )


@dataclass
class MeshNode(object):
    """
    cellCode: 单元编码
    planeCode: 平面编码
    clusterId: 集群编号
    """
    cellCode: str = None
    planeCode: str = None
    clusterId: str = None

    @classmethod
    def from_public_params(cls, params: "InnerIstioPublicParams") -> "MeshNode":
        """从 InnerIstioPublicParams 构造 MeshNode。"""
        return cls(
            cellCode=params.cell_code,
            planeCode=params.plane_code,
            clusterId=params.cluster_id,
        )


# ==================== 测试公共参数 dataclass ====================


@dataclass
class UbmPublicParams(object):
    """UBM OpenAPI 测试公共参数（对应 api_env 键均使用 snake_case 暴露给测试层）。"""
    control_plane_code: Optional[str] = None
    belong_code: Optional[str] = None
    plane_code: Optional[str] = None
    plane_name: Optional[str] = None
    cell_code: Optional[str] = None
    cell_name: Optional[str] = None


@dataclass
class CmfPublicParams(object):
    """CMF OpenAPI 测试公共参数。"""
    control_plane_name: Optional[str] = None
    control_plane_code: Optional[str] = None
    env_code: Optional[str] = None
    application_code: Optional[str] = None
    function_class_name: Optional[str] = None
    func_ser_name: Optional[str] = None
    func_ser_code: Optional[str] = None


@dataclass
class IngressPublicParams(object):
    """Ingress OpenAPI 测试公共参数。"""
    mesh_gateway_name: Optional[str] = None
    sys_code: Optional[str] = None
    unit_code: Optional[str] = None
    plane_code: Optional[str] = None


@dataclass
class InnerIstioPublicParams(object):
    """Inner ISTIO API 测试公共参数。"""
    mesh_gateway_name: Optional[str] = None
    mesh_vs_name: Optional[str] = None
    sys_code: Optional[str] = None
    cell_code: Optional[str] = None
    plane_code: Optional[str] = None
    cluster_id: Optional[str] = None
    tenant_code: Optional[str] = None
    basic_auth_username: Optional[str] = None


@dataclass
class IstioPublicParams(object):
    """Istio Gateway OpenAPI 测试公共参数。"""
    sys_code: Optional[str] = None
    cell_code: Optional[str] = None
    plane_code: Optional[str] = None
    mesh_gateway_name: Optional[str] = None
    rule_name: Optional[str] = None
    mesh_vs_name: Optional[str] = None


# ==================== Istio Gateway 场景 Entity ====================


@dataclass
class GatewayMeta(object):
    """Istio 网关三元组基础元数据（systemCode/cellCode/planeCode）。"""
    system_code: Optional[str] = None
    cell_code: Optional[str] = None
    plane_code: Optional[str] = None

    @classmethod
    def from_public_params(cls, params: "IstioPublicParams") -> "GatewayMeta":
        """从 IstioPublicParams 构造 GatewayMeta（sys_code -> system_code）。"""
        return cls(
            system_code=params.sys_code,
            cell_code=params.cell_code,
            plane_code=params.plane_code,
        )


@dataclass
class GatewayInstanceQuery(object):
    """
    Istio 入口网关实例查询/更新/删除通用请求体。

    仅传入本次请求需要的字段即可，其余字段为 None 时由 service 层过滤。
    """
    meta: GatewayMeta
    name: Optional[str] = None
    page: Optional[int] = None
    rows: Optional[int] = None
    type: Optional[str] = None
    remark: Optional[str] = None


@dataclass
class GatewayRuleEntity(object):
    """Istio 网关规则请求体。"""
    meta: GatewayMeta
    gateway_name: Optional[str] = None
    rule_name: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    page: Optional[int] = None
    rows: Optional[int] = None
    remark: Optional[str] = None


@dataclass
class VirtualServiceEntity(object):
    """Istio 虚拟服务请求体。"""
    meta: GatewayMeta
    vs_name: Optional[str] = None
    gateway_name: Optional[str] = None
    rule_name: Optional[str] = None
    page: Optional[int] = None
    rows: Optional[int] = None
    remark: Optional[str] = None


# ==================== CMF 场景 Entity ====================


@dataclass
class CmfServiceMeta(object):
    """CMF 服务定位元数据（controlPlaneName/controlPlaneCode/envCode/applicationCode/...）。"""
    control_plane_name: Optional[str] = None
    control_plane_code: Optional[str] = None
    env_code: Optional[str] = None
    application_code: Optional[str] = None
    function_class_name: Optional[str] = None
    func_ser_name: Optional[str] = None
    func_ser_code: Optional[str] = None

    @classmethod
    def from_public_params(cls, params: "CmfPublicParams") -> "CmfServiceMeta":
        """从 CmfPublicParams 构造 CmfServiceMeta（字段名一致）。"""
        return cls(
            control_plane_name=params.control_plane_name,
            control_plane_code=params.control_plane_code,
            env_code=params.env_code,
            application_code=params.application_code,
            function_class_name=params.function_class_name,
            func_ser_name=params.func_ser_name,
            func_ser_code=params.func_ser_code,
        )


@dataclass
class CmfDegradeEntity(object):
    """CMF 降级配置请求体（新增/更新/状态切换/删除通用）。"""
    meta: CmfServiceMeta
    degrade_rule: Optional[Dict[str, Any]] = None
    state: Optional[str] = None


@dataclass
class CmfCircuitBreakingEntity(object):
    """CMF 熔断配置请求体。"""
    meta: CmfServiceMeta
    circuit_breaking_rule: Optional[Dict[str, Any]] = None
    state: Optional[str] = None


@dataclass
class FuncserEntity(object):
    """CMF 单体服务定义（批量新增用）。"""
    application_code: Optional[str] = None
    function_class_name: Optional[str] = None
    func_ser_code: Optional[str] = None
    func_ser_name: Optional[str] = None
    type: str = "SINGLE"


# ==================== UBM 策略场景 Entity ====================


@dataclass
class StrategyRuleEntity(object):
    """UBM 策略内嵌规则（type/paramKey/paramType/paramValue/targetValue）。"""
    type: Optional[str] = None
    param_key: Optional[str] = None
    param_type: Optional[str] = None
    param_value: Optional[str] = None
    target_value: Optional[str] = None


@dataclass
class StrategyEntity(object):
    """UBM 策略请求体（batch_add_strategy 单元素）。"""
    strategy_code: Optional[str] = None
    belong_code: Optional[str] = None
    scope: Optional[str] = None
    kind: Optional[str] = None
    strategy: Optional[StrategyRuleEntity] = None


@dataclass
class StrategyStatusEntity(object):
    """UBM 策略状态变更单元素。"""
    strategy_code: Optional[str] = None
    belong_code: Optional[str] = None
    status: Optional[str] = None


@dataclass
class ClusterInfoEntity(object):
    """UBM 策略状态变更集群信息单元素。"""
    plane_code: Optional[str] = None
    plane_name: Optional[str] = None
    cell_code: Optional[str] = None
    cell_name: Optional[str] = None


@dataclass
class BatchStrategyStatusEntity(object):
    """UBM 批量策略状态变更请求体。"""
    control_plane_code: Optional[str] = None
    scope: Optional[str] = None
    kind: Optional[str] = None
    strategy_infos: List[StrategyStatusEntity] = field(default_factory=list)
    cluster_infos: List[ClusterInfoEntity] = field(default_factory=list)


__all__ = [
    "Ingress",
    "IngressConfig",
    "NginxParam",
    "NginxParamStatus",
    "IngressIns",
    "GatewayInstance",
    "Kem",
    "MeshVS",
    "MeshNode",
    "UbmPublicParams",
    "CmfPublicParams",
    "IngressPublicParams",
    "InnerIstioPublicParams",
    "IstioPublicParams",
    "GatewayMeta",
    "GatewayInstanceQuery",
    "GatewayRuleEntity",
    "VirtualServiceEntity",
    "CmfServiceMeta",
    "CmfDegradeEntity",
    "CmfCircuitBreakingEntity",
    "FuncserEntity",
    "StrategyRuleEntity",
    "StrategyEntity",
    "StrategyStatusEntity",
    "ClusterInfoEntity",
    "BatchStrategyStatusEntity",
]
