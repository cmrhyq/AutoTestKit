"""
弹性计算 OpenAPI LimitRange 接口测试


- testHostCluster=0：标准集群，只查询 + 更新 + PATCH（在 cellCode/sysCode 命名空间内）
- testHostCluster=1：托管集群，完整生命周期（创建/查询/更新/PATCH/删除，在 hostCellCode/hostSysCode）

本文件用 pytest.mark.skipif 根据 yaml 中 testHostCluster 决定跳过哪个分支。
"""
import allure
import pytest

from base.api.entity.elastic_compute.openapi import (
    K8sLimitRangeEntity,
    LimitrangeHostParams,
    LimitrangeStandardParams,
)
from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.constants import ApiCode, ClusterFlag, Tenant
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("LimitRange 生命周期接口")
class TestEcOpenapiLimitRange:
    """
    根据 testHostCluster 环境变量运行不同分支：
    - 0 标准集群：查询详情 → 查询列表 → PUT → PATCH（不创建/删除）
    - 1 托管集群：查询详情 → 若存在删除 → 创建 → 列表 → 更新 → PATCH → 删除
    """

    TENANT = Tenant.MONITOR_GROUP

    @pytest.fixture(scope="class")
    def ec_service(self, service_factory):
        with service_factory(ElasticComputeOpenService, self.TENANT) as svc:
            yield svc

    @pytest.fixture(scope="class")
    def std_params(self, test_env) -> LimitrangeStandardParams:
        """标准集群参数（cellCode / sysCode）。"""
        return LimitrangeStandardParams(
            cell_code=test_env.get("cellCode"),
            sys_code=test_env.get("sysCode"),
            test_host_cluster=str(test_env.get("hostCellCode")),
        )

    @pytest.fixture(scope="class")
    def host_params(self, test_env) -> LimitrangeHostParams:
        """托管集群参数（hostCellCode / hostSysCode）。"""
        return LimitrangeHostParams(
            cell_code=test_env.get("hostCellCode"),
            sys_code=test_env.get("hostSysCode"),
            test_host_cluster=str(test_env.get("testHostCluster")),
        )

    # ---------------------------- 标准集群分支 ----------------------------

    @allure.title("[标准集群] 查询 LimitRange 详情")
    @allure.description("标准集群下查询命名空间 LimitRange，验证业务码为 2000或不存在")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="lr_std_query")
    @pytest.mark.order(1)
    def test_std_query_limitrange(self, ec_service, std_params, api_cache):
        """标准集群查询 LimitRange 详情。"""
        if std_params.test_host_cluster != ClusterFlag.STANDARD:
            pytest.skip("testHostCluster != 0, 跳过标准集群分支")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_limitranges_by_ns_v2(
                cell_code=std_params.cell_code,
                sys_code=std_params.sys_code,
            )
            code = resp.get("code")
            assert code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                f"[标准] 查询 LimitRange 返回异常 code: {code}, 响应: {resp}"
            )
            api_cache.set("ec_std_lr_get_code", code)

    @allure.title("[标准集群] 查询 LimitRange 列表")
    @allure.description("标准集群下查询全 cell LimitRange 列表，验证业务码为 2000")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="lr_std_list", depends=["lr_std_query"])
    @pytest.mark.order(2)
    def test_std_list_limitranges(self, ec_service, std_params):
        """标准集群下查询 LimitRange 列表。"""
        if std_params.test_host_cluster != ClusterFlag.STANDARD:
            pytest.skip("testHostCluster != 0, 跳过标准集群分支")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_limitranges_by_cell_v2(
                cell_code=std_params.cell_code,
            )
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"[标准] 查询 LimitRange 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("[标准集群] PUT 更新 LimitRange")
    @allure.description("标准集群下若查询命中(业务码为 2000)则 更新 LimitRange，验证业务码为 2000；否则跳过")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="lr_std_put", depends=["lr_std_list"])
    @pytest.mark.order(3)
    def test_std_put_limitrange(self, ec_service, std_params, api_cache):
        """标准集群下 PUT 更新 LimitRange（仅当 GET 成功时）。"""
        if std_params.test_host_cluster != ClusterFlag.STANDARD:
            pytest.skip("testHostCluster != 0, 跳过标准集群分支")
        if api_cache.get("ec_std_lr_get_code") != ApiCode.SUCCESS:
            pytest.skip("[标准] 未命中已存在的 LimitRange, 跳过更新")

        with AllureHelper.api_test(ec_service):
            limit_range = K8sLimitRangeEntity(name=std_params.sys_code)
            resp = ec_service.update_limitrange_ns(
                cell_code=std_params.cell_code,
                sys_code=std_params.sys_code,
                limit_range=limit_range,
            )
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"[标准] PUT LimitRange 失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("[标准集群] PATCH 增量更新 LimitRange")
    @allure.description("标准集群下若查询命中(业务码为 2000)则 增量更新 LimitRange，验证业务码为 2000；否则跳过")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="lr_std_patch", depends=["lr_std_put"])
    @pytest.mark.order(4)
    def test_std_patch_limitrange(self, ec_service, std_params, api_cache):
        """标准集群下 PATCH 增量更新 LimitRange。"""
        if std_params.test_host_cluster != ClusterFlag.STANDARD:
            pytest.skip("testHostCluster != 0, 跳过标准集群分支")
        if api_cache.get("ec_std_lr_get_code") != ApiCode.SUCCESS:
            pytest.skip("[标准] 未命中已存在的 LimitRange, 跳过 PATCH")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.patch_limitrange_ns(
                cell_code=std_params.cell_code,
                sys_code=std_params.sys_code,
                limit_range=None,
            )
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"[标准] PATCH LimitRange 失败, code: {resp.get('code')}, 响应: {resp}"
            )

    # ---------------------------- 托管集群分支 ----------------------------

    @allure.title("[托管集群] 查询 LimitRange 并清理已有资源")
    @allure.description(
        "托管集群下查询命名空间 LimitRange，若已存在则先删除以保证后续创建的幂等性"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="lr_host_query_cleanup")
    @pytest.mark.order(10)
    def test_host_query_and_cleanup(
        self, ec_service, host_params, api_cache
    ):
        """托管集群下查询 LimitRange，若已存在则先删除。"""
        if host_params.test_host_cluster != ClusterFlag.HOST:
            pytest.skip("testHostCluster != 1, 跳过托管集群分支")

        with AllureHelper.api_test(ec_service):
            get_resp = ec_service.list_limitranges_by_ns_v2(
                cell_code=host_params.cell_code,
                sys_code=host_params.sys_code,
            )
            code = get_resp.get("code")
            assert code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                f"[托管] 查询 LimitRange 返回异常 code: {code}, 响应: {get_resp}"
            )

            if code == ApiCode.SUCCESS:
                del_resp = ec_service.delete_limitrange_ns(
                    cell_code=host_params.cell_code,
                    sys_code=host_params.sys_code,
                )
                assert del_resp.get("code") == ApiCode.SUCCESS, (
                    f"[托管] 删除已有 LimitRange 失败, code: {del_resp.get('code')}, "
                    f"响应: {del_resp}"
                )
            api_cache.set("ec_host_lr_created", False)

    @allure.title("[托管集群] 创建 LimitRange")
    @allure.description("托管集群下创建 LimitRange 资源，验证业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(
        name="lr_host_create", depends=["lr_host_query_cleanup"]
    )
    @pytest.mark.order(11)
    def test_host_create_limitrange(
        self, ec_service, host_params, api_cache
    ):
        """托管集群下创建 LimitRange。"""
        if host_params.test_host_cluster != ClusterFlag.HOST:
            pytest.skip("testHostCluster != 1, 跳过托管集群分支")

        with AllureHelper.api_test(ec_service):
            limit_range = K8sLimitRangeEntity(name=host_params.sys_code)
            resp = ec_service.create_limitrange_ns(
                cell_code=host_params.cell_code,
                sys_code=host_params.sys_code,
                limit_range=limit_range,
            )
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"[托管] 创建 LimitRange 失败, code: {resp.get('code')}, 响应: {resp}"
            )
            api_cache.set("ec_host_lr_created", True)
            api_cache.set("ec_host_lr_create_code", resp.get("code"))

    @allure.title("[托管集群] 查询 LimitRange 列表")
    @allure.description("托管集群下查询全 cell LimitRange 列表，验证业务码为 2000")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="lr_host_list", depends=["lr_host_create"])
    @pytest.mark.order(12)
    def test_host_list_limitranges(self, ec_service, host_params):
        """托管集群下查询 LimitRange 列表。"""
        if host_params.test_host_cluster != ClusterFlag.HOST:
            pytest.skip("testHostCluster != 1, 跳过托管集群分支")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_limitranges_by_cell_v2(
                cell_code=host_params.cell_code,
            )
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"[托管] 查询 LimitRange 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("[托管集群] PUT 更新 LimitRange")
    @allure.description("托管集群下 全量更新 LimitRange，验证业务码为 2000")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="lr_host_put", depends=["lr_host_list"])
    @pytest.mark.order(13)
    def test_host_put_limitrange(self, ec_service, host_params, api_cache):
        """托管集群下 PUT 更新 LimitRange。"""
        if host_params.test_host_cluster != ClusterFlag.HOST:
            pytest.skip("testHostCluster != 1, 跳过托管集群分支")
        if api_cache.get("ec_host_lr_create_code") != ApiCode.SUCCESS:
            pytest.skip("[托管] 未成功创建 LimitRange, 跳过更新")

        with AllureHelper.api_test(ec_service):
            limit_range = K8sLimitRangeEntity(name=host_params.sys_code)
            resp = ec_service.update_limitrange_ns(
                cell_code=host_params.cell_code,
                sys_code=host_params.sys_code,
                limit_range=limit_range,
            )
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"[托管] PUT LimitRange 失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("[托管集群] PATCH 增量更新 LimitRange")
    @allure.description("托管集群下 增量更新 LimitRange，验证业务码为 2000")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="lr_host_patch", depends=["lr_host_put"])
    @pytest.mark.order(14)
    def test_host_patch_limitrange(self, ec_service, host_params, api_cache):
        """托管集群下 PATCH 增量更新 LimitRange。"""
        if host_params.test_host_cluster != ClusterFlag.HOST:
            pytest.skip("testHostCluster != 1, 跳过托管集群分支")
        if api_cache.get("ec_host_lr_create_code") != ApiCode.SUCCESS:
            pytest.skip("[托管] 未成功创建 LimitRange, 跳过 PATCH")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.patch_limitrange_ns(
                cell_code=host_params.cell_code,
                sys_code=host_params.sys_code,
                limit_range=None,
            )
            assert resp.get("code") == ApiCode.SUCCESS, (
                f"[托管] PATCH LimitRange 失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("[托管集群] 删除 LimitRange")
    @allure.description("托管集群清理阶段：删除 LimitRange，验证业务码为 2000或不存在")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(depends=["lr_host_patch"])
    @pytest.mark.order(15)
    def test_host_delete_limitrange(self, ec_service, host_params, api_cache):
        """托管集群下删除 LimitRange。"""
        if host_params.test_host_cluster != ClusterFlag.HOST:
            pytest.skip("testHostCluster != 1, 跳过托管集群分支")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.delete_limitrange_ns(
                cell_code=host_params.cell_code,
                sys_code=host_params.sys_code,
            )
            code = resp.get("code")
            assert code in (ApiCode.SUCCESS, ApiCode.NOT_FOUND), (
                f"[托管] 删除 LimitRange 返回异常 code: {code}, 响应: {resp}"
            )
            api_cache.set("ec_host_lr_created", False)
