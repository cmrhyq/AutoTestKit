import logging
from typing import Dict, Any

from base import BaseService
from config import env_manager


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头"""
    env = env_manager.get_config()
    return {
        "apikey": "67d5da7b76b1030ea6888f7644e05195",
        "username": env.get("basic_auth_username"),
        "tenantCode": env.get("tenant_code")
    }


class PanJiMicroservicesInnerService(BaseService):
    DEFAULT_BASE_URL = 'http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030'

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        """
        初始化 Panji Microservices InnerAPI 服务

        Args:
            base_url: API 基础 URL
            logger: 日志记录器
        """
        super().__init__(
            base_url=base_url or self.DEFAULT_BASE_URL,
            logger=logger
        )
        self.logger.info(f"Initializing PanJi Microservices InnerAPI Service with base_url: {self.base_url}")

    # ==================== ISTIO网关内部接口 ====================

    def kem_check(self, data: list) -> Dict[str, Any]:
        """
        统一校验接口
        Args: 
            data: list 校验数据
        """
        self.logger.info("KEM check")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/kem/check"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def kem_create(self, data: list) -> Dict[str, Any]:
        """
        统一创建接口
        Args:
            data: list 创建数据
        """
        self.logger.info("KEM create")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/kem/create"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def kem_delete(self, data: list) -> Dict[str, Any]:
        """
        统一删除接口
        Args:
            data: list 删除数据
        """
        self.logger.info("KEM delete")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/kem/delete"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def batch_create_secret(self, data: list) -> Dict[str, Any]:
        """
        批量上传证书
        Args:
            data: list 证书数据
        """
        self.logger.info("Batch create secret")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/kem/batchCreateSecret"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def list_virtual_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询虚拟服务列表
        Args:
            data: Dict 查询参数
        """
        self.logger.info("List virtual service")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/v2/mesh/virtualservice/list"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def get_virtual_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        精确查询虚拟服务信息
        Args:
            data: Dict 查询参数
        """
        self.logger.info("Get virtual service")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/v2/mesh/virtualservice/getVirtualService"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def add_virtual_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        新增虚拟服务
        Args:
            data: Dict 虚拟服务数据
        """
        self.logger.info("Add virtual service")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/v2/mesh/virtualservice/add"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def delete_virtual_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        删除虚拟服务
        Args:
            data: Dict 删除参数
        """
        self.logger.info("Delete virtual service")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/v2/mesh/virtualservice/delete"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()

    def get_gateway_name(self) -> Dict[str, Any]:
        """
        查询网关配置名称
        """
        self.logger.info("Get gateway name")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/v3/mesh/gateway/getGatewayName"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def list_node(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询节点列表
        Args:
            data: Dict 查询参数
        """
        self.logger.info("List node")
        url = "/ms-mesh/microservice-mesh-console/openapi/internal/v1/mesh/node/list"
        response = self.post(endpoint=url, json=data, headers=_get_default_headers())
        return response.json()
