"""
弹性计算 Native CRD (CustomResourceDefinition) 接口测试

测试内容：CustomResourceDefinition 原生接口-特权接口（查询、创建、列表、删除）
"""
import json

import allure
import pytest

from base.api.entity.elastic_compute import CrdEntity, CrdNativePublicParams
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
@allure.story("CustomResourceDefinition 原生接口")
class TestEcNativeCrd:
    """
    注意：CRD 为特权接口，使用 X-API-KEY 鉴权。
    """

    TENANT = Tenant.ADMIN

    @pytest.fixture(scope="class")
    def native_service(self, service_factory):
        with service_factory(ElasticComputeNativeService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> CrdNativePublicParams:
        """提取 CRD 测试所需的公共参数。"""
        return CrdNativePublicParams(
            cluster_id=str(api_env.get("clusterId", "1")),
            name="crontabs.stable.example.com",
        )

    # ==================== 生命周期测试（每接口一函数）====================

    @pytest.mark.dependency(name="crd_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询指定 CRD 并清理已有资源")
    @allure.description("查询指定 CustomResourceDefinition 确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_crd_and_cleanup(self, native_service, public_params, api_cache):
        """查询指定 CRD，若已存在则删除。"""
        cluster_id = public_params.cluster_id
        name = public_params.name

        with AllureHelper.api_test(native_service):
            get_http_code, get_resp = native_service.get_crd(
                cluster_id=cluster_id, name=name,
            )

            assert get_http_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), (
                f"查询 CRD 返回异常, 期望200或404, 实际: {get_http_code}"
            )

            if get_http_code == HttpStatus.OK:
                native_service.delete_crd(
                    cluster_id=cluster_id, name=name,
                )
                assert native_service.last_response.status_code == HttpStatus.OK, (
                    f"删除已存在的 CRD 失败, status={native_service.last_response.status_code}"
                )

            api_cache.set("ec_crd_created", False)

    @pytest.mark.dependency(name="crd_create", depends=["crd_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 CustomResourceDefinition")
    @allure.description("创建 CRD 资源，验证 HTTP 状态码为 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_crd(self, native_service, public_params, api_cache):
        """创建 CRD，断言创建成功。"""
        cluster_id = public_params.cluster_id
        name = public_params.name

        with AllureHelper.api_test(native_service):
            crd = CrdEntity(
                name=name,
                group="stable.example.com",
                scope="Namespaced",
                plural="crontabs",
                singular="crontab",
                kind="CronTab",
                short_names=["ct"],
                version_name="v1",
                properties={
                    "cronSpec": {"type": "string"},
                    "image": {"type": "string"},
                    "replicas": {"type": "integer"},
                },
            )
            create_resp = native_service.create_crd(
                cluster_id=cluster_id, crd=crd,
            )
            create_http_code = native_service.last_response.status_code

            assert create_http_code == HttpStatus.CREATED, (
                f"创建 CRD 失败, 期望201, 实际: {create_http_code}, 响应: {create_resp}"
            )

            api_cache.set("ec_crd_created", True)

    @pytest.mark.dependency(name="crd_list", depends=["crd_create"])
    @pytest.mark.order(3)
    @allure.title("查询 CRD 列表")
    @allure.description("按标签选择器查询 CRD 列表，验证包含新创建的 CRD")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_crds(self, native_service, public_params):
        """查询 CRD 列表，断言包含目标资源。"""
        cluster_id = public_params.cluster_id
        name = public_params.name

        with AllureHelper.api_test(native_service):
            list_resp = native_service.list_crds(
                cluster_id=cluster_id,
                label_selector=f"name={name},test=crd",
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"查询 CRD 列表失败, status={native_service.last_response.status_code}"
            )
            resp_str = json.dumps(list_resp, ensure_ascii=False)
            assert name in resp_str, (
                f"CRD 列表未找到 {name}, 响应: {list_resp}"
            )

    @pytest.mark.dependency(name="crd_delete", depends=["crd_list"])
    @pytest.mark.order(4)
    @allure.title("删除 CustomResourceDefinition")
    @allure.description("删除创建的 CRD 清理测试环境，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_crd(self, native_service, public_params, api_cache):
        """删除 CRD，断言删除成功。"""
        cluster_id = public_params.cluster_id
        name = public_params.name

        with AllureHelper.api_test(native_service):
            native_service.delete_crd(
                cluster_id=cluster_id, name=name,
            )

            assert native_service.last_response.status_code == HttpStatus.OK, (
                f"删除 CRD 失败, status={native_service.last_response.status_code}"
            )

            api_cache.set("ec_crd_created", False)
