"""
插件 OpenAPI 服务封装（Bearer 鉴权）

面向磐基（PanJi）插件市场 / 插件管理平台的 **对外开放接口** 客户端，覆盖插件元信息、
安装信息、MCP 任务校验等场景。

业务域覆盖：
- 插件安装信息查询（按插件名）
- 当前环境插件版本数据上报
- MCP 任务配置与特性校验
- 权限转移能力查询

鉴权：`Authorization: Bearer <token>`
      （由测试层 `service_factory` 从 `TokenManager` 注入）。
URL 前缀：`/openapi/plugin-mgmt/api/v1/...`。
"""
from typing import Dict, Any, Optional

from base import BaseService
from core import get_logger

logger = get_logger(__name__)


class PluginOpenService(BaseService):
    """
    插件 OpenAPI 服务（对外开放接口）。

    - 鉴权：`Authorization: Bearer <token>`
      （由测试层 `service_factory` 从 `TokenManager` 注入）
    - URL 前缀：`/openapi/plugin-mgmt/api/v1/...`
    - base_url：由 fixture `test_env["apiBaseUrl"]` 提供，必传
    """

    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        初始化 Panji Plugin OpenAPI 服务

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
                "and pass via fixture: test_env.get('apiBaseUrl')"
            )
        super().__init__(
            base_url=base_url,
            auth_type="bearer" if token else None,
            auth_credentials={"token": token} if token else None,
        )
        logger.info(f"Initializing PanJi Plugin OpenAPI Service with base_url: {self.base_url}")

    def get_plugin_install_info(self, plugin_name: str) -> Dict[str, Any]:
        """
        统计插件安装信息
        GET /openapi/plugin-mgmt/api/v1/plugin/{plugin_name}/installationInfo
        Args:
            plugin_name: 插件名称
        """
        logger.info(f"Getting Plugin Install Information")
        url = f"/openapi/plugin-mgmt/api/v1/plugin/{plugin_name}/installationInfo"
        response = self.get(endpoint=url)
        return response.json()

    def get_current_env_list(self) -> Dict[str, Any]:
        """
        获取当前环境插件数据
        GET /openapi/plugin-mgmt/api/v1/plugin/version/data-report
        """
        logger.info(f"Getting Current Environment Plugins List")
        url = f"/openapi/plugin-mgmt/api/v1/plugin/version/data-report"
        response = self.get(endpoint=url)
        return response.json()

    def verify_task_config(self):
        """
        验证任务配置
        POST /openapi/plugin-mgmt/api/v1/mcp/validate/task
        """
        logger.info(f"Verifying Task Config")
        url = f"/openapi/plugin-mgmt/api/v1/mcp/validate/task"
        entity = {
            "type": "kubernetes",
            "content": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: example-config\ndata:\n  config.yaml: |\n    key: value"
        }
        response = self.post(
            endpoint=url, body=entity
        )
        return response.json()

    def verify_task_feature(self):
        """
        验证任务feature
        POST /openapi/plugin-mgmt/api/v1/mcp/validate/feature
        """
        logger.info(f"Verifying Task Feature")
        url = f"/openapi/plugin-mgmt/api/v1/mcp/validate/feature"
        entity = {
            "type": "feature",
            "content": "name: example-feature\ndescription: 示例特性\ntype: menu\nposition: /admin/plugins"
        }
        response = self.post(
            endpoint=url, body=entity
        )
        return response.json()

    def get_plugin_support_permission_transfer(self):
        """
        获取所有支持权限转让的插件
        GET /openapi/plugin-mgmt/api/v1/auth-transfer/all
        """
        logger.info(f"Get All Plugins That Support Permission Transfer")
        url = f"/openapi/plugin-mgmt/api/v1/auth-transfer/all"
        response = self.get(endpoint=url)
        return response.json()
