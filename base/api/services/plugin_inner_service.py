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
        """
        logger.info(f"Getting Plugin Install Count")
        url = "/plugin/server/api/v1/plugin/list/instance"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()
