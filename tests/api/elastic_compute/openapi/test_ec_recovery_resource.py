"""
弹性计算 OpenAPI 容灾组件资源接口测试

测试内容：容灾组件资源生命周期（查询+清理 → 创建 → 查询验证 → Apply）
"""
import json

import allure
import pytest

from base.api.entity.elastic_compute.openapi import (
    RecoveryResourceEntity,
    RecoveryResourcePublicParams,
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
@allure.story("容灾组件资源生命周期接口")
class TestEcOpenapiRecoveryResource:
    """
    拆分为独立接口测试函数，通过 pytest-dependency 保证执行顺序和依赖关系。
    执行顺序：查询+清理 → 创建 → 查询验证 → Apply
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, test_env) -> RecoveryResourcePublicParams:
        """提取容灾组件测试所需的公共参数。"""
        return RecoveryResourcePublicParams(
            cell_code=test_env.get("cellCode", "PROD_PLANE1_CELL3"),
            sys_code=test_env.get("sysCode", "test"),
            resource_name="test-resource-deploy-001",
            app_name="app-nginx-test",
            kind="Deployment",
            image=test_env.get("nginxImageName", "hpe_containers/nginx:latest"),
            tenant_code=test_env.get("paasTenantCode", "monitor-group"),
            app_code=test_env.get("grantAppCode", "probe-deploy"),
            plane_code=test_env.get("planeCode", "PLANE"),
            unit_code=test_env.get("unitCode", "test"),
            env_code=test_env.get("paasEnvCode", "PROD"),
            user=test_env.get("user", "PROD"),
        )

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询容灾组件资源列表")
    @allure.description("查询容灾组件资源列表确认当前状态，若目标资源存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="recovery_resource_query_and_cleanup")
    @pytest.mark.order(1)
    def test_query_recovery_resource_and_cleanup(self, ec_service, public_params):
        """查询容灾组件资源，若目标资源已存在则删除，确保测试环境干净。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_recovery_resources(
                sys_code=public_params.sys_code,
                cell_code=public_params.cell_code,
            )
            ec_code = list_resp.get("code")

            assert ec_code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                f"查询容灾组件资源返回异常 code: {ec_code}, 响应: {list_resp}"
            )

            # 若目标资源存在，先删除
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            if ec_code == ApiCode.SUCCESS and public_params.resource_name in resp_str:
                del_resp = ec_service.delete_recovery_resources(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    resource_names=[public_params.resource_name],
                )
                assert del_resp.get("code") == ApiCode.SUCCESS, (
                    f"删除已存在的容灾资源失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

    @allure.title("创建容灾组件资源")
    @allure.description("创建容灾组件资源，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="recovery_resource_create", depends=["recovery_resource_query_and_cleanup"],
    )
    @pytest.mark.order(2)
    def test_create_recovery_resource(self, ec_service, public_params):
        """创建容灾组件资源，断言创建成功。"""
        with AllureHelper.api_test(ec_service):
            resource = RecoveryResourceEntity(
                name=public_params.resource_name,
                app_name=public_params.app_name,
                kind=public_params.kind,
                image=public_params.image,
                tenant_code=public_params.tenant_code,
                app_code=public_params.app_code,
                plane_code=public_params.plane_code,
                unit_code=public_params.unit_code,
                env_code=public_params.env_code,
                username=public_params.user,
            )
            create_resp = ec_service.create_recovery_resources(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                resources=[resource],
            )

            assert create_resp.get("code") == ApiCode.SUCCESS, (
                f"创建容灾组件资源失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )

    @allure.title("查询验证容灾组件资源已创建")
    @allure.description("创建后再次查询容灾组件资源列表，验证目标资源存在")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(
        name="recovery_resource_verify", depends=["recovery_resource_create"],
    )
    @pytest.mark.order(3)
    def test_verify_recovery_resource_created(self, ec_service, public_params):
        """创建后查询验证容灾组件资源已存在。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_recovery_resources(
                sys_code=public_params.sys_code,
                cell_code=public_params.cell_code,
            )

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询容灾组件资源列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert public_params.resource_name in resp_str, (
                f"容灾组件资源列表中未找到 {public_params.resource_name}, 响应: {list_resp}"
            )

    @allure.title("Apply 容灾组件资源")
    @allure.description("Apply 容灾组件资源，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="recovery_resource_apply", depends=["recovery_resource_verify"],
    )
    @pytest.mark.order(4)
    def test_apply_recovery_resource(self, ec_service, public_params):
        """Apply 容灾组件资源，断言操作成功。"""
        with AllureHelper.api_test(ec_service):
            resource = RecoveryResourceEntity(
                name=public_params.resource_name,
                app_name=public_params.app_name,
                kind=public_params.kind,
                image=public_params.image,
                tenant_code=public_params.tenant_code,
                app_code=public_params.app_code,
                plane_code=public_params.plane_code,
                unit_code=public_params.unit_code,
                env_code=public_params.env_code,
                username=public_params.user,
            )
            apply_resp = ec_service.apply_recovery_resources(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                resources=[resource],
            )

            assert apply_resp.get("code") == ApiCode.SUCCESS, (
                f"Apply 容灾组件资源失败, code: {apply_resp.get('code')}, 响应: {apply_resp}"
            )
