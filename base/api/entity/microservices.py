"""
Microservices（微服务）相关实体模型。

- Open API 使用：Ingress / IngressConfig / NginxParam / NginxParamStatus /
  IngressIns / GatewayInstance
- Inner API 使用：Kem / MeshVS / MeshNode
"""

from dataclasses import dataclass, field


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
    """
    name: str = None
    code: str = None
    sysCode: str = None
    sysName: str = None
    unitCode: str = None
    unitName: str = None
    planeCode: str = None
    planeName: str = None


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
]
