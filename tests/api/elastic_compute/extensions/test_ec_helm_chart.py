"""
Helm & Chart 完整生命周期接口测试（Extensions - apikey 鉴权）

转换自 JMeter 脚本: helm-chart.jmx
测试内容：
    1) Chart 上传/查询/下载/删除
    2) Helm 服务 Install/Manifest/List/Upgrade/History/Rollback/Uninstall
    3) Helm 服务 v1 批量创建/升级/卸载
    4) Helm 服务 v2 批量创建/升级/卸载

依赖：
    - config/env_*.yaml 需提供：apiInnerBaseUrl / clusterId / namespace / cellCode / sysCode /
        chartName / chartVersion / helmReleaseName / helmChartFilePath /
        nginxImageRepo / nginxImageTag / paasAppCode / paasOwner /
        paasTenantCode / paasEnvCode / paasPlaneCode
    - Chart 上传接口涉及文件上传（multipart/form-data），需要本地 Chart 包文件；
        若 helmChartFilePath 未配置或文件不存在，整个类将 skip（因为后续所有用例均依赖上传成功）。
"""

import json
import os

import allure
import pytest

from base.api.services.elastic_compute_ext_service import (
    ElasticComputeExtService,
)
from core.reporting.allure_helper import AllureHelper

BUSINESS_SUCCESS_CODE = 2000
RESOURCE_CONFLICT_CODE = 4009
RESOURCE_CONFLICT_MSG = "RESOURCE CONFLICT"
HTTP_OK = 200
DEFAULT_ROLLBACK_REVISION = 1


@pytest.mark.api
@pytest.mark.extension
@allure.epic("磐基API自动化测试")
@allure.feature("磐基弹性计算Extensions接口")
@allure.story("Helm/Chart 完整生命周期接口")
class TestEcExtensionsHelmChart:
    """
    对应 JMeter 脚本: helm-chart.jmx
    线程组: Thread Group - helm

    执行流程（对齐 JMX）：
        upload_chart → list_charts → download_chart
        → helm_install → helm_manifest → helm_list → helm_upgrade
        → helm_history → helm_rollback → helm_uninstall
        → batch_install_v1 → batch_upgrade_v1 → batch_uninstall_v1
        → batch_install_v2 → batch_upgrade_v2 → batch_uninstall_v2
        → delete_chart
    """

    TENANT = None

    @pytest.fixture(scope="class")
    def ec_ext_service(self, api_env):
        """Extensions 类接口使用 apikey 鉴权，不需要 Bearer token。"""
        service = ElasticComputeExtService(
            base_url=api_env.get("apiInnerBaseUrl"),
        )
        yield service
        service.close()

    @pytest.fixture(scope="class")
    def public_params(self, api_env):
        """提取 Helm/Chart 测试所需的公共参数（对齐 JMX 用户参数默认值）。"""
        return {
            "cluster_id": str(api_env.get("clusterId", "1")),
            "namespace": api_env.get("namespace", "test-admin"),
            "cell_code": api_env.get("cellCode", "TEST"),
            "sys_code": api_env.get("sysCode", "test-admin"),
            "chart_name": "nginx",
            "chart_version": "0.1.0",
            "release_name": "inner-test-nginx-demo",
            "image": api_env.get("nginxImageRepo", "192.168.18.3:1121/hpe_containers/nginx"),
            "image_tag": api_env.get("nginxImageTag", "latest"),
            "paas_app_code": api_env.get("appCodeDeploy", "test-app"),
            "paas_owner": api_env.get("user", "test-admin"),
            "paas_tenant_code": api_env.get("tenantCode", "tenant-001"),
            "paas_env_code": api_env.get("paasEnvCode", "ENV1"),
            "paas_plane_code": api_env.get("paasPlaneCode", "PLANE1"),
        }

    # ==================== payload 构造 helper（对齐 JMX 原始 body）====================

    @staticmethod
    def _build_helm_params(params: dict, *, extra_label_test: bool = False) -> dict:
        """构造 Helm install/upgrade 的 params 字典（键为带点的路径字符串）。

        对齐 JMX 中的原始 body 结构：包含 image.* 与 labels.* / service.labels.* 系列。
        当 ``extra_label_test`` 为 True 时，额外追加 ``labels.test=update`` 与
        ``service.labels.test=update``，对齐 upgrade / upgrade-batch 的 JMX 差异。
        """
        cluster_id = params["cluster_id"]
        namespace = params["namespace"]
        cell_code = params["cell_code"]
        name = params["release_name"]
        base = {
            "image.repository": params["image"],
            "image.tag": params["image_tag"],
            "labels.operation-source": "api",
            "labels.paas-resource-category": "tenant-app",
            "labels.paas-app-source": "helm",
            "labels.paas-owner": params["paas_owner"],
            "labels.paas-tenant-code": params["paas_tenant_code"],
            "labels.paas-env-code": params["paas_env_code"],
            "labels.paas-plane-code": params["paas_plane_code"],
            "labels.paas-unit-code": cell_code,
            "labels.paas-cluster-code": cluster_id,
            "labels.paas-system-code": namespace,
            "labels.paas-app-code": params["paas_app_code"],
            "labels.paas-workload-name": name,
            "labels.paas-app-service-version": "v1",
            "service.labels.operation-source": "api",
            "service.labels.paas-resource-category": "tenant-app",
            "service.labels.paas-app-source": "helm",
            "service.labels.paas-owner": params["paas_owner"],
            "service.labels.paas-tenant-code": params["paas_tenant_code"],
            "service.labels.paas-env-code": params["paas_env_code"],
            "service.labels.paas-plane-code": params["paas_plane_code"],
            "service.labels.paas-unit-code": cell_code,
            "service.labels.paas-cluster-code": cluster_id,
            "service.labels.paas-system-code": namespace,
            "service.labels.paas-app-code": params["paas_app_code"],
            "service.labels.paas-workload-name": name,
        }
        if extra_label_test:
            base["labels.test"] = "update"
            base["service.labels.test"] = "update"
        return base

    @classmethod
    def _build_helm_install_payload(cls, params: dict) -> dict:
        """构造 Helm Install / Batch install 单条 payload（对齐 JMX install body）。"""
        return {
            "name": params["release_name"],
            "chartName": params["chart_name"],
            "chartVersion": params["chart_version"],
            "params": cls._build_helm_params(params, extra_label_test=False),
        }

    @classmethod
    def _build_helm_upgrade_payload(cls, params: dict) -> dict:
        """构造 Helm Upgrade / Batch upgrade 单条 payload（对齐 JMX upgrade body，含 labels.test=update）。"""
        return {
            "name": params["release_name"],
            "chartName": params["chart_name"],
            "chartVersion": params["chart_version"],
            "params": cls._build_helm_params(params, extra_label_test=True),
        }

    @staticmethod
    def _build_batch_uninstall_payload(release_name: str) -> dict:
        """构造批量卸载 payload。"""
        return {"uninstallList": [release_name]}

    # ==================== 1) 上传 Chart ====================

    @pytest.mark.dependency(name="helm_chart_upload")
    @pytest.mark.order(1)
    @allure.title("上传 Chart 包")
    @allure.description("上传本地 Chart 包到集群 Helm 仓库，作为后续 Install/List/Download 的前置")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_upload_helm_chart(self, ec_ext_service, public_params, api_env):
        """上传 Chart 包（对应 JMX 第一步），若文件缺失则 skip 后续全部依赖用例。"""
        cluster_id = public_params["cluster_id"]
        chart_file_path = api_env.get("helmChartFilePath", "")

        if not chart_file_path or not os.path.exists(chart_file_path):
            pytest.skip(f"helmChartFilePath 未配置或文件不存在: {chart_file_path!r}")

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.upload_helm_chart(
                cluster_id=cluster_id,
                file_path=chart_file_path,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"上传 Chart 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 2) 查询 Chart 列表（带 keyword 过滤）====================

    @pytest.mark.dependency(name="helm_chart_list", depends=["helm_chart_upload"])
    @pytest.mark.order(2)
    @allure.title("查询指定集群下的 Chart 列表")
    @allure.description("按 chartName 关键字过滤查询 Chart 列表，验证响应包含目标 Chart 名称与版本")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_helm_charts(self, ec_ext_service, public_params):
        """查询 Chart 列表，断言业务码为成功且响应包含 chartName / chartVersion。"""
        cluster_id = public_params["cluster_id"]
        chart_name = public_params["chart_name"]
        chart_version = public_params["chart_version"]

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.list_helm_charts(
                cluster_id=cluster_id,
                keyword=chart_name,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Chart 列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
            resp_str = json.dumps(response_json, ensure_ascii=False)
            assert f'"name":"{chart_name}"' in resp_str, (
                f"Chart 列表未找到 name={chart_name}, 响应: {response_json}"
            )
            assert f'"version":"{chart_version}"' in resp_str, (
                f"Chart 列表未找到 version={chart_version}, 响应: {response_json}"
            )

    # ==================== 3) 下载 Chart ====================

    @pytest.mark.dependency(name="helm_chart_download", depends=["helm_chart_list"])
    @pytest.mark.order(3)
    @allure.title("下载指定 Chart 包")
    @allure.description("从集群 Helm 仓库下载指定版本的 Chart 包，验证 HTTP 200 且内容非空")
    @allure.severity(allure.severity_level.NORMAL)
    def test_download_helm_chart(self, ec_ext_service, public_params):
        """下载 Chart 包，断言 HTTP 200 且响应内容非空。"""
        cluster_id = public_params["cluster_id"]
        chart_name = public_params["chart_name"]
        chart_version = public_params["chart_version"]

        with AllureHelper.api_test(ec_ext_service):
            status_code, content = ec_ext_service.download_helm_chart(
                cluster_id=cluster_id,
                chart_name=chart_name,
                chart_version=chart_version,
            )

            assert status_code == HTTP_OK, f"下载 Chart 失败, HTTP status: {status_code}"
            assert content and len(content) > 0, "下载的 Chart 包内容为空"

    # ==================== 4) Helm Install（幂等：4009=冲突先 uninstall，然后重新 install）====================

    @pytest.mark.dependency(name="helm_install", depends=["helm_chart_download"])
    @pytest.mark.order(4)
    @allure.title("安装 Helm Release")
    @allure.description("在指定命名空间下安装 Helm Release，若 4009 冲突则先卸载再重装")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_helm_install(self, ec_ext_service, public_params, api_cache):
        """Helm Install，若 4009 冲突则先 uninstall 再 install，确保最终 code==2000。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_ext_service):
            payload = self._build_helm_install_payload(public_params)
            response_json = ec_ext_service.helm_install(
                cluster_id=cluster_id,
                namespace=namespace,
                payload=payload,
            )
            install_code = response_json.get("code")

            # 若发生资源冲突（4009），对齐 JMX：先卸载再重装
            if install_code == RESOURCE_CONFLICT_CODE:
                uninstall_resp = ec_ext_service.helm_uninstall(
                    cluster_id=cluster_id, namespace=namespace, name=release_name,
                )
                assert uninstall_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"冲突场景下预卸载失败, 响应: {uninstall_resp}"
                )
                response_json = ec_ext_service.helm_install(
                    cluster_id=cluster_id, namespace=namespace, payload=payload,
                )
                install_code = response_json.get("code")

            assert install_code == BUSINESS_SUCCESS_CODE, (
                f"Helm Install 失败, code: {install_code}, 响应: {response_json}"
            )
            api_cache.set("helm_installed", True)

    # ==================== 5) Helm Manifest ====================

    @pytest.mark.dependency(name="helm_manifest", depends=["helm_install"])
    @pytest.mark.order(5)
    @allure.title("查询 Helm Release Manifest")
    @allure.description("查询指定 Helm Release 的 Manifest 详情，验证业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_helm_manifest(self, ec_ext_service, public_params):
        """查询 Helm Manifest，断言业务码为成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.helm_manifest(
                cluster_id=cluster_id,
                namespace=namespace,
                name=release_name,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Helm Manifest 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 6) Helm List（校验列表中包含 release name）====================

    @pytest.mark.dependency(name="helm_list", depends=["helm_manifest"])
    @pytest.mark.order(6)
    @allure.title("查询 Helm Release 列表")
    @allure.description("查询指定命名空间下的 Helm Release 列表，验证包含目标 release 名称")
    @allure.severity(allure.severity_level.NORMAL)
    def test_helm_list_releases(self, ec_ext_service, public_params):
        """查询 Helm Release 列表，断言业务码为成功且包含目标 release name。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.helm_list_releases(
                cluster_id=cluster_id,
                namespace=namespace,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Helm Release 列表失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
            resp_str = json.dumps(response_json, ensure_ascii=False)
            assert f'"name":"{release_name}"' in resp_str, (
                f"Helm Release 列表未找到 {release_name}, 响应: {response_json}"
            )

    # ==================== 7) Helm Upgrade ====================

    @pytest.mark.dependency(name="helm_upgrade", depends=["helm_list"])
    @pytest.mark.order(7)
    @allure.title("升级 Helm Release")
    @allure.description("升级指定 Helm Release，追加 labels.test=update 后验证升级成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_helm_upgrade(self, ec_ext_service, public_params):
        """Helm Upgrade，断言业务码为成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_ext_service):
            payload = self._build_helm_upgrade_payload(public_params)
            response_json = ec_ext_service.helm_upgrade(
                cluster_id=cluster_id,
                namespace=namespace,
                name=release_name,
                payload=payload,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Helm Upgrade 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 8) Helm History ====================

    @pytest.mark.dependency(name="helm_history", depends=["helm_upgrade"])
    @pytest.mark.order(8)
    @allure.title("查询 Helm Release 历史版本")
    @allure.description("查询指定 Helm Release 的版本升级历史，验证业务码为成功")
    @allure.severity(allure.severity_level.NORMAL)
    def test_helm_history(self, ec_ext_service, public_params):
        """查询 Helm History，断言业务码为成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.helm_history(
                cluster_id=cluster_id,
                namespace=namespace,
                name=release_name,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"查询 Helm History 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 9) Helm Rollback（revision 走 query 参数）====================

    @pytest.mark.dependency(name="helm_rollback", depends=["helm_history"])
    @pytest.mark.order(9)
    @allure.title("回滚 Helm Release 到指定版本")
    @allure.description("通过 revision query 参数将 Helm Release 回滚至初始版本，验证业务码为成功")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_helm_rollback(self, ec_ext_service, public_params):
        """Helm Rollback，断言业务码为成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.helm_rollback(
                cluster_id=cluster_id,
                namespace=namespace,
                name=release_name,
                revision=DEFAULT_ROLLBACK_REVISION,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Helm Rollback 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )

    # ==================== 10) Helm Uninstall ====================

    @pytest.mark.dependency(name="helm_uninstall", depends=["helm_rollback"])
    @pytest.mark.order(10)
    @allure.title("卸载 Helm Release")
    @allure.description("卸载指定 Helm Release，为后续批量测试腾出干净环境")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_helm_uninstall(self, ec_ext_service, public_params, api_cache):
        """Helm Uninstall，断言业务码为成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.helm_uninstall(
                cluster_id=cluster_id,
                namespace=namespace,
                name=release_name,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Helm Uninstall 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
            api_cache.set("helm_installed", False)

    # ==================== 11-13) Helm 批量操作（v1）====================

    @pytest.mark.dependency(name="helm_batch_install_v1", depends=["helm_uninstall"])
    @pytest.mark.order(11)
    @allure.title("批量安装 Helm Release（v1）")
    @allure.description("通过 v1 批量接口按 clusterId/namespace 安装 Helm Release，若冲突则先批量卸载再重装")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_helm_batch_install_v1(self, ec_ext_service, public_params):
        """Helm Batch Install v1：断言 code==2000 且 data[0].isSuccess=true，若冲突先卸载再重装。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_ext_service):
            payload = {"installList": [self._build_helm_install_payload(public_params)]}
            response_json = ec_ext_service.helm_batch_install(
                cluster_id=cluster_id, namespace=namespace, payload=payload,
            )

            code = response_json.get("code")
            data = response_json.get("data") or [{}]
            is_success = data[0].get("isSuccess")
            error_msg = data[0].get("errorMessage") or ""

            # 冲突场景：批量卸载后重新批量创建（对齐 JMX "IF 控制器 批量创建 fail" 分支）
            if code == BUSINESS_SUCCESS_CODE and is_success is False and RESOURCE_CONFLICT_MSG in error_msg:
                uninstall_payload = self._build_batch_uninstall_payload(release_name)
                uninstall_resp = ec_ext_service.helm_batch_uninstall(
                    cluster_id=cluster_id, namespace=namespace, payload=uninstall_payload,
                )
                assert uninstall_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"冲突场景下批量卸载失败, 响应: {uninstall_resp}"
                )
                response_json = ec_ext_service.helm_batch_install(
                    cluster_id=cluster_id, namespace=namespace, payload=payload,
                )
                code = response_json.get("code")
                data = response_json.get("data") or [{}]
                is_success = data[0].get("isSuccess")

            assert code == BUSINESS_SUCCESS_CODE, (
                f"Helm Batch Install v1 失败, code: {code}, 响应: {response_json}"
            )
            assert is_success is True, (
                f"Helm Batch Install v1 data[0].isSuccess 非 true, 响应: {response_json}"
            )

    @pytest.mark.dependency(name="helm_batch_upgrade_v1", depends=["helm_batch_install_v1"])
    @pytest.mark.order(12)
    @allure.title("批量升级 Helm Release（v1）")
    @allure.description("通过 v1 批量接口升级 Helm Release，验证 code==2000 且 data[0].isSuccess=true")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_helm_batch_upgrade_v1(self, ec_ext_service, public_params):
        """Helm Batch Upgrade v1，断言业务码为成功且第一个条目升级成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]

        with AllureHelper.api_test(ec_ext_service):
            payload = {"upgradeList": [self._build_helm_upgrade_payload(public_params)]}
            response_json = ec_ext_service.helm_batch_upgrade(
                cluster_id=cluster_id, namespace=namespace, payload=payload,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Helm Batch Upgrade v1 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
            data = response_json.get("data") or [{}]
            assert data[0].get("isSuccess") is True, (
                f"Helm Batch Upgrade v1 data[0].isSuccess 非 true, 响应: {response_json}"
            )

    @pytest.mark.dependency(name="helm_batch_uninstall_v1", depends=["helm_batch_upgrade_v1"])
    @pytest.mark.order(13)
    @allure.title("批量卸载 Helm Release（v1）")
    @allure.description("通过 v1 批量接口卸载 Helm Release，为 v2 批量测试腾出干净环境")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_helm_batch_uninstall_v1(self, ec_ext_service, public_params):
        """Helm Batch Uninstall v1，断言业务码为成功且第一个条目卸载成功。"""
        cluster_id = public_params["cluster_id"]
        namespace = public_params["namespace"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_ext_service):
            payload = self._build_batch_uninstall_payload(release_name)
            response_json = ec_ext_service.helm_batch_uninstall(
                cluster_id=cluster_id, namespace=namespace, payload=payload,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Helm Batch Uninstall v1 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
            data = response_json.get("data") or [{}]
            assert data[0].get("isSuccess") is True, (
                f"Helm Batch Uninstall v1 data[0].isSuccess 非 true, 响应: {response_json}"
            )

    # ==================== 14-16) Helm 批量操作（v2, cells/systems 路径）====================

    @pytest.mark.dependency(name="helm_batch_install_v2", depends=["helm_batch_uninstall_v1"])
    @pytest.mark.order(14)
    @allure.title("批量安装 Helm Release（v2）")
    @allure.description("通过 v2 批量接口按 cellCode/sysCode 安装 Helm Release，若冲突则先批量卸载再重装")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_helm_batch_install_v2(self, ec_ext_service, public_params):
        """Helm Batch Install v2：断言 code==2000 且 data[0].isSuccess=true，若冲突先卸载再重装。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_ext_service):
            payload = {"installList": [self._build_helm_install_payload(public_params)]}
            response_json = ec_ext_service.helm_batch_install_v2(
                cell_code=cell_code, sys_code=sys_code, payload=payload,
            )

            code = response_json.get("code")
            data = response_json.get("data") or [{}]
            is_success = data[0].get("isSuccess")
            error_msg = data[0].get("errorMessage") or ""

            if code == BUSINESS_SUCCESS_CODE and is_success is False and RESOURCE_CONFLICT_MSG in error_msg:
                uninstall_payload = self._build_batch_uninstall_payload(release_name)
                uninstall_resp = ec_ext_service.helm_batch_uninstall_v2(
                    cell_code=cell_code, sys_code=sys_code, payload=uninstall_payload,
                )
                assert uninstall_resp.get("code") == BUSINESS_SUCCESS_CODE, (
                    f"冲突场景下 v2 批量卸载失败, 响应: {uninstall_resp}"
                )
                response_json = ec_ext_service.helm_batch_install_v2(
                    cell_code=cell_code, sys_code=sys_code, payload=payload,
                )
                code = response_json.get("code")
                data = response_json.get("data") or [{}]
                is_success = data[0].get("isSuccess")

            assert code == BUSINESS_SUCCESS_CODE, (
                f"Helm Batch Install v2 失败, code: {code}, 响应: {response_json}"
            )
            assert is_success is True, (
                f"Helm Batch Install v2 data[0].isSuccess 非 true, 响应: {response_json}"
            )

    @pytest.mark.dependency(name="helm_batch_upgrade_v2", depends=["helm_batch_install_v2"])
    @pytest.mark.order(15)
    @allure.title("批量升级 Helm Release（v2）")
    @allure.description("通过 v2 批量接口升级 Helm Release，验证 code==2000 且 data[0].isSuccess=true")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_helm_batch_upgrade_v2(self, ec_ext_service, public_params):
        """Helm Batch Upgrade v2，断言业务码为成功且第一个条目升级成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]

        with AllureHelper.api_test(ec_ext_service):
            payload = {"upgradeList": [self._build_helm_upgrade_payload(public_params)]}
            response_json = ec_ext_service.helm_batch_upgrade_v2(
                cell_code=cell_code, sys_code=sys_code, payload=payload,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Helm Batch Upgrade v2 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
            data = response_json.get("data") or [{}]
            assert data[0].get("isSuccess") is True, (
                f"Helm Batch Upgrade v2 data[0].isSuccess 非 true, 响应: {response_json}"
            )

    @pytest.mark.dependency(name="helm_batch_uninstall_v2", depends=["helm_batch_upgrade_v2"])
    @pytest.mark.order(16)
    @allure.title("批量卸载 Helm Release（v2）")
    @allure.description("通过 v2 批量接口卸载 Helm Release，为最终 Chart 删除腾出干净环境")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_helm_batch_uninstall_v2(self, ec_ext_service, public_params):
        """Helm Batch Uninstall v2，断言业务码为成功且第一个条目卸载成功。"""
        cell_code = public_params["cell_code"]
        sys_code = public_params["sys_code"]
        release_name = public_params["release_name"]

        with AllureHelper.api_test(ec_ext_service):
            payload = self._build_batch_uninstall_payload(release_name)
            response_json = ec_ext_service.helm_batch_uninstall_v2(
                cell_code=cell_code, sys_code=sys_code, payload=payload,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"Helm Batch Uninstall v2 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
            data = response_json.get("data") or [{}]
            assert data[0].get("isSuccess") is True, (
                f"Helm Batch Uninstall v2 data[0].isSuccess 非 true, 响应: {response_json}"
            )

    # ==================== 17) 删除 Chart（最终清理）====================

    @pytest.mark.dependency(name="helm_chart_delete", depends=["helm_batch_uninstall_v2"])
    @pytest.mark.order(17)
    @allure.title("删除指定 Chart")
    @allure.description("对齐 JMX 最终清理步骤：按 chartName + version 删除已上传的 Chart")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_helm_chart(self, ec_ext_service, public_params):
        """删除 Chart，断言业务码为成功。"""
        cluster_id = public_params["cluster_id"]
        chart_name = public_params["chart_name"]
        chart_version = public_params["chart_version"]

        with AllureHelper.api_test(ec_ext_service):
            response_json = ec_ext_service.delete_helm_chart(
                cluster_id=cluster_id,
                chart_name=chart_name,
                chart_version=chart_version,
            )

            assert response_json.get("code") == BUSINESS_SUCCESS_CODE, (
                f"删除 Chart 失败, code: {response_json.get('code')}, 响应: {response_json}"
            )
