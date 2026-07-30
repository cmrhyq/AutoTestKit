"""
Operation（运营运维）相关实体模型。

- MetricQuery: 批量指标查询接口中，单个 PromQL 指标查询的请求参数。
  用于 operation_open_service.batch_query_metrics()。
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class MetricQuery(object):
    """
    单个 PromQL 指标查询参数。

    promql: PromQL 查询语句，例如 "up{job='kube_svc_redis-exporter'}[30m]"
    range: 查询区间，例如 "0-1"
    start_time: 起始时间戳，默认空字符串（由服务端根据 range 推断）
    end_time: 结束时间戳，默认空字符串（由服务端根据 range 推断）
    """
    promql: str
    range: str
    start_time: str = ""
    end_time: str = ""

    def to_payload(self) -> Dict[str, Any]:
        """转换为接口请求所需的驼峰命名字典结构。"""
        return {
            "promql": self.promql,
            "range": self.range,
            "startTime": self.start_time,
            "endTime": self.end_time,
        }


__all__ = [
    "MetricQuery",
]
