"""
微服务 CMF OpenAPI 接口测试脚本

覆盖 CMF（配置管理面）12 个用例：
- 批量新增单体服务 & 批量查询服务
- 降级配置 CRUD（新增/详情/修改/上下线/删除）
- 熔断配置 CRUD（新增/详情/修改/上下线/删除）
"""
import allure
import pytest

from base.api.entity.microservices import (
    CmfCircuitBreakingEntity,
    CmfDegradeEntity,
    CmfPublicParams,
    CmfServiceMeta,
    FuncserEntity,
)
from base.api.services.microservices_open_service import (
    MicroservicesOpenService,
)
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.microservice
@allure.epic("磐基API自动化测试")
@allure.feature("磐基微服务OpenAPI接口")
@allure.story("CMF OpenAPI 接口")
class TestMicroservicesCmf:
    """
    Microservices CMF（Central Management Framework）OpenAPI 测试

    数据流：新增服务 → 查询服务 → 降级 CRUD → 熔断 CRUD
    """

    TENANT = "tenant_admin"

    @pytest.fixture(scope="class")
    def cmf_service(self, service_factory):
        with service_factory(MicroservicesOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> CmfPublicParams:
        """提取 CMF 测试所需的公共参数。"""
        return CmfPublicParams(
            control_plane_name=api_env.get("controlPlaneName"),
            control_plane_code=api_env.get("controlPlaneCode"),
            env_code=api_env.get("envCode"),
            application_code=api_env.get("applicationCode"),
            function_class_name=api_env.get("functionClassName"),
            func_ser_name=api_env.get("funcSerName"),
            func_ser_code=api_env.get("funcserCode"),
        )

    # ==================== 服务信息 ====================

    @allure.title("批量新增单体服务 SINGLE")
    @allure.description("批量新增 SINGLE 类型的单体服务")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_add_funcser(self, cmf_service, public_params):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("构造 funcsers 列表并发送 POST"):
                funcsers = [
                    FuncserEntity(
                        application_code=public_params.application_code,
                        function_class_name=public_params.function_class_name,
                        func_ser_code=public_params.func_ser_code,
                        func_ser_name=public_params.func_ser_name,
                        type="SINGLE",
                    )
                ]
                response_json = cmf_service.batch_add_funcser(
                    public_params.control_plane_name, funcsers
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("根据服务编码批量精确查询服务信息")
    @allure.description("按服务编码列表批量精确查询服务信息")
    @allure.severity(allure.severity_level.NORMAL)
    def test_batch_get_funcser(self, cmf_service, public_params):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 GET 请求批量查询服务信息"):
                response_json = cmf_service.batch_get_funcser(
                    control_plane_code=public_params.control_plane_code,
                    application_code=public_params.application_code,
                    funcser_codes=[public_params.func_ser_code],
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== CMF 降级 CRUD ====================

    @allure.title("CMF 新增降级配置")
    @allure.description("为指定服务新增降级配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_cmf_degrade(self, cmf_service, public_params):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求新增降级"):
                entity = CmfDegradeEntity(
                    meta=CmfServiceMeta.from_public_params(public_params),
                    degrade_rule={"type": "DEFAULT"},
                )
                response_json = cmf_service.add_cmf_degrade(entity)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 获取降级配置详情")
    @allure.description("获取指定服务的降级配置详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_cmf_degrade_detail(self, cmf_service, public_params):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求获取降级详情"):
                response_json = cmf_service.get_cmf_degrade_detail(
                    control_plane_name=public_params.control_plane_name,
                    env_code=public_params.env_code,
                    func_ser_name=public_params.func_ser_name,
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 修改降级配置")
    @allure.description("修改指定服务的降级配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_cmf_degrade(self, cmf_service, public_params):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求修改降级"):
                entity = CmfDegradeEntity(
                    meta=CmfServiceMeta.from_public_params(public_params),
                    degrade_rule={"type": "DEFAULT", "updated": True},
                )
                response_json = cmf_service.update_cmf_degrade(entity)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 降级配置上线或者下线")
    @allure.description("上线或下线指定服务的降级配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_cmf_degrade_state(self, cmf_service, public_params):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求上下线降级"):
                entity = CmfDegradeEntity(
                    meta=CmfServiceMeta.from_public_params(public_params),
                    state="UP",
                )
                response_json = cmf_service.update_cmf_degrade_state(entity)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 删除降级配置")
    @allure.description("删除指定服务的降级配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_cmf_degrade(self, cmf_service, public_params):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求删除降级"):
                entity = CmfDegradeEntity(meta=CmfServiceMeta.from_public_params(public_params))
                response_json = cmf_service.delete_cmf_degrade(entity)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    # ==================== CMF 熔断 CRUD ====================

    @allure.title("CMF 新增熔断配置")
    @allure.description("为指定服务新增熔断配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_add_cmf_circuit_breaking(self, cmf_service, public_params):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求新增熔断"):
                entity = CmfCircuitBreakingEntity(
                    meta=CmfServiceMeta.from_public_params(public_params),
                    circuit_breaking_rule={"type": "DEFAULT"},
                )
                response_json = cmf_service.add_cmf_circuit_breaking(entity)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 获取熔断配置详情")
    @allure.description("获取指定服务的熔断配置详情")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_cmf_circuit_breaking_detail(self, cmf_service, public_params):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求获取熔断详情"):
                response_json = cmf_service.get_cmf_circuit_breaking_detail(
                    control_plane_name=public_params.control_plane_name,
                    env_code=public_params.env_code,
                    func_ser_name=public_params.func_ser_name,
                )
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 修改熔断配置")
    @allure.description("修改指定服务的熔断配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_cmf_circuit_breaking(self, cmf_service, public_params):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求修改熔断"):
                entity = CmfCircuitBreakingEntity(
                    meta=CmfServiceMeta.from_public_params(public_params),
                    circuit_breaking_rule={"type": "DEFAULT", "updated": True},
                )
                response_json = cmf_service.update_cmf_circuit_breaking(entity)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 熔断配置上线或者下线")
    @allure.description("上线或下线指定服务的熔断配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_cmf_circuit_breaking_state(self, cmf_service, public_params):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求上下线熔断"):
                entity = CmfCircuitBreakingEntity(
                    meta=CmfServiceMeta.from_public_params(public_params),
                    state="UP",
                )
                response_json = cmf_service.update_cmf_circuit_breaking_state(entity)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json

    @allure.title("CMF 删除熔断配置")
    @allure.description("删除指定服务的熔断配置")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_cmf_circuit_breaking(self, cmf_service, public_params):
        with AllureHelper.api_test(cmf_service):
            with AllureHelper.step("发送 POST 请求删除熔断"):
                entity = CmfCircuitBreakingEntity(meta=CmfServiceMeta.from_public_params(public_params))
                response_json = cmf_service.delete_cmf_circuit_breaking(entity)
            with AllureHelper.step("验证响应"):
                assert "code" in response_json
