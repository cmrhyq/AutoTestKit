import logging
from dataclasses import dataclass
from typing import Dict, Any

from base import BaseService
from core import DataCache


@dataclass
class Log(object):
    """
    namespace: 命名空间
    cluster_name: 集群名称
    pod_name: Pod名称
    container_name: 容器名称
    start_time: 开始时间戳
    end_time: 结束时间戳
    component_type: 组件类型，默认app
    sync: 是否同步，默认false
    size: 返回数量，默认100
    """
    namespace: str
    cluster_name: str
    pod_name: str
    container_name: str
    start_time: int
    end_time: int
    component_type: str = "app"
    sync: bool = False
    size: int = 100

@dataclass
class LogContext(object):
    """
    log_id: 日志ID
    timestamp: 时间戳
    offset: 偏移量
    log_file_path: 日志文件路径
    host_ip: 主机IP
    namespace: 命名空间
    cluster_name: 集群名称
    pod_name: Pod名称
    container_name: 容器名称
    sync: 是否同步
    size: 返回数量
    """
    log_id: str
    timestamp: int
    offset: int
    log_file_path: str
    host_ip: str
    namespace: str
    cluster_name: str
    pod_name: str
    container_name: str
    sync: bool = False
    size: int = 100

@dataclass
class QueryModelConf(object):
    """
    page: 页码
    per_page: 每页数量
    with_logo: 是否包含logo
    with_props: 是否包含属性
    with_relations: 是否包含关系
    with_graph: 是否包含图
    with_confs_count: 是否包含配置数量
    """
    page: int = 1,
    per_page: int = 10,
    with_logo: bool = True,
    with_props: bool = True,
    with_relations: bool = True,
    with_graph: bool = True,
    with_confs_count: bool = True


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头"""
    cache = DataCache.get_instance()
    return {
        "Authorization": cache.get("token"),
    }


class PanJiObservableOpenService(BaseService):
    DEFAULT_BASE_URL = 'http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030'

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        """
        初始化 Panji Observable OpenAPI 服务

        Args:
            base_url: API 基础 URL
            logger: 日志记录器
        """
        super().__init__(
            base_url=base_url or self.DEFAULT_BASE_URL,
            logger=logger
        )
        self.logger.info(f"Initializing PanJi Observable OpenAPI Service with base_url: {self.base_url}")

    # ==================== observable-log 日志相关接口 ====================

    def query_log_by_quadruple(self, log: Log) -> Dict[str, Any]:
        """
        根据四元组检索日志

        Args:
            log: 日志数据类
        """
        self.logger.info(f"Query log by quadruple: {log.namespace}/{log.cluster_name}/{log.pod_name}/{log.container_name}")
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
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    def pull_log_by_request_id(self, request_id: str) -> Dict[str, Any]:
        """
        根据日志检索requestId轮询拉取日志列表

        Args:
            request_id: 请求ID
        """
        self.logger.info(f"Pull log by request_id: {request_id}")
        url = "/openapi/monitor-o11y/webgate-log-console/3rd/log/pull"
        params = {"requestId": request_id}
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    def query_log_context(self, context: LogContext) -> Dict[str, Any]:
        """
        查询日志上下文

        Args:
            context：日志上下文
        """
        self.logger.info(f"Query log context, id: {context.log_id}")
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
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    def pull_log_context_by_request_id(self, request_id: str) -> Dict[str, Any]:
        """
        根据上下文检索requestId获取上下文日志列表

        Args:
            request_id: 上下文请求ID
        """
        self.logger.info(f"Pull log context by request_id: {request_id}")
        url = "/openapi/monitor-o11y/webgate-log-console/3rd/log/context/pull"
        params = {"requestId": request_id}
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    # ==================== observable-query 模型相关接口 ====================

    def query_models(self, config: QueryModelConf) -> Dict[str, Any]:
        """
        查询模型列表

        Args:
            config: 查询配置
        """
        self.logger.info(f"Query models, page: {config.page}, per_page: {config.per_page}")
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
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    def get_model_by_id_or_name(self, model_id_or_name: str) -> Dict[str, Any]:
        """
        根据ID或名称获取模型

        Args:
            model_id_or_name: 模型ID或名称
        """
        self.logger.info(f"Get model by id or name: {model_id_or_name}")
        url = f"/openapi/monitor-o11y/amdb-console/publish/v3/confs/models/{model_id_or_name}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def search_conf_items(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        配置项结构化查询

        Args:
            query: 查询条件对象
        """
        self.logger.info("Search conf items")
        url = "/openapi/monitor-o11y/amdb-console/publish/v3/confs/search/conf-items"
        response = self.get(endpoint=url, json=query, headers=_get_default_headers())
        return response.json()