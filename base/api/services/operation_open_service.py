import logging
from typing import Dict, Any

from base import BaseService
from core import DataCache


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头"""
    cache = DataCache.get_instance()
    return {
        "Authorization": cache.get("token"),
    }


class PanJiOperationOpenService(BaseService):
    DEFAULT_BASE_URL = 'http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030'

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        """
        初始化 Panji Operation OpenAPI 服务

        Args:
            base_url: API 基础 URL
            logger: 日志记录器
        """
        super().__init__(
            base_url=base_url or self.DEFAULT_BASE_URL,
            logger=logger
        )
        self.logger.info(f"Initializing PanJi Operation OpenAPI Service with base_url: {self.base_url}")

    def query_alarms_number_three(self):
        """
        查询最近3小时指定告警数量
        """
        self.logger.info("Query the number of specified alarms in the last 3 hours")
        url = "/openapi/monitor-inspection/cluster-inspection/api/alertLabelsFiring/selectRecentAlerts"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def query_interface_synthetic_log(self, log_id: int) -> Dict[str, Any]:
        """
        查询接口拨测日志详情

        Args:
            log_id: 日志ID, 运营运维/云拨测/任务分析页面，找接口编排的数据id=15174
        """
        self.logger.info(f"Query interface synthetic log detail, id: {log_id}")
        url = "/openapi/monitor-inspection/cluster-inspection/api/synthetic/interface/log"
        response = self.get(endpoint=url, params={"id": log_id}, headers=_get_default_headers())
        return response.json()

    def query_service_synthetic_log(self, log_id: int) -> Dict[str, Any]:
        """
        查询服务拨测日志详情

        Args:
            log_id: 日志ID
        """
        self.logger.info(f"Query service synthetic log detail, id: {log_id}")
        url = "/openapi/monitor-inspection/cluster-inspection/api/synthetic/service/log"
        response = self.get(endpoint=url, params={"id": log_id}, headers=_get_default_headers())
        return response.json()

    def batch_query_metrics(self, metrics: list, step_seconds: int = 1) -> Dict[str, Any]:
        """
        通过promql对象批量查询指标

        Args:
            metrics: 指标列表，每个元素包含 promql, range, startTime, endTime
            step_seconds: 步长秒数，默认1
            for example:
            {
              "metrics": [
                {
                  "promql": "up{job='kube_svc_redis-exporter'}[30m]",
                  "range": "0-1",
                  "startTime": "",
                  "endTime": ""
                }
              ],
              "stepSeconds": 1
            }
        """
        self.logger.info(f"Batch query metrics, count: {len(metrics)}")
        url = "/openapi/monitor-inspection/cluster-inspection/api/component/batchQuery"
        payload = {
            "metrics": metrics,
            "stepSeconds": step_seconds
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def execute_inspection_task(self, task_name: str) -> Dict[str, Any]:
        """
        通过任务名称执行巡检任务

        Args:
            task_name: 任务名称
        """
        self.logger.info(f"Execute inspection task: {task_name}")
        url = "/openapi/monitor-inspection/cluster-inspection/api/inspectionTask/executeTask"
        payload = {"taskName": task_name}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()
