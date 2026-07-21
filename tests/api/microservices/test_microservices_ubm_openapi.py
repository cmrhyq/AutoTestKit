"""
微服务 UBM OpenAPI 接口测试脚本

基于 JMeter auto_test_pro/auto-test/files/microservices/openapi/msubm.jmx 转换。
覆盖 UBM 相关 5 个用例：
- 查询平面单元列表
- 查询租户信息
- 批量新增策略
- 批量更新策略状态
- 批量更新策略状态进度查询
"""
from typing import Dict

import allure
import pytest

from base.api.services.microservices_open_service import (
    PanJiMicroservicesOpenService,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基微服务 UBM OpenAPI 服务")
@allure.story("Microservices UBM OpenAPI 接口测试")
class TestMicroservicesUbmOpenApi:
    """
    Microservices UBM OpenAPI 测试

    数据流：批量新增策略 → 批量更新策略状态（返回 batchCode）→ 批量查询状态进度
    """

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def ubm_service(self, api_env, api_logger):
        """创建 Microservices OpenAPI 服务实例"""
        service = PanJiMicroservicesOpenService(
            base_url=api_env.get("api_base_url"),
            logger=api_logger,
        )
        yield service
        service.close()

    # ==================== UBM 查询接口 ====================

    @allure.title("查询平面单元列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_cells(self, ubm_service):
        with AllureHelper.api_test(ubm_service):
            with AllureHelper.step("发送 GET 请求查询平面单元列表"):
                response_json = ubm_service.get_cells()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("查询租户信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_tenant_detail(self, ubm_service):
        with AllureHelper.api_test(ubm_service):
            with AllureHelper.step("发送 GET 请求查询租户信息"):
                response_json = ubm_service.get_tenant_detail()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    # ==================== UBM 策略接口 ====================

    @allure.title("批量新增策略")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_add_strategy(self, ubm_service, api_env):
        with AllureHelper.api_test(ubm_service):
            with AllureHelper.step("构造策略数据并发送 POST 请求"):
                control_plane_code = api_env.get("ms_control_plane")
                belong_code = api_env.get("ms_application_code")
                strategies = [
                    {
                        "strategyCode": "CUSTOM-demoA",
                        "belongCode": belong_code,
                        "scope": "Application",
                        "kind": "ROUTE",
                        "strategy": {
                            "type": "CUSTOM",
                            "paramKey": "route-key",
                            "paramType": "B",
                            "paramValue": "cust",
                            "targetValue": "cluestA",
                        },
                    },
                    {
                        "strategyCode": "CUSTOM-demoB",
                        "belongCode": belong_code,
                        "scope": "Application",
                        "kind": "ROUTE",
                        "strategy": {
                            "type": "CUSTOM",
                            "paramKey": "route-key",
                            "paramType": "D",
                            "paramValue": "cust",
                            "targetValue": "cluestB",
                        },
                    },
                ]
                response_json = ubm_service.batch_add_strategy(control_plane_code, strategies)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("批量更新策略状态")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_update_strategy_status(self, ubm_service, api_env, api_cache):
        with AllureHelper.api_test(ubm_service):
            with AllureHelper.step("构造策略状态数据并发送 PUT 请求"):
                data = {
                    "controlPlaneCode": api_env.get("ms_control_plane"),
                    "scope": "Application",
                    "kind": "ROUTE",
                    "strategyInfos": [
                        {"strategyCode": "CUSTOM-demoA", "belongCode": api_env.get("ms_application_code"), "status": "UP"},
                        {"strategyCode": "CUSTOM-demoB", "belongCode": api_env.get("ms_application_code"), "status": "UP"},
                    ],
                    "clusterInfos": [
                        {
                            "planeCode": api_env.get("cell_code"),
                            "planeName": api_env.get("cell_code"),
                            "cellCode": api_env.get("cell_code"),
                            "cellName": api_env.get("cell_code"),
                        }
                    ],
                }
                response_json = ubm_service.batch_update_strategy_status(data)

            with AllureHelper.step("验证响应并缓存 batchCode"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                if response_json.get("code") == 0 and response_json.get("data"):
                    batch_code = response_json["data"].get("batchCode")
                    if batch_code:
                        api_cache.set("ms_batch_code", batch_code)

    @allure.title("批量更新策略状态进度查询")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_strategy_batch_detail(self, ubm_service, api_cache):
        with AllureHelper.api_test(ubm_service):
            with AllureHelper.step("从缓存读取 batchCode"):
                if not api_cache.has("ms_batch_code"):
                    pytest.skip("缺少 upstream 依赖：ms_batch_code 未缓存")
                batch_code = api_cache.get("ms_batch_code")

            with AllureHelper.step(f"发送 GET 请求查询批次详情：{batch_code}"):
                response_json = ubm_service.get_strategy_batch_detail(batch_code)

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"
