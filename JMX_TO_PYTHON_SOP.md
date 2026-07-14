# JMX 接口测试脚本转换为 Python pytest 测试代码 SOP

## 一、概述

本文档描述如何将 JMeter（.jmx）接口测试脚本转换为本项目（AutoTestKit）中的 Python pytest 测试代码。转换需要遵循项目已有的代码风格和架构约定。

---

## 二、项目架构（必须理解）

```
AutoTestKit/
├── base/api/services/          # 服务层（封装 HTTP 请求）
│   ├── base_service.py         # 基础服务类（提供 get/post/put/delete 方法）
│   ├── portal_inner_service.py # 门户内部API服务（含 Entity 数据类）
│   └── portal_open_service.py  # 门户OpenAPI服务
├── config/
│   └── env_bcv25_arm.yaml      # 环境配置文件（测试参数在此定义）
├── core/
│   ├── cache/data_cache.py     # 数据缓存（测试间共享数据）
│   └── reporting/allure_helper.py # Allure 报告辅助类
├── tests/api/
│   ├── conftest.py             # 仅一行: from base.api.fixtures import *
│   ├── test_portal_innerapi.py # InnerAPI 测试
│   └── test_portal_openapi.py  # OpenAPI 测试
└── base/api/fixtures.py        # 全局 fixtures（api_env, api_cache, api_logger等）
```

### 关键组件说明

| 组件 | 作用 | 用法 |
|------|------|------|
| `api_env` | fixture，从 yaml 配置文件加载的字典 | `api_env.get("参数名")` |
| `api_cache` | fixture，DataCache 实例，跨测试共享数据 | `api_cache.set(key, val)` / `api_cache.get(key)` |
| `api_logger` | fixture，日志记录器 | 传入 service 构造函数 |
| `BaseService` | HTTP 客户端基类 | `.get()` `.post()` `.put()` `.delete()` |
| `AllureHelper.step()` | Allure 步骤上下文管理器 | `with AllureHelper.step("描述"):` |

---

## 三、转换流程（Step by Step）

### Step 1：分析 JMX 文件结构

JMX 文件是 XML 格式，需要识别以下关键元素：

| JMX 元素 | 含义 | 位置 |
|----------|------|------|
| `<ThreadGroup>` | 线程组 = 一个测试类 | 顶层 hashTree |
| `<Arguments>` (用户定义变量) | 测试参数 | ThreadGroup 下的第一个 hashTree |
| `<HeaderManager>` | 公共请求头 | ThreadGroup 下 |
| `<ConfigTestElement>` (HTTP默认值) | base_url, port, protocol | ThreadGroup 下 |
| `<HTTPSamplerProxy>` | 一个 HTTP 请求 = 一个测试步骤 | hashTree 内 |
| `<ResponseAssertion>` | 断言 | HTTPSamplerProxy 的子 hashTree |
| `<JSONPostProcessor>` | 从响应中提取值 | HTTPSamplerProxy 的子 hashTree |
| `<IfController>` | 条件分支 | hashTree 内 |

### Step 2：提取测试参数写入 YAML

将 JMX 中 `<Arguments>` 的用户定义变量提取出来，写入 `config/env_bcv25_arm.yaml`。

**命名规则：**
- 全部使用 `snake_case`（下划线分隔小写）
- 如果变量名和已有 YAML 变量**名称相同且值相同**，直接复用已有变量
- 如果**名称相同但值不同**，添加前缀区分（如 `inner_system_code` vs `portal_system_code`）
- 每个参数上方加中文注释说明用途

**示例：**
```yaml
# InnerAPI 系统编码 - 用于创建系统时的 systemName 和 systemCode
inner_system_code: testxt20250711
```

### Step 3：确认/创建 Service 层

检查 `base/api/services/` 下是否已有对应的 Service 类。

- **已有**：直接使用，查看已有方法是否覆盖 JMX 中的接口
- **缺少方法**：在已有 Service 类中补充新方法
- **完全没有**：创建新的 Service 类继承 `BaseService`

**Service 类规范：**
```python
class XxxService(BaseService):
    def __init__(self, base_url=None, logger=None):
        super().__init__(base_url=base_url or self.DEFAULT_BASE_URL, logger=logger)

    def some_api(self, param1, param2) -> Dict[str, Any]:
        """接口描述"""
        url = "/path/to/api"
        response = self.get(endpoint=url, headers=_get_default_headers(), params={...})
        return response.json()
```

### Step 4：编写测试文件

在 `tests/api/` 下创建测试文件，命名为 `test_{jmx文件名去横线}.py`。

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

from base.api.fixtures import api_cache
from base.api.services.xxx_service import (
    XxxService,
    SomeEntity,
)
from core.reporting.allure_helper import AllureHelper


@pytest.mark.api
@allure.feature("{模块名}")
@allure.story("{jmx文件对应的测试故事}")
class TestXxx:
    """
    对应 JMeter 脚本: {filename}.jmx
    线程组: {线程组名称}
    """

    @pytest.fixture(scope="class")
    def xxx_service(self, api_env, api_logger):
        """创建服务实例"""
        service = XxxService(
            base_url=api_env.get("api_inner_base_url"), logger=api_logger
        )
        yield service
        service.close()

    @allure.title("{接口中文名}")
    @allure.description("{HTTP方法} {路径} - {验证描述}")
    @allure.severity(allure.severity_level.CRITICAL)  # 或 NORMAL
    def test_some_api(self, xxx_service, api_env, api_cache):
        with AllureHelper.step("发送请求"):
            response_json = xxx_service.some_api(param=api_env.get("param_name"))

        with AllureHelper.step("验证响应数据"):
            assert isinstance(response_json, dict), "响应应该是字典类型"
            assert response_json.get("code") == 0 or "data" in response_json
```

---

## 五、转换映射规则

### 5.1 HTTP 请求映射

| JMX | Python |
|-----|--------|
| `HTTPSamplerProxy` method=GET | `service.get(endpoint=url, params={...}, headers={...})` |
| `HTTPSamplerProxy` method=POST + `postBodyRaw=true` | `service.post(endpoint=url, json={...}, headers={...})` |
| `HTTPSamplerProxy` method=POST + `postBodyRaw=false` | `service.post(endpoint=url, data={...}, headers={...})` |
| `HTTPSamplerProxy` method=PUT | `service.put(endpoint=url, json={...}, headers={...})` |
| `HTTPSamplerProxy` method=DELETE | `service.delete(endpoint=url, headers={...})` |

### 5.2 JMX 变量引用映射

| JMX | Python |
|-----|--------|
| `${variableName}` (用户定义变量) | `api_env.get("variable_name")` |
| `${extractedVar}` (JSON提取器结果) | `api_cache.get("extracted_var")` |

### 5.3 JSON 提取器映射

| JMX JSONPostProcessor | Python |
|----------------------|--------|
| `$.data[0].id` | `data = response_json.get("data", []); val = data[0].get("id") if data else None` |
| `$.data[?(@.code=="xxx")].id` | `val = next((item.get("id") for item in data if item.get("code") == "xxx"), None)` |

提取后缓存：`api_cache.set("variable_name", val)`

### 5.4 断言映射

| JMX ResponseAssertion | Python |
|----------------------|--------|
| `Assertion.response_code` 包含 `200` | `assert response.status_code == 200`（通常在 service 层已处理） |
| `Assertion.response_data` 包含 `xxx` | `assert "xxx" in response_json.get("data", "")` |
| `test_type=8` (equals) | `assert value == expected` |
| `test_type=2` (contains) | `assert expected in value` |
| `test_type=16` (not) | `assert value != expected` |

### 5.5 条件分支映射

| JMX IfController | Python |
|-----------------|--------|
| `${__jexl2("${var}"=="expected",)}` | `if var == expected:` 或拆分为独立逻辑 |
| 条件判断后执行不同请求 | 在同一测试方法内用 if/else 处理 |

### 5.6 请求体解码

JMX 中 POST body 使用 XML 实体编码：
- `&quot;` → `"`
- `&#xd;` → 换行（忽略）
- `&amp;` → `&`
- `&lt;` → `<`
- `&gt;` → `>`

转换时需要还原为正常 JSON 格式。

---

## 六、严格禁止事项

1. **不要创建独立的 `test_data` fixture** — 所有测试参数通过 `api_env.get("param_name")` 直接从 YAML 配置读取
2. **不要在测试文件中硬编码 URL** — base_url 从 `api_env` 获取，传给 Service 构造函数
3. **不要直接使用 `requests` 库** — 必须通过 Service 层的方法发请求
4. **不要在测试方法中写 `print`** — 使用 `AllureHelper.step()` 记录步骤
5. **不要用 `unittest.TestCase`** — 使用 pytest class 风格
6. **不要用驼峰命名测试方法** — 用 `test_snake_case` 格式
7. **不要忽略 JMX 中的数据依赖** — 如果接口 B 依赖接口 A 的响应数据，必须通过 `api_cache` 传递
8. **不要把多个逻辑完整的流程放在同一个测试方法中** — 除非是 CRUD 全流程（创建→查询→修改→删除是一个完整流程，应放在一个方法中）
9. **不要自己定义 conftest.py 中的 fixture** — `tests/api/conftest.py` 只有 `from base.api.fixtures import *`，全局 fixture 已在 `base/api/fixtures.py` 中定义
10. **不要修改 Service 层中已有方法的签名** — 只允许新增方法

---

## 七、注意事项

### 7.1 YAML 参数命名规范

- 全部 `snake_case`
- 字符串数字需加引号：`user_id: "201214"`
- 相关参数用空行和注释分组

### 7.2 测试方法排列顺序

按照 JMX 中 HTTPSamplerProxy 的出现顺序排列测试方法，因为：
- JMX 是顺序执行的，后面的请求可能依赖前面的数据
- 保持顺序便于对照验证

### 7.3 数据依赖处理

如果测试 B 依赖测试 A 提取的数据：
- 测试 A 中：`api_cache.set("key", value)`
- 测试 B 中：`value = api_cache.get("key"); if not value: pytest.skip("原因")`

### 7.4 条件分支的处理策略

JMX 中的 IfController 通常是为了处理"数据存在/不存在"两种情况。转换时：
- 合并为一个测试方法
- 先查询判断状态，再决定操作路径
- 典型模式：查询 → 存在则先删除 → 创建 → 验证 → 清理

### 7.5 allure 装饰器

每个测试方法必须有：
- `@allure.title("中文标题")` — 简短描述接口功能
- `@allure.description("详细描述")` — 包含 HTTP 方法和路径
- `@allure.severity(...)` — CRITICAL（核心流程）或 NORMAL（辅助接口）

### 7.6 Service 方法中的 headers

InnerAPI 使用 `_get_default_headers()` 函数获取默认请求头（包含 apikey、tenantCode 等），这些头信息从环境配置中读取，不需要在测试方法中手动传递。

### 7.7 Entity 数据类

对于 POST/PUT 请求的复杂 body，使用 `@dataclass` 定义 Entity 类：
- 放在对应的 Service 文件中
- 必填字段无默认值，选填字段有默认值
- 在 Service 方法中将 Entity 转为字典发送

---

## 八、检查清单（转换完成后核对）

- [ ] 测试文件在 `tests/api/` 目录下
- [ ] 文件名格式：`test_{模块名}.py`
- [ ] 所有参数在 YAML 中有定义
- [ ] YAML 参数名全部是 snake_case
- [ ] import 路径正确（`from base.api.services.xxx import ...`）
- [ ] 类装饰器包含 `@pytest.mark.api`、`@allure.feature`、`@allure.story`
- [ ] 每个测试方法有 `@allure.title`、`@allure.description`、`@allure.severity`
- [ ] 使用 `AllureHelper.step()` 包裹关键操作
- [ ] 数据依赖通过 `api_cache` 传递
- [ ] 缺少前置数据时使用 `pytest.skip()` 跳过
- [ ] 没有硬编码的 URL、密码、token
- [ ] Service fixture 使用 `yield` + `service.close()`
- [ ] JMX 中所有 HTTPSamplerProxy 都有对应的测试步骤
- [ ] JMX 中的 JSONPostProcessor 逻辑都有对应的数据提取和缓存

---

## 九、示例参考

完整转换示例请参考：
- JMX 源文件：`I:\Code\auto_test_pro\auto-test\files\portal\innerapi\portal-innerapi.jmx`
- 转换结果：`tests/api/test_portal_innerapi.py`
- Service 层：`base/api/services/portal_inner_service.py`
- 配置文件：`config/env_bcv25_arm.yaml`（InnerAPI 测试数据部分）
