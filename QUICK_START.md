# 快速开始指南

本指南帮助您快速上手测试自动化框架，从安装到编写第一个测试。

## 目录

1. [环境准备](#环境准备)
2. [安装步骤](#安装步骤)
3. [验证安装](#验证安装)
4. [编写第一个 UI 测试](#编写第一个-ui-测试)
5. [编写第一个 API 测试](#编写第一个-api-测试)
6. [运行测试](#运行测试)
7. [查看报告](#查看报告)
8. [常见问题](#常见问题)

## 环境准备

### 系统要求

- **Python**: 3.9 或更高版本
- **操作系统**: Windows, macOS, 或 Linux
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 2GB 可用空间

### 检查 Python 版本

```bash
python --version
# 或
python3 --version
```

如果版本低于 3.9，请从 [python.org](https://www.python.org/downloads/) 下载最新版本。

## 安装步骤

### 1. 克隆或下载项目

```bash
# 如果使用 Git
git clone <repository-url>
cd test-automation-framework

# 或直接下载并解压项目文件
```

### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

这将安装以下主要依赖：
- pytest: 测试框架
- playwright: UI 自动化
- requests: API 测试
- allure-pytest: 报告生成
- hypothesis: 属性测试

### 4. 安装 Playwright 浏览器

```bash
playwright install
```

这将下载 Chromium, Firefox, 和 WebKit 浏览器。

如果只需要 Chromium：
```bash
playwright install chromium
```

### 5. 安装 Allure 命令行工具（可选，用于查看报告）

**macOS (使用 Homebrew):**
```bash
brew install allure
```

**Windows (使用 Scoop):**
```bash
scoop install allure
```

**Linux (手动安装):**
```bash
# 从 https://github.com/allure-framework/allure2/releases 下载最新版本
# 解压并添加到 PATH
```

## 验证安装

运行以下命令验证安装是否成功：

```bash
# 验证 pytest
pytest --version

# 验证 playwright
playwright --version

# 验证 allure (如果已安装)
allure --version

# 运行示例测试
pytest examples/ui_test_example.py -v
```

如果所有命令都成功执行，说明安装完成！

## 编写第一个 UI 测试

### 1. 创建测试文件

在 `tests/ui/` 目录下创建 `test_my_first_ui.py`:

```python
"""
我的第一个 UI 测试
"""

import pytest
from base.ui.pages.base import BasePage


@pytest.mark.ui
def test_visit_example_website(page, logger):
    """
    测试访问示例网站
    """
    # 创建页面对象
    base_page = BasePage(page, logger)

    # 导航到网站
    base_page.navigate("https://example.com")

    # 获取页面标题
    title = base_page.get_title()
    logger.info(f"页面标题: {title}")

    # 验证标题
    assert "Example Domain" in title

    # 获取页面文本
    heading = base_page.get_text("h1")
    logger.info(f"页面标题文本: {heading}")

    # 验证标题文本
    assert "Example Domain" == heading
```

### 2. 运行测试

```bash
pytest tests/ui/test_my_first_ui.py -v
```

## 编写第一个 API 测试

### 1. 创建测试文件

在 `tests/api/` 目录下创建 `test_my_first_api.py`:

```python
"""
我的第一个 API 测试
"""

import pytest


@pytest.mark.api
def test_get_user(base_service, logger):
    """
    测试获取用户信息
    """
    # 发送 GET 请求
    response = base_service.get("https://jsonplaceholder.typicode.com/users/1")
    
    # 验证状态码
    assert response.status_code == 200
    logger.info(f"响应状态码: {response.status_code}")
    
    # 解析响应数据
    user_data = response.json()
    logger.info(f"用户数据: {user_data}")
    
    # 验证数据
    assert "name" in user_data
    assert "email" in user_data
    
    # 提取并缓存数据
    user_id = base_service.extract_and_cache(response, "user_id", "id")
    logger.info(f"缓存的用户 ID: {user_id}")
    
    assert user_id == 1
```

### 2. 运行测试

```bash
pytest tests/api/test_my_first_api.py -v
```

## 运行测试

### 基本命令

```bash
# 运行所有测试
pytest

# 运行特定目录的测试
pytest tests/ui/
pytest tests/api/

# 运行特定文件
pytest tests/ui/test_my_first_ui.py

# 运行特定测试函数
pytest tests/ui/test_my_first_ui.py::test_visit_example_website
```

### 使用标记过滤测试

```bash
# 只运行 UI 测试
pytest -m ui

# 只运行 API 测试
pytest -m api

# 只运行冒烟测试
pytest -m smoke

# 排除慢速测试
pytest -m "not slow"
```

### 并行执行

```bash
# 自动检测 CPU 核心数并并行执行
pytest -n auto

# 指定 worker 数量
pytest -n 4
```

### 详细输出

```bash
# 显示详细信息
pytest -v

# 显示更详细的信息（包括测试输出）
pytest -vv

# 显示每个测试的执行时间
pytest --durations=10
```

## 查看报告

### 方式 1: 使用便捷脚本（推荐）

```bash
# 运行测试
pytest

# 生成并查看报告
python generate_report.py serve
```

浏览器会自动打开 Allure 报告。

### 方式 2: 使用 Allure 命令

```bash
# 运行测试并生成结果
pytest --alluredir=report/allure-results

# 启动 Allure 服务器查看报告
allure serve report/allure-results --language zh-CN
```

### 方式 3: 生成静态报告

```bash
# 生成静态 HTML 报告
allure generate allure-results -o allure-report --clean --language zh-CN

# 打开报告
allure open allure-report
```

### Allure 报告功能

报告包含以下信息：
- ✅ 测试执行概览（通过率、失败率）
- ✅ 测试时长统计
- ✅ 失败截图（UI 测试）
- ✅ 详细日志
- ✅ 请求/响应信息（API 测试）
- ✅ 测试步骤
- ✅ 趋势图表

## 常见问题

### Q1: 安装 Playwright 浏览器失败

**问题**: `playwright install` 命令失败或超时

**解决方案**:
```bash
# 设置环境变量使用国内镜像
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/

# 然后重新安装
playwright install
```

### Q2: 测试运行时浏览器无法启动

**问题**: 错误信息 "Executable doesn't exist"

**解决方案**:
```bash
# 重新安装浏览器
playwright install --force
```

### Q3: 并行执行时测试失败

**问题**: 使用 `-n auto` 时部分测试失败

**解决方案**:
- 检查测试是否有共享状态依赖
- 使用 DataCache 确保线程安全
- 减少 worker 数量: `pytest -n 2`

### Q4: Allure 报告无法生成

**问题**: `allure: command not found`

**解决方案**:
```bash
# 使用 Python 脚本生成报告（不需要 Allure CLI）
python generate_report.py generate

# 或安装 Allure CLI
# macOS: brew install allure
# Windows: scoop install allure
```

### Q5: 日志文件过多占用空间

**问题**: `logs/` 目录文件过多

**解决方案**:
```python
# 在 config/settings.py 中配置日志清理
# 或手动清理旧日志
from utils.file_helper import FileHelper

# 删除 7 天前的日志
FileHelper.clean_directory("logs", "*.log", older_than_days=7)
```

### Q6: API 测试连接超时

**问题**: API 请求超时

**解决方案**:
```python
# 在 config/settings.py 中增加超时时间
API_TIMEOUT = 60  # 增加到 60 秒

# 或在环境变量中设置
export API_TIMEOUT=60
```

### Q7: 如何在无头模式运行 UI 测试

**问题**: 需要在 CI/CD 中运行测试

**解决方案**:
```bash
# 设置环境变量
export HEADLESS=true

# 或在 config/settings.py 中修改
HEADLESS = True

# 然后运行测试
pytest -m ui
```

## 下一步

现在您已经掌握了基础知识，可以：

1. **查看示例代码**: 浏览 `examples/` 目录了解更多用法
2. **阅读完整文档**: 查看 `README.md` 了解所有功能
3. **学习 Page Object 模式**: 查看 `ui/pages/base_page.py`
4. **了解 API 服务封装**: 查看 `api/services/base_service.py`
5. **探索配置选项**: 查看 `config/settings.py` 和 `config/ENV_CONFIG_README.md`
6. **学习属性测试**: 查看 `tests/test_data_cache.py` 中的属性测试示例

## 获取帮助

- **查看示例**: `examples/` 目录包含各种功能的演示代码
- **查看文档**: `README.md` 包含完整的功能说明
- **查看测试**: `tests/` 目录包含实际的测试示例
- **查看日志**: `logs/` 目录包含详细的执行日志

祝您测试愉快！🚀
