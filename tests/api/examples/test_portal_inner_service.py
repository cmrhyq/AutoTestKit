# from typing import Dict
#
# import allure
# import pytest
#
# from base.api.fixtures import api_cache
# from base.api.services.portal_inner_service import PanJiPortalInnerService
# from core.reporting.allure_helper import AllureHelper
#
#
# @pytest.mark.api
# @allure.feature("磐基门户InnerAPI服务")
# @allure.story("统一门户")
# class TestPanjiPortalInnerAPI:
#
#     @pytest.fixture(scope="class")
#     def portal_inner_service(self, api_env, api_logger):
#         """创建 Panji Portal Inner API 服务实例"""
#         service = PanJiPortalInnerService(base_url=api_env.get("apiInnerBaseUrl"), logger=api_logger)
#         yield service
#         service.close()
#
#     @allure.title("测试获取用户全量数据")
#     @allure.description("验证能够成功获取用户全量数据")
#     @allure.severity(allure.severity_level.CRITICAL)
#     def test_get_user_full_data(self, portal_inner_service, api_env, api_cache, api_logger):
#         with AllureHelper.step("发送 POST 请求获取用户全量数据"):
#             response_json = portal_inner_service.get_user_full_data()
#
#         with AllureHelper.step("验证响应数据"):
#             assert isinstance(response_json, Dict), "响应应该是字典类型"
#             assert response_json["code"] == 0, "响应Code应等于0"
#
#         allure.attach(
#             str(response_json),
#             name="接口响应信息",
#             attachment_type=allure.attachment_type.JSON
#         )
