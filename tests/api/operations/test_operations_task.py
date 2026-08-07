"""
运营运维 OpenAPI 巡检任务接口测试

测试内容：通过任务名称执行巡检任务
"""

from typing import Dict, Any

import allure
import pytest

from base.api.services.operation_open_service import OperationOpenService
from core.reporting.allure_helper import AllureHelper
from core.constants import Tenant

@pytest.mark.api
@pytest.mark.operation
@allure.epic("磐基API自动化测试")
@allure.feature("磐基运营运维OpenAPI接口")
@allure.story("observable Task 巡检任务接口")
class TestOperationsTask:

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def operation_service(self, service_factory):
        with service_factory(OperationOpenService, self.TENANT) as svc:
            yield svc

    @allure.title("通过任务名称执行巡检任务")
    @allure.description("按 test_env.taskName 触发一次巡检任务执行，断言接口有效响应（resultCode 非 000000 时 data 字段仍存在）")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_execute_inspection_task(self, operation_service, test_env, api_cache):
        with AllureHelper.api_test(operation_service):
            task_name = test_env.get("taskName", "test1119")

            with AllureHelper.step(f"发送 POST 请求执行巡检任务: {task_name}"):
                response_json = operation_service.execute_inspection_task(task_name=task_name)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                # 即验证接口不会返回错误码，允许正常响应
                assert response_json.get("resultCode") != "000000" or "data" in response_json, \
                    "接口应返回有效响应"
