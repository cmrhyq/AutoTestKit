import logging
from typing import Dict, Any

from base import BaseService


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头"""
    return {
        "apikey": "67d5da7b76b1030ea6888f7644e05195",
    }


class PanJiPluginInnerService(BaseService):
    DEFAULT_BASE_URL = 'http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030'

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        """
        初始化 Panji Plugin InnerAPI 服务

        Args:
            base_url: API 基础 URL
            logger: 日志记录器
        """
        super().__init__(
            base_url=base_url or self.DEFAULT_BASE_URL,
            logger=logger
        )
        self.logger.info(f"Initializing PanJi Plugin InnerAPI Service with base_url: {self.base_url}")

    def get_plugin_install_count(self) -> Dict[str, Any]:
        """
        统计插件安装数量
        """
        self.logger.info(f"Getting Plugin Install Count")
        url = "/plugin/api/v1/plugin/list/instance"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()
