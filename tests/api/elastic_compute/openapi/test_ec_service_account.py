"""
弹性计算 OpenAPI ServiceAccount 接口测试

测试内容：ServiceAccount 查询接口（全集群列表/命名空间列表/查询指定）
"""
import json

import allure
import pytest

from base.api.entity.elastic_compute.openapi import ServiceAccountPublicParams
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("ServiceAccount 查询接口")
class TestEcOpenapiServiceAccount:
    """
    拆分为独立接口测试函数，通过 pytest-dependency 保证执行顺序和依赖关系。
    执行顺序：全集群列表 → 命名空间列表 → 查询指定 ServiceAccount
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> ServiceAccountPublicParams:
        """提取 ServiceAccount 测试所需的公共参数。"""
        return ServiceAccountPublicParams(
            cell_code=api_env.get("cellCode", "test"),
            sys_code=api_env.get("sysCode", "test-sys"),
        )

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询全集群 ServiceAccount 列表")
    @allure.description("查询全集群 ServiceAccount 列表，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="sa_list_cell")
    @pytest.mark.order(1)
    def test_list_service_accounts_by_cell(self, ec_service, public_params):
        """查询全集群 ServiceAccount 列表，断言成功。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_service_accounts_by_cell(
                cell_code=public_params.cell_code,
            )

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询全集群 ServiceAccount 列表失败, code: {list_resp.get('code')}, "
                f"响应: {list_resp}"
            )

    @allure.title("查询命名空间 ServiceAccount 列表")
    @allure.description("查询指定命名空间下 ServiceAccount 列表，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="sa_list_ns", depends=["sa_list_cell"])
    @pytest.mark.order(2)
    def test_list_service_accounts_by_ns(self, ec_service, api_cache, public_params):
        """查询 Namespace 下 ServiceAccount 列表，断言成功。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_service_accounts_by_ns(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
            )

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询 Namespace ServiceAccount 列表失败, code: {list_resp.get('code')}, "
                f"响应: {list_resp}"
            )

            # 提取首条 ServiceAccount 名称供后续 get 接口使用
            data = list_resp.get("data", [])
            sa_name = data[0]["metadata"]["name"] if data else "default"
            api_cache.set("sa_name", sa_name)

    @allure.title("查询指定 ServiceAccount")
    @allure.description("查询指定 ServiceAccount 详情，验证响应包含目标名称")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="sa_get", depends=["sa_list_ns"])
    @pytest.mark.order(3)
    def test_get_service_account(self, ec_service, public_params, api_cache):
        """查询指定 ServiceAccount，断言返回成功且包含目标名称。"""
        sa_name = api_cache.get("sa_name", "default")

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_service_account(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=sa_name,
            )

            assert get_resp.get("code") == ApiCode.SUCCESS, (
                f"查询 ServiceAccount 失败, code: {get_resp.get('code')}, 响应: {get_resp}"
            )
            resp_str = json.dumps(get_resp, ensure_ascii=False)
            assert sa_name in resp_str, (
                f"响应中未包含 ServiceAccount 名称 {sa_name}, 响应: {get_resp}"
            )
