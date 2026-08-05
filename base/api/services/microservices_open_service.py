from typing import Dict, Any, List, Optional

from base import BaseService

from base.api.entity.microservices import (
    BatchStrategyStatusEntity,
    CmfCircuitBreakingEntity,
    CmfDegradeEntity,
    FuncserEntity,
    GatewayInstance,
    GatewayInstanceQuery,
    GatewayRuleEntity,
    Ingress,
    IngressConfig,
    IngressIns,
    NginxParam,
    NginxParamStatus,
    StrategyEntity,
    VirtualServiceEntity,
)
from core import get_logger

logger = get_logger(__name__)


class MicroservicesOpenService(BaseService):

    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        初始化 Panji Microservices OpenAPI 服务

        Args:
            base_url: API 基础 URL（必传，来自 config/env_*.yaml 的 apiBaseUrl）
            token: Bearer Token

        Raises:
            ValueError: 如果 base_url 为空
        """
        if not base_url:
            raise ValueError(
                "base_url is required. "
                "Configure it in config/env_*.yaml (apiBaseUrl) "
                "and pass via fixture: api_env.get('apiBaseUrl')"
            )
        super().__init__(
            base_url=base_url,
            auth_type="bearer" if token else None,
            auth_credentials={"token": token} if token else None,
        )
        logger.info(f"Initializing PanJi Microservices OpenAPI Service with base_url: {self.base_url}")

    # ==================== ingressnginx Ingress网关实例相关接口 ====================

    def add_ingress_instance(self, data: Ingress) -> Dict[str, Any]:
        """
        新增ingress网关实例
        Args:
            data: Ingress 网关实例数据，数据类参数全必填
        """
        logger.info("Add ingress gateway instance")
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
        response = self.post(endpoint=url, json=body)
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
        logger.info(f"Get ingress instance by code: {data.code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/detailCode"
        payload = {"code": data.code, "systemCode": data.sysCode, "unitCode": data.unitCode}
        response = self.post(endpoint=url, json=payload)
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
        logger.info(f"Delete ingress instance by code: {data.code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/deleteCode"
        payload = {"code": data.code, "systemCode": data.sysCode, "unitCode": data.unitCode}
        response = self.post(endpoint=url, json=payload)
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
        logger.info("Add ingress gateway config")
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
        response = self.post(endpoint=url, json=body)
        return response.json()

    def list_ingress_config(self, data: IngressConfig) -> Dict[str, Any]:
        """
        查询ingress网关配置列表
        Args:
            data: Dict 查询参数
        """
        logger.info("List ingress gateway config")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/list"
        body = {
            "name": data.name,
            "softLoadCode": data.softLoadCode,
            "systemCode": data.sysCode,
            "unitCode": data.unitCode
        }
        response = self.post(endpoint=url, json=body)
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
        logger.info("Update ingress gateway config")
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
        response = self.post(endpoint=url, json=body)
        return response.json()

    def get_ingress_config_detail(self, data: IngressConfig) -> Dict[str, Any]:
        """
        ingress网关配置详情
        Args:
            data: Dict 查询参数
        """
        logger.info("Get ingress gateway config detail")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/detail"
        body = {
            "name": data.name,
            "softLoadCode": data.softLoadCode,
            "systemCode": data.sysCode,
            "unitCode": data.unitCode
        }
        response = self.post(endpoint=url, json=body)
        return response.json()

    def get_ingress_by_service_name(self, data: IngressConfig) -> Dict[str, Any]:
        """
        ingress网关配置通过service获取配置详情
        Args:
            data: 网关配置，必填：
            -
        """
        logger.info("Get ingress by service name")
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
        response = self.post(endpoint=url, json=body)
        return response.json()

    def delete_ingress_config_by_code(self, data: IngressConfig) -> Dict[str, Any]:
        """
        ingress网关配置删除接口
        Args:
            data: Dict 删除参数
        """
        logger.info("Delete ingress gateway config")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/deleteCode"
        body = {
            "name": data.name,
            "softLoadCode": data.softLoadCode,
            "systemCode": data.sysCode,
            "unitCode": data.unitCode
        }
        response = self.post(endpoint=url, json=body)
        return response.json()

    # ==================== msingressgw Nginx参数模板相关接口 ====================

    def add_nginx_param(self, data: NginxParam) -> Dict[str, Any]:
        """
        新增nginx参数模板
        Args:
            data: NginxParam 参数模板数据
        """
        logger.info("Add nginx param template")
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
        response = self.post(endpoint=url, json=body)
        return response.json()

    def update_nginx_param(self, data: NginxParam) -> Dict[str, Any]:
        """
        修改nginx参数模板
        Args:
            data: NginxParam 更新数据
        """
        logger.info("Update nginx param template")
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
        response = self.post(endpoint=url, json=body)
        return response.json()

    def query_all_nginx_param(self, param_type: str = "All") -> Dict[str, Any]:
        """
        查询nginx参数模板列表
        Args:
            param_type: str 参数类型，默认All
        """
        logger.info("Query all nginx param templates")
        url = f"/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/queryAll?type={param_type}"
        response = self.get(endpoint=url)
        return response.json()

    def update_nginx_param_status(self, data: NginxParamStatus) -> Dict[str, Any]:
        """
        nginx参数模板上线/下线接口
        Args:
            data: NginxParamStatus 状态更新数据
        """
        logger.info("Update nginx param status")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/updateStatus"
        body = {
            "id": data.id,
            "page": data.page,
            "type": data.type,
            "keyword": data.keyword,
            "rows": data.rows,
            "status": data.status
        }
        response = self.post(endpoint=url, json=body)
        return response.json()

    def list_nginx_param(self, data: NginxParamStatus) -> Dict[str, Any]:
        """
        分页查询nginx参数模板列表
        Args:
            data: NginxParamStatus 分页查询参数
        """
        logger.info("List nginx param templates")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/list"
        body = {
            "id": data.id,
            "page": data.page,
            "type": data.type,
            "keyword": data.keyword,
            "rows": data.rows,
            "status": data.status
        }
        response = self.post(endpoint=url, json=body)
        return response.json()

    def delete_nginx_param_by_code(self, code: str, param_type: str) -> Dict[str, Any]:
        """
        根据nginx参数模板删除接口
        Args:
            code: str 参数模板编码
            param_type: str 参数类型
        """
        logger.info(f"Delete nginx param by code: {code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/deleteCode"
        payload = {"code": code, "type": param_type}
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def list_ingress_instance(self, data: IngressIns) -> Dict[str, Any]:
        """
        查询ingress网关实例信息-分页
        Args:
            data: IngressIns 分页查询参数
        """
        logger.info("List ingress instances")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/list"
        body = {
            "systemCode": data.systemCode,
            "unitCode": data.unitCode,
            "planeCode": data.planeCode,
            "page": data.page,
            "keyword": data.keyword,
            "rows": data.rows,
        }
        response = self.post(endpoint=url, json=body)
        return response.json()

    def update_ingress_instance(self, data: Ingress) -> Dict[str, Any]:
        """
        修改ingress网关实例
        Args:
            data: Ingress 网关数据类，需填 name/code/sysCode/unitCode/planeCode，可选 remark
        """
        logger.info("Update ingress instance")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/update"
        payload: Dict[str, Any] = {
            "name": data.name,
            "code": data.code,
            "sysCode": data.sysCode,
            "unitCode": data.unitCode,
            "planeCode": data.planeCode,
        }
        if data.remark is not None:
            payload["remark"] = data.remark
        response = self.post(endpoint=url, json=payload)
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
        logger.info(f"Start ingress instance by code: {data.code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadInstance/startCode"
        payload = {
            "code": data.code,
            "systemCode": data.sysCode,
            "unitCode": data.unitCode
        }
        response = self.post(endpoint=url, json=payload)
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
        logger.info(f"Stop ingress instance by code: {data.code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadInstance/stopCode"
        payload = {
            "code": data.code,
            "systemCode": data.sysCode,
            "unitCode": data.unitCode
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def scale_ingress_instance(self, instance_id: str, deploy_type: str, replicas: int) -> Dict[str, Any]:
        """
        ingress网关实例扩缩容
        Args:
            instance_id: str 实例ID
            deploy_type: str 部署类型
            replicas: int 副本数
        """
        logger.info(f"Scale ingress instance: {instance_id}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadInstance/scale"
        payload = {
            "id": instance_id,
            "deployType": deploy_type,
            "replicas": replicas
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    # ==================== msistiogateway Istio网关相关接口 ====================

    def add_gateway_instance(self, data: GatewayInstance) -> Dict[str, Any]:
        """
        新增入口网关实例
        Args:
            data: Dict 网关实例数据
        """
        logger.info("Add gateway instance")
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
        response = self.post(endpoint=url, json=body)
        return response.json()

    def get_gateway_instance(self, data: GatewayInstanceQuery) -> Dict[str, Any]:
        """
        精确入口网关实例信息
        Args:
            data: GatewayInstanceQuery，需要 meta.system_code/cell_code/plane_code 与 name
        """
        logger.info("Get gateway instance")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/getGatewayInstance"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "name": data.name,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def list_gateway_instance(self, data: GatewayInstanceQuery) -> Dict[str, Any]:
        """
        查询入口网关实例信息，分页展示
        Args:
            data: GatewayInstanceQuery，需要 meta + page/rows + type
        """
        logger.info("List gateway instances")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/list"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "page": data.page,
            "rows": data.rows,
            "type": data.type,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def update_gateway_instance(self, data: GatewayInstanceQuery) -> Dict[str, Any]:
        """
        更新入口网关实例
        Args:
            data: GatewayInstanceQuery，需要 meta + name + type + 可选 remark
        """
        logger.info("Update gateway instance")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/update"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "name": data.name,
            "type": data.type,
        }
        if data.remark is not None:
            payload["remark"] = data.remark
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def list_ingress_egress_gateway(self, data: GatewayInstanceQuery) -> Dict[str, Any]:
        """
        查询网关实例信息，分页展示包含入口和出口网关
        Args:
            data: GatewayInstanceQuery，需要 meta + page/rows
        """
        logger.info("List ingress and egress gateway instances")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/ingressEgressList"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "page": data.page,
            "rows": data.rows,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def add_gateway_rule(self, data: GatewayRuleEntity) -> Dict[str, Any]:
        """
        新增网关规则
        Args:
            data: GatewayRuleEntity，需要 meta + gateway_name + rule_name + port + protocol
        """
        logger.info("Add gateway rule")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/add"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "gatewayName": data.gateway_name,
            "ruleName": data.rule_name,
            "port": data.port,
            "protocol": data.protocol,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def list_gateway_rule(self, data: GatewayRuleEntity) -> Dict[str, Any]:
        """
        查询网关规则信息，分页展示
        Args:
            data: GatewayRuleEntity，需要 meta + gateway_name + page/rows
        """
        logger.info("List gateway rules")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/list"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "gatewayName": data.gateway_name,
            "page": data.page,
            "rows": data.rows,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def get_gateway_rule(self, data: GatewayRuleEntity) -> Dict[str, Any]:
        """
        精确查询网关配置信息
        Args:
            data: GatewayRuleEntity，需要 meta + gateway_name + rule_name
        """
        logger.info("Get gateway rule")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/getGateway"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "gatewayName": data.gateway_name,
            "ruleName": data.rule_name,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def update_gateway_rule(self, data: GatewayRuleEntity) -> Dict[str, Any]:
        """
        更新网关规则
        Args:
            data: GatewayRuleEntity，需要 meta + gateway_name + rule_name + port + protocol + 可选 remark
        """
        logger.info("Update gateway rule")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/update"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "gatewayName": data.gateway_name,
            "ruleName": data.rule_name,
            "port": data.port,
            "protocol": data.protocol,
        }
        if data.remark is not None:
            payload["remark"] = data.remark
        response = self.post(endpoint=url, json=payload)
        return response.json()

    # ==================== mscmf CMF服务相关接口 ====================

    def batch_add_funcser(self, control_plane_code: str, funcsers: List[FuncserEntity]) -> Dict[str, Any]:
        """
        批量新增单体服务SINGLE
        Args:
            control_plane_code: str 控制面编码
            funcsers: List[FuncserEntity] 服务定义列表
        """
        logger.info("Batch add funcser")
        url = "/openapi/ms-ubm/microservice-ubm/v2/funcser/batch"
        payload: Dict[str, Any] = {
            "controlPlaneCode": control_plane_code,
            "funcsers": [
                {
                    "applicationCode": f.application_code,
                    "functionClassName": f.function_class_name,
                    "funcSerCode": f.func_ser_code,
                    "funcSerName": f.func_ser_name,
                    "type": f.type,
                }
                for f in funcsers
            ],
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def batch_get_funcser(self, control_plane_code: str, application_code: str, funcser_codes: list) -> Dict[str, Any]:
        """
        根据服务编码批量精确查询服务信息
        Args:
            control_plane_code: str 控制面编码
            application_code: str 应用编码
            funcser_codes: list 服务编码列表
        """
        logger.info("Batch get funcser")
        url = "/openapi/ms-ubm/microservice-ubm/v2/funcser/batch"
        params = {
            "controlPlaneCode": control_plane_code,
            "applicationCode": application_code,
            "funcserCodes": ",".join(funcser_codes) if isinstance(funcser_codes, list) else funcser_codes,
        }
        response = self.get(endpoint=url, params=params)
        return response.json()

    def add_cmf_degrade(self, data: CmfDegradeEntity) -> Dict[str, Any]:
        """
        CMF新增降级配置
        Args:
            data: CmfDegradeEntity 需要 meta + degrade_rule
        """
        logger.info("Add CMF degrade config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade"
        payload: Dict[str, Any] = {
            "controlPlaneName": data.meta.control_plane_name,
            "controlPlaneCode": data.meta.control_plane_code,
            "envCode": data.meta.env_code,
            "applicationCode": data.meta.application_code,
            "functionClassName": data.meta.function_class_name,
            "funcSerName": data.meta.func_ser_name,
            "funcSerCode": data.meta.func_ser_code,
        }
        if data.degrade_rule is not None:
            payload["degradeRule"] = data.degrade_rule
        if data.state is not None:
            payload["state"] = data.state
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def get_cmf_degrade_detail(self, control_plane_name: str, env_code: str, func_ser_name: str) -> Dict[str, Any]:
        """
        CMF获取降级配置详情
        Args:
            control_plane_name: str 控制面名称
            env_code: str 环境编码
            func_ser_name: str 服务名称
        """
        logger.info("Get CMF degrade detail")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade/detail"
        payload = {"controlPlaneName": control_plane_name, "envCode": env_code, "funcSerName": func_ser_name}
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def update_cmf_degrade(self, data: CmfDegradeEntity) -> Dict[str, Any]:
        """
        CMF修改降级配置
        Args:
            data: CmfDegradeEntity 需要 meta + degrade_rule
        """
        logger.info("Update CMF degrade config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade/update"
        payload: Dict[str, Any] = {
            "controlPlaneName": data.meta.control_plane_name,
            "controlPlaneCode": data.meta.control_plane_code,
            "envCode": data.meta.env_code,
            "applicationCode": data.meta.application_code,
            "functionClassName": data.meta.function_class_name,
            "funcSerName": data.meta.func_ser_name,
            "funcSerCode": data.meta.func_ser_code,
        }
        if data.degrade_rule is not None:
            payload["degradeRule"] = data.degrade_rule
        if data.state is not None:
            payload["state"] = data.state
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def update_cmf_degrade_state(self, data: CmfDegradeEntity) -> Dict[str, Any]:
        """
        CMF熔断配置上线或者下线
        Args:
            data: CmfDegradeEntity 需要 meta + state
        """
        logger.info("Update CMF degrade state")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade/updateState"
        payload: Dict[str, Any] = {
            "controlPlaneName": data.meta.control_plane_name,
            "controlPlaneCode": data.meta.control_plane_code,
            "envCode": data.meta.env_code,
            "applicationCode": data.meta.application_code,
            "functionClassName": data.meta.function_class_name,
            "funcSerName": data.meta.func_ser_name,
            "funcSerCode": data.meta.func_ser_code,
        }
        if data.state is not None:
            payload["state"] = data.state
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def delete_cmf_degrade(self, data: CmfDegradeEntity) -> Dict[str, Any]:
        """
        CMF删除降级配置
        Args:
            data: CmfDegradeEntity 需要 meta
        """
        logger.info("Delete CMF degrade config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade/delete"
        payload: Dict[str, Any] = {
            "controlPlaneName": data.meta.control_plane_name,
            "controlPlaneCode": data.meta.control_plane_code,
            "envCode": data.meta.env_code,
            "applicationCode": data.meta.application_code,
            "functionClassName": data.meta.function_class_name,
            "funcSerName": data.meta.func_ser_name,
            "funcSerCode": data.meta.func_ser_code,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def add_cmf_circuit_breaking(self, data: CmfCircuitBreakingEntity) -> Dict[str, Any]:
        """
        CMF新增熔断配置
        Args:
            data: CmfCircuitBreakingEntity 需要 meta + circuit_breaking_rule
        """
        logger.info("Add CMF circuit breaking config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking"
        payload: Dict[str, Any] = {
            "controlPlaneName": data.meta.control_plane_name,
            "controlPlaneCode": data.meta.control_plane_code,
            "envCode": data.meta.env_code,
            "applicationCode": data.meta.application_code,
            "functionClassName": data.meta.function_class_name,
            "funcSerName": data.meta.func_ser_name,
            "funcSerCode": data.meta.func_ser_code,
        }
        if data.circuit_breaking_rule is not None:
            payload["circuitBreakingRule"] = data.circuit_breaking_rule
        if data.state is not None:
            payload["state"] = data.state
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def get_cmf_circuit_breaking_detail(self, control_plane_name: str, env_code: str, func_ser_name: str) -> Dict[str, Any]:
        """
        CMF获取熔断配置详情
        Args:
            control_plane_name: str 控制面名称
            env_code: str 环境编码
            func_ser_name: str 服务名称
        """
        logger.info("Get CMF circuit breaking detail")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking/detail"
        payload = {"controlPlaneName": control_plane_name, "envCode": env_code, "funcSerName": func_ser_name}
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def update_cmf_circuit_breaking(self, data: CmfCircuitBreakingEntity) -> Dict[str, Any]:
        """
        CMF修改熔断配置
        Args:
            data: CmfCircuitBreakingEntity 需要 meta + circuit_breaking_rule
        """
        logger.info("Update CMF circuit breaking config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking/update"
        payload: Dict[str, Any] = {
            "controlPlaneName": data.meta.control_plane_name,
            "controlPlaneCode": data.meta.control_plane_code,
            "envCode": data.meta.env_code,
            "applicationCode": data.meta.application_code,
            "functionClassName": data.meta.function_class_name,
            "funcSerName": data.meta.func_ser_name,
            "funcSerCode": data.meta.func_ser_code,
        }
        if data.circuit_breaking_rule is not None:
            payload["circuitBreakingRule"] = data.circuit_breaking_rule
        if data.state is not None:
            payload["state"] = data.state
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def update_cmf_circuit_breaking_state(self, data: CmfCircuitBreakingEntity) -> Dict[str, Any]:
        """
        CMF熔断配置上线或者下线
        Args:
            data: CmfCircuitBreakingEntity 需要 meta + state
        """
        logger.info("Update CMF circuit breaking state")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking/updateState"
        payload: Dict[str, Any] = {
            "controlPlaneName": data.meta.control_plane_name,
            "controlPlaneCode": data.meta.control_plane_code,
            "envCode": data.meta.env_code,
            "applicationCode": data.meta.application_code,
            "functionClassName": data.meta.function_class_name,
            "funcSerName": data.meta.func_ser_name,
            "funcSerCode": data.meta.func_ser_code,
        }
        if data.state is not None:
            payload["state"] = data.state
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def delete_cmf_circuit_breaking(self, data: CmfCircuitBreakingEntity) -> Dict[str, Any]:
        """
        CMF删除熔断配置
        Args:
            data: CmfCircuitBreakingEntity 需要 meta
        """
        logger.info("Delete CMF circuit breaking config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking/delete"
        payload: Dict[str, Any] = {
            "controlPlaneName": data.meta.control_plane_name,
            "controlPlaneCode": data.meta.control_plane_code,
            "envCode": data.meta.env_code,
            "applicationCode": data.meta.application_code,
            "functionClassName": data.meta.function_class_name,
            "funcSerName": data.meta.func_ser_name,
            "funcSerCode": data.meta.func_ser_code,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def list_virtualservice_by_gateway_config(self, data: VirtualServiceEntity) -> Dict[str, Any]:
        """
        根据网关规则查询虚拟服务列表
        Args:
            data: VirtualServiceEntity，需要 meta + gateway_name + rule_name
        """
        logger.info("List virtualservice by gateway config")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v2/mesh/virtualservice/listByGatewayConfig"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "gatewayName": data.gateway_name,
            "ruleName": data.rule_name,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def add_virtual_service(self, data: VirtualServiceEntity) -> Dict[str, Any]:
        """
        新增虚拟服务
        Args:
            data: VirtualServiceEntity，需要 meta + gateway_name + rule_name + vs_name
        """
        logger.info("Add virtual service (openapi)")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v2/mesh/virtualservice/add"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "gatewayName": data.gateway_name,
            "ruleName": data.rule_name,
            "vsName": data.vs_name,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def get_virtual_service(self, data: VirtualServiceEntity) -> Dict[str, Any]:
        """
        精确查询虚拟服务信息
        Args:
            data: VirtualServiceEntity，需要 meta + vs_name
        """
        logger.info("Get virtual service (openapi)")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v2/mesh/virtualservice/getVirtualService"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "vsName": data.vs_name,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def update_virtual_service(self, data: VirtualServiceEntity) -> Dict[str, Any]:
        """
        更新虚拟服务
        Args:
            data: VirtualServiceEntity，需要 meta + vs_name + gateway_name + rule_name + 可选 remark
        """
        logger.info("Update virtual service (openapi)")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v2/mesh/virtualservice/update"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "vsName": data.vs_name,
            "gatewayName": data.gateway_name,
            "ruleName": data.rule_name,
        }
        if data.remark is not None:
            payload["remark"] = data.remark
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def list_virtual_service(self, data: VirtualServiceEntity) -> Dict[str, Any]:
        """
        查询虚拟服务列表
        Args:
            data: VirtualServiceEntity，需要 meta + page/rows
        """
        logger.info("List virtual service (openapi)")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v2/mesh/virtualservice/list"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "page": data.page,
            "rows": data.rows,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def delete_virtual_service(self, data: VirtualServiceEntity) -> Dict[str, Any]:
        """
        删除虚拟服务
        Args:
            data: VirtualServiceEntity，需要 meta + vs_name
        """
        logger.info("Delete virtual service (openapi)")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v2/mesh/virtualservice/delete"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "vsName": data.vs_name,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def delete_gateway_rule(self, data: GatewayRuleEntity) -> Dict[str, Any]:
        """
        删除网关规则
        Args:
            data: GatewayRuleEntity，需要 meta + gateway_name + rule_name
        """
        logger.info("Delete gateway rule")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/delete"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "gatewayName": data.gateway_name,
            "ruleName": data.rule_name,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def delete_gateway_instance(self, data: GatewayInstanceQuery) -> Dict[str, Any]:
        """
        删除入口网关实例
        Args:
            data: GatewayInstanceQuery，需要 meta + name
        """
        logger.info("Delete gateway instance")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/delete"
        payload: Dict[str, Any] = {
            "systemCode": data.meta.system_code,
            "cellCode": data.meta.cell_code,
            "planeCode": data.meta.plane_code,
            "name": data.name,
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    # ==================== msubm UBM相关接口 ====================

    def get_cells(self) -> Dict[str, Any]:
        """
        查询平面单元列表
        """
        logger.info("Get cells list")
        url = "/openapi/ms-ubm/microservice-ubm/v2/cells"
        response = self.get(endpoint=url)
        return response.json()

    def get_tenant_detail(self) -> Dict[str, Any]:
        """
        查询租户信息
        """
        logger.info("Get tenant detail")
        url = "/openapi/ms-ubm/microservice-ubm/v2/tenant/detail"
        response = self.get(endpoint=url)
        return response.json()

    def batch_add_strategy(self, control_plane_code: str, strategies: List[StrategyEntity]) -> Dict[str, Any]:
        """
        批量新增策略
        Args:
            control_plane_code: str 控制面编码
            strategies: List[StrategyEntity] 策略列表
        """
        logger.info("Batch add strategy")
        url = "/openapi/ms-ubm/microservice-ubm/v2/strategy/batch"
        payload: Dict[str, Any] = {
            "controlPlaneCode": control_plane_code,
            "strategies": [
                {
                    "strategyCode": s.strategy_code,
                    "belongCode": s.belong_code,
                    "scope": s.scope,
                    "kind": s.kind,
                    "strategy": None
                    if s.strategy is None
                    else {
                        "type": s.strategy.type,
                        "paramKey": s.strategy.param_key,
                        "paramType": s.strategy.param_type,
                        "paramValue": s.strategy.param_value,
                        "targetValue": s.strategy.target_value,
                    },
                }
                for s in strategies
            ],
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def batch_update_strategy_status(self, data: BatchStrategyStatusEntity) -> Dict[str, Any]:
        """
        批量更新策略状态
        Args:
            data: BatchStrategyStatusEntity 状态更新数据
        """
        logger.info("Batch update strategy status")
        url = "/openapi/ms-ubm/microservice-ubm/v2/strategy/clusterstatus"
        payload: Dict[str, Any] = {
            "controlPlaneCode": data.control_plane_code,
            "scope": data.scope,
            "kind": data.kind,
            "strategyInfos": [
                {
                    "strategyCode": si.strategy_code,
                    "belongCode": si.belong_code,
                    "status": si.status,
                }
                for si in data.strategy_infos
            ],
            "clusterInfos": [
                {
                    "planeCode": ci.plane_code,
                    "planeName": ci.plane_name,
                    "cellCode": ci.cell_code,
                    "cellName": ci.cell_name,
                }
                for ci in data.cluster_infos
            ],
        }
        response = self.put(endpoint=url, json=payload)
        return response.json()

    def get_strategy_batch_detail(self, batch_code: str) -> Dict[str, Any]:
        """
        批量更新策略状态进度查询
        Args:
            batch_code: str 批次编码
        """
        logger.info(f"Get strategy batch detail: {batch_code}")
        url = f"/openapi/ms-ubm/microservice-ubm/v2/strategy/batch/detail/{batch_code}"
        response = self.get(endpoint=url)
        return response.json()
