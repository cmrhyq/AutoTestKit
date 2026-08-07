"""
微服务 UBM OpenAPI 接口测试脚本

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

from base.api.entity.microservices import (
    BatchStrategyStatusEntity,
    ClusterInfoEntity,
    StrategyEntity,
    StrategyRuleEntity,
    StrategyStatusEntity,
    UbmPublicParams,
)
from base.api.services.microservices_open_service import (
    MicroservicesOpenService,
)
from core.reporting.allure_helper import AllureHelper
from core.constants import Tenant

@pytest.mark.api
@pytest.mark.microservice
@allure.epic("磐基API自动化测试")
@allure.feature("磐基微服务OpenAPI接口")
@allure.story("UBM OpenAPI 接口")
class TestMicroservicesUbm:
    """
    Microservices UBM OpenAPI 测试

    数据流：批量新增策略 → 批量更新策略状态（返回 batchCode）→ 批量查询状态进度
    """

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def ubm_service(self, service_factory):
        with service_factory(MicroservicesOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, test_env) -> UbmPublicParams:
        """提取 UBM 测试所需的公共参数。"""
        return UbmPublicParams(
            control_plane_code=test_env.get("controlPlaneCode"),
            belong_code=test_env.get("belongCode"),
            plane_code=test_env.get("planeCode"),
            plane_name=test_env.get("planeName"),
            cell_code=test_env.get("cellCode"),
            cell_name=test_env.get("cellName"),
        )

    # ==================== UBM 查询接口 ====================

    @allure.title("查询平面单元列表")
    @allure.description("查询当前租户下的平面单元列表，断言响应为字典且包含 code 字段")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_cells(self, ubm_service):
        with AllureHelper.api_test(ubm_service):
            with AllureHelper.step("发送 GET 请求查询平面单元列表"):
                response_json = ubm_service.get_cells()

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("查询租户信息")
    @allure.description("查询当前登录租户的详细信息")
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
    @allure.description("批量新增 UBM 路由策略")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_add_strategy(self, ubm_service, public_params):
        with AllureHelper.api_test(ubm_service):
            with AllureHelper.step("构造策略数据并发送 POST 请求"):
                strategies = [
                    StrategyEntity(
                        strategy_code="CUSTOM-demoA",
                        belong_code=public_params.belong_code,
                        scope="Application",
                        kind="ROUTE",
                        strategy=StrategyRuleEntity(
                            type="CUSTOM",
                            param_key="route-key",
                            param_type="B",
                            param_value="cust",
                            target_value="cluestA",
                        ),
                    ),
                    StrategyEntity(
                        strategy_code="CUSTOM-demoB",
                        belong_code=public_params.belong_code,
                        scope="Application",
                        kind="ROUTE",
                        strategy=StrategyRuleEntity(
                            type="CUSTOM",
                            param_key="route-key",
                            param_type="D",
                            param_value="cust",
                            target_value="cluestB",
                        ),
                    ),
                ]
                response_json = ubm_service.batch_add_strategy(
                    public_params.control_plane_code, strategies
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                assert "code" in response_json, "响应缺少 code 字段"

    @allure.title("批量更新策略状态")
    @allure.description("批量更新 UBM 策略状态并返回 batchCode")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_update_strategy_status(self, ubm_service, public_params, api_cache):
        with AllureHelper.api_test(ubm_service):
            with AllureHelper.step("构造策略状态数据并发送 PUT 请求"):
                entity = BatchStrategyStatusEntity(
                    control_plane_code=public_params.control_plane_code,
                    scope="Application",
                    kind="ROUTE",
                    strategy_infos=[
                        StrategyStatusEntity(
                            strategy_code="CUSTOM-demoA",
                            belong_code=public_params.belong_code,
                            status="UP",
                        ),
                        StrategyStatusEntity(
                            strategy_code="CUSTOM-demoB",
                            belong_code=public_params.belong_code,
                            status="UP",
                        ),
                    ],
                    cluster_infos=[
                        ClusterInfoEntity(
                            plane_code=public_params.plane_code,
                            plane_name=public_params.plane_name,
                            cell_code=public_params.cell_code,
                            cell_name=public_params.cell_name,
                        )
                    ],
                )
                response_json = ubm_service.batch_update_strategy_status(entity)

            with AllureHelper.step("验证响应并缓存 batchCode"):
                assert isinstance(response_json, Dict), "响应应该是字典类型"
                if response_json.get("code") == 0 and response_json.get("data"):
                    batch_code = response_json["data"].get("batchCode")
                    if batch_code:
                        api_cache.set("ms_batch_code", batch_code)

    @allure.title("批量更新策略状态进度查询")
    @allure.description("根据 batchCode 查询批量策略状态更新进度")
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
