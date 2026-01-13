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


class PanJiPluginOpenService(BaseService):
    DEFAULT_BASE_URL = 'http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030'

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        """
        初始化 Panji Plugin OpenAPI 服务

        Args:
            base_url: API 基础 URL
            logger: 日志记录器
        """
        super().__init__(
            base_url=base_url or self.DEFAULT_BASE_URL,
            logger=logger
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
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_current_env_list(self) -> Dict[str, Any]:
        """
        获取当前环境插件数据
        """
        self.logger.info(f"Getting Current Environment Plugins List")
        url = f"/openapi/plugin-mgmt/api/v1/plugin/version/data-report"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def verify_task_config(self):
        """
        验证任务配置
        """
        self.logger.info(f"Verifying Task Config")
        url = f"/openapi/plugin-mgmt/api/v1/mcp/validate/task"
        body = {
            "type": "kubernetes",
            "content": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: example-config\ndata:\n  config.yaml: |\n    key: value"
        }
        response = self.post(endpoint=url, body=body, headers=_get_default_headers())
        return response.json()

    def verify_task_feature(self):
        """
        验证任务feature
        """
        self.logger.info(f"Verifying Task Feature")
        url = f"/openapi/plugin-mgmt/api/v1/mcp/validate/feature"
        body = {
            "type": "feature",
            "content": "name: example-feature\ndescription: 示例特性\ntype: menu\nposition: /admin/plugins"
        }
        response = self.post(endpoint=url, body=body, headers=_get_default_headers())
        return response.json()

    def get_plugin_support_permission_transfer(self):
        """
        获取所有支持权限转让的插件
        """
        self.logger.info(f"Get All Plugins That Support Permission Transfer")
        url = f"/openapi/plugin-mgmt/api/v1/auth-transfer/all"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()
