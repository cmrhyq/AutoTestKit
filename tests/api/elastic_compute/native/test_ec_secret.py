"""
弹性计算 Native Secret 接口测试

测试内容：Secret 原生接口完成生命周期测试（查询、创建、列表、更新、删除）

注意：Secret 的 data 字段值需要 Base64 编码。
"""
import json
import time

import allure
import pytest

from base.api.entity.elastic_compute import SecretEntity, SecretNativePublicParams
from base.api.services.elastic_compute_native_service import (
    ElasticComputeNativeService,
)
from core.log import get_logger
from core.reporting.allure_helper import AllureHelper
from core.constants import HttpStatus, Tenant

logger = get_logger(__name__)



@pytest.mark.api
@pytest.mark.native
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Native接口")
@allure.story("Secret 原生接口")
class TestEcNativeSecret:

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, test_env) -> SecretNativePublicParams:
        """提取 Secret 测试所需的公共参数。"""
        return SecretNativePublicParams(
            cluster_id=str(test_env.get("clusterId", "1")),
            namespace=test_env.get("namespace", "test-admin"),
            name="native-test-secret-001",
            paas_owner=test_env.get("user", "panji_probe"),
        )

    @pytest.mark.dependency(name="secret_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 Secret 并清理已有资源")
    @allure.description("查询指定 Secret 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_secret_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 Secret，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, _ = native_service.get_secret(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 Secret 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_secret(
                    cluster_id=cluster_id, namespace=namespace, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 Secret 失败, "
                    f"status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_secret_created", False)

    @pytest.mark.dependency(name="secret_create", depends=["secret_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 Secret")
    @allure.description("创建 Secret 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_secret(self, native_service, public_params, api_cache):
        """创建 Secret，断言创建成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace

        with AllureHelper.api_test(native_service):
            secret = SecretEntity(
                name=public_params.name,
                paas_owner=public_params.paas_owner,
            )
            create_resp = native_service.create_secret(
                cluster_id=cluster_id, namespace=namespace, secret=secret,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 Secret 失败, 期望201, 实际: {create_http_code}, 响应: {create_resp}"
            )

            api_cache.set("ec_secret_created", True)

    @pytest.mark.dependency(name="secret_list", depends=["secret_create"])
    @pytest.mark.order(3)
    @allure.title("查询 Secret 列表")
    @allure.description("查询 Secret 列表，验证包含新创建的 Secret")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_secrets(self, native_service, public_params):
        """查询 Secret 列表，断言包含目标资源。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        time.sleep(2)

        with AllureHelper.api_test(native_service):
            list_resp = native_service.list_secrets(
                cluster_id=cluster_id, namespace=namespace,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 Secret 列表失败, status={native_service.last_response.status_code}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert name in resp_str, (
                f"Secret 列表未找到 {name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="secret_update", depends=["secret_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 Secret")
    @allure.description("全量更新 Secret（含 data 与 labels 变更），验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_secret(self, native_service, public_params):
        """PUT 全量更新 Secret，断言更新成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            secret = SecretEntity(
                name=public_params.name,
                paas_owner=public_params.paas_owner,
                data={"test": "dXBkYXRl"},
                extra_labels={"test": "update"},
            )
            native_service.update_secret(
                cluster_id=cluster_id, namespace=namespace, name=name, secret=secret,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"更新 Secret 失败, status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(name="secret_delete", depends=["secret_update"])
    @pytest.mark.order(5)
    @allure.title("删除 Secret")
    @allure.description("删除创建的 Secret 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_secret(self, native_service, public_params, api_cache):
        """删除 Secret，断言删除成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            native_service.delete_secret(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 Secret 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_secret_created", False)
