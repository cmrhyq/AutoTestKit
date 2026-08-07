"""
门户 InnerAPI 服务封装（apikey 鉴权）

面向磐基（PanJi）门户系统的 **内部管控接口** 客户端，覆盖门户核心元数据（用户、租户、
角色、菜单、系统、应用）的全生命周期管理与授权。

业务域覆盖：
- 用户 / 租户 / 角色 / 菜单：门户核心 IAM 元数据
- 字典 / API / 系统配置 / 版本 / 平台 / 全局配置 / 域：门户配置元数据
- 授权：用户 - 租户 / 用户 - 角色 / 用户 - 系统 / 用户 - 应用 授权
- 消息：门户内消息通道
- 系统 / 应用管理：内部系统与应用注册
- 实例查询 / 菜单管理：门户仪表盘数据源

鉴权：`apikey` 请求头（静态值）+ `tenantCode` + `x-app-id: portal` 三件头。
URL 前缀：`/portal/server/api/...`、`/portal/server/api/v2/...`
（无 `/openapi/` 前缀）。
"""
from typing import Dict, Any, List

from base.api.services.base_service import BaseService
from core import get_logger
from core.config import get_env_config

from base.api.entity.portal import (
    InnerSystemEntity,
    ApplicationEntity,
    MenuEntity,
    RoleEntity,
    TenantEntity,
    InnerUserEntity,
)

logger = get_logger(__name__)


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头"""
    return {
        "tenantCode": get_env_config().get("tenant_code"),
        "x-app-id": "portal",
    }


class PortalInnerService(BaseService):
    """
    门户 InnerAPI 服务（内部管控接口）。

    - 鉴权：`apikey` 请求头（静态值）+ `tenantCode` + `x-app-id: portal` 三件头
    - URL 前缀：`/portal/server/api/...`、`/portal/server/api/v2/...`
    - base_url：由 fixture `test_env["apiBaseUrl"]` 提供，必传
    """

    def __init__(self, base_url: str):
        """
        初始化 Panji Portal InnerAPI 服务

        Args:
            base_url: API 基础 URL（必传，来自 config/env_*.yaml 的 apiBaseUrl）

        Raises:
            ValueError: 如果 base_url 为空
        """
        if not base_url:
            raise ValueError(
                "base_url is required. "
                "Configure it in config/env_*.yaml (apiBaseUrl) "
                "and pass via fixture: test_env.get('apiBaseUrl')"
            )
        super().__init__(
            base_url=base_url,
            auth_type="api_key",
            auth_credentials={
                "api_key": "67d5da7b76b1030ea6888f7644e05195",
                "header_name": "apikey"
            },
        )
        logger.info(f"Initializing PanJi Portal InnerAPI Service with base_url: {self.base_url}")

    # ==================== 用户相关接口 ====================

    def get_user_full_data(self) -> Dict[str, Any]:
        """
        获取用户全量数据
        GET /portal/server/api/user/list
        Returns:
            Dict[str, Any]: 用户列表数据
        """
        logger.info("Getting User's Full Data")
        # 本地调用时需要在portal后加入/server，其他情况则去除
        url = "/portal/server/api/user/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """
        查询用户
        GET /portal/server/api/v2/users/{username}
        Args:
            username: 用户名
        Returns:
            Dict[str, Any]: 用户信息
        """
        logger.info(f"Getting user info for: {username}")
        url = f"/portal/server/api/v2/users/{username}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def create_user(self, user: InnerUserEntity) -> Dict[str, Any]:
        """
        创建用户
        POST /portal/server/api/v2/tenant
        Args:
            user: 用户数据类
        Returns:
            Dict[str, Any]: 创建结果
        """
        logger.info(f"Creating role: {user.username}")
        url = "/portal/server/api/v2/tenant"
        payload = {
            "userName": user.username,
            "alias": user.alias,
            "phone": user.phone,
            "email": user.email,
            "tenantCode": user.tenant_code,
            "roleCode": user.role_code,
            "createId": user.create_id,
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def delete_user(self, username: str) -> Dict[str, Any]:
        """
        删除用户
        DELETE /portal/server/api/v2/users/{username}
        Args:
            username: 用户名称
        Returns:
            Dict[str, Any]: 删除结果
        """
        logger.info(f"Deleting user: {username}")
        url = f"/portal/server/api/v2/users/{username}"
        response = self.delete(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 租户相关接口 ====================

    def get_tenant_full_data(self) -> Dict[str, Any]:
        """
        获取租户全量数据
        GET /portal/server/api/tenant/list
        Returns:
            Dict[str, Any]: 租户列表数据
        """
        logger.info("Getting Tenant's Full Data")
        url = "/portal/server/api/tenant/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def bind_user_tenant(self, username: str, tenant_code: str) -> Dict[str, Any]:
        """
        用户租户绑定
        POST /portal/server/api/v2/users/{username}/tenants/{tenant_code}/bind
        Args:
            username: 用户名
            tenant_code: 租户编码
        Returns:
            Dict[str, Any]: 绑定结果
        """
        logger.info(f"Binding user {username} to tenant {tenant_code}")
        url = f"/portal/server/api/v2/users/{username}/tenants/{tenant_code}/bind"
        response = self.post(endpoint=url, headers=_get_default_headers())
        return response.json()

    def unbind_user_tenant(self, username: str, tenant_code: str) -> Dict[str, Any]:
        """
        用户租户解绑
        POST /portal/server/api/v2/users/{username}/tenants/{tenant_code}/unbind
        Args:
            username: 用户名
            tenant_code: 租户编码
        Returns:
            Dict[str, Any]: 解绑结果
        """
        logger.info(f"Unbinding user {username} from tenant {tenant_code}")
        url = f"/portal/server/api/v2/users/{username}/tenants/{tenant_code}/unbind"
        response = self.post(endpoint=url, headers=_get_default_headers())
        return response.json()

    def bind_user_tenant_role(self, username: str, tenant_code: str, role_code: str) -> Dict[str, Any]:
        """
        用户租户角色绑定
        POST /portal/server/api/v2/users/{username}/tenants/{tenant_code}/roles/{role_code}/bind
        Args:
            username: 用户名
            tenant_code: 租户编码
            role_code: 角色编码
        Returns:
            Dict[str, Any]: 绑定结果
        """
        logger.info(f"Binding role {role_code} to user {username} in tenant {tenant_code}")
        url = f"/portal/server/api/v2/users/{username}/tenants/{tenant_code}/roles/{role_code}/bind"
        response = self.post(endpoint=url, headers=_get_default_headers())
        return response.json()

    def unbind_user_tenant_role(self, username: str, tenant_code: str, role_code: str) -> Dict[str, Any]:
        """
        用户租户角色解绑
        POST /portal/server/api/v2/users/{username}/tenants/{tenant_code}/roles/{role_code}/unbind
        Args:
            username: 用户名
            tenant_code: 租户编码
            role_code: 角色编码
        Returns:
            Dict[str, Any]: 解绑结果
        """
        logger.info(f"Unbinding role {role_code} from user {username} in tenant {tenant_code}")
        url = f"/portal/server/api/v2/users/{username}/tenants/{tenant_code}/roles/{role_code}/unbind"
        response = self.post(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_tenant(self, tenant_code: str) -> Dict[str, Any]:
        """
        查询租户
        GET /portal/server/api/v2/tenants/{tenant_code}
        Args:
            tenant_code: 租户编码
        Returns:
            Dict[str, Any]: 租户列表数据
        """
        logger.info("Getting Tenant's info")
        url = f"/portal/server/api/v2/tenants/{tenant_code}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def create_tenant(self, tenant: TenantEntity) -> Dict[str, Any]:
        """
        创建租户
        POST /portal/server/api/v2/tenant
        Args:
            tenant: 租户数据类
        Returns:
            Dict[str, Any]: 创建结果
        """
        logger.info(f"Creating tenant: {tenant.tenant_code}")
        url = "/portal/server/api/v2/tenant"
        payload = {
            "tenantCode": tenant.tenant_code,
            "tenantName": tenant.tenant_name,
            "tenantLever": tenant.tenant_lever,
            "tenantParentId": tenant.tenant_parent_id,
            "tenantArea": tenant.tenant_area,
            "deptCode": tenant.dept_code,
            "sourceCode": tenant.source_code,
            "createUserId": tenant.create_user_id
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def delete_tenant(self, tenant_code: str) -> Dict[str, Any]:
        """
        删除租户
        DELETE /portal/server/api/v2/tenants/{tenant_code}
        Args:
            tenant_code: 租户编码
        Returns:
            Dict[str, Any]: 删除结果
        """
        logger.info(f"Deleting tenant: {tenant_code}")
        url = f"/portal/server/api/v2/tenants/{tenant_code}"
        response = self.delete(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 角色相关接口 ====================

    def get_role_full_data(self) -> Dict[str, Any]:
        """
        获取角色全量数据
        GET /portal/server/api/role/list
        Returns:
            Dict[str, Any]: 角色列表数据
        """
        logger.info("Getting Role's Full Data")
        url = "/portal/server/api/role/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_roles(self) -> Dict[str, Any]:
        """
        查询角色
        GET /portal/server/api/v2/roles
        Returns:
            Dict[str, Any]: 角色列表数据
        """
        logger.info("Getting roles (v2)")
        url = "/portal/server/api/v2/roles"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def create_role(self, role: RoleEntity) -> Dict[str, Any]:
        """
        创建角色
        POST /portal/server/api/role/add
        Args:
            role: 角色数据类
        Returns:
            Dict[str, Any]: 创建结果
        """
        logger.info(f"Creating role: {role.role_code}")
        url = "/portal/server/api/role/add"
        payload = {
            "roleName": role.role_name,
            "roleCode": role.role_code,
            "roleDesc": role.role_desc,
            "roleType": role.role_type,
            "hasEdit": role.has_edit,
            "createId": role.create_id
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def update_role(self, role: RoleEntity) -> Dict[str, Any]:
        """
        修改角色
        PUT /portal/server/api/v2/roles/{role.role_name}
        Args:
            role: 角色数据类
        Returns:
            Dict[str, Any]: 修改结果
        """
        logger.info(f"Updating role: {role.role_name}")
        url = f"/portal/server/api/v2/roles/{role.role_name}"
        payload = {
            "roleName": role.role_name,
            "roleDesc": role.role_desc,
            "roleType": role.role_type,
            "hasEdit": role.has_edit
        }
        response = self.put(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def delete_role(self, role_code: str) -> Dict[str, Any]:
        """
        删除角色
        DELETE /portal/server/api/v2/roles/{role_code}
        Args:
            role_code: 角色编码
        Returns:
            Dict[str, Any]: 删除结果
        """
        logger.info(f"Deleting role: {role_code}")
        url = f"/portal/server/api/v2/roles/{role_code}"
        response = self.delete(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 字典相关接口 ====================

    def get_dict_by_module(self, module_name: str, dict_type: str = None) -> Dict[str, Any]:
        """
        根据模块名称查询字典数据
        GET /portal/server/api/dict/list/{module_name}
        Args:
            module_name: 模块名称
            dict_type: 字典类型，如 ENVIRONMENT
        Returns:
            Dict[str, Any]: 字典数据
        """
        logger.info(f"Getting dict data for module: {module_name}")
        url = f"/portal/server/api/dict/list/{module_name}"
        params = {}
        if dict_type:
            params["dictType"] = dict_type
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    # ==================== API相关接口 ====================

    def get_role_api_full_data(self) -> Dict[str, Any]:
        """
        获取API全量数据
        GET /portal/server/api/roleApi/list
        Returns:
            Dict[str, Any]: API列表数据
        """
        logger.info("Getting Role API Full Data")
        url = "/portal/server/api/roleApi/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_api_list(self, module_name: str) -> Dict[str, Any]:
        """
        API列表查询
        GET /portal/server/api/v2/apiDefines
        Args:
            module_name: 模块名称
        Returns:
            Dict[str, Any]: API列表数据
        """
        logger.info("Getting API list")
        url = "/portal/server/api/v2/apiDefines"
        params = {
            "moduleName": module_name
        }
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    def api_bulk_authorization(self, role_code, api_list: List[Dict[str,Any]]) -> Dict[str, Any]:
        """
        API批量授权
        POST /portal/server/api/v2/roles/{role_code}/apis/auth
        Args:
            role_code: 角色编码
            api_list: 授权API列表数据，数据可以由API列表查询接口获得
                例如: [{"apiId":"131","authorizedMethod":"get"},{"apiId":"133","authorizedMethod":"post"}]
        Returns:
            Dict[str, Any]: 授权结果
        """
        logger.info(f"API bulk authorization")
        url = f"/portal/server/api/v2/roles/{role_code}/apis/auth"
        payload = api_list
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def api_bulk_reauthorization(self, role_code, api_list: List[Dict[str,Any]]) -> Dict[str, Any]:
        """
        API批量解除授权
        POST /portal/server/api/v2/roles/{role_code}/apis/unAuth
        Args:
            role_code: 角色编码
            api_list: 解除授权API列表数据，数据可以由API列表查询接口获得
                例如: [{"apiId":"131","authorizedMethod":"get"},{"apiId":"133","authorizedMethod":"post"}]
        Returns:
            Dict[str, Any]: 解除授权结果
        """
        logger.info(f"API bulk authorization")
        url = f"/portal/server/api/v2/roles/{role_code}/apis/unAuth"
        payload = api_list
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    # ==================== 系统配置相关接口 ====================

    def get_system_config(self, key: str = "platformCode") -> Dict[str, Any]:
        """
        获取系统参数
        GET /portal/server/api/systemConfig/list
        Args:
            key: 参数键名，如 platformCode
        Returns:
            Dict[str, Any]: 系统参数数据
        """
        logger.info(f"Getting system config, key: {key}")
        url = "/portal/server/api/systemConfig/list"
        params = {}
        if key:
            params["key"] = key
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    # ==================== 版本相关接口 ====================

    def add_version_info(self, component_name: str, component_code: str, component_version: str) -> Dict[str, Any]:
        """
        添加组件版本信息
        POST /portal/server/api/version/addVersionInfo
        Args:
            component_name: 组件名称
            component_code: 组件编码
            component_version: 组件版本
        Returns:
            Dict[str, Any]: 添加结果
        """
        logger.info(f"Adding version info for component: {component_code}")
        url = "/portal/server/api/version/addVersionInfo"
        payload = {
            "componentName": component_name,
            "componentCode": component_code,
            "componentVersion": component_version
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def get_license_info(self, module_code: str) -> Dict[str, Any]:
        """
        获取license信息
        GET /portal/server/api/license/{module_code}
        Args:
            module_code: 模块编码
        Returns:
            Dict[str, Any]: license信息
        """
        logger.info(f"Getting license info for module: {module_code}")
        url = f"/portal/server/api/license/{module_code}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_platform_version(self) -> Dict[str, Any]:
        """
        获取平台版本信息
        GET /portal/server/api/v1/version
        Returns:
            Dict[str, Any]: 平台版本信息
        """
        logger.info("Getting platform version")
        url = "/portal/server/api/v1/version"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 平台相关接口 ====================

    def get_platform_base_info(self) -> Dict[str, Any]:
        """
        获取平台基本信息
        GET /portal/server/api/v1/platform/baseInfo
        Returns:
            Dict[str, Any]: 平台基本信息
        """
        logger.info("Getting platform base info")
        url = "/portal/server/api/v1/platform/baseInfo"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_platform_enable_modules(self) -> Dict[str, Any]:
        """
        获取平台开启模块信息
        GET /portal/server/api/v1/platform/enableModules
        Returns:
            Dict[str, Any]: 开启的模块列表
        """
        logger.info("Getting platform enabled modules")
        url = "/portal/server/api/v1/platform/enableModules"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 全局配置相关接口 ====================

    def get_paas_config(self) -> Dict[str, Any]:
        """
        获取全局配置
        GET /portal/server/api/paasConfig
        Returns:
            Dict[str, Any]: 全局配置数据
        """
        logger.info("Getting PaaS config")
        url = "/portal/server/api/paasConfig"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def update_global_config(self, modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        全局配置修改 和 全局配置修改-还原
        POST /portal/server/api/globalConfig/update
        Args:
            modules: 模块配置列表，如 [{"moduleCode": "component", "enabled": true}]
        Returns:
            Dict[str, Any]: 修改结果
        """
        logger.info("Updating global config")
        url = "/portal/server/api/globalConfig/update"
        payload = {"modules": modules}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    # ==================== 授权相关接口 ====================

    def get_auth_info(self) -> Dict[str, Any]:
        """
        获取系统应用全量授权信息
        GET /portal/server/api/getAuthInfo
        Returns:
            Dict[str, Any]: 授权信息
        """
        logger.info("Getting auth info")
        url = "/portal/server/api/getAuthInfo"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 消息相关接口 ====================

    def send_message(self, users: List[str], content: str) -> Dict[str, Any]:
        """
        站内消息发送
        POST /portal/server/api/msg/send
        Args:
            users: 用户列表，username的list
            content: 消息内容
        Returns:
            Dict[str, Any]: 发送结果
        """
        logger.info(f"Sending message to users: {users}")
        url = "/portal/server/api/msg/send"
        payload = {
            "users": users,
            "content": content
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()


    # ==================== 域相关接口 ====================

    def get_first_field_list(self) -> Dict[str, Any]:
        """
        查询一级域列表
        GET /portal/server/api/firstFieldInfo/list
        Returns:
            Dict[str, Any]: 一级域列表
        """
        logger.info("Getting first field list")
        url = "/portal/server/api/firstFieldInfo/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_second_field_list(self, system_id: str) -> Dict[str, Any]:
        """
        查询二级域列表
        GET /portal/server/api/secondFieldInfo/list
        Args:
            system_id: 系统ID
        Returns:
            Dict[str, Any]: 二级域列表
        """
        logger.info(f"Getting second field list for system: {system_id}")
        url = "/portal/server/api/secondFieldInfo/list"
        params = {"systemId": system_id}
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    # ==================== 系统管理相关接口 ====================

    def create_system(self, system: InnerSystemEntity) -> Dict[str, Any]:
        """
        创建系统
        POST /portal/server/api/system/add
        Args:
            system: 系统数据类
        Returns:
            Dict[str, Any]: 创建结果
        """
        logger.info(f"Creating system: {system.system_code}")
        url = "/portal/server/api/system/add"
        payload = {
            "systemName": system.system_name,
            "fieldOne": system.field_one,
            "fieldTwo": system.field_two,
            "systemSection": system.system_section,
            "systemLevel": system.system_level,
            "systemDesc": system.system_desc,
            "systemCode": system.system_code,
            "systemEnvironment": system.system_environment,
            "tenantId": system.tenant_id,
            "createId": system.create_id,
            "userName": system.username
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def get_system_full_data(self) -> Dict[str, Any]:
        """
        获取系统全量数据
        GET /portal/server/api/system/list
        Returns:
            Dict[str, Any]: 系统列表数据
        """
        logger.info("Getting system full data")
        url = "/portal/server/api/system/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 应用管理相关接口 ====================

    def create_application(self, app: ApplicationEntity) -> Dict[str, Any]:
        """
        创建应用
        POST /portal/server/api/application/add
        Args:
            app: 应用数据类
        Returns:
            Dict[str, Any]: 创建结果
        """
        logger.info(f"Creating application: {app.app_code}")
        url = "/portal/server/api/application/add"
        payload = {
            "environment": app.environment,
            "applicationSourceName": app.app_name,
            "applicationSourceCode": app.app_code,
            "applicationSourceType": app.app_type,
            "workloadType": app.workload_type,
            "microServiceCode": app.micro_service_code,
            "systemId": app.system_id,
            "tenantId": app.tenant_id,
            "createId": app.create_id,
            "userName": app.username
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def get_application_full_data(self) -> Dict[str, Any]:
        """
        获取应用全量数据
        GET /portal/server/api/application/list
        Returns:
            Dict[str, Any]: 应用列表数据
        """
        logger.info("Getting application full data")
        url = "/portal/server/api/application/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 实例查询相关接口 ====================

    def get_all_instances(self, model_code: str) -> Dict[str, Any]:
        """
        全量查询接口（环境/平面/单元/产品实例）
        POST /portal/server/api/all-instances
        Args:
            model_code: 模型编码，可选值：ENVIRONMENT, PLANE, CELL, PROD_INST
        Returns:
            Dict[str, Any]: 实例列表数据
        """
        logger.info(f"Getting all instances for model: {model_code}")
        url = "/portal/server/api/all-instances"
        payload = {"modelCode": model_code}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def get_instances_by_example(self, model_code: str, prod_inst_code: str) -> Dict[str, Any]:
        """
        按条件查询接口（环境/平面/单元/产品实例）
        POST /portal/server/api/list-instance-by-example
        Args:
            model_code: 模型编码，可选值：ENVIRONMENT, PLANE, CELL, PROD_INST
            prod_inst_code: prod实例编码
        Returns:
            Dict[str, Any]: 实例列表数据
        """
        logger.info(f"Getting instances by example for model: {model_code}")
        url = "/portal/server/api/list-instance-by-example"
        payload = {
            "modelCode": model_code,
            "modelExample": {
                "prodInstCode": prod_inst_code
            }
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()


    # ==================== 菜单管理相关接口 ====================

    def get_menu_list(self, source_code: str, all_menu: int = 1) -> Dict[str, Any]:
        """
        查询菜单权限数据
        GET /portal/server/api/menu/list
        Args:
            source_code: 来源编码，如 observability
            all_menu: 是否查询全部菜单，1为是
        Returns:
            Dict[str, Any]: 菜单列表数据
        """
        logger.info(f"Getting menu list for source: {source_code}")
        url = "/portal/server/api/menu/list"
        params = {
            "sourceCode": source_code,
            "allMenu": all_menu
        }
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    def add_menu(self, menu: MenuEntity) -> Dict[str, Any]:
        """
        新增插件菜单
        POST /portal/server/api/menu/add
        Args:
            menu: 菜单数据类
        Returns:
            Dict[str, Any]: 添加结果
        """
        logger.info(f"Adding menu: {menu.menu_name}")
        url = "/portal/server/api/menu/add"
        payload = {
            "viewType": menu.view_type,
            "menuName": menu.menu_name,
            "url": menu.url_path,
            "pluginUrl": menu.plugin_url,
            "sortno": menu.sort_no,
            "status": menu.status,
            "menuType": menu.menu_type,
            "menuIcon": menu.menu_icon,
            "permissionCode": menu.permission_code,
            "parentId": menu.parent_id,
            "pluginFlag": menu.plugin_flag,
            "roles": menu.roles,
            "sourceCode": menu.source_code
        }
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def delete_menu(self, menu_ids: List[str]) -> Dict[str, Any]:
        """
        删除插件菜单
        POST /portal/server/api/menu/delete
        Args:
            menu_ids: 要删除的菜单ID列表
        Returns:
            Dict[str, Any]: 删除结果
        """
        logger.info(f"Deleting menus: {menu_ids}")
        url = "/portal/server/api/menu/delete"
        payload = {"menuIds": menu_ids}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def disable_menu(self, menu_ids: List[str]) -> Dict[str, Any]:
        """
        停用插件菜单
        POST /portal/server/api/menu/disable
        Args:
            menu_ids: 要停用的菜单ID列表
        Returns:
            Dict[str, Any]: 停用结果
        """
        logger.info(f"Disabling menus: {menu_ids}")
        url = "/portal/server/api/menu/disable"
        payload = {"menuIds": menu_ids}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def enable_menu(self, menu_ids: List[str]) -> Dict[str, Any]:
        """
        启用插件菜单
        POST /portal/server/api/menu/enable
        Args:
            menu_ids: 要启用的菜单ID列表
        Returns:
            Dict[str, Any]: 启用结果
        """
        logger.info(f"Enabling menus: {menu_ids}")
        url = "/portal/server/api/menu/enable"
        payload = {"menuIds": menu_ids}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()
