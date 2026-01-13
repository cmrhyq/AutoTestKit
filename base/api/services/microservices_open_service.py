import logging
from typing import Dict, Any

from base import BaseService
from core import DataCache


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

    def add_ingress_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """新增ingress网关实例"""
        self.logger.info("Add ingress gateway instance")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/add"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def get_ingress_instance_by_code(self, code: str, system_code: str, unit_code: str) -> Dict[str, Any]:
        """根据编码查询ingress网关实例详情"""
        self.logger.info(f"Get ingress instance by code: {code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/detailCode"
        payload = {"code": code, "systemCode": system_code, "unitCode": unit_code}
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def delete_ingress_instance_by_code(self, code: str, system_code: str, unit_code: str) -> Dict[str, Any]:
        """根据网关实例编码删除网关实例"""
        self.logger.info(f"Delete ingress instance by code: {code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/deleteCode"
        payload = {"code": code, "systemCode": system_code, "unitCode": unit_code}
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def add_ingress_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """新增ingress网关配置"""
        self.logger.info("Add ingress gateway config")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/add"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def list_ingress_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """查询ingress网关配置列表"""
        self.logger.info("List ingress gateway config")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/list"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def update_ingress_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新ingress网关配置"""
        self.logger.info("Update ingress gateway config")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/update"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def get_ingress_config_detail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ingress网关配置详情"""
        self.logger.info("Get ingress gateway config detail")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/detail"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def delete_ingress_config_by_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ingress网关配置删除接口"""
        self.logger.info("Delete ingress gateway config")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadIngress/deleteCode"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    # ==================== msingressgw Nginx参数模板相关接口 ====================

    def add_nginx_param(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """新增nginx参数模板"""
        self.logger.info("Add nginx param template")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/add"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def update_nginx_param(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修改nginx参数模板"""
        self.logger.info("Update nginx param template")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/update"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def query_all_nginx_param(self, param_type: str = "All") -> Dict[str, Any]:
        """查询nginx参数模板列表"""
        self.logger.info("Query all nginx param templates")
        url = f"/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/queryAll?type={param_type}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def update_nginx_param_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """nginx参数模板上线/下线接口"""
        self.logger.info("Update nginx param status")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/updateStatus"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def list_nginx_param(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分页查询nginx参数模板列表"""
        self.logger.info("List nginx param templates")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/list"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def delete_nginx_param_by_code(self, code: str, param_type: str) -> Dict[str, Any]:
        """根据nginx参数模板删除接口"""
        self.logger.info(f"Delete nginx param by code: {code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/nginxParam/deleteCode"
        payload = {"code": code, "type": param_type}
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def list_ingress_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """查询ingress网关实例信息-分页"""
        self.logger.info("List ingress instances")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/list"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def update_ingress_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修改ingress网关实例"""
        self.logger.info("Update ingress instance")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoad/update"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    # ==================== msingressksr Ingress网关实例启停扩缩容接口 ====================

    def start_ingress_instance_by_code(self, code: str, system_code: str, unit_code: str) -> Dict[str, Any]:
        """根据网关实例编码启动ingress网关实例"""
        self.logger.info(f"Start ingress instance by code: {code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadInstance/startCode"
        payload = {"code": code, "systemCode": system_code, "unitCode": unit_code}
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def stop_ingress_instance_by_code(self, code: str, system_code: str, unit_code: str) -> Dict[str, Any]:
        """根据网关实例编码停止ingress网关实例"""
        self.logger.info(f"Stop ingress instance by code: {code}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadInstance/stopCode"
        payload = {"code": code, "systemCode": system_code, "unitCode": unit_code}
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def scale_ingress_instance(self, instance_id: str, deploy_type: str, replicas: int) -> Dict[str, Any]:
        """ingress网关实例扩缩容"""
        self.logger.info(f"Scale ingress instance: {instance_id}")
        url = "/openapi/ms-ingress/microservice-ingress-console/openapi/tenant/v1/mesh/softLoadInstance/scale"
        payload = {"id": instance_id, "deployType": deploy_type, "replicas": replicas}
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    # ==================== msistiogateway Istio网关相关接口 ====================

    def add_gateway_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """新增入口网关实例"""
        self.logger.info("Add gateway instance")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/add"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def get_gateway_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """精确入口网关实例信息"""
        self.logger.info("Get gateway instance")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/getGatewayInstance"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def list_gateway_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """查询入口网关实例信息，分页展示"""
        self.logger.info("List gateway instances")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/list"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def update_gateway_instance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新入口网关实例"""
        self.logger.info("Update gateway instance")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/update"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def list_ingress_egress_gateway(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """查询网关实例信息，分页展示包含入口和出口网关"""
        self.logger.info("List ingress and egress gateway instances")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v1/mesh/gatewayinstance/ingressEgressList"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def add_gateway_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """新增网关规则"""
        self.logger.info("Add gateway rule")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/add"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def list_gateway_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """查询网关规则信息，分页展示"""
        self.logger.info("List gateway rules")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/list"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def get_gateway_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """精确查询网关配置信息"""
        self.logger.info("Get gateway rule")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/getGateway"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def update_gateway_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新网关规则"""
        self.logger.info("Update gateway rule")
        url = "/openapi/ms-mesh/microservice-mesh-console/openapi/tenant/v3/mesh/gateway/update"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    # ==================== mscmf CMF服务相关接口 ====================

    def batch_add_funcser(self, control_plane_code: str, funcsers: list) -> Dict[str, Any]:
        """批量新增单体服务SINGLE"""
        self.logger.info("Batch add funcser")
        url = "/openapi/ms-ubm/microservice-ubm/v2/funcser/batch"
        payload = {"controlPlaneCode": control_plane_code, "funcsers": funcsers}
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def batch_get_funcser(self, control_plane_code: str, application_code: str, funcser_codes: list) -> Dict[str, Any]:
        """根据服务编码批量精确查询服务信息"""
        self.logger.info("Batch get funcser")
        url = "/openapi/ms-ubm/microservice-ubm/v2/funcser/batch"
        payload = {"controlPlaneCode": control_plane_code, "applicationCode": application_code, "funcserCodes": funcser_codes}
        return self.get(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def add_cmf_degrade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """CMF新增降级配置"""
        self.logger.info("Add CMF degrade config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def get_cmf_degrade_detail(self, control_plane_name: str, env_code: str, func_ser_name: str) -> Dict[str, Any]:
        """CMF获取降级配置详情"""
        self.logger.info("Get CMF degrade detail")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade/detail"
        payload = {"controlPlaneName": control_plane_name, "envCode": env_code, "funcSerName": func_ser_name}
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def update_cmf_degrade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """CMF修改降级配置"""
        self.logger.info("Update CMF degrade config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade/update"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def update_cmf_degrade_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """CMF熔断配置上线或者下线"""
        self.logger.info("Update CMF degrade state")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade/updateState"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def delete_cmf_degrade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """CMF删除降级配置"""
        self.logger.info("Delete CMF degrade config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/degrade/delete"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def add_cmf_circuit_breaking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """CMF新增熔断配置"""
        self.logger.info("Add CMF circuit breaking config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    def get_cmf_circuit_breaking_detail(self, control_plane_name: str, env_code: str, func_ser_name: str) -> Dict[str, Any]:
        """CMF获取熔断配置详情"""
        self.logger.info("Get CMF circuit breaking detail")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking/detail"
        payload = {"controlPlaneName": control_plane_name, "envCode": env_code, "funcSerName": func_ser_name}
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def update_cmf_circuit_breaking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """CMF修改熔断配置"""
        self.logger.info("Update CMF circuit breaking config")
        url = "/openapi/ms-ubm/microservice-ubm/openapi/tenant/cmf/circuitBreaking/update"
        return self.post(endpoint=url, json=data, headers=_get_default_headers()).json()

    # ==================== msubm UBM相关接口 ====================

    def get_cells(self) -> Dict[str, Any]:
        """查询平面单元列表"""
        self.logger.info("Get cells list")
        url = "/openapi/ms-ubm/microservice-ubm/v2/cells"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def get_tenant_detail(self) -> Dict[str, Any]:
        """查询租户信息"""
        self.logger.info("Get tenant detail")
        url = "/openapi/ms-ubm/microservice-ubm/v2/tenant/detail"
        return self.get(endpoint=url, headers=_get_default_headers()).json()

    def batch_add_strategy(self, control_plane_code: str, strategies: list) -> Dict[str, Any]:
        """批量新增策略"""
        self.logger.info("Batch add strategy")
        url = "/openapi/ms-ubm/microservice-ubm/v2/strategy/batch"
        payload = {"controlPlaneCode": control_plane_code, "strategies": strategies}
        return self.post(endpoint=url, json=payload, headers=_get_default_headers()).json()

    def batch_update_strategy_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """批量更新策略状态"""
        self.logger.info("Batch update strategy status")
        url = "/openapi/ms-ubm/microservice-ubm/v2/strategy/clusterstatus"
        return self.put(endpoint=url, json=data, headers=_get_default_headers()).json()

    def get_strategy_batch_detail(self, batch_code: str) -> Dict[str, Any]:
        """批量更新策略状态进度查询"""
        self.logger.info(f"Get strategy batch detail: {batch_code}")
        url = f"/openapi/ms-ubm/microservice-ubm/v2/strategy/batch/detail/{batch_code}"
        return self.get(endpoint=url, headers=_get_default_headers()).json()