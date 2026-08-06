"""
弹性计算 Native ConfigMap 接口测试

测试内容：ConfigMap 原生接口完成生命周期测试（查询、创建、列表、更新、删除）
"""
import json

import allure
import pytest

from base.api.entity.elastic_compute import (
    ConfigMapEntity,
    ConfigMapNativePublicParams,
)
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
@allure.story("ConfigMap 原生接口")
class TestEcNativeConfigmap:

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> ConfigMapNativePublicParams:
        """提取 ConfigMap (Native) 测试所需的公共参数。"""
        return ConfigMapNativePublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            namespace=api_env.get("namespace", "test-admin"),
            name="native-test-cm",
            paas_owner=api_env.get("user", "panji_probe"),
        )

    # ==================== 生命周期测试（每接口一函数）====================

    @pytest.mark.dependency(name="native_cm_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 ConfigMap 并清理已有资源")
    @allure.description("查询指定 ConfigMap(Native) 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_configmap_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 ConfigMap，若已存在则删除。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, get_resp = native_service.get_native_configmap(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 ConfigMap 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_native_configmap(
                    cluster_id=cluster_id, namespace=namespace, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 ConfigMap 失败, status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_native_cm_created", False)

    @pytest.mark.dependency(name="native_cm_create", depends=["native_cm_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 ConfigMap")
    @allure.description("创建 ConfigMap(Native) 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_configmap(self, native_service, public_params, api_cache):
        """创建 ConfigMap，断言创建成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace

        with AllureHelper.api_test(native_service):
            cm = ConfigMapEntity(
                name=public_params.name,
                paas_owner=public_params.paas_owner,
            )
            create_resp = native_service.create_native_configmap(
                cluster_id=cluster_id, namespace=namespace, cm=cm,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 ConfigMap 失败, 期望201, 实际: {create_http_code}, 响应: {create_resp}"
            )

            api_cache.set("ec_native_cm_created", True)

    @pytest.mark.dependency(name="native_cm_list", depends=["native_cm_create"])
    @pytest.mark.order(3)
    @allure.title("查询 ConfigMap 列表")
    @allure.description("按标签选择器查询 ConfigMap 列表，验证包含新创建的 ConfigMap")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_configmaps(self, native_service, public_params):
        """查询 ConfigMap 列表，断言包含目标资源。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            list_resp = native_service.list_native_configmaps(
                cluster_id=cluster_id,
                namespace=namespace,
                label_selector=f"name={name}",
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 ConfigMap 列表失败, status={native_service.last_response.status_code}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert f'"name":"{name}"' in resp_str or name in resp_str, (
                f"ConfigMap 列表未找到 {name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="native_cm_update", depends=["native_cm_create"])
    @pytest.mark.order(4)
    @allure.title("PUT 全量更新 ConfigMap")
    @allure.description("全量更新 ConfigMap 的 data 和 labels 字段，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_configmap(self, native_service, public_params):
        """PUT 全量更新 ConfigMap，断言更新成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            cm = ConfigMapEntity(
                name=public_params.name,
                paas_owner=public_params.paas_owner,
                data={"test": "update"},
                extra_labels={"test": "update"},
            )
            native_service.update_native_configmap(
                cluster_id=cluster_id, namespace=namespace, name=name, cm=cm,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"更新 ConfigMap 失败, status={native_service.last_response.status_code}"
            )

    @pytest.mark.dependency(name="native_cm_delete", depends=["native_cm_update"])
    @pytest.mark.order(5)
    @allure.title("删除 ConfigMap")
    @allure.description("删除创建的 ConfigMap(Native) 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_configmap(self, native_service, public_params, api_cache):
        """删除 ConfigMap，断言删除成功。"""
        cluster_id = public_params.cluster_id
        namespace = public_params.namespace
        name = public_params.name

        with AllureHelper.api_test(native_service):
            native_service.delete_native_configmap(
                cluster_id=cluster_id, namespace=namespace, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 ConfigMap 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_native_cm_created", False)
