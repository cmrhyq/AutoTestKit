"""
微服务 CMF OpenAPI 接口测试脚本

基于 JMeter auto_test_pro/auto-test/files/microservices/openapi/mscmf.jmx 转换。
覆盖 CMF（配置管理面）12 个用例：
- 批量新增单体服务 & 批量查询服务
- 降级配置 CRUD（新增/详情/修改/上下线/删除）
- 熔断配置 CRUD（新增/详情/修改/上下线/删除）
"""
from typing import Dict

import allure
import pytest

from base.api.services.microservices_open_service import (
    PanJiMicroservicesOpenService,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("磐基微服务 CMF OpenAPI 服务")
@allure.story("Microservices CMF OpenAPI 接口测试")
class TestMicroservicesCmfOpenApi:
    """
    Microservices CMF（Central Management Framework）OpenAPI 测试

    数据流：新增服务 → 查询服务 → 降级 CRUD → 熔断 CRUD
    """

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def cmf_service(self, api_env, api_logger):
        service = PanJiMicroservicesOpenService(
            base_url=api_env.get("apiBaseUrl"),
            logger=api_logger,
        )
        yield service
        service.close()

    def _degrade_payload(self, api_env) -> Dict:
        return {
            "controlPlaneName": api_env.get("controlPlaneName"),
            "controlPlaneCode": api_env.get("controlPlaneCode"),
            "envCode": api_env.get("envCode"),
            "applicationCode": api_env.get("applicationCode"),
            "functionClassName": api_env.get("functionClassName"),
            "funcSerName": api_env.get("funcSerName"),
            "funcSerCode": api_env.get("funcserCode"),
        }

    # ==================== 服务信息 ====================

    @allure.title("批量新增单体服务 SINGLE")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_add_funcser(self, cmf_service, api_env):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("构造 funcsers 列表并发送 POST"):
                funcsers = [
                    {
                        "applicationCode": api_env.get("applicationCode"),
                        "functionClassName": api_env.get("functionClassName"),
                        "funcSerCode": api_env.get("funcserCode"),
                        "funcSerName": api_env.get("funcSerName"),
                        "type": "SINGLE",
                    }
                ]
                response_json = cmf_service.batch_add_funcser(
                    api_env.get("controlPlaneName"), funcsers
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据服务编码批量精确查询服务信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_get_funcser(self, cmf_service, api_env):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 GET 请求批量查询服务信息"):
                response_json = cmf_service.batch_get_funcser(
                    control_plane_code=api_env.get("controlPlaneCode"),
                    application_code=api_env.get("applicationCode"),
                    funcser_codes=[api_env.get("funcserCode")],
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== CMF 降级 CRUD ====================

    @allure.title("CMF 新增降级配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_cmf_degrade(self, cmf_service, api_env):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求新增降级"):
                payload = self._degrade_payload(api_env)
                payload["degradeRule"] = {"type": "DEFAULT"}
                response_json = cmf_service.add_cmf_degrade(payload)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 获取降级配置详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_cmf_degrade_detail(self, cmf_service, api_env):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求获取降级详情"):
                response_json = cmf_service.get_cmf_degrade_detail(
                    control_plane_name=api_env.get("controlPlaneName"),
                    env_code=api_env.get("envCode"),
                    func_ser_name=api_env.get("funcSerName"),
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 修改降级配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_cmf_degrade(self, cmf_service, api_env):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求修改降级"):
                payload = self._degrade_payload(api_env)
                payload["degradeRule"] = {"type": "DEFAULT", "updated": True}
                response_json = cmf_service.update_cmf_degrade(payload)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 降级配置上线或者下线")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_cmf_degrade_state(self, cmf_service, api_env):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求上下线降级"):
                payload = self._degrade_payload(api_env)
                payload["state"] = "UP"
                response_json = cmf_service.update_cmf_degrade_state(payload)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 删除降级配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_cmf_degrade(self, cmf_service, api_env):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求删除降级"):
                payload = self._degrade_payload(api_env)
                response_json = cmf_service.delete_cmf_degrade(payload)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== CMF 熔断 CRUD ====================

    @allure.title("CMF 新增熔断配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_cmf_circuit_breaking(self, cmf_service, api_env):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求新增熔断"):
                payload = self._degrade_payload(api_env)
                payload["circuitBreakingRule"] = {"type": "DEFAULT"}
                response_json = cmf_service.add_cmf_circuit_breaking(payload)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 获取熔断配置详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_cmf_circuit_breaking_detail(self, cmf_service, api_env):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求获取熔断详情"):
                response_json = cmf_service.get_cmf_circuit_breaking_detail(
                    control_plane_name=api_env.get("controlPlaneName"),
                    env_code=api_env.get("envCode"),
                    func_ser_name=api_env.get("funcSerName"),
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 修改熔断配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_cmf_circuit_breaking(self, cmf_service, api_env):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求修改熔断"):
                payload = self._degrade_payload(api_env)
                payload["circuitBreakingRule"] = {"type": "DEFAULT", "updated": True}
                response_json = cmf_service.update_cmf_circuit_breaking(payload)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 熔断配置上线或者下线")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_cmf_circuit_breaking_state(self, cmf_service, api_env):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求上下线熔断"):
                payload = self._degrade_payload(api_env)
                payload["state"] = "UP"
                response_json = cmf_service.update_cmf_circuit_breaking_state(payload)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 删除熔断配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_cmf_circuit_breaking(self, cmf_service, api_env):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求删除熔断"):
                payload = self._degrade_payload(api_env)
                response_json = cmf_service.delete_cmf_circuit_breaking(payload)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json
