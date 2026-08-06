"""
弹性计算 OpenAPI Namespace 级别 CustomResource 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/CustomResource-ns.jmx
线程组: Thread Group - CustomResource-ns
测试内容：Namespace 级别 CR 完整生命周期（查询/删除/创建/列表/PUT 更新/PATCH 增量更新/删除）
"""
import json

import allure
import pytest

from base.api.entity.elastic_compute_openapi import (
    CrNsPublicParams,
    NsCustomResourceEntity,
    NsCustomResourcePatchEntity,
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
@allure.story("Namespace 级别 CustomResource 生命周期接口")
class TestEcOpenapiCrNs:
    """
    对应 JMeter 脚本: CustomResource-ns.jmx
    线程组: Thread Group - CustomResource-ns

    拆分为独立接口测试函数，通过 pytest-dependency 保证执行顺序和依赖关系。
    执行顺序：查询 → 清理已存在 → 创建 → 列表查询 → PUT更新 → PATCH更新 → 删除 → 验证删除
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> CrNsPublicParams:
        """提取 Namespace 级别 CR 测试所需的公共参数。"""
        return CrNsPublicParams(
            cell_code=api_env.get("cellCode"),
            sys_code=api_env.get("sysCode"),
        )

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询指定 Namespace 级别 CR")
    @allure.description("查询指定 Namespace 级别 CR 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="cr_ns_query_and_cleanup")
    @pytest.mark.order(1)
    def test_query_cr_ns_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 Namespace 级别 CR，若已存在则删除，确保测试环境干净。"""
        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_ns_custom_resource(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                name=public_params.cr_name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                f"查询 Namespace CR 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            if ec_get_code == ApiCode.SUCCESS:
                del_resp = ec_service.delete_ns_custom_resource(
                    cell_code=public_params.cell_code,
                    sys_code=public_params.sys_code,
                    group=public_params.cr_group,
                    version=public_params.cr_version,
                    kind=public_params.cr_kind,
                    name=public_params.cr_name,
                )
                assert del_resp.get("code") == ApiCode.SUCCESS, (
                    f"删除已存在的 Namespace CR 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

            api_cache.set("ec_cr_ns_created", False)

    @allure.title("创建 Namespace 级别 CR")
    @allure.description("创建 Namespace 级别 CustomResource，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="cr_ns_create", depends=["cr_ns_query_and_cleanup"])
    @pytest.mark.order(2)
    def test_create_cr_ns(self, ec_service, public_params, api_cache):
        """创建 Namespace 级别 CR，断言创建成功。"""
        with AllureHelper.api_test(ec_service):
            custom_resource = NsCustomResourceEntity(
                name=public_params.cr_name,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                color="red",
            )
            create_resp = ec_service.create_ns_custom_resource(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                custom_resource=custom_resource,
            )

            assert create_resp.get("code") == ApiCode.SUCCESS, (
                f"创建 Namespace CR 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )
            resp_str = json.dumps(create_resp, ensure_ascii=False)
            assert public_params.cr_name in resp_str, (
                f"创建 Namespace CR 响应中未包含资源名称 {public_params.cr_name}, 响应: {create_resp}"
            )

            api_cache.set("ec_cr_ns_created", True)

    @allure.title("查询 Namespace 级别 CR 列表")
    @allure.description("查询 Namespace 级别 CR 列表，验证包含新创建的 CR")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="cr_ns_list", depends=["cr_ns_create"])
    @pytest.mark.order(3)
    def test_list_cr_ns(self, ec_service, public_params):
        """查询 Namespace 级别 CR 列表，断言包含目标 CR。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_ns_custom_resources(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
            )

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询 Namespace CR 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert public_params.cr_name in resp_str, (
                f"Namespace CR 列表未找到 {public_params.cr_name}, 响应: {list_resp}"
            )

    @allure.title("PUT 全量更新 Namespace 级别 CR")
    @allure.description("使用 PUT 方法全量更新 Namespace 级别 CR 的 spec 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="cr_ns_put", depends=["cr_ns_create"])
    @pytest.mark.order(4)
    def test_put_update_cr_ns(self, ec_service, public_params):
        """PUT 全量更新 Namespace 级别 CR，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            custom_resource = NsCustomResourceEntity(
                name=public_params.cr_name,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                color="green",
            )
            put_resp = ec_service.update_ns_custom_resource(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                name=public_params.cr_name,
                custom_resource=custom_resource,
            )

            assert put_resp.get("code") == ApiCode.SUCCESS, (
                f"PUT 更新 Namespace CR 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
            )
            resp_str = json.dumps(put_resp, ensure_ascii=False)
            assert "green" in resp_str, (
                f"PUT 更新后响应中未包含预期数据 'green', 响应: {put_resp}"
            )

    @allure.title("PATCH 增量更新 Namespace 级别 CR")
    @allure.description("使用 PATCH 方法增量更新 Namespace 级别 CR 的 labels 和 spec 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="cr_ns_patch", depends=["cr_ns_put"])
    @pytest.mark.order(5)
    def test_patch_update_cr_ns(self, ec_service, public_params):
        """PATCH 增量更新 Namespace 级别 CR，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            patch_entity = NsCustomResourcePatchEntity(
                color="blue",
                labels={"test": "test2"},
            )
            patch_resp = ec_service.patch_ns_custom_resource(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                name=public_params.cr_name,
                custom_resource=patch_entity,
            )

            assert patch_resp.get("code") == ApiCode.SUCCESS, (
                f"PATCH 增量更新 Namespace CR 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
            )
            resp_str = json.dumps(patch_resp, ensure_ascii=False)
            assert "blue" in resp_str, (
                f"PATCH 更新后响应中未包含预期数据 'blue', 响应: {patch_resp}"
            )

    @allure.title("删除 Namespace 级别 CR")
    @allure.description("删除创建的 Namespace 级别 CR 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="cr_ns_delete", depends=["cr_ns_patch"])
    @pytest.mark.order(6)
    def test_delete_cr_ns(self, ec_service, public_params, api_cache):
        """删除 Namespace 级别 CR，断言删除成功。"""
        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_ns_custom_resource(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                name=public_params.cr_name,
            )

            assert del_resp.get("code") == ApiCode.SUCCESS, (
                f"删除 Namespace CR 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )

            api_cache.set("ec_cr_ns_created", False)

    @allure.title("验证 Namespace 级别 CR 删除后不存在")
    @allure.description("删除后再次查询 Namespace 级别 CR，验证返回资源不存在")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(depends=["cr_ns_delete"])
    @pytest.mark.order(7)
    def test_verify_cr_ns_deleted(self, ec_service, public_params):
        """删除后验证 Namespace 级别 CR 已不存在。"""
        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_ns_custom_resource(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                name=public_params.cr_name,
            )

            assert get_resp.get("code") == ApiCode.NOT_FOUND, (
                f"Namespace CR 删除后仍能查询到, code: {get_resp.get('code')}, 响应: {get_resp}"
            )
