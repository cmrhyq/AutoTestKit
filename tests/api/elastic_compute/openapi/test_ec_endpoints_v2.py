"""
弹性计算 OpenAPI Endpoints 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/EndpointsV2.jmx
线程组: Thread Group - Endpoints
测试内容：Endpoints 查询接口（查询列表 + 查询指定 Endpoints）
"""
import json

import allure
import pytest

from base.api.entity.elastic_compute.openapi import EndpointsV2PublicParams
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant
from core.reporting.allure_helper import AllureHelper

@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("Endpoints 查询接口")
class TestEcOpenapiEndpointsV2:
    """
    对应 JMeter 脚本: EndpointsV2.jmx
    线程组: Thread Group - Endpoints

    包含 2 个接口：查询 Endpoints 列表 → 从列表提取 name → 查询指定 Endpoints。
    通过 pytest-dependency 保证执行顺序。
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> EndpointsV2PublicParams:
        """提取 Endpoints 测试所需的公共参数。"""
        return EndpointsV2PublicParams(
            cell_code=api_env.get("cellCode"),
            sys_code=api_env.get("sysCode"),
        )

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询 Endpoints 列表")
    @allure.description("查询指定命名空间下的 Endpoints 列表，验证返回业务码为 2000 并提取首条 name")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="endpoints_list")
    @pytest.mark.order(1)
    def test_list_endpoints(self, ec_service, public_params, api_cache):
        """查询 Endpoints 列表，断言成功并缓存首条 name。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_endpoints(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
            )

            # 断言：业务码为成功
            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询 Endpoints 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )
            # 断言：返回数据不为空
            data = list_resp.get("data")
            assert data is not None and len(data) > 0, (
                f"查询 Endpoints 列表返回 data 为空, 响应: {list_resp}"
            )

            # 提取首条 Endpoints 的 name（对应 JMX JSONPostProcessor: $.data[0].metadata.name）
            ep_name = data[0].get("metadata", {}).get("name")
            assert ep_name is not None, (
                f"Endpoints 列表首条数据缺少 metadata.name, 响应: {list_resp}"
            )
            api_cache.set("endpoints_name", ep_name)

    @allure.title("查询指定 Endpoints")
    @allure.description("根据列表中提取的 name 查询指定 Endpoints，验证返回业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="endpoints_get", depends=["endpoints_list"])
    @pytest.mark.order(2)
    def test_get_endpoints(self, ec_service, public_params, api_cache):
        """查询指定 Endpoints，断言成功。"""
        ep_name = api_cache.get("endpoints_name")

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_endpoints(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=ep_name,
            )

            # 断言：业务码为成功
            assert get_resp.get("code") == ApiCode.SUCCESS, (
                f"查询指定 Endpoints 失败, code: {get_resp.get('code')}, 响应: {get_resp}"
            )
            # 断言：响应中包含目标 name
            resp_str = json.dumps(get_resp, ensure_ascii=False)
            assert ep_name in resp_str, (
                f"查询指定 Endpoints 响应中未包含 {ep_name}, 响应: {get_resp}"
            )
