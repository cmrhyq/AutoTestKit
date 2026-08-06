"""
弹性计算 OpenAPI ReplicaSet 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/ReplicaSetV2.jmx
线程组: Thread Group - ReplicaSetV2Api
测试内容：ReplicaSet 查询接口（全集群列表 → 命名空间列表 → 指定 ReplicaSet）
"""
import allure
import pytest

from base.api.entity.elastic_compute_openapi import ReplicaSetPublicParams
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, Tenant
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("ReplicaSet 查询接口")
class TestEcOpenapiReplicaSet:
    """
    对应 JMeter 脚本: ReplicaSetV2.jmx
    线程组: Thread Group - ReplicaSetV2Api

    拆分为独立接口测试函数，通过 pytest-dependency 保证执行顺序和依赖关系。
    执行顺序：全集群列表 → 命名空间列表（提取 name） → 查询指定 ReplicaSet
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def public_params(self, api_env) -> ReplicaSetPublicParams:
        """提取 ReplicaSet 测试所需的公共参数。"""
        return ReplicaSetPublicParams(
            cell_code=api_env.get("cellCode", "TEST"),
            sys_code=api_env.get("sysCode", "istio-ingress"),
        )

    # ---------------------------- Test cases ----------------------------

    @allure.title("查询全集群 ReplicaSet 列表")
    @allure.description("查询全集群 ReplicaSet 列表，验证接口返回成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="replicaset_list_cell")
    @pytest.mark.order(1)
    def test_list_replica_sets_by_cell(self, ec_service, public_params):
        """查询全集群 ReplicaSet 列表，断言返回成功。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_replica_sets_by_cell(cell_code=public_params.cell_code)

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询全集群 ReplicaSet 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )

    @allure.title("查询命名空间下 ReplicaSet 列表")
    @allure.description("查询命名空间下 ReplicaSet 列表，提取第一个 ReplicaSet 名称用于后续查询")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="replicaset_list_ns", depends=["replicaset_list_cell"],
    )
    @pytest.mark.order(2)
    def test_list_replica_sets_by_ns(self, ec_service, public_params, api_cache):
        """查询命名空间下 ReplicaSet 列表，提取第一个名称。"""
        with AllureHelper.api_test(ec_service):
            list_resp = ec_service.list_replica_sets_by_ns(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
            )

            assert list_resp.get("code") == ApiCode.SUCCESS, (
                f"查询命名空间 ReplicaSet 列表失败, code: {list_resp.get('code')}, 响应: {list_resp}"
            )

            # 提取第一个 ReplicaSet 的 name ($.data.items[0].metadata.name)
            items = (
                list_resp.get("data", {}).get("items")
                or list_resp.get("items")
                or []
            )
            assert len(items) > 0, (
                f"命名空间下 ReplicaSet 列表为空, 响应: {list_resp}"
            )
            rs_name = items[0].get("metadata", {}).get("name", "")
            assert rs_name, (
                f"无法提取 ReplicaSet 名称, items[0]: {items[0]}"
            )
            api_cache.set("ec_replicaset_name", rs_name)

    @allure.title("查询指定 ReplicaSet")
    @allure.description("根据从列表中提取的名称查询指定 ReplicaSet，验证返回成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="replicaset_get", depends=["replicaset_list_ns"],
    )
    @pytest.mark.order(3)
    def test_get_replica_set(self, ec_service, public_params, api_cache):
        """查询指定 ReplicaSet，断言返回成功。"""
        rs_name = api_cache.get("ec_replicaset_name")

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.get_replica_set(
                cell_code=public_params.cell_code,
                sys_code=public_params.sys_code,
                name=rs_name,
            )

            assert get_resp.get("code") == ApiCode.SUCCESS, (
                f"查询指定 ReplicaSet 失败, code: {get_resp.get('code')}, 响应: {get_resp}"
            )
