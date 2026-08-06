"""
插件 InnerAPI 服务封装（apikey 鉴权）

面向磐基（PanJi）插件管理平台的 **内部接口** 客户端，与对外 `plugin_open` 系统互补，
供门户后台聚合展示等场景使用。

业务域覆盖：
- 插件安装数量统计

鉴权：`apikey` 请求头（硬编码为固定值，供 Portal 后台集成使用）
      + `x-app-id: portal` 应用标识。
URL 前缀：`/plugin/server/api/v1/...`（无 `/openapi/` 前缀）。
"""
from typing import Dict, Any

from base import BaseService
from core import get_logger

logger = get_logger(__name__)


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头"""
    return {
        "x-app-id": "portal",
    }


class PluginInnerService(BaseService):
    """
    插件 InnerAPI 服务（内部接口）。

    - 鉴权：`apikey` 请求头（静态值，供 Portal 后台集成）+ `x-app-id: portal`
    - URL 前缀：`/plugin/server/api/v1/...`
    - base_url：由 fixture `api_env["apiBaseUrl"]` 提供，必传
    """

    def __init__(self, base_url: str):
        """
        初始化 Panji Plugin InnerAPI 服务

        Args:
            base_url: API 基础 URL（必传，来自 config/env_*.yaml 的 apiBaseUrl）

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
            auth_type="api_key",
            auth_credentials={
                "api_key": "67d5da7b76b1030ea6888f7644e05195",
                "header_name": "apikey"
            },
        )
        logger.info(f"Initializing PanJi Plugin InnerAPI Service with base_url: {self.base_url}")

    def get_plugin_install_count(self) -> Dict[str, Any]:
        """
        统计插件安装数量
        GET /plugin/server/api/v1/plugin/list/instance
        """
        logger.info(f"Getting Plugin Install Count")
        url = "/plugin/server/api/v1/plugin/list/instance"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()
