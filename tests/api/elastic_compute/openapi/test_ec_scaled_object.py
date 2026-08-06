"""
弹性计算 OpenAPI ScaledObject 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/ScaledObject.jmx
线程组: Thread Group - ScaledObject完整生命周期
测试内容：ScaledObject 完整生命周期（查询/清理 → 创建 → 更新 → 删除）
"""
import allure
import pytest

from base.api.entity.elastic_compute_openapi import (
    ScaledObjectEntity,
    ScaledObjectPatchEntity,
    ScaledObjectPublicParams,
)
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("ScaledObject 生命周期接口")
class TestEcOpenapiScaledObject:
    """
    对应 JMeter 脚本: ScaledObject.jmx
    线程组: Thread Group - ScaledObject完整生命周期

    拆分为独立接口测试函数，通过 pytest-dependency 保证执行顺序和依赖关系。
    执行顺序：查询+清理 → 创建 → 更新 → 删除
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> ScaledObjectPublicParams:
        """提取 ScaledObject 测试所需的公共参数。"""
        return ScaledObjectPublicParams(
            cell_code=api_env.get("cellCode", "PROD_PLANE1_CELL3"),
            sys_code=api_env.get("sysCode", "test"),
            so_name="test-scaled-object-001",
            workload_kind=api_env.get("soWorkloadKind", "Deployment"),
            workload_name=api_env.get("soWorkloadName", "auto-test-deploy-probe-ns-test-0002"),
        )

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询指定 ScaledObject")
    @allure.description("查询指定 ScaledObject 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="scaled_object_query_and_cleanup")
    @pytest.mark.order(1)
    def test_query_scaled_object_and_cleanup(self, ec_service, public_params):
        """查询指定 ScaledObject，若已存在则删除，确保测试环境干净。"""
        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_scaled_object(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=public_params.so_name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                f"查询 ScaledObject 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            # 若已存在，先删除以保证幂等
            if ec_get_code == ApiCode.SUCCESS:
                del_resp = ec_service.delete_scaled_object(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    name=public_params.so_name,
                )
                assert del_resp.get("code") == ApiCode.SUCCESS, (
                    f"删除已存在的 ScaledObject 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

    @allure.title("创建 ScaledObject")
    @allure.description("创建 ScaledObject 资源，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="scaled_object_create", depends=["scaled_object_query_and_cleanup"],
    )
    @pytest.mark.order(2)
    def test_create_scaled_object(self, ec_service, public_params):
        """创建 ScaledObject，断言创建成功。"""
        with AllureHelper.api_test(ec_service):
            scaled_object = ScaledObjectEntity(
                name=public_params.so_name,
                workload_kind=public_params.workload_kind,
                workload_name=public_params.workload_name,
            )
            create_resp = ec_service.create_scaled_object(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                scaled_object=scaled_object,
            )

            assert create_resp.get("code") == ApiCode.SUCCESS, (
                f"创建 ScaledObject 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )

    @allure.title("更新 ScaledObject")
    @allure.description("使用 PUT 方法更新 ScaledObject 的定时伸缩参数，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="scaled_object_update", depends=["scaled_object_create"],
    )
    @pytest.mark.order(3)
    def test_update_scaled_object(self, ec_service, public_params):
        """PUT 更新 ScaledObject，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            patch = ScaledObjectPatchEntity()
            update_resp = ec_service.update_scaled_object(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=public_params.so_name,
                patch=patch,
            )

            assert update_resp.get("code") == ApiCode.SUCCESS, (
                f"更新 ScaledObject 失败, code: {update_resp.get('code')}, 响应: {update_resp}"
            )

    @allure.title("删除 ScaledObject")
    @allure.description("删除创建的 ScaledObject 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="scaled_object_delete", depends=["scaled_object_update"],
    )
    @pytest.mark.order(4)
    def test_delete_scaled_object(self, ec_service, public_params):
        """删除 ScaledObject，断言删除成功。"""
        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_scaled_object(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=public_params.so_name,
            )

            assert del_resp.get("code") == ApiCode.SUCCESS, (
                f"删除 ScaledObject 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )
