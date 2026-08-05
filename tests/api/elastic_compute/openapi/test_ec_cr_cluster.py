"""
Cluster 级别 CustomResource 接口测试

转换自 JMeter 脚本: cr-cluster.jmx
测试内容：针对 Cluster 级别 CR 增删改查进行测试（查询、创建、列表、PUT 更新、PATCH 更新、删除）
"""
import json
from typing import Any, Dict

import allure
import pytest

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
    """
    对应 JMeter 脚本: cr-cluster.jmx
    线程组: Thread Group - cluster custom resource
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc
    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Cluster CR 测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode"),
            "cr_group": "test.example.com",
            "cr_version": "v1",
            "cr_kind": "Apple",
            "cr_name": "test-apple",
        }

    # ==================== Helper 方法 ====================

    @staticmethod
    def _build_cr_create_payload(
        group: str, version: str, kind: str, name: str,
    ) -> Dict[str, Any]:
        """构造 Cluster 级别 CR 创建请求体。"""
        return {
            "apiVersion": f"{group}/{version}",
            "kind": kind,
            "metadata": {
                "name": name,
                "labels": {
                    "name": name,
                    "kind": kind,
                },
            },
            "spec": {
                "message": "I have an apple!",
                "replicas": 1,
            },
        }

    @staticmethod
    def _build_cr_update_payload(
        group: str, version: str, kind: str, name: str,
    ) -> Dict[str, Any]:
        """构造 Cluster 级别 CR PUT 全量更新请求体。"""
        return {
            "apiVersion": f"{group}/{version}",
            "kind": kind,
            "metadata": {
                "name": name,
                "labels": {
                    "name": name,
                    "kind": kind,
                    "test": "update",
                },
            },
            "spec": {
                "message": "I have two apple!",
                "replicas": 2,
            },
        }

    @staticmethod
    def _build_cr_patch_payload() -> Dict[str, Any]:
        """构造 Cluster 级别 CR PATCH 增量更新请求体。"""
        return {
            "metadata": {
                "labels": {
                    "test": "patch-update",
                },
            },
            "spec": {
                "replicas": 3,
            },
        }

    # ==================== 测试方法 ====================

    @pytest.mark.dependency(name="cr_cluster_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 Cluster CR 并清理环境")
    @allure.description("查询指定 Cluster CR 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_cr_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 Cluster CR，若已存在则删除，确保测试环境干净。"""
        cell_code = public_params["cell_code"]
        cr_group = public_params["cr_group"]
        cr_version = public_params["cr_version"]
        cr_kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_cluster_custom_resource(
                cell_code=cell_code,
                group=cr_group,
                version=cr_version,
                kind=cr_kind,
                name=cr_name,
            )
            ec_get_code = get_resp.get("code")

            # 断言：接口返回正常（2000=存在，4004=不存在，两者均为正常）
            assert ec_get_code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                f"查询 Cluster CR 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            # 若已存在，先删除以保证幂等
            if ec_get_code == ApiCode.SUCCESS:
                del_resp = ec_service.delete_cluster_custom_resource(
                    cell_code=cell_code,
                    group=cr_group,
                    version=cr_version,
                    kind=cr_kind,
                    name=cr_name,
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
        cell_code = public_params["cell_code"]
        cr_group = public_params["cr_group"]
        cr_version = public_params["cr_version"]
        cr_kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            create_payload = self._build_cr_create_payload(
                group=cr_group, version=cr_version, kind=cr_kind, name=cr_name,
            )
            create_resp = ec_service.create_cluster_custom_resource(
                cell_code=cell_code,
                group=cr_group,
                version=cr_version,
                kind=cr_kind,
                payload=create_payload,
            )

            # 断言：业务码为成功
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
        cell_code = public_params["cell_code"]
        cr_group = public_params["cr_group"]
        cr_version = public_params["cr_version"]
        cr_kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            label_selector = f"name={cr_name},kind=Pod"
            list_resp = ec_service.list_cluster_custom_resources(
                cell_code=cell_code,
                group=cr_group,
                version=cr_version,
                kind=cr_kind,
                label_selector=label_selector,
            )

            # 断言：业务码为成功
            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询 Cluster CR 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            # 断言：列表中包含目标 CR 名称
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert cr_name in resp_str, (
                f"Cluster CR 列表中未找到 {cr_name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="cr_cluster_put", depends=["cr_cluster_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 Cluster CR")
    @allure.description("使用 PUT 方法全量更新 Cluster CR 的 labels 和 spec 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_put_update_cluster_cr(self, ec_service, public_params):
        """PUT 全量更新 Cluster CR，断言更新成功。"""
        cell_code = public_params["cell_code"]
        cr_group = public_params["cr_group"]
        cr_version = public_params["cr_version"]
        cr_kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            put_payload = self._build_cr_update_payload(
                group=cr_group, version=cr_version, kind=cr_kind, name=cr_name,
            )
            put_resp = ec_service.update_cluster_custom_resource(
                cell_code=cell_code,
                group=cr_group,
                version=cr_version,
                kind=cr_kind,
                name=cr_name,
                payload=put_payload,
            )

            # 断言：业务码为成功
            assert put_resp.get("code") == ApiCode.SUCCESS, (
                f"PUT 更新 Cluster CR 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
            )

    @pytest.mark.dependency(name="cr_cluster_patch", depends=["cr_cluster_put"])
    @pytest.mark.order(5)
    @allure.title("PATCH 增量更新 Cluster CR")
    @allure.description("使用 PATCH 方法增量更新 Cluster CR 的 labels 和 replicas，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_patch_update_cluster_cr(self, ec_service, public_params):
        """PATCH 增量更新 Cluster CR，断言更新成功。"""
        cell_code = public_params["cell_code"]
        cr_group = public_params["cr_group"]
        cr_version = public_params["cr_version"]
        cr_kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            patch_payload = self._build_cr_patch_payload()
            patch_resp = ec_service.patch_cluster_custom_resource(
                cell_code=cell_code,
                group=cr_group,
                version=cr_version,
                kind=cr_kind,
                name=cr_name,
                payload=patch_payload,
            )

            # 断言：业务码为成功
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
        cell_code = public_params["cell_code"]
        cr_group = public_params["cr_group"]
        cr_version = public_params["cr_version"]
        cr_kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_cluster_custom_resource(
                cell_code=cell_code,
                group=cr_group,
                version=cr_version,
                kind=cr_kind,
                name=cr_name,
            )

            # 断言：业务码为成功
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
        cell_code = public_params["cell_code"]
        cr_group = public_params["cr_group"]
        cr_version = public_params["cr_version"]
        cr_kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_cluster_custom_resource(
                cell_code=cell_code,
                group=cr_group,
                version=cr_version,
                kind=cr_kind,
                name=cr_name,
            )

            # 断言：业务码为资源不存在
            assert get_resp.get("code") == ApiCode.NOT_FOUND, (
                f"Cluster CR 删除后仍能查询到, code: {get_resp.get('code')}, 响应: {get_resp}"
            )
