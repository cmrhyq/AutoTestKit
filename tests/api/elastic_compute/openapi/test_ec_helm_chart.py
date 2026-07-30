"""
弹性计算 OpenAPI Helm Chart 接口测试

转换自 JMeter 脚本: elastic-compute/openapi/helm-chart.jmx
线程组: Thread Group - helm-chart
测试内容：Helm Chart 上传/查询/下载/Install/Manifest/Release 列表/Apps/Upgrade/History/Rollback/Uninstall/删除 Chart
"""
import json
import os
import time
from typing import Any, Dict

import allure
import pytest

from base.api.services.elastic_compute_open_service import (
    ElasticComputeOpenService,
)
from core.reporting.allure_helper import AllureHelper


# 业务码 / 常量（顶部集中定义，禁止方法内魔法数字）
BUSINESS_SUCCESS_CODE = 2000
RESOURCE_NOT_FOUND_CODE = 4004

HTTP_STATUS_OK = 200


@pytest.mark.api
@pytest.mark.openapi
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算OpenAPI接口")
@allure.story("Helm Chart 生命周期接口")
class TestEcOpenapiHelmChart:
    """
    对应 JMeter 脚本: helm-chart.jmx
    线程组: Thread Group - helm-chart

    执行顺序：
      1) 上传 Chart
      2) 查询 Chart 列表
      3) 下载 Chart
      4) Helm Install
      5) Helm Manifest / list / apps
      6) Helm Upgrade → History → Rollback
      7) Helm Uninstall
      8) 删除 Chart
    """

    TENANT = "monitor-group"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def ec_service(self, api_env, api_logger):
        """创建服务实例，base_url 从 yaml 显式传入（camelCase key）。"""
        service = ElasticComputeOpenService(
            base_url=api_env.get("apiBaseUrl"),
            logger=api_logger,
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Helm Chart 测试所需的公共参数。"""
        return {
            "cell_code": api_env.get("cellCode"),
            "sys_code": api_env.get("sysCode"),
            "release_name": "auto-test-helm-release-0001",
            "chart_name": "nginx",
            "chart_version": "1.0.0",
            "chart_file_path": api_env.get("helmChartFilePath"),
            "image": api_env.get("nginxImageRepo"),
            "image_tag": api_env.get("nginxImageTag"),
            "interval_seconds": 3,
        }

    # ---------------- Body helpers（对应 JMX POST 请求体，从 XML 实体还原） ----------------

    @staticmethod
    def _build_helm_install_payload(
        release_name: str, chart_name: str, chart_version: str,
        image: str, image_tag: str,
    ) -> Dict[str, Any]:
        """
        构造 Helm Install 请求体（来源 JMX Helm Install sampler）。
        - values 采用 JSON string 传递，兼容 JMX 原始格式
        """
        values = {
            "image": {"repository": image, "tag": image_tag},
            "replicaCount": 1,
        }
        return {
            "name": release_name,
            "chart": chart_name,
            "version": chart_version,
            "values": json.dumps(values, ensure_ascii=False),
        }

    @staticmethod
    def _build_helm_upgrade_payload(
        chart_name: str, chart_version: str,
        image: str, image_tag: str,
    ) -> Dict[str, Any]:
        """构造 Helm Upgrade 请求体（来源 JMX Helm Upgrade sampler）。"""
        values = {
            "image": {"repository": image, "tag": image_tag},
            "replicaCount": 2,
        }
        return {
            "chart": chart_name,
            "version": chart_version,
            "values": json.dumps(values, ensure_ascii=False),
        }

    # ---------------------------- Test cases ----------------------------

    @allure.title("上传 Helm Chart")
    @allure.description("上传本地 Chart 包，验证业务码为成功。若无本地包则跳过。")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="helm_upload")
    @pytest.mark.order(1)
    def test_upload_chart(self, ec_service, public_params):
        """上传 Chart 到指定 cell。"""
        cell_code = public_params["cell_code"]
        chart_path = public_params["chart_file_path"]
        if not chart_path or not os.path.exists(chart_path):
            pytest.skip(f"Chart 包不存在，跳过上传: {chart_path}")

        with AllureHelper.api_test(ec_service):
            resp = ec_service.upload_helm_chart(
                cell_code=cell_code, chart_file_path=chart_path,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"上传 Chart 失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("查询 Helm Chart 列表")
    @allure.description("按 keyword 查询 Chart 列表，验证包含目标 chart")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="helm_list_charts", depends=["helm_upload"])
    @pytest.mark.order(2)
    def test_list_charts(self, ec_service, public_params):
        """查询 Chart 列表。"""
        cell_code = public_params["cell_code"]
        chart_name = public_params["chart_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_helm_charts(
                cell_code=cell_code, keyword=chart_name,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Chart 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )
            resp_str = json.dumps(resp, ensure_ascii=False)
            assert chart_name in resp_str, (
                f"Chart 列表未找到 {chart_name}, 响应: {resp}"
            )

    @allure.title("下载 Helm Chart")
    @allure.description("下载指定版本的 Chart，验证 HTTP 200 且响应体非空")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="helm_download", depends=["helm_list_charts"])
    @pytest.mark.order(3)
    def test_download_chart(self, ec_service, public_params):
        """下载 Chart。"""
        cell_code = public_params["cell_code"]
        chart_name = public_params["chart_name"]
        chart_version = public_params["chart_version"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.download_helm_chart(
                cell_code=cell_code, chart_name=chart_name,
                chart_version=chart_version,
            )
            assert resp.status_code == HTTP_STATUS_OK, (
                f"下载 Chart 状态码异常: {resp.status_code}"
            )
            assert resp.content, "下载 Chart 响应体为空"

    @allure.title("Helm Install")
    @allure.description("执行 Helm Install，验证业务码为成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="helm_install", depends=["helm_download"])
    @pytest.mark.order(4)
    def test_helm_install(self, ec_service, public_params):
        """执行 Helm Install。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_helm_install_payload(
                release_name=public_params["release_name"],
                chart_name=public_params["chart_name"],
                chart_version=public_params["chart_version"],
                image=public_params["image"],
                image_tag=public_params["image_tag"],
            )
            resp = ec_service.helm_install(
                cell_code=cell_code, sys_code=sys_code, payload=payload,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Helm Install 失败, code: {resp.get('code')}, 响应: {resp}"
            )
            time.sleep(public_params["interval_seconds"])

    @allure.title("Helm Manifest 详情")
    @allure.description("查询指定 Helm Release 的 Manifest 详情，验证业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="helm_manifest", depends=["helm_install"])
    @pytest.mark.order(5)
    def test_helm_manifest(self, ec_service, public_params):
        """查询 Helm Manifest。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.get_helm_manifest(
                cell_code=cell_code, sys_code=sys_code, name=release_name,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Helm Manifest 失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("Helm Release 列表")
    @allure.description("查询 Helm Release 列表，验证包含目标 release")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="helm_list_releases", depends=["helm_manifest"])
    @pytest.mark.order(6)
    def test_helm_list_releases(self, ec_service, public_params):
        """查询 Helm Release 列表。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_helm_releases(
                cell_code=cell_code, sys_code=sys_code,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Helm Release 列表失败, code: {resp.get('code')}, 响应: {resp}"
            )
            resp_str = json.dumps(resp, ensure_ascii=False)
            assert release_name in resp_str, (
                f"Release 列表未找到 {release_name}, 响应: {resp}"
            )

    @allure.title("Helm Release 关联 Apps 状态列表")
    @allure.description("查询 Helm Release 关联应用服务状态列表，验证业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="helm_release_apps", depends=["helm_list_releases"])
    @pytest.mark.order(7)
    def test_helm_release_apps(self, ec_service, public_params):
        """查询 Helm Release 关联 Apps。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_helm_release_apps(
                cell_code=cell_code, sys_code=sys_code, name=release_name,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Helm Release Apps 失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("Helm Upgrade")
    @allure.description("执行 Helm Upgrade，验证业务码为成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="helm_upgrade", depends=["helm_release_apps"])
    @pytest.mark.order(8)
    def test_helm_upgrade(self, ec_service, public_params):
        """执行 Helm Upgrade。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_service):
            payload = self._build_helm_upgrade_payload(
                chart_name=public_params["chart_name"],
                chart_version=public_params["chart_version"],
                image=public_params["image"],
                image_tag=public_params["image_tag"],
            )
            resp = ec_service.helm_upgrade(
                cell_code=cell_code, sys_code=sys_code,
                name=release_name, payload=payload,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Helm Upgrade 失败, code: {resp.get('code')}, 响应: {resp}"
            )
            time.sleep(public_params["interval_seconds"])

    @allure.title("Helm 历史版本列表")
    @allure.description("查询 Helm Release 历史版本列表，验证业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.dependency(name="helm_history", depends=["helm_upgrade"])
    @pytest.mark.order(9)
    def test_helm_history(self, ec_service, public_params):
        """查询 Helm History。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.list_helm_history(
                cell_code=cell_code, sys_code=sys_code, name=release_name,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Helm History 失败, code: {resp.get('code')}, 响应: {resp}"
            )

    @allure.title("Helm Rollback")
    @allure.description("回滚 Helm Release 到 revision=1，验证业务码为成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="helm_rollback", depends=["helm_history"])
    @pytest.mark.order(10)
    def test_helm_rollback(self, ec_service, public_params):
        """执行 Helm Rollback。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.helm_rollback(
                cell_code=cell_code, sys_code=sys_code,
                name=release_name, revision=1,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Helm Rollback 失败, code: {resp.get('code')}, 响应: {resp}"
            )
            time.sleep(public_params["interval_seconds"])

    @allure.title("Helm Uninstall")
    @allure.description("卸载 Helm Release，验证业务码为成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(name="helm_uninstall", depends=["helm_rollback"])
    @pytest.mark.order(11)
    def test_helm_uninstall(self, ec_service, public_params):
        """执行 Helm Uninstall。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.helm_uninstall(
                cell_code=cell_code, sys_code=sys_code, name=release_name,
            )
            assert resp.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Helm Uninstall 失败, code: {resp.get('code')}, 响应: {resp}"
            )
            time.sleep(public_params["interval_seconds"])

    @allure.title("删除 Helm Chart")
    @allure.description("清理阶段：删除测试期间上传的 Chart，验证业务码为成功或不存在")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.dependency(depends=["helm_uninstall"])
    @pytest.mark.order(12)
    def test_delete_chart(self, ec_service, public_params):
        """收尾：删除 Chart。"""
        cell_code = public_params["cell_code"]
        chart_name = public_params["chart_name"]
        chart_version = public_params["chart_version"]

        with AllureHelper.api_test(ec_service):
            resp = ec_service.delete_helm_chart_by_name(
                cell_code=cell_code, chart_name=chart_name, version=chart_version,
            )
            code = resp.get("code")
            assert code in (BUSINESS_SUCCESS_CODE, RESOURCE_NOT_FOUND_CODE), (
                f"删除 Chart 返回异常 code: {code}, 响应: {resp}"
            )



