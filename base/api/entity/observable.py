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


@dataclass
class ObservableLogPublicParams(object):
    """
    可观测日志接口测试的公共参数集合。

    默认变量包含四元组（namespace/cluster/pod/container）、
    时间戳范围、日志上下文参数（log id / timestamp / offset / file_path / host_ip）等。

    Attributes:
        obs_namespace / obs_cluster_name / obs_pod_name / obs_container_name: 日志四元组
        obs_start_time / obs_end_time: 查询时间范围（ms 时间戳）
        obs_id / obs_timestamp / obs_offset: 上下文查询定位参数
        obs_log_file_path / obs_host_ip: 上下文查询的物理定位参数
        obs_component_type: 组件类型（默认 "app"）
        obs_size: 单次返回条数
    """
    obs_namespace: str
    obs_cluster_name: str
    obs_pod_name: str
    obs_container_name: str
    obs_start_time: int
    obs_end_time: int
    obs_id: str
    obs_timestamp: int
    obs_offset: int
    obs_log_file_path: str
    obs_host_ip: str
    obs_component_type: str = "app"
    obs_size: int = 1


__all__ = [
    "Log",
    "LogContext",
    "QueryModelConf",
    "ObservableLogPublicParams",
]
