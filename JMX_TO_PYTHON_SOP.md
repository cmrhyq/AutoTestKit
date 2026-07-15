# JMX 接口测试脚本转换为 Python pytest 测试代码 SOP

## 一、概述

本文档描述如何将 JMeter（.jmx）接口测试脚本转换为本项目（AutoTestKit）中的 Python pytest 测试代码。转换需要遵循项目已有的代码风格和架构约定。

本 SOP 与 `tests/api/` 下现有实现保持同步，若代码与本文档冲突，以代码为准并回头修订本 SOP。

---

## 二、项目架构（必须理解）

```
AutoTestKit/
├── base/api/
│   ├── fixtures.py                       # 全局 API fixtures（api_env / api_cache / api_logger 等）
│   └── services/                         # 服务层（封装 HTTP 请求 + Entity 数据类）
│       ├── base_service.py               # 基础服务类，含 get/post/put/delete；已 raise_for_status
│       ├── portal_inner_service.py       # 门户 InnerAPI 服务
│       ├── portal_open_service.py        # 门户 OpenAPI 服务
│       ├── microservices_inner_service.py
│       ├── microservices_open_service.py
│       ├── observable_open_service.py
│       ├── operation_open_service.py
│       └── plugin_open_service.py
├── config/
│   ├── env_test.yaml                     # 默认测试环境配置
│   └── env_bcv25_arm.yaml                # BCV25 ARM 环境配置（key 必须与 env_test.yaml 保持一致）
├── core/
│   ├── cache/data_cache.py               # DataCache 单例，进程内共享；has/get/set/clear/get_all_keys
│   └── reporting/allure_helper.py        # AllureHelper.step / AllureHelper.api_test
├── tests/api/
│   ├── conftest.py                       # 转出全局 fixtures + 定义 get_token 多租户登录工厂
│   ├── portal/                           # portal 业务域测试
│   │   ├── test_portal_innerapi.py
│   │   └── test_portal_openapi.py
│   ├── observable/                       # observable 业务域测试
│   ├── operations/                       # operations 业务域测试
│   ├── plugin/                           # plugin 业务域测试
│   └── examples/                         # 示例与脚手架，不参与 CI
└── conftest.py                           # 根 conftest：xdist、Allure environment、session hooks
```

新增测试必须按业务域放到 `tests/api/<domain>/` 下（现存的 domain：`portal`、`observable`、`operations`、`plugin`）。若 JMX 属于新业务域，需要新建目录并加 `__init__.py`。

### 关键组件说明

| 组件 | 作用 | 用法 |
|------|------|------|
| `api_env` | fixture，从 yaml 配置文件加载的字典 | `api_env.get("参数名")` |
| `api_cache` | fixture，`DataCache` 实例，测试间共享数据 | `api_cache.set(k, v)` / `api_cache.get(k)` / `api_cache.has(k)` |
| `api_logger` | fixture，日志记录器 | 传入 Service 构造函数；禁止打印 password / token 明文 |
| `get_token(tenant_code)` | fixture（`tests/api/conftest.py`），懒加载多租户登录工厂 | `get_token("tenant_admin")`，内部会覆写 `cache["token"]` |
| `BaseService` | HTTP 客户端基类，`.get/.post/.put/.delete` 内部已 `raise_for_status()` | 测试只需断业务字段，不需断 HTTP status |
| `AllureHelper.step("...")` | Allure 步骤上下文管理器 | `with AllureHelper.step("发送请求"):` |
| `AllureHelper.api_test(service)` | 包住整个测试用例，自动 attach 该 service 的请求/响应到 Allure | `with AllureHelper.api_test(svc): ...` |

### Token 数据流（务必理解）

```
config/env_*.yaml           get_token("X") 首次调用             _get_default_headers()
   tenants: {...}   -->   Login 接口 -> cache["token::X"]  -->   cache.get("token")
                                       cache["token"]              被 service 塞进 Authorization
```

- 每个测试类顶部声明 `TENANT = "..."`；
- 一个 autouse `_login` fixture 每个用例前调用 `get_token(self.TENANT)`；
- 该调用会把当前租户 token 写入 `cache["token"]`，`_get_default_headers()` 读它拼 `Authorization`；
- 若同一 session 内其他类切了别的租户，只要下一个用例的 `_login` 再跑一次，`cache["token"]` 就被切回来。

---

## 三、转换流程（Step by Step）

### Step 1：分析 JMX 文件结构

JMX 文件是 XML 格式，需要识别以下关键元素：

| JMX 元素 | 含义 | 位置 |
|----------|------|------|
| `<ThreadGroup>` | 线程组 = 一个测试类 | 顶层 hashTree |
| `<Arguments>`（用户定义变量） | 测试参数 | ThreadGroup 下的第一个 hashTree |
| `<HeaderManager>` | 公共请求头 | ThreadGroup 下 |
| `<ConfigTestElement>`（HTTP 默认值） | base_url、port、protocol | ThreadGroup 下 |
| `<HTTPSamplerProxy>` | 一个 HTTP 请求 = 一个测试步骤 | hashTree 内 |
| `<ResponseAssertion>` | 断言 | HTTPSamplerProxy 的子 hashTree |
| `<JSONPostProcessor>` | 从响应中提取值 | HTTPSamplerProxy 的子 hashTree |
| `<IfController>` | 条件分支 | hashTree 内 |

### Step 2：提取测试参数写入 YAML

将 JMX 中 `<Arguments>` 的用户定义变量提取出来，写入当前 `TEST_ENV` 对应的 `config/env_<env>.yaml`。

**硬约束：所有 env yaml 的 key 必须对齐。** 新增任何一个 key，`config/env_test.yaml` 与 `config/env_bcv25_arm.yaml`（以及未来新加的 env 文件）都要同步添加；否则切换环境时 `api_env.get(...)` 会返回 `None`，导致隐蔽的 401 或断言失败。

**命名规则：**

- 全部使用 `snake_case`（下划线分隔小写）
- 如果变量名和已有 YAML 变量**名称相同且值相同**，直接复用已有变量
- 如果**名称相同但值不同**，添加前缀区分（如 `inner_system_code` vs `portal_system_code`）
- 每个参数上方加中文注释说明用途
- 字符串数字加引号：`user_id: "201214"`
- 相关参数用空行和注释分组

**示例：**

```yaml
# InnerAPI 系统编码 - 用于创建系统时的 systemName 和 systemCode
inner_system_code: testxt20250711
```

### Step 3：确认 / 创建 Service 层

检查 `base/api/services/` 下是否已有对应的 Service 类。

- **已有**：直接使用，查看已有方法是否覆盖 JMX 中的接口
- **缺少方法**：在已有 Service 类中补充新方法
- **完全没有**：创建新的 Service 类继承 `BaseService`

**Service 类规范：**

```python
class XxxService(BaseService):
    DEFAULT_BASE_URL = "http://openapi.xxx.example.com:20030"

    def __init__(self, base_url: str = None, logger: logging.Logger = None):
        super().__init__(
            base_url=base_url or self.DEFAULT_BASE_URL,
            logger=logger,
        )

    def some_api(self, param1: str, param2: int) -> Dict[str, Any]:
        """接口描述。"""
        url = "/path/to/api"
        response = self.get(
            endpoint=url,
            headers=_get_default_headers(),
            params={"p1": param1, "p2": param2},
        )
        return response.json()
```

- `DEFAULT_BASE_URL` 仅作为**兜底**，测试的 fixture 必须显式从 `api_env.get("api_base_url")`（或对应 key）传入；禁止在测试文件中出现任何 URL 字面量。
- 免鉴权接口（如 login、健康检查）不加 `_get_default_headers()`；其他所有接口都必须带上。

### Step 4：编写测试文件

在 `tests/api/<domain>/` 下创建测试文件，命名为 `test_{jmx文件名去横线}.py`。`<domain>` 与 JMX 归属的业务模块一致（portal / observable / operations / plugin），JMX 原始文件建议同步放到该 domain 下的 `assets/`（或统一入口）中，便于对照。

---

## 四、代码模板

```python
"""
{模块中文名} 接口测试

转换自 JMeter 脚本: {filename}.jmx
测试内容：{简要描述测试覆盖的功能点}
"""

from typing import Dict, Any

import allure
import pytest

from base.api.fixtures import api_cache  # noqa: F401  仅为让 IDE 感知 fixture 存在
from base.api.services.xxx_service import (
    XxxService,
    SomeEntity,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("{模块名}")
@allure.story("{jmx 文件对应的测试故事}")
class TestXxx:
    """
    对应 JMeter 脚本: {filename}.jmx
    线程组: {线程组名称}
    """

    TENANT = "tenant_admin"

    @pytest.fixture(autouse=True)
    def _login(self, get_token):
        """每个用例前自动切换到本测试类声明的租户 token。"""
        get_token(self.TENANT)

    @pytest.fixture(scope="class")
    def xxx_service(self, api_env, api_logger):
        """创建服务实例，base_url 从 env yaml 显式传入。"""
        service = XxxService(
            base_url=api_env.get("api_base_url"),
            logger=api_logger,
        )
        yield service
        service.close()

    @allure.title("{接口中文名}")
    @allure.description("{HTTP 方法} {路径} - {验证描述}")
    @allure.severity(allure.severity_level.CRITICAL)  # 或 NORMAL
    def test_some_api(self, xxx_service, api_env, api_cache):
        with AllureHelper.api_test(xxx_service):
            with AllureHelper.step("发送请求"):
                response_json = xxx_service.some_api(
                    param1=api_env.get("some_param"),
                    param2=api_cache.get("upstream_id"),
                )

            with AllureHelper.step("验证响应数据"):
                assert isinstance(response_json, dict), "响应应该是字典类型"
                assert response_json.get("code") == 0, (
                    f"业务码非 0: {response_json}"
                )

            with AllureHelper.step("缓存供下游用例使用"):
                api_cache.set("some_id", response_json["data"]["id"])
```

要点：

- **`TENANT` + `_login` autouse 缺一不可**：没有它整个类拿不到 `Authorization`，第一条用例就会 401。
- **`AllureHelper.api_test(service)` 包住整个用例体**：无论成功失败都会把 service 层发出的请求/响应完整 attach 到 Allure。
- **`AllureHelper.step(...)` 分段包住关键操作**：请求、断言、缓存写入分别成段。
- **参数来自 `api_env` 或 `api_cache`**：禁止在测试方法里出现字面量参数（URL、账号、明文 token、写死的 id 等）。

---

## 五、转换映射规则

### 5.1 HTTP 请求映射

| JMX | Python |
|-----|--------|
| `HTTPSamplerProxy` method=GET | `service.get(endpoint=url, params={...}, headers=_get_default_headers())` |
| `HTTPSamplerProxy` method=POST + `postBodyRaw=true` | `service.post(endpoint=url, json={...}, headers=_get_default_headers())` |
| `HTTPSamplerProxy` method=POST + `postBodyRaw=false` | `service.post(endpoint=url, data={...}, headers=_get_default_headers())` |
| `HTTPSamplerProxy` method=PUT | `service.put(endpoint=url, json={...}, headers=_get_default_headers())` |
| `HTTPSamplerProxy` method=DELETE | `service.delete(endpoint=url, headers=_get_default_headers())` |

### 5.2 JMX 变量引用映射

| JMX | Python |
|-----|--------|
| `${variableName}`（用户定义变量） | `api_env.get("variable_name")` |
| `${extractedVar}`（JSON 提取器结果） | `api_cache.get("extracted_var")` |

### 5.3 JSON 提取器映射

| JMX JSONPostProcessor | Python |
|----------------------|--------|
| `$.data[0].id` | `data = response_json.get("data") or []; val = data[0].get("id") if data else None` |
| `$.data[?(@.code=="xxx")].id` | `val = next((item.get("id") for item in data if item.get("code") == "xxx"), None)` |

提取后缓存：`api_cache.set("variable_name", val)`。**若下游用例强依赖该值，本用例中提取失败应直接 `pytest.fail(...)` 明确暴露；下游用例开头则用 `if not api_cache.get("variable_name"): pytest.skip("缺少 upstream")` 优雅跳过。**

### 5.4 断言映射

Service 层的 `get/post/put/delete` 已经内部调用了 `raise_for_status()`（非 2xx 直接抛异常），**测试代码不需要再断 HTTP `status_code`**。测试应关注两件事：

1. **响应结构断言**：`assert isinstance(response_json, dict)`；
2. **业务码断言**：InnerAPI 与部分下游服务用 `response_json["code"] == 0`；OpenAPI 的登录接口返回 `code == 200`，其他 OpenAPI 业务接口大多是 `code == 0`。**转换前先跑一次原 JMX 看真实响应，再决定断哪个值**，不要臆测。

| JMX ResponseAssertion | Python |
|----------------------|--------|
| `Assertion.response_code` 包含 `200` | 由 `raise_for_status()` 覆盖，测试代码通常无需再断 |
| `Assertion.response_data` 包含 `"code":0` | `assert response_json.get("code") == 0` |
| `Assertion.response_data` 包含 `xxx` | `assert "xxx" in json.dumps(response_json, ensure_ascii=False)` |
| `test_type=8`（equals） | `assert value == expected` |
| `test_type=2`（contains） | `assert expected in value` |
| `test_type=16`（not） | `assert value != expected` |

### 5.5 条件分支映射

| JMX IfController | Python |
|-----------------|--------|
| `${__jexl2("${var}"=="expected",)}` | `if str(api_cache.get("var")) == "expected":` |
| 数字类比较 | `if int(api_cache.get("var")) > 0:`（JMX 里 `${var}` 展开为字符串，注意类型转换） |
| 条件判断后执行不同请求 | 在同一测试方法内用 `if/else` 处理 |

### 5.6 请求体 XML 实体解码

JMX 中 POST body 使用 XML 实体编码，转换时需要还原：

| JMX 转义 | 还原 |
|---------|------|
| `&quot;` | `"` |
| `&apos;` | `'` |
| `&amp;` | `&` |
| `&lt;` | `<` |
| `&gt;` | `>` |
| `&#xd;` | `\r`（一般直接忽略） |
| `&#xa;` | `\n`（一般直接忽略） |

---

## 六、严格禁止事项

1. **不要创建独立的 `test_data` fixture** — 所有测试参数通过 `api_env.get("param_name")` 从 YAML 配置读取。
2. **不要在测试文件中出现任何 URL / 账号 / token 字面量** — base_url 从 `api_env` 获取，账号密码走 `tenants` 配置，token 走 `get_token`。
3. **不要直接使用 `requests` 库** — 必须通过 Service 层的方法发请求。
4. **不要在测试方法中写 `print`** — 使用 `AllureHelper.step()` / `api_logger` 记录。
5. **不要用 `unittest.TestCase`** — 使用 pytest class 风格。
6. **不要用驼峰命名测试方法** — 用 `test_snake_case` 格式。
7. **不要忽略 JMX 中的数据依赖** — 如果接口 B 依赖接口 A 的响应数据，必须通过 `api_cache` 传递。
8. **不要把 CRUD 全流程塞进一个测试方法** — 每个 API 一个 test 方法，跨用例数据用 `api_cache.set/get` 传递；下游用例缺前置数据时 `pytest.skip(...)` 跳过。这一条与 7.3 相呼应，且与项目现存实现一致（见 `tests/api/portal/test_portal_openapi.py`）。
9. **不要在具体 test 文件里定义 session / class 级 fixture 顶替 `base/api/fixtures.py` 或 `tests/api/conftest.py` 里的同名 fixture** — 尤其是 `api_env / api_cache / api_logger / get_token`。若确实需要扩展，改进对应共享文件而不是在测试里覆盖。
10. **不要修改 Service 层中已有方法的签名** — 只允许新增方法。修签名必须同步改所有调用方并通过 CI。
11. **不要在测试类里省略 `TENANT` 类属性和 `_login` autouse fixture** — 缺任意一个会导致 `Authorization` 为空。免鉴权接口的类可显式声明 `TENANT = None` 并在 `_login` 里跳过。
12. **不要在日志 / Allure step 描述里打印敏感字段** — password、token、apikey、身份证、手机号等必须脱敏或不打印。
13. **不要在 dataclass 字段末尾写逗号** — 否则会被解析成单元素 tuple（详见 7.7）。

---

## 七、注意事项

### 7.1 YAML 参数命名规范

- 全部 `snake_case`；
- 字符串数字加引号：`user_id: "201214"`；
- 相关参数用空行和注释分组；
- **同一份 key 必须存在于所有 `env_*.yaml`**，跨环境保持结构一致（值可以不同）。

### 7.2 测试方法排列顺序

按照 JMX 中 `HTTPSamplerProxy` 的出现顺序排列测试方法，因为：

- JMX 是顺序执行的，后面的请求可能依赖前面的数据；
- 保持顺序便于对照验证。

pytest 默认按源码顺序执行同一个类内的方法，符合此约定；不要用 `pytest-ordering` 之类的插件重排。

### 7.3 数据依赖处理

如果测试 B 依赖测试 A 提取的数据：

- 测试 A 中：`api_cache.set("key", value)`；
- 测试 B 中：

  ```python
  value = api_cache.get("key")
  if not value:
      pytest.skip("缺少 A 提供的 key")
  ```

### 7.4 条件分支的处理策略

JMX 中的 `IfController` 通常是为了处理"数据存在 / 不存在"两种情况。转换时：

- 合并为一个测试方法内的分支；
- 先查询判断状态，再决定操作路径；
- 典型模式：查询 → 若存在则先删除 → 创建 → 验证 → 清理。

注意：JMX 里 `${var}` 展开是字符串，Python 端做数值比较需要 `int(...)`。

### 7.5 Allure 装饰器

每个测试方法必须有：

- `@allure.title("中文标题")` — 简短描述接口功能；
- `@allure.description("详细描述")` — 包含 HTTP 方法和路径；
- `@allure.severity(...)` — `CRITICAL`（核心流程）或 `NORMAL`（辅助接口）。

每个测试方法体建议：

- 最外层用 `with AllureHelper.api_test(service):` 包裹（保证请求/响应都 attach 到报告）；
- 内部用 `with AllureHelper.step("..."):` 分段。

### 7.6 Service 方法中的 headers

InnerAPI / OpenAPI 都通过 `_get_default_headers()` 获取默认请求头（内部会读 `DataCache.get("token")` 拼 `Authorization`）。这是 `get_token` fixture 与 Service 层之间约定的接口，**测试方法里绝对不要手动拼 `Authorization`**。免鉴权接口（login、健康检查）不加 `_get_default_headers()`。

### 7.7 Entity 数据类（`@dataclass`）

- 放在对应的 Service 文件中；
- 必填字段无默认值，选填字段有默认值；
- 在 Service 方法中将 Entity 转为字典发送。

**两个高频陷阱，一定避免：**

1. **字段末尾禁止逗号。** 下面这种写法会让字段变成单元素 tuple `(1,)`，运行时几乎必然出错：

   ```python
   # 反例（现存代码里已经踩过）
   @dataclass
   class Foo:
       tenant_id: int = 1,   # 错：tenant_id 变成 (1,)
       status: int = 0,      # 错：status 变成 (0,)
   ```

   正确写法：

   ```python
   @dataclass
   class Foo:
       tenant_id: int = 1
       status: int = 0
   ```

2. **可变默认值必须用 `field(default_factory=...)`**，不能直接写 `[]` / `{}`：

   ```python
   from dataclasses import dataclass, field

   @dataclass
   class Bar:
       roles: list[str] = field(default_factory=lambda: ["platform_manager"])
   ```

### 7.8 xdist 并行执行下的 api_cache 拆分

根 `conftest.py` 支持 `pytest -n auto`。**`DataCache` 是进程内单例**，被 xdist 拆到不同 worker 的用例之间**无法共享 cache**。这会破坏 7.3 的数据依赖假设。

处理办法（三选一）：

- **推荐**：跑接口测试时用 `--dist=loadfile` 或 `--dist=loadscope`（同一文件 / 同一类的用例保证跑在同一 worker）；
- 或者对强依赖上下文的类加 `@pytest.mark.serial` 并在 `pytest.ini` 里配置该 mark 走单 worker；
- 或者把强依赖的一整条流程合并到一个 test 方法里（仅在 JMX 本身就是原子流程时才这么做，避免与"禁止事项 8"冲突）。

`get_token` 是懒加载的，每个 worker 各自登录各自的租户，行为正确；只是要注意后端登录频控 = worker 数 × 用到的租户数。

### 7.9 敏感字段脱敏

- 日志 / Allure 描述 / 断言消息里不得出现明文 password、token、apikey、身份证、手机号等；
- 需要判定 token 是否存在时，使用 `bool(token)` 或长度断言，不要 `f"...{token}..."` 拼到消息里；
- Service 层若确实需要打印 token 值用于本地排错，仅限 DEBUG 级别，且不得进入生产日志。

---

## 八、检查清单（转换完成后核对）

- [ ] 测试文件在 `tests/api/<domain>/` 目录下（domain 与业务模块一致）
- [ ] 文件名格式：`test_{模块名}.py`
- [ ] 所有参数在**每一份** `config/env_*.yaml` 中都有对应 key
- [ ] YAML 参数名全部是 snake_case
- [ ] import 路径正确（`from base.api.services.xxx import ...`）
- [ ] 类装饰器包含 `@pytest.mark.api`、`@allure.feature`、`@allure.story`
- [ ] 测试类顶部声明 `TENANT = "..."`，并有 `autouse` 的 `_login` fixture 调 `get_token(self.TENANT)`
- [ ] 每个测试方法有 `@allure.title`、`@allure.description`、`@allure.severity`
- [ ] 测试方法体最外层用 `AllureHelper.api_test(service)` 包裹
- [ ] 关键操作用 `AllureHelper.step()` 分段
- [ ] Service 方法调用带上 `_get_default_headers()`（免鉴权接口除外）
- [ ] 数据依赖通过 `api_cache` 传递，缺前置数据使用 `pytest.skip()`
- [ ] 依赖 `api_cache` 的用例已避免被 xdist 跨 worker 拆分（`--dist=loadscope` 或加 `serial` mark）
- [ ] 断言的是 `response_json["code"]` 之类的业务字段，不是 HTTP status
- [ ] 没有硬编码的 URL、账号、明文 token；日志和 Allure 中无敏感字段明文
- [ ] Service fixture 使用 `yield` + `service.close()`
- [ ] `@dataclass` 字段末尾无逗号；可变默认值使用 `field(default_factory=...)`
- [ ] JMX 中所有 `HTTPSamplerProxy` 都有对应的测试步骤
- [ ] JMX 中的 `JSONPostProcessor` 逻辑都有对应的数据提取和缓存

---

## 九、示例参考

仓库内可对照的完整转换示例：

- 转换结果：[tests/api/portal/test_portal_innerapi.py](tests/api/portal/test_portal_innerapi.py)、[tests/api/portal/test_portal_openapi.py](tests/api/portal/test_portal_openapi.py)
- Service 层：[base/api/services/portal_inner_service.py](base/api/services/portal_inner_service.py)、[base/api/services/portal_open_service.py](base/api/services/portal_open_service.py)
- 多租户登录工厂：[tests/api/conftest.py](tests/api/conftest.py)
- 环境配置：[config/env_test.yaml](config/env_test.yaml)、[config/env_bcv25_arm.yaml](config/env_bcv25_arm.yaml)

JMX 原始文件应与本项目分离维护；PR 中提交 test 时，请在描述里附上对应 JMX 的路径 / 版本，以便 Reviewer 对照。

