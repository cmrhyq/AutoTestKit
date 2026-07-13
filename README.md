# API UI Test Automation Framework

AUTestAutomation 是一款基于 Pytest + Playwright + Requests + Allure 的高性能 UI/API 自动化测试框架

## 项目简介

这是一个功能完整、高度可维护的自动化测试框架，提供以下核心能力：

- ✅ **UI 自动化测试**: 基于 Playwright 的跨浏览器测试
- ✅ **API 自动化测试**: 基于 Requests 的接口测试
- ✅ **并行执行**: 利用 pytest-xdist 实现智能并行测试
- ✅ **智能日志**: 多级别日志记录，支持控制台和文件输出
- ✅ **失败截图**: UI 测试失败时自动截图
- ✅ **数据缓存**: 单例模式的线程安全数据缓存
- ✅ **美观报告**: Allure 报告集成
- ✅ **属性测试**: 基于 Hypothesis 的属性测试支持

## 项目结构

```
AutoTestKit/
├── base/                               # 基础测试模块
│   ├── ui/                             # UI 测试模块
│   │   ├── pages/                      # Page Object 页面对象
│   │   │   ├── base_page.py            # 基础页面类
│   │   │   └── example_page.py         # 示例页面对象（example.com / 搜索页）
│   │   └── fixtures.py                 # UI 测试 fixtures（browser/context/page 等）
│   └── api/                            # API 测试模块
│       ├── services/                   # API 服务封装
│       │   ├── base_service.py         # 基础服务类（重试/认证/缓存）
│       │   └── jsonplaceholder_service.py  # 示例服务（JSONPlaceholder）
│       └── fixtures.py                 # API 测试 fixtures
├── core/                               # 核心功能模块
│   ├── cache/                          # 数据缓存
│   │   └── data_cache.py               # 线程安全单例 DataCache
│   ├── config/                         # 配置管理
│   │   ├── settings.py                 # 全局配置 Settings
│   │   ├── env_config.py               # 多环境配置加载（YAML + Jinja2）
│   │   └── system_config.py            # 框架系统配置加载
│   ├── log/                            # 日志
│   │   └── logger.py                   # TestLogger（RotatingFileHandler + colorlog）
│   └── reporting/                      # 报告
│       └── allure_helper.py            # AllureHelper 附件/步骤工具
├── config/                             # 配置文件
│   ├── config_system.yaml              # 框架系统级配置
│   ├── env_test.yaml                   # test 环境配置
│   └── env_sit5.yaml                   # sit5 环境配置
├── utils/                              # 工具模块
│   ├── file_helper.py                  # 文件操作工具
│   ├── data_helper.py                  # 数据处理工具
│   ├── internet_utils.py               # 网络相关工具
│   └── snow_id_utils.py                # 雪花 ID 工具
├── tests/                              # 测试用例
│   ├── ui/                             # UI 测试用例
│   │   └── examples/                   # UI 示例套件
│   ├── api/                            # API 测试用例
│   │   └── examples/                   # API 示例套件
│   ├── test_data_cache.py              # DataCache 单元测试
│   └── test_thread_safety.py           # 并发安全测试
├── examples/                           # 独立可运行的用法示例
├── performance/                        # 性能测试（Locust）
│   └── locustfile.py
├── report/                             # 报告输出目录（自动创建）
│   ├── allure-results/                 # Allure 原始结果
│   └── allure-report/                  # Allure HTML 报告
├── logs/                               # 日志文件目录（自动创建）
├── screenshots/                        # UI 自动化测试截图目录（自动创建）
├── .env.example                        # 环境变量示例（复制为 .env 后使用）
├── conftest.py                         # Pytest 全局配置与 hook
├── pytest.ini                          # Pytest 配置文件
├── pyproject.toml                      # 项目与依赖定义（uv 管理）
├── requirements.txt                    # 依赖清单（pip 兼容）
├── Jenkinsfile                         # Jenkins CI 流水线
├── QUICK_START.md                      # 快速开始指南
└── README.md                           # 项目文档
```

## 快速开始

### 1. 环境要求

- Python 3.9 或更高版本
- pip 包管理器

### 2. 安装依赖

```bash
# 安装 Python 依赖包
pip install -r requirements.txt

# 安装 Playwright 浏览器驱动
playwright install
```

### 3. 新增配置

在config目录新建config_system.yaml文件并写入以下内容
```yaml
# ======================= 测试环境配置 =======================
# 测试环境：dev, test, staging, prod
test_env: test

# ======================= 浏览器配置 =======================
# 浏览器类型：chromium, firefox, webkit
browser_type: chromium
# 是否使用无头模式运行浏览器 (true/false)
headless: false
# 浏览器操作超时时间（毫秒）
browser_timeout: 30000
# 页面加载超时时间（毫秒）
page_load_timeout: 30000
# 浏览器启动参数（逗号分隔）
browser_args:
# 视口宽度
viewport_width: 1920
# 视口高度
viewport_height: 1080
# 是否启用浏览器开发者工具 (true/false)
devtools: false

# ======================= API 配置 =======================
# API 请求超时时间（秒）
api_timeout: 30
# API 连接超时时间（秒）
api_connect_timeout: 10
# API 读取超时时间（秒）
api_read_timeout: 30
# 是否验证 SSL 证书
api_verify_ssl: true

# ======================= 日志配置 =======================
# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level: DEBUG
# 日志目录
log_dir: logs
# 日志文件名格式
log_file_format: test_{timestamp}.log
# 是否在控制台输出日志 (true/false)
log_to_console: true
# 是否输出日志到文件 (true/false)
log_to_file: true
# 日志格式
log_format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# 日志时间格式
log_date_format: "%Y-%m-%d %H:%M:%S"

# ======================= 并行执行配置 =======================
# 并行 worker 数量：auto 表示自动检测 CPU 核心数，或指定具体数字
parallel_workers: auto
# 是否启用并行执行 (true/false)
enable_parallel: true
# 并行执行分发策略：loadscope, loadfile, loadgroup, load
parallel_dist_mode: loadscope

# ======================= 重试配置 =======================
# 最大重试次数
max_retries: 3
# 重试延迟时间（秒）
retry_delay: 1
# 是否启用失败重试 (true/false)
enable_retry: false

# ======================= Allure 报告配置 =======================
# Allure 结果目录
allure_results_dir: report/allure-results
# Allure 报告目录
allure_report_dir: report/allure-report
# 是否清理旧的 Allure 结果 (true/false)
allure_clean_results: true

# ======================= 截图配置 =======================
# 截图保存目录
screenshot_dir: screenshots
# 是否在失败时自动截图 (true/false)
screenshot_on_failure: true
# 截图格式：png, jpeg
screenshot_format: png
# 截图质量（仅对 jpeg 有效，1-100）
screenshot_quality: 80
```

### 3. 运行测试

```bash
# 运行所有测试
pytest

# 详细模式
pytest -v

# 显示测试输出
pytest -s

# 显示失败的详细信息
pytest -vv

# 运行 UI 测试
pytest -m ui

# 运行 API 测试
pytest -m api

# 运行特定测试文件
pytest tests/ui/test_example.py

# 运行特定测试用例
pytest tests/ui/test_example.py::test_login

# 并行执行测试（自动检测 CPU 核心数）
pytest -n auto

# 并行执行测试（指定 worker 数量）
pytest -n 4

# 运行属性测试
pytest -m property

# 运行冒烟测试
pytest -m smoke

# 使用关键字过滤
pytest -k "user"  # 运行所有包含 "user" 的测试
```

### 4. 查看测试报告

框架集成了 Allure 报告系统，提供美观、详细的测试报告。

#### 安装 Allure 命令行工具

```bash
# macOS (使用 Homebrew)
brew install allure

# Windows (使用 Scoop)
scoop install allure

# Linux (手动安装)
# 从 https://github.com/allure-framework/allure2/releases 下载最新版本
# 解压并添加到 PATH
```

#### 生成和查看报告

**使用便捷脚本（推荐）:**

```bash
# 运行测试
pytest --alluredir=allure-results

# 生成并查看报告
python generate_report.py serve

# 或生成静态报告
python generate_report.py generate

# 打开已生成的报告
python generate_report.py open

# 清理报告文件
python generate_report.py clean
```

**使用 Allure 命令:**

```bash
# 方式 1: 运行测试并立即查看报告（推荐）
pytest --alluredir=./report/allure-results
allure serve ./report/allure-results --language zh-CN

# 方式 2: 生成静态报告到指定目录
pytest --alluredir=allure-results
allure generate ./report/allure-results/ -o ./report/allure-report/ --clean --language zh-CN

# 方式 3: 打开已生成的静态报告
allure open ./report/allure-report

# 方式 4: 清理旧结果并重新生成
pytest --alluredir=./report/allure-results --clean-alluredir
allure serve ./report/allure-results
```

#### Allure 报告功能

Allure 报告提供以下信息：

- ✅ **测试执行概览**: 通过率、失败率、跳过率
- ✅ **测试时长统计**: 每个测试的执行时间
- ✅ **测试状态**: Passed、Failed、Broken、Skipped
- ✅ **失败截图**: UI 测试失败时的自动截图
- ✅ **日志附件**: 每个测试的详细日志
- ✅ **测试步骤**: 使用 `AllureHelper.step()` 组织的测试步骤
- ✅ **环境信息**: 测试环境、浏览器、Python 版本等
- ✅ **测试分类**: 按 Feature、Story、Severity 分类
- ✅ **趋势图表**: 历史测试结果趋势
- ✅ **附件支持**: 截图、日志、JSON 数据等

#### 报告配置

在 `pytest.ini` 中配置 Allure：

```ini
[pytest]
addopts = 
    --alluredir=report/allure-results
    --clean-alluredir
```

在 `config/settings.py` 中配置目录：

```python
ALLURE_RESULTS_DIR = "report/allure-results"  # 结果目录
ALLURE_REPORT_DIR = "report/allure-report"  # 报告目录
ALLURE_CLEAN_RESULTS = True  # 是否清理旧结果
```

## 核心功能

### UI 测试

使用 Playwright 进行浏览器自动化测试：

```python
from base.ui.pages.base_page import BasePage


def test_example_ui(page, logger):
    base_page = BasePage(page, logger)
    base_page.navigate("https://example.com")
    base_page.click("button#submit")
    text = base_page.get_text("h1")
    assert text == "Expected Title"
```

**特性**:
- 支持 Chromium、Firefox、WebKit 浏览器
- 智能等待机制
- 失败自动截图
- Page Object Model 模式

### API 测试

使用 Requests 进行接口测试：

```python
from base.api.services.base_service import BaseService


def test_example_api(api_service, logger):
    response = api_service.get("/users/1")
    assert response.status_code == 200

    # 提取数据并缓存
    user_id = api_service.extract_and_cache(response, "user_id", "$.id")
```

**特性**:
- 支持所有 HTTP 方法
- 自动请求/响应日志
- 数据提取和缓存
- 多种认证方式支持

### 数据缓存

使用单例模式的线程安全数据缓存：

```python
from core.cache.data_cache import DataCache

cache = DataCache.get_instance()
cache.set("user_id", 12345)
user_id = cache.get("user_id")
```

**特性**:
- 单例模式确保全局唯一
- 线程锁保证并发安全
- 支持任意类型数据

### 日志记录

多级别日志记录系统：

```python
from core.log.logger import TestLogger

logger = TestLogger.get_logger(__name__)
logger.info("Test started")
logger.debug("Debug information")
logger.error("Error occurred")
```

**特性**:
- 五个日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- 同时输出到控制台和文件
- 自动附加到 Allure 报告
- 统一的日志格式

### Allure 辅助工具

增强 Allure 报告的辅助工具：

```python
from core.allure.allure_helper import AllureHelper, allure_step

# 附加截图
screenshot = page.screenshot()
AllureHelper.attach_screenshot(screenshot, "Login Page")

# 附加日志
AllureHelper.attach_log(log_content, "Test Log")

# 附加 JSON 数据
AllureHelper.attach_json({"status": "success"}, "API Response")

# 创建测试步骤
with AllureHelper.step("Login to application"):
    page.fill("#username", "user")
    page.click("#login")

# 或使用便捷函数
with allure_step("Verify dashboard"):
    assert page.title() == "Dashboard"
```

**特性**:
- 截图附件（PNG 格式）
- 日志附件（文本格式）
- JSON 数据附件
- HTML 附件
- 测试步骤组织
- 动态添加描述、标题、标签
- 链接到外部资源（如 JIRA）

### 并行执行

使用 pytest-xdist 实现并行测试：

```bash
# 自动检测 CPU 核心数
pytest -n auto

# 指定 worker 数量
pytest -n 4
```

**特性**:
- 自动 CPU 核心检测
- 智能测试分发
- 线程安全的资源访问
- 结果自动聚合

## 配置说明

### 浏览器配置

在 `config/settings.py` 中配置浏览器选项：

```python
BROWSER_TYPE = "chromium"  # chromium, firefox, webkit
HEADLESS = False           # 是否无头模式
BROWSER_TIMEOUT = 30000    # 超时时间（毫秒）
```

### API 配置

```python
API_BASE_URL = "https://api.example.com"
API_TIMEOUT = 30           # 超时时间（秒）
```

### 日志配置

```python
LOG_LEVEL = "INFO"         # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR = "logs"           # 日志文件目录
```

### 并行配置

```python
PARALLEL_WORKERS = "auto"  # auto 或具体数字
```

### 环境配置

框架支持多环境配置管理，可以轻松在不同环境（dev、test、staging、prod）之间切换。

#### 使用环境变量

通过设置 `TEST_ENV` 环境变量来指定运行环境：

```bash
# Linux/macOS
export TEST_ENV=dev
pytest

# Windows (CMD)
set TEST_ENV=staging
pytest

# Windows (PowerShell)
$env:TEST_ENV="prod"
pytest
```

#### 环境特定配置

每个环境可以有自己的配置：

```python
from core.config import get_env_config, switch_env

# 获取当前环境配置
config = get_env_config()
print(f"API URL: {config.api_base_url}")
print(f"Log Level: {config.log_level}")

# 切换到其他环境
switch_env("staging")
config = get_env_config()
```

#### 默认环境配置

- **dev**: 开发环境，headless=False，log_level=DEBUG
- **test**: 测试环境（默认），headless=True，log_level=INFO
- **staging**: 预发布环境，headless=True，log_level=INFO
- **prod**: 生产环境，headless=True，log_level=WARNING

#### 从配置文件加载

创建 `env_config.json` 文件来自定义环境配置：

```json
{
  "dev": {
    "api_base_url": "http://localhost:3000",
    "headless": false,
    "log_level": "DEBUG"
  },
  "test": {
    "api_base_url": "https://test-api.example.com",
    "headless": true,
    "log_level": "INFO"
  }
}
```

然后在代码中加载：

```python
from core.config import EnvironmentManager

env_manager = EnvironmentManager(config_file="env_config.json")
config = env_manager.get_config()
```

#### 环境配置验证

框架会自动验证配置的有效性：

```python
from core.config import validate_config

is_valid, errors = validate_config()
if not is_valid:
    for error in errors:
        print(f"配置错误: {error}")
```

#### 查看配置摘要

```python
from core.config import env_manager

summary = env_manager.get_config_summary()
print(summary)
```

更多示例请参考 `examples/env_config_demo.py`

## 编写测试

### UI 测试示例

```python
import pytest
from base.ui.pages.base_page import BasePage


@pytest.mark.ui
def test_login(page, logger):
    """测试用户登录功能"""
    base_page = BasePage(page, logger)

    # 导航到登录页面
    base_page.navigate("https://example.com/login")

    # 填写表单
    base_page.fill("input#username", "testuser")
    base_page.fill("input#password", "password123")

    # 点击登录按钮
    base_page.click("button#login")

    # 验证登录成功
    welcome_text = base_page.get_text("h1.welcome")
    assert "Welcome" in welcome_text
```

### API 测试示例

```python
import pytest
from base.api.services.base_service import BaseService


@pytest.mark.api
def test_create_user(api_service, logger):
    """测试创建用户接口"""
    # 创建用户
    payload = {
        "name": "Test User",
        "email": "test@example.com"
    }
    response = api_service.post("/users", json=payload)

    # 验证响应
    assert response.status_code == 201
    assert response.json()["name"] == "Test User"

    # 提取并缓存用户 ID
    user_id = api_service.extract_and_cache(
        response, "user_id", "$.id"
    )
    logger.info(f"Created user with ID: {user_id}")
```

### 属性测试示例

```python
import pytest
from hypothesis import given, strategies as st
from core.cache.data_cache import DataCache


@pytest.mark.property
# Feature: test-automation-framework, Property 10: Cache data round-trip
@given(key=st.text(min_size=1), value=st.integers())
def test_cache_round_trip(key, value):
    """测试缓存数据往返一致性"""
    cache = DataCache.get_instance()
    cache.set(key, value)
    retrieved = cache.get(key)
    assert retrieved == value
```

### 使用 Allure 装饰器增强报告

```python
import allure
from core.allure.allure_helper import AllureHelper


@allure.feature("User Management")
@allure.story("User Login")
@allure.title("测试用户登录功能")
@allure.description("验证用户可以使用正确的凭据登录系统")
@allure.severity(allure.severity_level.BLOCKER)
@allure.tag("smoke", "authentication")
@allure.link("https://jira.example.com/ISSUE-123", name="JIRA Issue")
def test_user_login(page, logger):
    """测试用户登录"""

    # 使用步骤组织测试逻辑
    with AllureHelper.step("打开登录页面"):
        page.goto("https://example.com/login")
        logger.info("Login page opened")

    with AllureHelper.step("输入用户凭据"):
        page.fill("#username", "testuser")
        page.fill("#password", "password123")
        logger.info("Credentials entered")

    with AllureHelper.step("点击登录按钮"):
        page.click("#login-button")
        logger.info("Login button clicked")

    with AllureHelper.step("验证登录成功"):
        assert page.is_visible(".welcome-message")
        logger.info("Login successful")

        # 附加截图
        screenshot = page.screenshot()
        AllureHelper.attach_screenshot(screenshot, "Login Success")

        # 附加 JSON 数据
        AllureHelper.attach_json({
            "username": "testuser",
            "login_time": "2024-01-01 12:00:00",
            "status": "success"
        }, "Login Details")
```

### Allure 严重程度级别

使用 `@allure.severity()` 标记测试的严重程度：

- `allure.severity_level.BLOCKER`: 阻塞性问题，必须立即修复
- `allure.severity_level.CRITICAL`: 严重问题，影响核心功能
- `allure.severity_level.NORMAL`: 普通问题（默认）
- `allure.severity_level.MINOR`: 次要问题
- `allure.severity_level.TRIVIAL`: 微小问题

## 最佳实践

### 1. 使用 Page Object Model

将页面元素和操作封装到页面类中：

```python
class LoginPage(BasePage):
    def __init__(self, page, logger):
        super().__init__(page, logger)
        self.username_input = "input#username"
        self.password_input = "input#password"
        self.login_button = "button#login"
    
    def login(self, username, password):
        self.fill(self.username_input, username)
        self.fill(self.password_input, password)
        self.click(self.login_button)
```

### 2. 使用服务类封装 API

```python
class UserService(BaseService):
    def __init__(self, base_url, logger):
        super().__init__(base_url, logger)
    
    def get_user(self, user_id):
        return self.get(f"/users/{user_id}")
    
    def create_user(self, user_data):
        return self.post("/users", json=user_data)
```

### 3. 使用 Fixtures 管理测试数据

```python
@pytest.fixture
def test_user():
    return {
        "username": "testuser",
        "password": "password123"
    }
```

### 4. 使用标记组织测试

```python
@pytest.mark.smoke
@pytest.mark.ui
def test_critical_feature():
    pass
```

## 故障排查

### 常见问题

**1. Playwright 浏览器未安装**
```bash
playwright install
```

**2. 并行执行时资源冲突**
- 确保使用线程安全的资源访问
- 使用 DataCache 的锁机制

**3. 测试超时**
- 增加 `BROWSER_TIMEOUT` 或 `API_TIMEOUT`
- 检查网络连接

**4. Allure 报告无法生成**
```bash
# 确保安装了 Allure 命令行工具
# macOS
brew install allure

# Windows
scoop install allure

# Linux
# 从 https://github.com/allure-framework/allure2/releases 下载
```

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Test Automation

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install --with-deps
      
      - name: Run tests
        run: pytest -n auto --alluredir=allure-results
        continue-on-error: true
      
      - name: Get Allure history
        uses: actions/checkout@v3
        if: always()
        continue-on-error: true
        with:
          ref: gh-pages
          path: gh-pages
      
      - name: Allure Report action
        uses: simple-elf/allure-report-action@master
        if: always()
        with:
          allure_results: allure-results
          allure_history: allure-history
          keep_reports: 20
      
      - name: Deploy report to Github Pages
        if: always()
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_branch: gh-pages
          publish_dir: allure-history
      
      - name: Upload Allure results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: allure-results
          path: allure-results
          retention-days: 30
```

### Jenkins 集成

```groovy
pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh '''
                    pip install -r requirements.txt
                    playwright install --with-deps
                '''
            }
        }
        
        stage('Run Tests') {
            steps {
                sh 'pytest -n auto --alluredir=allure-results'
            }
        }
    }
    
    post {
        always {
            // 生成 Allure 报告
            allure([
                includeProperties: false,
                jdk: '',
                properties: [],
                reportBuildPolicy: 'ALWAYS',
                results: [[path: 'allure-results']]
            ])
            
            // 清理工作空间
            cleanWs()
        }
    }
}
```

### GitLab CI 示例

```yaml
stages:
  - test
  - report

test:
  stage: test
  image: python:3.11
  before_script:
    - pip install -r requirements.txt
    - playwright install --with-deps chromium
  script:
    - pytest -n auto --alluredir=allure-results
  artifacts:
    when: always
    paths:
      - allure-results/
    expire_in: 1 week
  allow_failure: true

pages:
  stage: report
  image: 
    name: frankescobar/allure-docker-service
    entrypoint: [""]
  script:
    - allure generate allure-results -o public --clean
  artifacts:
    paths:
      - public
  only:
    - main
```

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请创建 Issue 或联系维护者。

---

**Happy Testing! 🚀**
