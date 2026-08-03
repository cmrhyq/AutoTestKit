"""
弹性计算 OpenAPI Namespace 级别 CustomResource 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/CustomResource-ns.jmx
线程组: Thread Group - CustomResource-ns
测试内容：Namespace 级别 CR 完整生命周期（查询/删除/创建/列表/PUT 更新/PATCH 增量更新/删除）
"""
import json
from typing import Any, Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper

# 业务码 / 常量
BUSINESS_SUCCESS_CODE = 2000
RESOURCE_NOT_FOUND_CODE = 4004

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

    TENANT = "monitor-group"

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc
    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Namespace 级别 CR 测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode"),
            "sys_code": api_env.get("sysCode"),
            "cr_group": "test.example.com",
            "cr_version": "v1",
            "cr_kind": "Apple",
            "cr_name": "auto-test-probe-cr-ns-test-0001",
        }

    # ---------------- Body helpers ----------------

    @staticmethod
    def _build_cr_create_payload(name: str) -> Dict[str, Any]:
        """
        构造创建 Namespace 级别 CR 请求体。

        源自 JMX CustomResource-ns.jmx 中"创建CR请求" sampler 的 postBodyRaw。
        """
        return {
            "apiVersion": "test.example.com/v1",
            "kind": "Apple",
            "metadata": {
                "name": name,
            },
            "spec": {
                "color": "red",
            },
        }

    @staticmethod
    def _build_cr_put_payload(name: str) -> Dict[str, Any]:
        """
        构造 PUT 全量更新 Namespace 级别 CR 请求体。

        源自 JMX CustomResource-ns.jmx 中"更新指定CR" sampler 的 postBodyRaw。
        """
        return {
            "apiVersion": "test.example.com/v1",
            "kind": "Apple",
            "metadata": {
                "name": name,
            },
            "spec": {
                "color": "green",
            },
        }

    @staticmethod
    def _build_cr_patch_payload() -> Dict[str, Any]:
        """
        构造 PATCH 增量更新 Namespace 级别 CR 请求体。

        源自 JMX CustomResource-ns.jmx 中"增量更新指定CR" sampler 的 postBodyRaw。
        """
        return {
            "metadata": {
                "labels": {
                    "test": "test2",
                },
            },
            "spec": {
                "color": "blue",
            },
        }

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询指定 Namespace 级别 CR")
    @allure.description("查询指定 Namespace 级别 CR 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="cr_ns_query_and_cleanup")
    @pytest.mark.order(1)
    def test_query_cr_ns_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 Namespace 级别 CR，若已存在则删除，确保测试环境干净。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        group = public_params["cr_group"]
        version = public_params["cr_version"]
        kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_ns_custom_resource(
                cell_code=cell_code, sys_code=sys_code,
                group=group, version=version, kind=kind, name=cr_name,
            )
            ec_get_code = get_resp.get("code")

            # 断言：接口返回正常（2000=存在，4004=不存在，两者均为正常）
            assert ec_get_code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"查询 Namespace CR 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            # 若已存在，先删除以保证幂等
            if ec_get_code == BUSINESS_SUCCESS_CODE:
                del_resp = ec_service.delete_ns_custom_resource(
                    cell_code=cell_code, sys_code=sys_code,
                    group=group, version=version, kind=kind, name=cr_name,
                )
                assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
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
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        group = public_params["cr_group"]
        version = public_params["cr_version"]
        kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            create_payload = self._build_cr_create_payload(cr_name)
            create_resp = ec_service.create_ns_custom_resource(
                cell_code=cell_code, sys_code=sys_code,
                group=group, version=version, kind=kind,
                payload=create_payload,
            )

            # 断言：业务码为成功
            assert create_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"创建 Namespace CR 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )
            # 断言：返回数据中包含 CR 名称
            resp_str = json.dumps(create_resp, ensure_ascii=False)
            assert cr_name in resp_str, (
                f"创建 Namespace CR 响应中未包含资源名称 {cr_name}, 响应: {create_resp}"
            )

            api_cache.set("ec_cr_ns_created", True)

    @allure.title("查询 Namespace 级别 CR 列表")
    @allure.description("查询 Namespace 级别 CR 列表，验证包含新创建的 CR")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="cr_ns_list", depends=["cr_ns_create"])
    @pytest.mark.order(3)
    def test_list_cr_ns(self, ec_service, public_params):
        """查询 Namespace 级别 CR 列表，断言包含目标 CR。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        group = public_params["cr_group"]
        version = public_params["cr_version"]
        kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_ns_custom_resources(
                cell_code=cell_code, sys_code=sys_code,
                group=group, version=version, kind=kind,
            )

            # 断言：业务码为成功
            assert list_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Namespace CR 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            # 断言：列表中包含目标 CR
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert cr_name in resp_str, (
                f"Namespace CR 列表未找到 {cr_name}, 响应: {list_resp}"
            )

    @allure.title("PUT 全量更新 Namespace 级别 CR")
    @allure.description("使用 PUT 方法全量更新 Namespace 级别 CR 的 spec 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="cr_ns_put", depends=["cr_ns_create"])
    @pytest.mark.order(4)
    def test_put_update_cr_ns(self, ec_service, public_params):
        """PUT 全量更新 Namespace 级别 CR，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        group = public_params["cr_group"]
        version = public_params["cr_version"]
        kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            put_payload = self._build_cr_put_payload(cr_name)
            put_resp = ec_service.update_ns_custom_resource(
                cell_code=cell_code, sys_code=sys_code,
                group=group, version=version, kind=kind, name=cr_name,
                payload=put_payload,
            )

            # 断言：业务码为成功
            assert put_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PUT 更新 Namespace CR 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
            )
            # 断言：响应中包含更新后的数据值
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
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        group = public_params["cr_group"]
        version = public_params["cr_version"]
        kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            patch_payload = self._build_cr_patch_payload()
            patch_resp = ec_service.patch_ns_custom_resource(
                cell_code=cell_code, sys_code=sys_code,
                group=group, version=version, kind=kind, name=cr_name,
                payload=patch_payload,
            )

            # 断言：业务码为成功
            assert patch_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"PATCH 增量更新 Namespace CR 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
            )
            # 断言：响应中包含增量更新后的数据值
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
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        group = public_params["cr_group"]
        version = public_params["cr_version"]
        kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_ns_custom_resource(
                cell_code=cell_code, sys_code=sys_code,
                group=group, version=version, kind=kind, name=cr_name,
            )

            # 断言：业务码为成功
            assert del_resp.get("code") == BUSINESS_SUCCESS_CODE, (
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
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        group = public_params["cr_group"]
        version = public_params["cr_version"]
        kind = public_params["cr_kind"]
        cr_name = public_params["cr_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_ns_custom_resource(
                cell_code=cell_code, sys_code=sys_code,
                group=group, version=version, kind=kind, name=cr_name,
            )

            # 断言：业务码为资源不存在
            assert get_resp.get("code") == RESOURCE_NOT_FOUND_CODE, (
                f"Namespace CR 删除后仍能查询到, code: {get_resp.get('code')}, 响应: {get_resp}"
            )
