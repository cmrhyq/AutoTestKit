import logging
from typing import Dict, Any, Optional

from base import BaseService
from base.api.entity.plugin import McpValidatePayload


class PluginOpenService(BaseService):

    def __init__(self, base_url: str, logger: logging.Logger = None, token: Optional[str] = None):
        """
        初始化 Panji Plugin OpenAPI 服务

        Args:
            base_url: API 基础 URL（必传，来自 config/env_*.yaml 的 apiBaseUrl）
            logger: 日志记录器

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
            logger=logger,
            auth_type="bearer" if token else None,
            auth_credentials={"token": token} if token else None,
        )
        self.logger.info(f"Initializing PanJi Plugin OpenAPI Service with base_url: {self.base_url}")

    def get_plugin_install_info(self, plugin_name: str) -> Dict[str, Any]:
        """
        统计插件安装信息
        Args:
            plugin_name: 插件名称
        """
        self.logger.info(f"Getting Plugin Install Information")
        url = f"/openapi/plugin-mgmt/api/v1/plugin/{plugin_name}/installationInfo"
        response = self.get(endpoint=url)
        return response.json()

    def get_current_env_list(self) -> Dict[str, Any]:
        """
        获取当前环境插件数据
        """
        self.logger.info(f"Getting Current Environment Plugins List")
        url = f"/openapi/plugin-mgmt/api/v1/plugin/version/data-report"
        response = self.get(endpoint=url)
        return response.json()

    def verify_task_config(self, payload: McpValidatePayload = None):
        """
        验证任务配置

        Args:
            payload: MCP 校验请求实体，默认使用 McpValidatePayload.default_task()
        """
        self.logger.info(f"Verifying Task Config")
        url = f"/openapi/plugin-mgmt/api/v1/mcp/validate/task"
        entity = payload or McpValidatePayload.default_task()
        response = self.post(
            endpoint=url, body=entity.to_payload()
        )
        return response.json()

    def verify_task_feature(self, payload: McpValidatePayload = None):
        """
        验证任务feature

        Args:
            payload: MCP 校验请求实体，默认使用 McpValidatePayload.default_feature()
        """
        self.logger.info(f"Verifying Task Feature")
        url = f"/openapi/plugin-mgmt/api/v1/mcp/validate/feature"
        entity = payload or McpValidatePayload.default_feature()
        response = self.post(
            endpoint=url, body=entity.to_payload()
        )
        return response.json()

    def get_plugin_support_permission_transfer(self):
        """
        获取所有支持权限转让的插件
        """
        self.logger.info(f"Get All Plugins That Support Permission Transfer")
        url = f"/openapi/plugin-mgmt/api/v1/auth-transfer/all"
        response = self.get(endpoint=url)
        return response.json()
