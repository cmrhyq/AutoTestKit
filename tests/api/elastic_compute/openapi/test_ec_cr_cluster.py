"""
Cluster 级别 CustomResource 接口测试

测试内容：针对 Cluster 级别 CR 增删改查进行测试（查询、创建、列表、PUT 更新、PATCH 更新、删除）
"""
import json

import allure
import pytest

from base.api.entity.elastic_compute.openapi import (
    ClusterCustomResourceEntity,
    ClusterCustomResourcePatchEntity,
    CrClusterPublicParams,
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
@allure.story("Cluster级别CustomResource生命周期接口")
class TestEcOpenapiCrCluster:

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, test_env) -> CrClusterPublicParams:
        """提取 Cluster CR 测试所需的公共参数。"""
        return CrClusterPublicParams(cell_code=test_env.get("cellCode"))

    # ==================== 测试方法 ====================

    @pytest.mark.dependency(name="cr_cluster_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 Cluster CR 并清理环境")
    @allure.description("查询指定 Cluster CR 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_cr_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 Cluster CR，若已存在则删除，确保测试环境干净。"""
        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_cluster_custom_resource(
                cell_code=public_params.cell_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                name=public_params.cr_name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                f"查询 Cluster CR 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            if ec_get_code == ApiCode.SUCCESS:
                del_resp = ec_service.delete_cluster_custom_resource(
                    cell_code=public_params.cell_code,
                    group=public_params.cr_group,
                    version=public_params.cr_version,
                    kind=public_params.cr_kind,
                    name=public_params.cr_name,
                )
                assert del_resp.get("code") == ApiCode.SUCCESS, (
                    f"删除已存在的 Cluster CR 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

            api_cache.set("ec_cr_cluster_created", False)

    @pytest.mark.dependency(name="cr_cluster_create", depends=["cr_cluster_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 Cluster CR")
    @allure.description("创建 Cluster 级别 CustomResource 资源，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_cluster_cr(self, ec_service, public_params, api_cache):
        """创建 Cluster CR，断言创建成功。"""
        with AllureHelper.api_test(ec_service):
            custom_resource = ClusterCustomResourceEntity(
                name=public_params.cr_name,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                message="I have an apple!",
                replicas=1,
            )
            create_resp = ec_service.create_cluster_custom_resource(
                cell_code=public_params.cell_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                custom_resource=custom_resource,
            )

            assert create_resp.get("code") == ApiCode.SUCCESS, (
                f"创建 Cluster CR 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )

            api_cache.set("ec_cr_cluster_created", True)

    @pytest.mark.dependency(name="cr_cluster_list", depends=["cr_cluster_create"])
    @pytest.mark.order(3)
    @allure.title("查询 Cluster CR 列表")
    @allure.description("查询 Cluster 级别 CR 列表并通过 labelSelector 过滤，验证包含新创建的 CR")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_cluster_crs(self, ec_service, public_params):
        """查询 Cluster CR 列表，断言包含目标 CR。"""
        with AllureHelper.api_test(ec_service):
            label_selector = f"name={public_params.cr_name},kind=Pod"
            list_resp = ec_service.list_cluster_custom_resources(
                cell_code=public_params.cell_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                label_selector=label_selector,
            )

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询 Cluster CR 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert public_params.cr_name in resp_str, (
                f"Cluster CR 列表中未找到 {public_params.cr_name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="cr_cluster_put", depends=["cr_cluster_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 Cluster CR")
    @allure.description("全量更新 Cluster CR 的 labels 和 spec 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_put_update_cluster_cr(self, ec_service, public_params):
        """PUT 全量更新 Cluster CR，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            custom_resource = ClusterCustomResourceEntity(
                name=public_params.cr_name,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                message="I have two apple!",
                replicas=2,
                extra_labels={"test": "update"},
            )
            put_resp = ec_service.update_cluster_custom_resource(
                cell_code=public_params.cell_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                name=public_params.cr_name,
                custom_resource=custom_resource,
            )

            assert put_resp.get("code") == ApiCode.SUCCESS, (
                f"PUT 更新 Cluster CR 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
            )

    @pytest.mark.dependency(name="cr_cluster_patch", depends=["cr_cluster_put"])
    @pytest.mark.order(5)
    @allure.title("PATCH 增量更新 Cluster CR")
    @allure.description("增量更新 Cluster CR 的 labels 和 replicas，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_patch_update_cluster_cr(self, ec_service, public_params):
        """PATCH 增量更新 Cluster CR，断言更新成功。"""
        with AllureHelper.api_test(ec_service):
            patch_entity = ClusterCustomResourcePatchEntity(
                replicas=3,
                labels={"test": "patch-update"},
            )
            patch_resp = ec_service.patch_cluster_custom_resource(
                cell_code=public_params.cell_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                name=public_params.cr_name,
                custom_resource=patch_entity,
            )

            assert patch_resp.get("code") == ApiCode.SUCCESS, (
                f"PATCH 增量更新 Cluster CR 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
            )

    @pytest.mark.dependency(name="cr_cluster_delete", depends=["cr_cluster_patch"])
    @pytest.mark.order(6)
    @allure.title("删除 Cluster CR")
    @allure.description("删除创建的 Cluster CR 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_cluster_cr(self, ec_service, public_params, api_cache):
        """删除 Cluster CR，断言删除成功并清理缓存标记。"""
        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_cluster_custom_resource(
                cell_code=public_params.cell_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                name=public_params.cr_name,
            )

            assert del_resp.get("code") == ApiCode.SUCCESS, (
                f"删除 Cluster CR 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )

            api_cache.set("ec_cr_cluster_created", False)

    @pytest.mark.dependency(depends=["cr_cluster_delete"])
    @pytest.mark.order(7)
    @allure.title("验证 Cluster CR 删除后不存在")
    @allure.description("删除后再次查询 Cluster CR，验证返回资源不存在")
    @allure.severity(allure.severity_level.NORMAL)
    def test_verify_cluster_cr_deleted(self, ec_service, public_params):
        """删除后验证 Cluster CR 已不存在。"""
        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_cluster_custom_resource(
                cell_code=public_params.cell_code,
                group=public_params.cr_group,
                version=public_params.cr_version,
                kind=public_params.cr_kind,
                name=public_params.cr_name,
            )

            assert get_resp.get("code") == ApiCode.NOT_FOUND, (
                f"Cluster CR 删除后仍能查询到, code: {get_resp.get('code')}, 响应: {get_resp}"
            )
