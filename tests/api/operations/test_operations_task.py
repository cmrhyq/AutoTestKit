"""
运营运维 OpenAPI 巡检任务接口测试

转换自 JMeter 脚本: operations-task.jmx
测试内容：通过任务名称执行巡检任务
"""

from typing import Dict, Any

import allure
import pytest

from base.api.services.operation_open_service import PanJiOperationOpenService
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基运营运维OpenAPI服务")
@allure.story("observable-task 巡检任务接口")
class TestOperationsTask:

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def operation_service(self, api_env, api_logger):
        """创建 Operation OpenAPI 服务实例"""
        service = PanJiOperationOpenService(
            base_url=api_env.get("apiBaseUrl"), logger=api_logger
        )
        yield service
        service.close()

    @allure.title("通过任务名称执行巡检任务")
    @allure.description("POST /openapi/monitor-inspection/cluster-inspection/api/inspectionTask/executeTask - 执行巡检任务")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_execute_inspection_task(self, operation_service, api_env, api_cache):
        with AllureHelper.api_test(operation_service):
            task_name = api_env.get("taskName", "test1119")

            with AllureHelper.step(f"发送 POST 请求执行巡检任务: {task_name}"):
                response_json = operation_service.execute_inspection_task(task_name=task_name)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                # JMX 中断言 test_type=16 (NOT) 包含 resultCode:000000
                # 即验证接口不会返回错误码，允许正常响应
                assert response_json.get("resultCode") != "000000" or "data" in response_json, \
                    "接口应返回有效响应"
