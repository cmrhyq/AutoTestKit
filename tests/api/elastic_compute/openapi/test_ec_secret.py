"""
弹性计算 OpenAPI Secret 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/SecretV2.jmx
线程组: Thread Group - secret
测试内容：Secret 完整生命周期（查询/删除/创建/列表/全集群列表/PUT 更新/PATCH 增量更新/删除）
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
@allure.story("Secret 生命周期接口")
class TestEcOpenapiSecret:
    """
    对应 JMeter 脚本: SecretV2.jmx
    线程组: Thread Group - secret

    拆分为独立接口测试函数，通过 pytest-dependency 保证执行顺序和依赖关系。
    执行顺序：查询 → 清理已存在 → 创建 → 列表查询 → 全集群列表查询 → PUT更新 → PATCH更新 → 删除清理
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc
    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Secret 测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode", "test"),
            "sys_code": api_env.get("sysCode", "test-sys"),
            "secret_name": "auto-test-probe-secret-test-0001",
        }

    # ---------------- Body helpers ----------------

    @staticmethod
    def _build_secret_create_payload(name: str) -> Dict[str, Any]:
        """构造创建 Secret 请求体。"""
        return {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
            },
            "type": "Opaque",
            "data": {
                "username": "YWRtaW4=",
                "password": "MWYyZDFlMmU2N2Rm",
            },
        }

    @staticmethod
    def _build_secret_put_payload(name: str) -> Dict[str, Any]:
        """构造 PUT 全量更新 Secret 请求体。"""
        return {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
            },
            "type": "Opaque",
            "data": {
                "username": "YWRtaW4=",
                "password": "dXBkYXRlZA==",
            },
        }

    @staticmethod
    def _build_secret_patch_payload() -> Dict[str, Any]:
        """构造 PATCH 增量更新 Secret 请求体。"""
        return {
            "metadata": {
                "labels": {
                    "test": "patch-test",
                },
            },
            "data": {
                "extra": "cGF0Y2hlZA==",
            },
        }

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询指定 Secret")
    @allure.description("查询指定 Secret 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="secret_query_and_cleanup")
    @pytest.mark.order(1)
    def test_query_secret_and_cleanup(self, ec_service, public_params, api_cache):
        """查询指定 Secret，若已存在则删除，确保测试环境干净。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        secret_name = public_params["secret_name"]

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_secret(
                cell_code=cell_code, sys_code=sys_code, name=secret_name,
            )
            ec_get_code = get_resp.get("code")

            assert ec_get_code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                f"查询 Secret 返回异常 code: {ec_get_code}, 响应: {get_resp}"
            )

            if ec_get_code == ApiCode.SUCCESS:
                del_resp = ec_service.delete_secret(
                    cell_code=cell_code, sys_code=sys_code, name=secret_name,
                )
                assert del_resp.get("code") == ApiCode.SUCCESS, (
                    f"删除已存在的 Secret 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
                )

            api_cache.set("ec_secret_created", False)

    @allure.title("创建 Secret 资源")
    @allure.description("创建 Opaque 类型 Secret，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="secret_create", depends=["secret_query_and_cleanup"])
    @pytest.mark.order(2)
    def test_create_secret(self, ec_service, public_params, api_cache):
        """创建 Secret，断言创建成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        secret_name = public_params["secret_name"]

        with AllureHelper.api_test(ec_service):
            create_payload = self._build_secret_create_payload(secret_name)
            create_resp = ec_service.create_secret(
                cell_code=cell_code, sys_code=sys_code, payload=create_payload,
            )

            assert create_resp.get("code") == ApiCode.SUCCESS, (
                f"创建 Secret 失败, code: {create_resp.get('code')}, 响应: {create_resp}"
            )
            resp_str = json.dumps(create_resp, ensure_ascii=False)
            assert secret_name in resp_str, (
                f"创建 Secret 响应中未包含资源名称 {secret_name}, 响应: {create_resp}"
            )

            api_cache.set("ec_secret_created", True)

    @allure.title("查询命名空间 Secret 列表")
    @allure.description("查询指定命名空间下 Secret 列表，验证包含新创建的 Secret")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="secret_list_ns", depends=["secret_create"])
    @pytest.mark.order(3)
    def test_list_secrets_by_namespace(self, ec_service, public_params):
        """查询 Namespace 下 Secret 列表，断言包含目标 Secret。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        secret_name = public_params["secret_name"]

        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_secrets_by_ns(
                cell_code=cell_code, sys_code=sys_code,
            )

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询 Namespace Secret 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert secret_name in resp_str, (
                f"Namespace Secret 列表未找到 {secret_name}, 响应: {list_resp}"
            )

    @allure.title("查询全集群 Secret 列表")
    @allure.description("查询全集群所有 Secret 列表，验证包含新创建的 Secret")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="secret_list_cell", depends=["secret_create"])
    @pytest.mark.order(4)
    def test_list_secrets_by_cell(self, ec_service, public_params):
        """查询全集群 Secret 列表，断言包含目标 Secret。"""
        cell_code = public_params["cell_code"]
        secret_name = public_params["secret_name"]

        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_secrets_by_cell(cell_code=cell_code)

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询全集群 Secret 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert secret_name in resp_str, (
                f"全集群 Secret 列表未找到 {secret_name}, 响应: {list_resp}"
            )

    @allure.title("PUT 全量更新 Secret")
    @allure.description("使用 PUT 方法全量更新 Secret 的 data 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="secret_put", depends=["secret_create"])
    @pytest.mark.order(5)
    def test_put_update_secret(self, ec_service, public_params):
        """PUT 全量更新 Secret，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        secret_name = public_params["secret_name"]

        with AllureHelper.api_test(ec_service):
            put_payload = self._build_secret_put_payload(secret_name)
            put_resp = ec_service.update_secret(
                cell_code=cell_code, sys_code=sys_code, name=secret_name,
                payload=put_payload,
            )

            assert put_resp.get("code") == ApiCode.SUCCESS, (
                f"PUT 更新 Secret 失败, code: {put_resp.get('code')}, 响应: {put_resp}"
            )

    @allure.title("PATCH 增量更新 Secret")
    @allure.description("使用 PATCH 方法增量更新 Secret 的 labels 和 data 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="secret_patch", depends=["secret_put"])
    @pytest.mark.order(6)
    def test_patch_update_secret(self, ec_service, public_params):
        """PATCH 增量更新 Secret，断言更新成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        secret_name = public_params["secret_name"]

        with AllureHelper.api_test(ec_service):
            patch_payload = self._build_secret_patch_payload()
            patch_resp = ec_service.patch_secret(
                cell_code=cell_code, sys_code=sys_code, name=secret_name,
                payload=patch_payload,
            )

            assert patch_resp.get("code") == ApiCode.SUCCESS, (
                f"PATCH 增量更新 Secret 失败, code: {patch_resp.get('code')}, 响应: {patch_resp}"
            )

    @allure.title("删除 Secret 资源")
    @allure.description("删除创建的 Secret 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="secret_delete", depends=["secret_patch"])
    @pytest.mark.order(7)
    def test_delete_secret(self, ec_service, public_params, api_cache):
        """删除 Secret，断言删除成功并清理缓存标记。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        secret_name = public_params["secret_name"]

        with AllureHelper.api_test(ec_service):
            del_resp = ec_service.delete_secret(
                cell_code=cell_code, sys_code=sys_code, name=secret_name,
            )

            assert del_resp.get("code") == ApiCode.SUCCESS, (
                f"删除 Secret 失败, code: {del_resp.get('code')}, 响应: {del_resp}"
            )

            api_cache.set("ec_secret_created", False)
