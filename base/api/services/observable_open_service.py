"""
可观测 OpenAPI 服务封装（Bearer 鉴权）

面向磐基（PanJi）可观测平台的 **对外开放接口** 客户端，覆盖日志检索与查询模型管理。

业务域覆盖：
- observable-log：四元组（namespace/cluster/pod/container）日志检索、日志拉取、
  日志上下文回溯
- observable-query：查询模型配置管理（新建 / 更新 / 列表 / 删除）

鉴权：`Authorization: Bearer <token>`
      （由测试层 `service_factory` 从 `TokenManager` 注入，必传）。
URL 前缀：`/openapi/monitor-o11y/webgate-log-console/3rd/log/...`
        与 `/openapi/monitor-o11y/webgate-log-console/3rd/query/...`。
"""
from typing import Dict, Any, Optional

from base import BaseService

from base.api.entity.observable import (
    Log,
    LogContext,
    QueryModelConf,
)
from core import get_logger

logger = get_logger(__name__)


class ObservableOpenService(BaseService):
    """
    可观测 OpenAPI 服务（对外开放接口）。

    - 鉴权：`Authorization: Bearer <token>`
      （由测试层 `service_factory` 从 `TokenManager` 注入，必传）
    - URL 前缀：`/openapi/monitor-o11y/webgate-log-console/3rd/...`
    - base_url：由 fixture `test_env["apiBaseUrl"]` 提供，必传
    """

    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        初始化 Panji Observable OpenAPI 服务

        Args:
            base_url: API 基础 URL（必传，来自 config/env_*.yaml 的 apiBaseUrl）
            token: Bearer Token（必传，由 service_factory 从 TokenManager 注入）

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
        logger.info(f"Initializing PanJi Observable OpenAPI Service with base_url: {self.base_url}")

    # ==================== observable-log 日志相关接口 ====================

    def query_log_by_quadruple(self, log: Log) -> Dict[str, Any]:
        """
        根据四元组检索日志
        GET /openapi/monitor-o11y/webgate-log-console/3rd/log/query
        Args:
            log: 日志数据类
        """
        logger.info(f"Query log by quadruple: {log.namespace}/{log.cluster_name}/{log.pod_name}/{log.container_name}")
        url = "/openapi/monitor-o11y/webgate-log-console/3rd/log/query"
        params = {
            "resource.k8s.namespace": log.namespace,
            "resource.k8s.cluster.name": log.cluster_name,
            "resource.k8s.pod.name": log.pod_name,
            "resource.k8s.container.name": log.container_name,
            "componentType": log.component_type,
            "sync": str(log.sync).lower(),
            "startTime": log.start_time,
            "endTime": log.end_time,
            "size": log.size
        }
        response = self.get(endpoint=url, params=params)
        return response.json()

    def pull_log_by_request_id(self, request_id: str) -> Dict[str, Any]:
        """
        根据日志检索requestId轮询拉取日志列表
        GET /openapi/monitor-o11y/webgate-log-console/3rd/log/pull
        Args:
            request_id: 请求ID
        """
        logger.info(f"Pull log by request_id: {request_id}")
        url = "/openapi/monitor-o11y/webgate-log-console/3rd/log/pull"
        params = {"requestId": request_id}
        response = self.get(endpoint=url, params=params)
        return response.json()

    def query_log_context(self, context: LogContext) -> Dict[str, Any]:
        """
        查询日志上下文
        GET /openapi/monitor-o11y/webgate-log-console/3rd/log/context
        Args:
            context：日志上下文
        """
        logger.info(f"Query log context, id: {context.log_id}")
        url = "/openapi/monitor-o11y/webgate-log-console/3rd/log/context"
        params = {
            "_id": context.log_id,
            "timestamp": context.timestamp,
            "attributes.offset": context.offset,
            "attributes.log.file.path": context.log_file_path,
            "properties.host_ip": context.host_ip,
            "resource.k8s.namespace": context.namespace,
            "resource.k8s.cluster.name": context.cluster_name,
            "resource.k8s.pod.name": context.pod_name,
            "resource.k8s.container.name": context.container_name,
            "sync": str(context.sync).lower(),
            "size": context.size
        }
        response = self.get(endpoint=url, params=params)
        return response.json()

    def pull_log_context_by_request_id(self, request_id: str) -> Dict[str, Any]:
        """
        根据上下文检索requestId获取上下文日志列表
        GET /openapi/monitor-o11y/webgate-log-console/3rd/log/context/pull
        Args:
            request_id: 上下文请求ID
        """
        logger.info(f"Pull log context by request_id: {request_id}")
        url = "/openapi/monitor-o11y/webgate-log-console/3rd/log/context/pull"
        params = {"requestId": request_id}
        response = self.get(endpoint=url, params=params)
        return response.json()

    # ==================== observable-query 模型相关接口 ====================

    def query_models(self, config: QueryModelConf) -> Dict[str, Any]:
        """
        查询模型列表
        GET /openapi/monitor-o11y/amdb-console/publish/v3/confs/models
        Args:
            config: 查询配置
        """
        logger.info(f"Query models, page: {config.page}, per_page: {config.per_page}")
        url = "/openapi/monitor-o11y/amdb-console/publish/v3/confs/models"
        params = {
            "page": config.page,
            "per_page": config.per_page,
            "with_logo": str(config.with_logo).lower(),
            "with_props": str(config.with_props).lower(),
            "with_relations": str(config.with_relations).lower(),
            "with_graph": str(config.with_graph).lower(),
            "with_confs_count": str(config.with_confs_count).lower()
        }
        response = self.get(endpoint=url, params=params)
        return response.json()

    def get_model_by_id_or_name(self, model_id_or_name: str) -> Dict[str, Any]:
        """
        根据ID或名称获取模型
        GET /openapi/monitor-o11y/amdb-console/publish/v3/confs/models/{model_id_or_name}
        Args:
            model_id_or_name: 模型ID或名称
        """
        logger.info(f"Get model by id or name: {model_id_or_name}")
        url = f"/openapi/monitor-o11y/amdb-console/publish/v3/confs/models/{model_id_or_name}"
        response = self.get(endpoint=url)
        return response.json()

    def search_conf_items(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        配置项结构化查询
        POST /openapi/monitor-o11y/amdb-console/publish/v3/confs/search/conf-items
        Args:
            query: 查询条件对象
        """
        logger.info("Search conf items")
        url = "/openapi/monitor-o11y/amdb-console/publish/v3/confs/search/conf-items"
        response = self.post(endpoint=url, json=query)
        return response.json()