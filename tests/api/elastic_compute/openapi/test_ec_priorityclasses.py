"""
PriorityClass 接口测试

转换自 JMeter 脚本: PriorityClassesV2.jmx
测试内容：PriorityClass 完整生命周期（查询、创建、列表、PUT更新、PATCH更新、删除）
"""
import json

import allure
import pytest

from base.api.entity.elastic_compute_openapi import (
    K8sPriorityClassEntity,
    K8sPriorityClassPatchEntity,
    PriorityClassPublicParams,
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
@allure.story("PriorityClass 生命周期接口")
class TestEcOpenapiPriorityClasses:
    """
    对应 JMeter 脚本: PriorityClassesV2.jmx
    线程组: PriorityClass
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> PriorityClassPublicParams:
        """提取 PriorityClass 测试所需的公共参数。"""
        return PriorityClassPublicParams(
            cell_code=api_env.get("cellCode", "TEST"),
            pc_name=api_env.get("priorityClassName", "pc-test"),
        )

    # -------------------- 测试用例 --------------------

    @pytest.mark.dependency(name="pc_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 PriorityClass")
    @allure.description("查询指定 PriorityClass 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_priorityclass_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 PriorityClass，若已存在则删除，确保测试环境干净。"""
        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_priority_class(
                cell_code=public_params.cell_code,
                name=public_params.pc_name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                f"查询 PriorityClass 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            if ec_get_code == ApiCode.SUCCESS:
                del_resp = ec_service.delete_priority_class(
                    cell_code=public_params.cell_code,
                    name=public_params.pc_name,
                )
                assert del_resp.get("code") == ApiCode.SUCCESS, (
                    f"删除已存在的 PriorityClass 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

            api_cache.set("ec_pc_created", False)

    @pytest.mark.dependency(name="pc_create", depends=["pc_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 PriorityClass")
    @allure.description("创建 PriorityClass 资源，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_priorityclass(self, ec_service, public_params, api_cache):
        """创建 PriorityClass，断言创建成功。"""
        with AllureHelper.api_test(ec_service):
            priority_class = K8sPriorityClassEntity(name=public_params.pc_name)
            create_resp = ec_service.create_priority_class(
                cell_code=public_params.cell_code,
                priority_class=priority_class,
            )

            assert create_resp.get("code") == ApiCode.SUCCESS, (
                f"创建 PriorityClass 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )

            api_cache.set("ec_pc_created", True)

    @pytest.mark.dependency(name="pc_list", depends=["pc_create"])
    @pytest.mark.order(3)
    @allure.title("查询 PriorityClass 列表")
    @allure.description("查询 PriorityClass 列表，验证包含新创建的资源")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_priorityclasses(self, ec_service, public_params):
        """查询 PriorityClass 列表，断言包含目标资源。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_priority_classes(cell_code=public_params.cell_code)

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询 PriorityClass 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )

            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert public_params.pc_name in resp_str, (
                f"PriorityClass 列表未找到 {public_params.pc_name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="pc_update", depends=["pc_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 PriorityClass")
    @allure.description("使用 PUT 方法全量更新 PriorityClass，验证响应包含资源名称")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_priorityclass(self, ec_service, public_params):
        """PUT 全量更新 PriorityClass，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            priority_class = K8sPriorityClassEntity(name=public_params.pc_name)
            put_resp = ec_service.update_priority_class(
                cell_code=public_params.cell_code,
                name=public_params.pc_name,
                priority_class=priority_class,
            )

            assert put_resp.get("code") == ApiCode.SUCCESS, (
                f"PUT 更新 PriorityClass 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
            )

            resp_str = json.dumps(put_resp, ensure_ascii=False)
            assert public_params.pc_name in resp_str, (
                f"PUT 更新后响应中未包含资源名称 {public_params.pc_name}, 响应: {put_resp}"
            )

    @pytest.mark.dependency(name="pc_patch", depends=["pc_update"])
    @pytest.mark.order(5)
    @allure.title("PATCH 增量更新 PriorityClass")
    @allure.description("使用 PATCH 方法增量更新 PriorityClass 的 description 和 metadata，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_patch_priorityclass(self, ec_service, public_params):
        """PATCH 增量更新 PriorityClass，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            patch = K8sPriorityClassPatchEntity()
            patch_resp = ec_service.patch_priority_class(
                cell_code=public_params.cell_code,
                name=public_params.pc_name,
                patch=patch,
            )

            assert patch_resp.get("code") == ApiCode.SUCCESS, (
                f"PATCH 增量更新 PriorityClass 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
            )

            resp_str = json.dumps(patch_resp, ensure_ascii=False)
            assert public_params.pc_name in resp_str, (
                f"PATCH 更新后响应中未包含资源名称 {public_params.pc_name}, 响应: {patch_resp}"
            )

    @pytest.mark.dependency(name="pc_delete", depends=["pc_patch"])
    @pytest.mark.order(6)
    @allure.title("删除 PriorityClass")
    @allure.description("删除创建的 PriorityClass 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_priorityclass(self, ec_service, public_params, api_cache):
        """删除 PriorityClass，断言删除成功。"""
        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_priority_class(
                cell_code=public_params.cell_code,
                name=public_params.pc_name,
            )

            assert del_resp.get("code") == ApiCode.SUCCESS, (
                f"删除 PriorityClass 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )

            api_cache.set("ec_pc_created", False)
