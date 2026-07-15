import logging
from dataclasses import dataclass, field
from typing import Dict, Any

from base import BaseService
from core import DataCache


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




def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头"""
    cache = DataCache.get_instance()
    return {
        "Authorization": cache.get("token"),
    }


class PanJiMicroservicesOpenService(BaseService):
    DEFAULT_BASE_URL = 'http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030'

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        """
        初始化 Panji Microservices OpenAPI 服务

        Args:
            base_url: API 基础 URL
            logger: 日志记录器
        """
        super().__init__(
            base_url=base_url or self.DEFAULT_BASE_URL,
            logger=logger
        )
        self.logger.info(f"Initializing PanJi Microservices OpenAPI Service with base_url: {self.base_url}")

    # ==================== ingressnginx Ingress网关实例相关接口 ====================

    def add_ingress_instance(self, data: Ingress) -> Dict[str, Any]:
        """
        新增ingress网关实例
        Args:
            data: Ingress 网关实例数据，数据类参数全必填
        """
        self.logger.info("Add ingress gateway instance")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/add"
        body = {
            "name": data.name,
            "code": data.code,
            "systemCode": data.sysCode,
            "systemName": data.sysName,
            "unitName": data.unitName,
            "unitCode": data.unitCode,
            "planeName": data.planeName,
            "planeCode": data.planeCode,
            "deployType": "Deployment",
            "replicas": 1,
            "svcExportType": "NodePort",
            "containerExportType": "HostIP",
            "dualStack": "Y",
            "servicePortInfos": [
                {
                    "protocol": "TCP",
                    "port": "81",
                    "hostPort": "30021"
                }
            ]
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def get_ingress_instance_by_code(self, data: Ingress) -> Dict[str, Any]:
        """
        根据编码查询ingress网关实例详情
        Args:
            data: Ingress 网关数据类，必填：
            - code: str 网关实例编码
            - system_code: str 系统编码
            - unit_code: str 单元编码
        """
        self.logger.info(f"Get ingress instance by code: {data.code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/detailCode"
        payload = {"code": data.code, "systemCode": data.sysCode, "unitCode": data.unitCode}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def delete_ingress_instance_by_code(self, data: Ingress) -> Dict[str, Any]:
        """
        根据网关实例编码删除网关实例
        Args:
            data: Ingress 网关数据类，必填：
            - code: str 网关实例编码
            - system_code: str 系统编码
            - unit_code: str 单元编码
        """
        self.logger.info(f"Delete ingress instance by code: {data.code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/deleteCode"
        payload = {"code": data.code, "systemCode": data.sysCode, "unitCode": data.unitCode}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def add_ingress_config(self, data: IngressConfig) -> Dict[str, Any]:
        """
        新增ingress网关配置
        Args:
            data: IngressConfig 网关配置数据，必填
            - name: ingress网关名称
            - code: ingress网关编码
            - sysCode: 系统编码
            - unitCode: 单元编码
            - softControllerId
        """
        self.logger.info("Add ingress gateway config")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/add"
        body = {
            "systemCode": data.sysCode,
            "softControllerId": data.softControllerId,
            "unitCode": data.unitCode,
            "name": data.name,
            "namespace": data.sysCode,
            "serviceInfo": [],
            "id": 10086,
            "protocolType": "HTTP(S)",
            "params": [],
            "softLoadCode": data.code,
            "httpRules": [
                {
                    "serviceInfo": [
                        {
                            "path": "/",
                            "port": "8080",
                            "name": data.serviceName,
                            "hostPort": "http"
                        }
                    ]
                }
            ],
            "softLoadName": data.name
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def list_ingress_config(self, data: IngressConfig) -> Dict[str, Any]:
        """
        查询ingress网关配置列表
        Args:
            data: Dict 查询参数
        """
        self.logger.info("List ingress gateway config")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/list"
        body = {
            "name": data.name,
            "softLoadCode": data.softLoadCode,
            "systemCode": data.sysCode,
            "unitCode": data.unitCode
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def update_ingress_config(self, data: IngressConfig) -> Dict[str, Any]:
        """
        更新ingress网关配置
        Args:
            data: IngressConfig 网关配置数据，必填
            - name: ingress网关名称
            - code: ingress网关编码
            - sysCode: 系统编码
            - unitCode: 单元编码
            - softControllerId
        """
        self.logger.info("Update ingress gateway config")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/update"
        body = {
            "systemCode": data.sysCode,
            "softControllerId": data.softControllerId,
            "unitCode": data.unitCode,
            "name": data.name,
            "namespace": data.sysCode,
            "serviceInfo": [],
            "id": 1,
            "protocolType": "HTTP(S)",
            "params": [],
            "softLoadCode": data.code,
            "httpRules": [
                {
                    "domain": "www.ingress.com",
                    "serviceInfo": [
                        {
                            "path": "/",
                            "port": "8080",
                            "name": data.serviceName,
                            "hostPort": "http"
                        }
                    ]
                }
            ],
            "softLoadName": data.name
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def get_ingress_config_detail(self, data: IngressConfig) -> Dict[str, Any]:
        """
        ingress网关配置详情
        Args:
            data: Dict 查询参数
        """
        self.logger.info("Get ingress gateway config detail")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/detail"
        body = {
            "name": data.name,
            "softLoadCode": data.softLoadCode,
            "systemCode": data.sysCode,
            "unitCode": data.unitCode
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def get_ingress_by_service_name(self, data: IngressConfig) -> Dict[str, Any]:
        """
        ingress网关配置通过service获取配置详情
        Args:
            data: 网关配置，必填：
            -
        """
        self.logger.info("Get ingress by service name")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/getIngressByServiceName"
        body = {
            "systemCode": data.sysCode,
            "softControllerId": data.softControllerId,
            "unitCode": data.unitCode,
            "name": data.name,
            "planeCode": data.planeCode,
            "serviceName": data.serviceName,
            "softLoadCode": data.softLoadCode
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def delete_ingress_config_by_code(self, data: IngressConfig) -> Dict[str, Any]:
        """
        ingress网关配置删除接口
        Args:
            data: Dict 删除参数
        """
        self.logger.info("Delete ingress gateway config")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/deleteCode"
        body = {
            "name": data.name,
            "softLoadCode": data.softLoadCode,
            "systemCode": data.sysCode,
            "unitCode": data.unitCode
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    # ==================== msingressgw Nginx参数模板相关接口 ====================

    def add_nginx_param(self, data: NginxParam) -> Dict[str, Any]:
        """
        新增nginx参数模板
        Args:
            data: NginxParam 参数模板数据
        """
        self.logger.info("Add nginx param template")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/add"
        body = {
            "loadType": data.loadType,
            "code": data.code,
            "defaultValue": data.defaultValue,
            "name": data.name,
            "id": data.id,
            "type": data.type,
            "desc": data.desc,
            "status": data.status,
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def update_nginx_param(self, data: NginxParam) -> Dict[str, Any]:
        """
        修改nginx参数模板
        Args:
            data: NginxParam 更新数据
        """
        self.logger.info("Update nginx param template")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/update"
        body = {
            "loadType": data.loadType,
            "code": data.code,
            "defaultValue": data.defaultValue,
            "name": data.name,
            "id": data.id,
            "type": data.type,
            "desc": data.desc,
            "status": data.status
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def query_all_nginx_param(self, param_type: str = "All") -> Dict[str, Any]:
        """
        查询nginx参数模板列表
        Args:
            param_type: str 参数类型，默认All
        """
        self.logger.info("Query all nginx param templates")
        url = f"/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/queryAll?type={param_type}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def update_nginx_param_status(self, data: NginxParamStatus) -> Dict[str, Any]:
        """
        nginx参数模板上线/下线接口
        Args:
            data: NginxParamStatus 状态更新数据
        """
        self.logger.info("Update nginx param status")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/updateStatus"
        body = {
            "id": data.id,
            "page": data.page,
            "type": data.type,
            "keyword": data.keyword,
            "rows": data.rows,
            "status": data.status
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def list_nginx_param(self, data: NginxParamStatus) -> Dict[str, Any]:
        """
        分页查询nginx参数模板列表
        Args:
            data: NginxParamStatus 分页查询参数
        """
        self.logger.info("List nginx param templates")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/list"
        body = {
            "id": data.id,
            "page": data.page,
            "type": data.type,
            "keyword": data.keyword,
            "rows": data.rows,
            "status": data.status
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def delete_nginx_param_by_code(self, code: str, param_type: str) -> Dict[str, Any]:
        """
        根据nginx参数模板删除接口
        Args:
            code: str 参数模板编码
            param_type: str 参数类型
        """
        self.logger.info(f"Delete nginx param by code: {code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/deleteCode"
        payload = {"code": code, "type": param_type}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def list_ingress_instance(self, data: IngressIns) -> Dict[str, Any]:
        """
        查询ingress网关实例信息-分页
        Args:
            data: IngressIns 分页查询参数
        """
        self.logger.info("List ingress instances")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/list"
        body = {
            "systemCode": data.systemCode,
            "unitCode": data.unitCode,
            "planeCode": data.planeCode,
            "page": data.page,
            "keyword": data.keyword,
            "rows": data.rows,
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def update_ingress_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        修改ingress网关实例
        Args:
            data: Dict 更新数据
        """
        self.logger.info("Update ingress instance")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/update"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    # ==================== msingressksr Ingress网关实例启停扩缩容接口 ====================

    def start_ingress_instance_by_code(self, data: Ingress) -> Dict[str, Any]:
        """
        根据网关实例编码启动ingress网关实例
        Args:
            data: Ingress 网关数据类，必填：
            - code: str 网关实例编码
            - system_code: str 系统编码
            - unit_code: str 单元编码
        """
        self.logger.info(f"Start ingress instance by code: {data.code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadInstance/startCode"
        payload = {
            "code": data.code,
            "systemCode": data.sysCode,
            "unitCode": data.unitCode
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def stop_ingress_instance_by_code(self, data: Ingress) -> Dict[str, Any]:
        """
        根据网关实例编码停止ingress网关实例
        Args:
            data: Ingress 网关数据类，必填：
            - code: str 网关实例编码
            - system_code: str 系统编码
            - unit_code: str 单元编码
        """
        self.logger.info(f"Stop ingress instance by code: {data.code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadInstance/stopCode"
        payload = {
            "code": data.code,
            "systemCode": data.sysCode,
            "unitCode": data.unitCode
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def scale_ingress_instance(self, instance_id: str, deploy_type: str, replicas: int) -> Dict[str, Any]:
        """
        ingress网关实例扩缩容
        Args:
            instance_id: str 实例ID
            deploy_type: str 部署类型
            replicas: int 副本数
        """
        self.logger.info(f"Scale ingress instance: {instance_id}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadInstance/scale"
        payload = {
            "id": instance_id,
            "deployType": deploy_type,
            "replicas": replicas
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    # ==================== msistiogateway Istio网关相关接口 ====================

    def add_gateway_instance(self, data: GatewayInstance) -> Dict[str, Any]:
        """
        新增入口网关实例
        Args:
            data: Dict 网关实例数据
        """
        self.logger.info("Add gateway instance")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/add"
        body = {
            "cellCode": data.cellCode,
            "channel": data.channel,
            "clusterId": data.clusterId,
            "dualstack": data.dualStack,
            "exposeType": data.exposeType,
            "maxBodySize": data.maxBodySize,
            "name": data.name,
            "nodes": data.nodes,
            "numTrustedProxies": data.numTrustedProxies,
            "planeCode": data.planeCode,
            "portMaps": data.portMaps,
            "replicas": data.replicas,
            "sysCode": data.sysCode
        }
        response = self.post(endpoint=url, json=body, headers=_get_default_headers())
        return response.json()

    def get_gateway_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        精确入口网关实例信息
        Args:
            data: Dict 查询参数
        """
        self.logger.info("Get gateway instance")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/getGatewayInstance"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def list_gateway_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询入口网关实例信息，分页展示
        Args:
            data: Dict 分页查询参数
        """
        self.logger.info("List gateway instances")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/list"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def update_gateway_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新入口网关实例
        Args:
            data: Dict 更新数据
        """
        self.logger.info("Update gateway instance")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/update"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def list_ingress_egress_gateway(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询网关实例信息，分页展示包含入口和出口网关
        Args:
            data: Dict 分页查询参数
        """
        self.logger.info("List ingress and egress gateway instances")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/ingressEgressList"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def add_gateway_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        新增网关规则
        Args:
            data: Dict 网关规则数据
        """
        self.logger.info("Add gateway rule")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/add"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def list_gateway_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询网关规则信息，分页展示
        Args:
            data: Dict 分页查询参数
        """
        self.logger.info("List gateway rules")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/list"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def get_gateway_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        精确查询网关配置信息
        Args:
            data: Dict 查询参数
        """
        self.logger.info("Get gateway rule")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/getGateway"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def update_gateway_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新网关规则
        Args:
            data: Dict 更新数据
        """
        self.logger.info("Update gateway rule")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/update"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    # ==================== mscmf CMF服务相关接口 ====================

    def batch_add_funcser(self, control_plane_code: str, funcsers: list) -> Dict[str, Any]:
        """
        批量新增单体服务SINGLE
        Args:
            control_plane_code: str 控制面编码
            funcsers: list 服务列表
        """
        self.logger.info("Batch add funcser")
        url = "/openapi/ms-ubm/microservice-ubm/v2/funcser/batch"
        payload = {"controlPlaneCode": control_plane_code, "funcsers": funcsers}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def batch_get_funcser(self, control_plane_code: str, application_code: str, funcser_codes: list) -> Dict[str, Any]:
        """
        根据服务编码批量精确查询服务信息
        Args:
            control_plane_code: str 控制面编码
            application_code: str 应用编码
            funcser_codes: list 服务编码列表
        """
        self.logger.info("Batch get funcser")
        url = "/openapi/ms-ubm/microservice-ubm/v2/funcser/batch"
        params = {
            "controlPlaneCode": control_plane_code,
            "applicationCode": application_code,
            "funcserCodes": ",".join(funcser_codes) if isinstance(funcser_codes, list) else funcser_codes,
        }
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    def add_cmf_degrade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CMF新增降级配置
        Args:
            data: Dict 降级配置数据
        """
        self.logger.info("Add CMF degrade config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def get_cmf_degrade_detail(self, control_plane_name: str, env_code: str, func_ser_name: str) -> Dict[str, Any]:
        """
        CMF获取降级配置详情
        Args:
            control_plane_name: str 控制面名称
            env_code: str 环境编码
            func_ser_name: str 服务名称
        """
        self.logger.info("Get CMF degrade detail")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade/detail"
        payload = {"controlPlaneName": control_plane_name, "envCode": env_code, "funcSerName": func_ser_name}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def update_cmf_degrade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CMF修改降级配置
        Args:
            data: Dict 更新数据
        """
        self.logger.info("Update CMF degrade config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade/update"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def update_cmf_degrade_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CMF熔断配置上线或者下线
        Args:
            data: Dict 状态更新数据
        """
        self.logger.info("Update CMF degrade state")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade/updateState"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def delete_cmf_degrade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CMF删除降级配置
        Args:
            data: Dict 删除参数
        """
        self.logger.info("Delete CMF degrade config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade/delete"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def add_cmf_circuit_breaking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CMF新增熔断配置
        Args:
            data: Dict 熔断配置数据
        """
        self.logger.info("Add CMF circuit breaking config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def get_cmf_circuit_breaking_detail(self, control_plane_name: str, env_code: str, func_ser_name: str) -> Dict[str, Any]:
        """
        CMF获取熔断配置详情
        Args:
            control_plane_name: str 控制面名称
            env_code: str 环境编码
            func_ser_name: str 服务名称
        """
        self.logger.info("Get CMF circuit breaking detail")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking/detail"
        payload = {"controlPlaneName": control_plane_name, "envCode": env_code, "funcSerName": func_ser_name}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def update_cmf_circuit_breaking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CMF修改熔断配置
        Args:
            data: Dict 更新数据
        """
        self.logger.info("Update CMF circuit breaking config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking/update"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def update_cmf_circuit_breaking_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CMF熔断配置上线或者下线
        Args:
            data: Dict 状态更新数据
        """
        self.logger.info("Update CMF circuit breaking state")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking/updateState"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def delete_cmf_circuit_breaking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CMF删除熔断配置
        Args:
            data: Dict 删除参数
        """
        self.logger.info("Delete CMF circuit breaking config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking/delete"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def list_virtualservice_by_gateway_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据网关规则查询虚拟服务列表
        Args:
            data: Dict 查询参数
        """
        self.logger.info("List virtualservice by gateway config")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v2/mesh/virtualservice/listByGatewayConfig"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def add_virtual_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        新增虚拟服务
        Args:
            data: Dict 虚拟服务数据
        """
        self.logger.info("Add virtual service (openapi)")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v2/mesh/virtualservice/add"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def get_virtual_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        精确查询虚拟服务信息
        Args:
            data: Dict 查询参数
        """
        self.logger.info("Get virtual service (openapi)")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v2/mesh/virtualservice/getVirtualService"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def update_virtual_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新虚拟服务
        Args:
            data: Dict 更新数据
        """
        self.logger.info("Update virtual service (openapi)")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v2/mesh/virtualservice/update"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def list_virtual_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询虚拟服务列表
        Args:
            data: Dict 分页查询参数
        """
        self.logger.info("List virtual service (openapi)")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v2/mesh/virtualservice/list"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def delete_virtual_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        删除虚拟服务
        Args:
            data: Dict 删除参数
        """
        self.logger.info("Delete virtual service (openapi)")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v2/mesh/virtualservice/delete"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def delete_gateway_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        删除网关规则
        Args:
            data: Dict 删除参数
        """
        self.logger.info("Delete gateway rule")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/delete"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def delete_gateway_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        删除入口网关实例
        Args:
            data: Dict 删除参数
        """
        self.logger.info("Delete gateway instance")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/delete"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    # ==================== msubm UBM相关接口 ====================

    def get_cells(self) -> Dict[str, Any]:
        """
        查询平面单元列表
        """
        self.logger.info("Get cells list")
        url = "/openapi/ms-ubm/microservice-ubm/v2/cells"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_tenant_detail(self) -> Dict[str, Any]:
        """
        查询租户信息
        """
        self.logger.info("Get tenant detail")
        url = "/openapi/ms-ubm/microservice-ubm/v2/tenant/detail"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def batch_add_strategy(self, control_plane_code: str, strategies: list) -> Dict[str, Any]:
        """
        批量新增策略
        Args:
            control_plane_code: str 控制面编码
            strategies: list 策略列表
        """
        self.logger.info("Batch add strategy")
        url = "/openapi/ms-ubm/microservice-ubm/v2/strategy/batch"
        payload = {"controlPlaneCode": control_plane_code, "strategies": strategies}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def batch_update_strategy_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量更新策略状态
        Args:
            data: Dict 状态更新数据
        """
        self.logger.info("Batch update strategy status")
        url = "/openapi/ms-ubm/microservice-ubm/v2/strategy/clusterstatus"
        response = self.put(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def get_strategy_batch_detail(self, batch_code: str) -> Dict[str, Any]:
        """
        批量更新策略状态进度查询
        Args:
            batch_code: str 批次编码
        """
        self.logger.info(f"Get strategy batch detail: {batch_code}")
        url = f"/openapi/ms-ubm/microservice-ubm/v2/strategy/batch/detail/{batch_code}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()
