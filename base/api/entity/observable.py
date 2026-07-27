"""
Observable（可观测）相关实体模型。

- Log: 日志查询请求参数
- LogContext: 日志上下文查询请求参数
- QueryModelConf: 模型配置查询参数
"""

from dataclasses import dataclass


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


__all__ = [
    "Log",
    "LogContext",
    "QueryModelConf",
]
