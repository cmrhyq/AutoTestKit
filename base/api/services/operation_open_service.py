from typing import Dict, Any, List, Optional, Union

from base import BaseService
from base.api.entity.operation import MetricQuery
from core import get_logger

logger = get_logger(__name__)


class OperationOpenService(BaseService):

    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        初始化 Panji Operation OpenAPI 服务

        Args:
            base_url: API 基础 URL（必传，来自 config/env_*.yaml 的 apiBaseUrl）
            token: Bearer Token

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
            auth_type="bearer" if token else None,
            auth_credentials={"token": token} if token else None,
        )
        logger.info(f"Initializing PanJi Operation OpenAPI Service with base_url: {self.base_url}")

    def query_alarms_number_three(self):
        """
        查询最近3小时指定告警数量
        GET /openapi/monitor-inspection/cluster-inspection/api/alertLabelsFiring/selectRecentAlerts
        """
        logger.info("Query the number of specified alarms in the last 3 hours")
        url = "/openapi/monitor-inspection/cluster-inspection/api/alertLabelsFiring/selectRecentAlerts"
        response = self.get(endpoint=url)
        return response.json()

    def query_interface_synthetic_log(self, log_id: int) -> Dict[str, Any]:
        """
        查询接口拨测日志详情
        GET /openapi/monitor-inspection/cluster-inspection/api/synthetic/interface/log
        Args:
            log_id: 日志ID, 运营运维/云拨测/任务分析页面，找接口编排的数据id=15174
        """
        logger.info(f"Query interface synthetic log detail, id: {log_id}")
        url = "/openapi/monitor-inspection/cluster-inspection/api/synthetic/interface/log"
        response = self.get(endpoint=url, params={"id": log_id})
        return response.json()

    def query_service_synthetic_log(self, log_id: int) -> Dict[str, Any]:
        """
        查询服务拨测日志详情
        GET /openapi/monitor-inspection/cluster-inspection/api/synthetic/service/log
        Args:
            log_id: 日志ID
        """
        logger.info(f"Query service synthetic log detail, id: {log_id}")
        url = "/openapi/monitor-inspection/cluster-inspection/api/synthetic/service/log"
        response = self.get(endpoint=url, params={"id": log_id})
        return response.json()

    def batch_query_metrics(
        self,
        metrics: List[Union[MetricQuery, Dict[str, Any]]],
        step_seconds: int = 1,
    ) -> Dict[str, Any]:
        """
        通过promql对象批量查询指标
        POST /openapi/monitor-inspection/cluster-inspection/api/component/batchQuery
        Args:
            metrics: 指标列表，元素为 MetricQuery 实体或等价的 dict
                     （包含 promql, range, startTime, endTime）
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
        logger.info(f"Batch query metrics, count: {len(metrics)}")
        url = "/openapi/monitor-inspection/cluster-inspection/api/component/batchQuery"
        normalized_metrics: List[Dict[str, Any]] = [
            m.to_payload() if isinstance(m, MetricQuery) else m for m in metrics
        ]
        payload = {
            "metrics": normalized_metrics,
            "stepSeconds": step_seconds
        }
        response = self.post(endpoint=url, json=payload)
        return response.json()

    def execute_inspection_task(self, task_name: str) -> Dict[str, Any]:
        """
        通过任务名称执行巡检任务
        POST /openapi/monitor-inspection/cluster-inspection/api/inspectionTask/executeTask
        Args:
            task_name: 任务名称
        """
        logger.info(f"Execute inspection task: {task_name}")
        url = "/openapi/monitor-inspection/cluster-inspection/api/inspectionTask/executeTask"
        payload = {"taskName": task_name}
        response = self.post(endpoint=url, json=payload)
        return response.json()
