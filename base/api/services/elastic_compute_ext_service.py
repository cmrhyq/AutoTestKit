"""
弹性计算 Extensions 服务封装（apikey 鉴权）

基于 auto_test_pro 的 auto-test/files/elastic-compute/extensions/*.jmx 转换：
- applications.jmx：查询应用服务列表

Extensions 类接口使用 apikey/username/tenantCode 三件头鉴权，
不需要走 Portal 登录、也不需要 Bearer Token。
所有敏感值均从 core.config.env_manager 的 yaml 配置读取，杜绝硬编码。
"""
from typing import Dict, Any

from base import BaseService
from config import get_env_config
from core import get_logger
from core.config import env_manager

logger = get_logger(__name__)


def _get_ext_headers() -> Dict[str, str]:
    """获取 Extensions 类接口的默认请求头。

    从 env yaml 中读取：
    - ec_apikey：apikey
    - basicAuthUsername：username
    - tenantCode：tenantCode
    """
    env = env_manager.get_config()
    return {
        "username": env.get("basicAuthUsername"),
        "tenantCode": env.get("tenantCode"),
    }


class ElasticComputeExtService(BaseService):
    """
    弹性计算 Extensions 服务（apikey 鉴权）

    与 openapi 类接口的区别：
    - 无需 Portal 登录 / Bearer Token
    - 通过 apikey + username + tenantCode 头进行鉴权
    - URL 前缀通常为 /elastic-compute/... 而非 /openapi/elastic-compute/...
    """

    def __init__(self, base_url: str):
        """
        初始化 PanJi 弹性计算 Extensions 服务

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
            auth_credentials={"api_key": get_env_config().get("ec_apikey")},
        )
        logger.info(
            f"Initializing PanJi ElasticCompute Extensions Service with base_url: {self.base_url}"
        )

    # ==================== applications 应用服务查询 ====================

    def search_app(self, kinds: str) -> Dict[str, Any]:
        """
        查询当前租户的所有应用服务信息。

        对应 JMX：弹性计算_extensions_applications_查询应用服务列表
        GET /elastic-compute/v2/searchApp?kinds=Deployment

        Args:
            kinds: 应用类型，如 "Deployment"、"StatefulSet" 等
        """
        logger.info(f"Search app with kinds: {kinds}")
        url = "/elastic-compute/server/v2/searchApp"
        params = {"kinds": kinds}
        response = self.get(endpoint=url, params=params, headers=_get_ext_headers())
        return response.json()
