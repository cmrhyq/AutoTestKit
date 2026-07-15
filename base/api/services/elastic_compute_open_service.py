"""
弹性计算 OpenAPI 服务封装（Bearer 鉴权）

基于 auto_test_pro 的 auto-test/files/elastic-compute/openapi/*.jmx 转换：
- cluster.jmx：集群管理生命周期
- namespace-api.jmx：分区管理
"""
import logging
from typing import Dict, Any

from base import BaseService
from core import DataCache


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头（走 Portal 登录得到的 Bearer Token）。"""
    cache = DataCache.get_instance()
    return {
        "Authorization": cache.get("token"),
    }


class PanJiElasticComputeOpenService(BaseService):
    """
    弹性计算 OpenAPI 服务

    - 走 Portal 的 Bearer Token（由 tests/api/conftest.py 的 get_token fixture 注入 cache["token"]）
    - base_url 由 api_env["api_base_url"] 提供
    """

    DEFAULT_BASE_URL = "http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030"

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        """
        初始化 PanJi 弹性计算 OpenAPI 服务

        Args:
            base_url: API 基础 URL
            logger: 日志记录器
        """
        super().__init__(
            base_url=base_url or self.DEFAULT_BASE_URL,
            logger=logger,
        )
        self.logger.info(
            f"Initializing PanJi ElasticCompute OpenAPI Service with base_url: {self.base_url}"
        )

    # ==================== cluster 集群管理接口 ====================

    def list_cluster_info_v1(self) -> Dict[str, Any]:
        """
        获取 paas 系统下集群列表信息（V1）。

        对应 JMX：弹性计算_openapi_cluster_获取paas系统下集群列表信息的接口
        GET /openapi/elastic-compute/v1/clusters/info
        """
        self.logger.info("List elastic-compute clusters info v1")
        url = "/openapi/elastic-compute/v1/clusters/info"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def list_cluster_info_v2(self) -> Dict[str, Any]:
        """
        获取运行面集群信息列表（V2）。

        对应 JMX：弹性计算_openapi_cluster_获取运行面集群信息列表V2
        GET /openapi/elastic-compute/v2/clusters/info
        """
        self.logger.info("List elastic-compute clusters info v2")
        url = "/openapi/elastic-compute/v2/clusters/info"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== namespace 分区管理接口 ====================

    def list_namespaces(self, cell_code: str) -> Dict[str, Any]:
        """
        查询指定单元下的 Namespace 列表。

        对应 JMX：弹性计算_openapi_namespace_查询NamespaceList
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems

        Args:
            cell_code: 单元编码
        """
        self.logger.info(f"List namespaces of cell: {cell_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_namespace_detail(self, cell_code: str, sys_code: str) -> Dict[str, Any]:
        """
        查询指定单元下指定系统 Namespace 详情。

        对应 JMX：弹性计算_openapi_namespace_查询Namespace详情
        GET /openapi/elastic-compute/v2/cells/{cellCode}/systems/{sysCode}

        Args:
            cell_code: 单元编码
            sys_code: 系统编码
        """
        self.logger.info(f"Get namespace detail: cell={cell_code}, sys={sys_code}")
        url = f"/openapi/elastic-compute/v2/cells/{cell_code}/systems/{sys_code}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()
