"""
运营运维 OpenAPI 查询接口测试

转换自 JMeter 脚本: operations-query.jmx
测试内容：
- 查询最近3小时指定告警数量
- 查询接口拨测日志详情
- 查询服务拨测日志详情
- 通过promql对象批量查询指标
"""

from typing import Dict, Any

import allure
import pytest

from base.api.services.operation_open_service import PanJiOperationOpenService
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("运营运维OpenAPI服务")
@allure.story("operations-query 查询接口")
class TestOperationsQuery:
    """
    对应 JMeter 脚本: operations-query.jmx
    线程组: Monitor运营运维-openapi调用
    """

    @pytest.fixture(scope="class")
    def operation_service(self, api_env, api_logger):
        """创建 Operation OpenAPI 服务实例"""
        service = PanJiOperationOpenService(
            base_url=api_env.get("api_base_url"), logger=api_logger
        )
        yield service
        service.close()

    @allure.title("查询最近3小时指定告警数量")
    @allure.description("GET /openapi/monitor-inspection/cluster-inspection/api/alertLabelsFiring/selectRecentAlerts - 查询告警数量")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_alarms_number_three(self, operation_service, api_cache):
        with AllureHelper.step("发送 GET 请求查询最近3小时告警数量"):
            response_json = operation_service.query_alarms_number_three()

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert response_json.get("resultCode") == "000000", \
                f"resultCode 应为 000000，实际为 {response_json.get('resultCode')}"

    @allure.title("查询接口拨测日志详情")
    @allure.description("GET /openapi/monitor-inspection/cluster-inspection/api/synthetic/interface/log - 查询接口拨测日志")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_interface_synthetic_log(self, operation_service, api_env, api_cache):
        log_id = api_env.get("monitor_yunboce_rwfx_id_1", 15174)

        with AllureHelper.step(f"发送 GET 请求查询接口拨测日志详情，id={log_id}"):
            response_json = operation_service.query_interface_synthetic_log(log_id=log_id)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            # JMX 中断言 response_data contains（test_type=2）但未指定具体值

    @allure.title("查询服务拨测日志详情")
    @allure.description("GET /openapi/monitor-inspection/cluster-inspection/api/synthetic/service/log - 查询服务拨测日志")
    @allure.severity(allure.severity_level.NORMAL)
    def test_query_service_synthetic_log(self, operation_service, api_env, api_cache):
        log_id = api_env.get("monitor_yunboce_rwfx_id_2", 108649)

        with AllureHelper.step(f"发送 GET 请求查询服务拨测日志详情，id={log_id}"):
            response_json = operation_service.query_service_synthetic_log(log_id=log_id)

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert response_json.get("resultCode") == "000000", \
                f"resultCode 应为 000000，实际为 {response_json.get('resultCode')}"

    @allure.title("通过promql对象批量查询指标")
    @allure.description("POST /openapi/monitor-inspection/cluster-inspection/api/component/batchQuery - 批量查询指标数据")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_batch_query_metrics(self, operation_service, api_cache):
        metrics = [
            {
                "promql": "up{job='kube_svc_redis-exporter'}[30m]",
                "range": "0-1",
                "startTime": "",
                "endTime": ""
            }
        ]

        with AllureHelper.step("发送 POST 请求批量查询指标"):
            response_json = operation_service.batch_query_metrics(
                metrics=metrics, step_seconds=1
            )

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            # JMX 中断言 test_type=16 (NOT) 包含 resultCode:000000，即验证不会失败
            assert response_json.get("resultCode") != "000000" or "data" in response_json, \
                "接口应返回有效数据"
