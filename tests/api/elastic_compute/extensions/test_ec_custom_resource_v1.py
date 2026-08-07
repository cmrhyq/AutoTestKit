"""
CustomResource V1 自定义资源接口测试

测试内容：CR 资源的查询、创建、列表、更新、删除完整生命周期
"""

import json

import allure
import pytest

from base.api.entity.elastic_compute import (
    CustomResourceCreateEntity,
    CustomResourcePublicParams,
    CustomResourceUpdateEntity,
)
from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.reporting.allure_helper import AllureHelper
from core.constants import HttpStatus


@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("CustomResource V1 自定义资源生命周期接口")
class TestEcExtensionsCustomResourceV1:

    TENANT = None

    @pytest.fixture(scope="class")
    def ec_ext_service(self, test_env):
        """Extensions 类接口使用 apikey 鉴权，不需要 Bearer token。"""
        service = ElasticComputeExtService(
            base_url=test_env.get("apiInnerBaseUrl"),
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, test_env) -> CustomResourcePublicParams:
        """提取 CustomResource 测试所需的公共参数。"""
        return CustomResourcePublicParams(
            cluster_id=str(test_env.get("clusterId", "1")),
            group="test.example.com",
            version="v1",
            namespace=test_env.get("namespace", "probe"),
            kind="Banana",
            name="test-banana-001",
        )

    @pytest.mark.dependency(name="cr_query_and_cleanup")
    @pytest.mark.order(1)
    @allure.title("查询 CR 资源并清理")
    @allure.description("查询指定 CR 资源确认当前状态，若存在则先删除以保证后续创建的幂等性")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_query_cr_and_cleanup(self, ec_ext_service, public_params, api_cache):
        """查询 CR 资源，若已存在则删除，确保测试环境干净。"""
        cluster_id = public_params.cluster_id
        group = public_params.group
        version = public_params.version
        namespace = public_params.namespace
        kind = public_params.kind
        name = public_params.name

        with AllureHelper.api_test(ec_ext_service):
            status_code, _ = ec_ext_service.get_custom_resource(
                cluster_id=cluster_id,
                group=group,
                version=version,
                namespace=namespace,
                kind=kind,
                name=name,
            )

            # 断言：接口返回正常（200=存在，404=不存在，两者均为正常）
            assert status_code in (HttpStatus.OK, HttpStatus.NOT_FOUND), f"查询 CR 返回异常 HTTP status: {status_code}"

            # 若已存在，先删除以保证幂等
            if status_code == HttpStatus.OK:
                del_status, _ = ec_ext_service.delete_custom_resource(
                    cluster_id=cluster_id,
                    group=group,
                    version=version,
                    namespace=namespace,
                    kind=kind,
                    name=name,
                )
                assert del_status == HttpStatus.OK, f"删除已存在的 CR 失败, HTTP status: {del_status}"

            api_cache.set("cr_created", False)

    @pytest.mark.dependency(name="cr_create", depends=["cr_query_and_cleanup"])
    @pytest.mark.order(2)
    @allure.title("创建 CR 实例")
    @allure.description("创建自定义资源实例，验证返回 HTTP 200")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_custom_resource(self, ec_ext_service, public_params, api_cache):
        """创建 CR 实例，断言 HTTP status 为 200。"""
        cluster_id = public_params.cluster_id
        group = public_params.group
        version = public_params.version
        namespace = public_params.namespace
        kind = public_params.kind
        name = public_params.name

        with AllureHelper.api_test(ec_ext_service):
            cr = CustomResourceCreateEntity.from_public_params(public_params)
            status_code, response_json = ec_ext_service.create_custom_resource(
                cluster_id=cluster_id,
                group=group,
                version=version,
                namespace=namespace,
                kind=kind,
                cr=cr,
            )

            assert status_code == HttpStatus.OK, f"创建 CR 失败, HTTP status: {status_code}, 响应: {response_json}"

            api_cache.set("cr_created", True)

    @pytest.mark.dependency(name="cr_list", depends=["cr_create"])
    @pytest.mark.order(3)
    @allure.title("查询 CR 列表")
    @allure.description("查询自定义资源列表，验证包含新创建的 CR 实例")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_custom_resources(self, ec_ext_service, public_params):
        """查询 CR 列表，断言包含目标 CR 名称。"""
        cluster_id = public_params.cluster_id
        group = public_params.group
        version = public_params.version
        namespace = public_params.namespace
        kind = public_params.kind
        name = public_params.name

        with AllureHelper.api_test(ec_ext_service):
            status_code, response_json = ec_ext_service.list_custom_resources(
                cluster_id=cluster_id,
                group=group,
                version=version,
                namespace=namespace,
                kind=kind,
            )

            assert status_code == HttpStatus.OK, f"查询 CR 列表失败, HTTP status: {status_code}, 响应: {response_json}"

            # 断言：列表中包含目标 CR 名称
            resp_str = json.dumps(response_json, ensure_ascii=False)
            assert name in resp_str, f"CR 列表未找到 {name}, 响应: {response_json}"

    @pytest.mark.dependency(name="cr_update", depends=["cr_list"])
    @pytest.mark.order(4)
    @allure.title("更新 CR 实例")
    @allure.description("全量更新自定义资源实例，验证更新成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_custom_resource(self, ec_ext_service, public_params):
        """更新 CR 实例，断言 HTTP status 为 200。"""
        cluster_id = public_params.cluster_id
        group = public_params.group
        version = public_params.version
        namespace = public_params.namespace
        kind = public_params.kind
        name = public_params.name

        with AllureHelper.api_test(ec_ext_service):
            cr = CustomResourceUpdateEntity.from_public_params(public_params)
            status_code, response_json = ec_ext_service.update_custom_resource(
                cluster_id=cluster_id,
                group=group,
                version=version,
                namespace=namespace,
                kind=kind,
                cr=cr,
            )

            assert status_code == HttpStatus.OK, f"更新 CR 失败, HTTP status: {status_code}, 响应: {response_json}"

    @pytest.mark.dependency(name="cr_delete", depends=["cr_update"])
    @pytest.mark.order(5)
    @allure.title("删除 CR 实例")
    @allure.description("删除自定义资源实例，验证删除成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_custom_resource(self, ec_ext_service, public_params, api_cache):
        """删除 CR 实例，断言 HTTP status 为 200。"""
        cluster_id = public_params.cluster_id
        group = public_params.group
        version = public_params.version
        namespace = public_params.namespace
        kind = public_params.kind
        name = public_params.name

        with AllureHelper.api_test(ec_ext_service):
            status_code, response_json = ec_ext_service.delete_custom_resource(
                cluster_id=cluster_id,
                group=group,
                version=version,
                namespace=namespace,
                kind=kind,
                name=name,
            )

            assert status_code == HttpStatus.OK, f"删除 CR 失败, HTTP status: {status_code}, 响应: {response_json}"

            api_cache.set("cr_created", False)

    @pytest.mark.dependency(depends=["cr_delete"])
    @pytest.mark.order(6)
    @allure.title("验证 CR 删除后不存在")
    @allure.description("删除后再次查询 CR 资源，验证返回 404 资源不存在")
    @allure.severity(allure.severity_level.NORMAL)
    def test_verify_cr_deleted(self, ec_ext_service, public_params):
        """删除后验证 CR 已不存在。"""
        cluster_id = public_params.cluster_id
        group = public_params.group
        version = public_params.version
        namespace = public_params.namespace
        kind = public_params.kind
        name = public_params.name

        with AllureHelper.api_test(ec_ext_service):
            status_code, _ = ec_ext_service.get_custom_resource(
                cluster_id=cluster_id,
                group=group,
                version=version,
                namespace=namespace,
                kind=kind,
                name=name,
            )

            assert status_code == HttpStatus.NOT_FOUND, f"CR 删除后仍能查询到, HTTP status: {status_code}"
