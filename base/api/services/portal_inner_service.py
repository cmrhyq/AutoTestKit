import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List

from base.api.services.base_service import BaseService
from core.config import get_env_config


@dataclass
class InnerSystemEntity(object):
    """
    system_name: 系统名称
    system_code: 系统编码
    field_one: 一级域ID
    field_two: 二级域ID
    create_id: 创建人ID
    username: 创建人用户名
    system_section: 系统分区
    system_level: 系统级别
    system_desc: 系统描述
    system_environment: 系统环境
    tenant_id: 租户ID
    """
    system_name: str
    system_code: str
    field_one: str
    field_two: str
    create_id: str
    username: str
    system_section: str = "算力调度"
    system_level: str = "SYS_1"
    system_desc: str = "test"
    system_environment: str = "PROD"
    tenant_id: int = 1

@dataclass
class ApplicationEntity(object):
    """
    app_name: 应用名称
    app_code: 应用编码
    app_type: 应用类型，如 web_type
    system_id: 系统ID
    create_id: 创建人ID
    username: 创建人用户名
    workload_type: 工作负载类型
    environment: 环境
    tenant_id: 租户ID
    micro_service_code: 微服务编码
    """
    app_name: str
    app_code: str
    app_type: str
    system_id: str
    create_id: str
    username: str
    workload_type: str
    environment: str = "PROD"
    tenant_id: int = 1,
    micro_service_code: str = None

@dataclass
class MenuEntity(object):
    """
    menu_name: 菜单名称
    url_path: 菜单URL
    plugin_url: 插件URL
    source_code: 来源编码，例如 observability
    roles: 角色编码list，例如 ["tenant_admin","platform_manager"]
    view_type: 视图类型，默认1
    sort_no: 排序号，默认1
    status: 状态，默认0
    menu_type: 菜单类型，默认0
    menu_icon: 菜单图标，默认空
    permission_code: 权限编码，例如 observability
    parent_id: 父菜单ID，默认Null
    plugin_flag: 插件标识，例如 observability
    """
    menu_name: str
    url_path: str
    plugin_url: str
    source_code: str = "observability"
    roles: list[str] = field(default_factory=lambda: ["platform_manager"])
    view_type: str = "1"
    sort_no: int = 1
    status: int = 0,
    menu_type: str = "D"
    menu_icon: str = ""
    permission_code: str = ""
    parent_id: str = None
    plugin_flag: str = "observability"

@dataclass
class RoleEntity(object):
    """
    role_name: 角色名称
    role_code: 角色编码
    role_desc: 角色描述，默认None
    role_type: 角色类型，默认1
    has_edit: 是否可编辑，默认1
    create_id: 创建用户id，默认None
    """
    role_name: str
    role_code: str
    role_desc: str = None
    role_type: int = 1
    has_edit: int = 1
    create_id: str = None

@dataclass
class TenantEntity(object):
    """
    tenant_name: 租户名称
    tenant_code: 租户编码
    tenant_lever: 租户等级
    tenant_parent_id: 父租户id
    tenant_area: 租户区域
    dept_code: 部门编码
    source_code: 来源编码，例如 plugin-center
    create_user_id: 创建者id
    """
    tenant_code: str = None
    tenant_name: str = None
    tenant_lever: int = None
    tenant_parent_id: int = None
    tenant_area: int = None
    dept_code: str = None
    source_code: str = "plugin-center"
    create_user_id: int = None

@dataclass
class InnerUserEntity(object):
    """
    username: 用户名，AES加密
    alias: 用户别名
    phone: 手机号，DES加密
    email: 邮箱，DES加密
    tenant_code: 租户编码
    role_code: 角色编码
    create_id: 创建者id
    """
    username: str = None
    alias: str = None
    phone: str = None
    email: str = None
    tenant_code: str = None
    role_code: str = None
    create_id: int = None


def _get_default_headers() -> Dict[str, str]:
    """获取默认请求头"""
    return {
        "apikey": get_env_config().get("apikey"),
        "tenantCode": get_env_config().get("tenant_code"),
        "x-app-id": "portal",
    }


class PanJiPortalInnerService(BaseService):
    """
    盘古门户 InnerAPI 服务类
    提供门户系统内部 API 的调用方法
    """
    DEFAULT_BASE_URL = 'http://openapi.portal.nbpod3-31-181-20030.4a.cmit.cloud:20030'

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        """
        初始化 Panji Portal InnerAPI 服务

        Args:
            base_url: API 基础 URL
            logger: 日志记录器
        """
        super().__init__(
            base_url=base_url or self.DEFAULT_BASE_URL,
            logger=logger
        )
        self.logger.info(f"Initializing PanJi Portal InnerAPI Service with base_url: {self.base_url}")

    # ==================== 用户相关接口 ====================

    def get_user_full_data(self) -> Dict[str, Any]:
        """
        获取用户全量数据

        Returns:
            Dict[str, Any]: 用户列表数据
        """
        self.logger.info("Getting User's Full Data")
        # 本地调用时需要在portal后加入/server，其他情况则去除
        url = "/portal/api/user/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """
        查询用户

        Args:
            username: 用户名

        Returns:
            Dict[str, Any]: 用户信息
        """
        self.logger.info(f"Getting user info for: {username}")
        url = f"/portal/api/v2/users/{username}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def create_user(self, user: InnerUserEntity) -> Dict[str, Any]:
        """
        创建用户

        Args:
            user: 用户数据类

        Returns:
            Dict[str, Any]: 创建结果
        """
        self.logger.info(f"Creating role: {user.username}")
        url = "/portal/api/v2/tenant"
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

        Args:
            username: 用户名称

        Returns:
            Dict[str, Any]: 删除结果
        """
        self.logger.info(f"Deleting user: {username}")
        url = f"/portal/api/v2/users/{username}"
        response = self.delete(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 租户相关接口 ====================

    def get_tenant_full_data(self) -> Dict[str, Any]:
        """
        获取租户全量数据

        Returns:
            Dict[str, Any]: 租户列表数据
        """
        self.logger.info("Getting Tenant's Full Data")
        url = "/portal/api/tenant/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def bind_user_tenant(self, username: str, tenant_code: str) -> Dict[str, Any]:
        """
        用户租户绑定

        Args:
            username: 用户名
            tenant_code: 租户编码

        Returns:
            Dict[str, Any]: 绑定结果
        """
        self.logger.info(f"Binding user {username} to tenant {tenant_code}")
        url = f"/portal/api/v2/users/{username}/tenants/{tenant_code}/bind"
        response = self.post(endpoint=url, headers=_get_default_headers())
        return response.json()

    def unbind_user_tenant(self, username: str, tenant_code: str) -> Dict[str, Any]:
        """
        用户租户解绑

        Args:
            username: 用户名
            tenant_code: 租户编码

        Returns:
            Dict[str, Any]: 解绑结果
        """
        self.logger.info(f"Unbinding user {username} from tenant {tenant_code}")
        url = f"/portal/api/v2/users/{username}/tenants/{tenant_code}/unbind"
        response = self.post(endpoint=url, headers=_get_default_headers())
        return response.json()

    def bind_user_tenant_role(self, username: str, tenant_code: str, role_code: str) -> Dict[str, Any]:
        """
        用户租户角色绑定

        Args:
            username: 用户名
            tenant_code: 租户编码
            role_code: 角色编码

        Returns:
            Dict[str, Any]: 绑定结果
        """
        self.logger.info(f"Binding role {role_code} to user {username} in tenant {tenant_code}")
        url = f"/portal/api/v2/users/{username}/tenants/{tenant_code}/roles/{role_code}/bind"
        response = self.post(endpoint=url, headers=_get_default_headers())
        return response.json()

    def unbind_user_tenant_role(self, username: str, tenant_code: str, role_code: str) -> Dict[str, Any]:
        """
        用户租户角色解绑

        Args:
            username: 用户名
            tenant_code: 租户编码
            role_code: 角色编码

        Returns:
            Dict[str, Any]: 解绑结果
        """
        self.logger.info(f"Unbinding role {role_code} from user {username} in tenant {tenant_code}")
        url = f"/portal/api/v2/users/{username}/tenants/{tenant_code}/roles/{role_code}/unbind"
        response = self.post(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_tenant(self, tenant_code: str) -> Dict[str, Any]:
        """
        查询租户

        Args:
            tenant_code: 租户编码

        Returns:
            Dict[str, Any]: 租户列表数据
        """
        self.logger.info("Getting Tenant's info")
        url = f"/portal/api/v2/tenants/{tenant_code}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def create_tenant(self, tenant: TenantEntity) -> Dict[str, Any]:
        """
        创建租户

        Args:
            tenant: 租户数据类

        Returns:
            Dict[str, Any]: 创建结果
        """
        self.logger.info(f"Creating tenant: {tenant.tenant_code}")
        url = "/portal/api/v2/tenant"
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

        Args:
            tenant_code: 租户编码

        Returns:
            Dict[str, Any]: 删除结果
        """
        self.logger.info(f"Deleting tenant: {tenant_code}")
        url = f"/portal/api/v2/tenants/{tenant_code}"
        response = self.delete(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 角色相关接口 ====================

    def get_role_full_data(self) -> Dict[str, Any]:
        """
        获取角色全量数据

        Returns:
            Dict[str, Any]: 角色列表数据
        """
        self.logger.info("Getting Role's Full Data")
        url = "/portal/api/role/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_roles(self) -> Dict[str, Any]:
        """
        查询角色

        Returns:
            Dict[str, Any]: 角色列表数据
        """
        self.logger.info("Getting roles (v2)")
        url = "/portal/api/v2/roles"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def create_role(self, role: RoleEntity) -> Dict[str, Any]:
        """
        创建角色

        Args:
            role: 角色数据类

        Returns:
            Dict[str, Any]: 创建结果
        """
        self.logger.info(f"Creating role: {role.role_code}")
        url = "/portal/api/role/add"
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

        Args:
            role: 角色数据类

        Returns:
            Dict[str, Any]: 修改结果
        """
        self.logger.info(f"Updating role: {role.role_name}")
        url = f"/portal/api/v2/roles/{role.role_name}"
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

        Args:
            role_code: 角色编码

        Returns:
            Dict[str, Any]: 删除结果
        """
        self.logger.info(f"Deleting role: {role_code}")
        url = f"/portal/api/v2/roles/{role_code}"
        response = self.delete(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 字典相关接口 ====================

    def get_dict_by_module(self, module_name: str, dict_type: str = None) -> Dict[str, Any]:
        """
        根据模块名称查询字典数据

        Args:
            module_name: 模块名称
            dict_type: 字典类型，如 ENVIRONMENT

        Returns:
            Dict[str, Any]: 字典数据
        """
        self.logger.info(f"Getting dict data for module: {module_name}")
        url = f"/portal/api/dict/list/{module_name}"
        params = {}
        if dict_type:
            params["dictType"] = dict_type
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    # ==================== API相关接口 ====================

    def get_role_api_full_data(self) -> Dict[str, Any]:
        """
        获取API全量数据

        Returns:
            Dict[str, Any]: API列表数据
        """
        self.logger.info("Getting Role API Full Data")
        url = "/portal/api/roleApi/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_api_list(self, module_name: str) -> Dict[str, Any]:
        """
        API列表查询

        Args:
            module_name: 模块名称

        Returns:
            Dict[str, Any]: API列表数据
        """
        self.logger.info("Getting API list")
        url = "/portal/api/v2/apiDefines"
        params = {
            "moduleName": module_name
        }
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    def api_bulk_authorization(self, role_code, api_list: List[Dict[str,Any]]) -> Dict[str, Any]:
        """
        API批量授权

        Args:
            role_code: 角色编码
            api_list: 授权API列表数据，数据可以由API列表查询接口获得
                例如: [{"apiId":"131","authorizedMethod":"get"},{"apiId":"133","authorizedMethod":"post"}]

        Returns:
            Dict[str, Any]: 授权结果
        """
        self.logger.info(f"API bulk authorization")
        url = f"/portal/api/v2/roles/{role_code}/apis/auth"
        payload = api_list
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def api_bulk_reauthorization(self, role_code, api_list: List[Dict[str,Any]]) -> Dict[str, Any]:
        """
        API批量解除授权

        Args:
            role_code: 角色编码
            api_list: 解除授权API列表数据，数据可以由API列表查询接口获得
                例如: [{"apiId":"131","authorizedMethod":"get"},{"apiId":"133","authorizedMethod":"post"}]

        Returns:
            Dict[str, Any]: 解除授权结果
        """
        self.logger.info(f"API bulk authorization")
        url = f"/portal/api/v2/roles/{role_code}/apis/unAuth"
        payload = api_list
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    # ==================== 系统配置相关接口 ====================

    def get_system_config(self, key: str = "platformCode") -> Dict[str, Any]:
        """
        获取系统参数

        Args:
            key: 参数键名，如 platformCode

        Returns:
            Dict[str, Any]: 系统参数数据
        """
        self.logger.info(f"Getting system config, key: {key}")
        url = "/portal/api/systemConfig/list"
        params = {}
        if key:
            params["key"] = key
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    # ==================== 版本相关接口 ====================

    def add_version_info(self, component_name: str, component_code: str, component_version: str) -> Dict[str, Any]:
        """
        添加组件版本信息

        Args:
            component_name: 组件名称
            component_code: 组件编码
            component_version: 组件版本

        Returns:
            Dict[str, Any]: 添加结果
        """
        self.logger.info(f"Adding version info for component: {component_code}")
        url = "/portal/api/version/addVersionInfo"
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

        Args:
            module_code: 模块编码

        Returns:
            Dict[str, Any]: license信息
        """
        self.logger.info(f"Getting license info for module: {module_code}")
        url = f"/portal/api/license/{module_code}"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_platform_version(self) -> Dict[str, Any]:
        """
        获取平台版本信息

        Returns:
            Dict[str, Any]: 平台版本信息
        """
        self.logger.info("Getting platform version")
        url = "/portal/api/v1/version"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 平台相关接口 ====================

    def get_platform_base_info(self) -> Dict[str, Any]:
        """
        获取平台基本信息

        Returns:
            Dict[str, Any]: 平台基本信息
        """
        self.logger.info("Getting platform base info")
        url = "/portal/api/v1/platform/baseInfo"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_platform_enable_modules(self) -> Dict[str, Any]:
        """
        获取平台开启模块信息

        Returns:
            Dict[str, Any]: 开启的模块列表
        """
        self.logger.info("Getting platform enabled modules")
        url = "/portal/api/v1/platform/enableModules"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 全局配置相关接口 ====================

    def get_paas_config(self) -> Dict[str, Any]:
        """
        获取全局配置

        Returns:
            Dict[str, Any]: 全局配置数据
        """
        self.logger.info("Getting PaaS config")
        url = "/portal/api/paasConfig"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def update_global_config(self, modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        全局配置修改 和 全局配置修改-还原

        Args:
            modules: 模块配置列表，如 [{"moduleCode": "component", "enabled": true}]

        Returns:
            Dict[str, Any]: 修改结果
        """
        self.logger.info("Updating global config")
        url = "/portal/api/globalConfig/update"
        payload = {"modules": modules}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    # ==================== 授权相关接口 ====================

    def get_auth_info(self) -> Dict[str, Any]:
        """
        获取系统应用全量授权信息

        Returns:
            Dict[str, Any]: 授权信息
        """
        self.logger.info("Getting auth info")
        url = "/portal/api/getAuthInfo"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 消息相关接口 ====================

    def send_message(self, users: List[str], content: str) -> Dict[str, Any]:
        """
        站内消息发送

        Args:
            users: 用户列表，username的list
            content: 消息内容

        Returns:
            Dict[str, Any]: 发送结果
        """
        self.logger.info(f"Sending message to users: {users}")
        url = "/portal/api/msg/send"
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

        Returns:
            Dict[str, Any]: 一级域列表
        """
        self.logger.info("Getting first field list")
        url = "/portal/api/firstFieldInfo/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    def get_second_field_list(self, system_id: str) -> Dict[str, Any]:
        """
        查询二级域列表

        Args:
            system_id: 系统ID

        Returns:
            Dict[str, Any]: 二级域列表
        """
        self.logger.info(f"Getting second field list for system: {system_id}")
        url = "/portal/api/secondFieldInfo/list"
        params = {"systemId": system_id}
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    # ==================== 系统管理相关接口 ====================

    def create_system(self, system: InnerSystemEntity) -> Dict[str, Any]:
        """
        创建系统

        Args:
            system: 系统数据类

        Returns:
            Dict[str, Any]: 创建结果
        """
        self.logger.info(f"Creating system: {system.system_code}")
        url = "/portal/api/system/add"
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

        Returns:
            Dict[str, Any]: 系统列表数据
        """
        self.logger.info("Getting system full data")
        url = "/portal/api/system/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 应用管理相关接口 ====================

    def create_application(self, app: ApplicationEntity) -> Dict[str, Any]:
        """
        创建应用

        Args:
            app: 应用数据类

        Returns:
            Dict[str, Any]: 创建结果
        """
        self.logger.info(f"Creating application: {app.app_code}")
        url = "/portal/api/application/add"
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

        Returns:
            Dict[str, Any]: 应用列表数据
        """
        self.logger.info("Getting application full data")
        url = "/portal/api/application/list"
        response = self.get(endpoint=url, headers=_get_default_headers())
        return response.json()

    # ==================== 实例查询相关接口 ====================

    def get_all_instances(self, model_code: str) -> Dict[str, Any]:
        """
        全量查询接口（环境/平面/单元/产品实例）

        Args:
            model_code: 模型编码，可选值：ENVIRONMENT, PLANE, CELL, PROD_INST

        Returns:
            Dict[str, Any]: 实例列表数据
        """
        self.logger.info(f"Getting all instances for model: {model_code}")
        url = "/portal/api/all-instances"
        payload = {"modelCode": model_code}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def get_instances_by_example(self, model_code: str, prod_inst_code: str) -> Dict[str, Any]:
        """
        按条件查询接口（环境/平面/单元/产品实例）

        Args:
            model_code: 模型编码，可选值：ENVIRONMENT, PLANE, CELL, PROD_INST
            prod_inst_code: prod实例编码

        Returns:
            Dict[str, Any]: 实例列表数据
        """
        self.logger.info(f"Getting instances by example for model: {model_code}")
        url = "/portal/api/list-instance-by-example"
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

        Args:
            source_code: 来源编码，如 observability
            all_menu: 是否查询全部菜单，1为是

        Returns:
            Dict[str, Any]: 菜单列表数据
        """
        self.logger.info(f"Getting menu list for source: {source_code}")
        url = "/portal/api/menu/list"
        params = {
            "sourceCode": source_code,
            "allMenu": all_menu
        }
        response = self.get(endpoint=url, params=params, headers=_get_default_headers())
        return response.json()

    def add_menu(self, menu: MenuEntity) -> Dict[str, Any]:
        """
        新增插件菜单

        Args:
            menu: 菜单数据类

        Returns:
            Dict[str, Any]: 添加结果
        """
        self.logger.info(f"Adding menu: {menu.menu_name}")
        url = "/portal/api/menu/add"
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

        Args:
            menu_ids: 要删除的菜单ID列表

        Returns:
            Dict[str, Any]: 删除结果
        """
        self.logger.info(f"Deleting menus: {menu_ids}")
        url = "/portal/api/menu/delete"
        payload = {"menuIds": menu_ids}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def disable_menu(self, menu_ids: List[str]) -> Dict[str, Any]:
        """
        停用插件菜单

        Args:
            menu_ids: 要停用的菜单ID列表

        Returns:
            Dict[str, Any]: 停用结果
        """
        self.logger.info(f"Disabling menus: {menu_ids}")
        url = "/portal/api/menu/disable"
        payload = {"menuIds": menu_ids}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()

    def enable_menu(self, menu_ids: List[str]) -> Dict[str, Any]:
        """
        启用插件菜单

        Args:
            menu_ids: 要启用的菜单ID列表

        Returns:
            Dict[str, Any]: 启用结果
        """
        self.logger.info(f"Enabling menus: {menu_ids}")
        url = "/portal/api/menu/enable"
        payload = {"menuIds": menu_ids}
        response = self.post(endpoint=url, json=payload, headers=_get_default_headers())
        return response.json()
