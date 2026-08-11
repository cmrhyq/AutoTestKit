"""
Alert 检测 Mixin

为 Page Object 提供页面错误弹窗（Element UI / Ant Design）检测能力。
混入 BasePage 后，所有页面对象自动获得 assert_no_alert / wait_alert_hidden 等方法。

要求宿主类具有 self.page 属性（BasePage 已满足）。
"""
from typing import List, Optional, Tuple

from playwright.sync_api import Frame, Locator, Page

from core import get_logger

logger = get_logger(__name__)

# ==================== 错误元素 CSS 选择器 ====================

# Element UI / Element Plus 错误类 alert / message / notification
_ELEMENT_ERROR_SELECTORS: List[str] = [
    ".el-alert--error",
    ".ep-message--error",
    ".el-message--error",
    ".el-icon-error",
    ".el-notification--error",
]

# Ant Design 错误类 alert / message / notification
# 说明：ant 类型仅在部分内嵌 iframe 页面出现（如 弹性计算-系统配置-权限管理-审计日志）
_ANT_ERROR_SELECTORS: List[str] = [
    ".ant-alert-error",
    ".ant-message-error",
    ".ant-notification-notice-icon-error",
]

# ant notification 的图标节点本身不含文案，文案在 message 节点上
_ANT_NOTIFICATION_ICON = ".ant-notification-notice-icon-error"
_ANT_NOTIFICATION_MESSAGE = ".ant-notification-notice-message"

# 主文档中需要检查的选择器（不含 ant，ant 仅在 iframe 中出现）
_MAIN_FRAME_SELECTORS: List[str] = _ELEMENT_ERROR_SELECTORS
# iframe 中需要检查的选择器（element + ant）
_IFRAME_SELECTORS: List[str] = _ELEMENT_ERROR_SELECTORS + _ANT_ERROR_SELECTORS

# 单轮检查未发现 alert 时的重试等待间隔（毫秒）
_DEFAULT_RETRY_INTERVAL_MS = 500


class AlertMixin:
    """
    Alert 检测 Mixin

    为 Page Object 提供页面错误弹窗检测能力。
    混入后自动获得 assert_no_alert / check_alert / wait_alert_hidden 方法。

    要求宿主类具有 self.page: Page 属性。

    使用示例::

        # 直接断言（推荐，失败时自动带上错误文案）
        self.home_page.assert_no_alert(retries=6)

        # 非断言版本，返回 (ok, message) 元组
        ok, msg = self.home_page.check_alert(retries=3)

        # 等待残留弹窗消失
        self.home_page.wait_alert_hidden()
    """

    # 类型标注，实际由 BasePage.__init__ 赋值
    page: Page

    def assert_no_alert(self, retries: int = 1, interval_ms: int = _DEFAULT_RETRY_INTERVAL_MS) -> None:
        """
        断言页面无错误弹窗

        检测主文档和 iframe 中的 Element UI / Ant Design 错误类元素，
        如果发现则抛出 AssertionError 并附带错误文案。

        Args:
            retries: 轮询次数，每轮间隔 interval_ms 毫秒
            interval_ms: 每轮检查间隔（毫秒），默认 500ms

        Raises:
            AssertionError: 检测到错误弹窗，message 为错误文案

        使用示例::

            self.home_page.assert_no_alert(retries=6)  # 最多等待约 3s
        """
        ok, message = self._check_alert(retries, interval_ms)
        assert ok, message

    def check_alert(self, retries: int = 1, interval_ms: int = _DEFAULT_RETRY_INTERVAL_MS) -> Tuple[bool, str]:
        """
        检查页面是否存在错误弹窗（非断言版本）

        Args:
            retries: 轮询次数
            interval_ms: 每轮检查间隔（毫秒）

        Returns:
            Tuple[bool, str]:
                - (True, "页面验证正常"): 未检测到报错
                - (False, 错误文案): 检测到报错
        """
        return self._check_alert(retries, interval_ms)

    def wait_alert_hidden(self) -> None:
        """
        等待页面上的 alert 错误元素消失

        若不等待其消失，残留的 alert 有概率影响下一个用例。
        逐一等待主文档与 iframe 中当前可见的错误元素进入 hidden 状态。

        使用示例::

            # 典型用法：一个用例结束前调用
            self.home_page.wait_alert_hidden()
        """
        self._wait_container_errors_hidden(self.page, _MAIN_FRAME_SELECTORS, scope="主文档")

        frame = self._get_iframe_content()
        if frame is not None:
            self._wait_container_errors_hidden(frame, _IFRAME_SELECTORS, scope="iframe")

    # ==================== 内部实现 ====================

    def _check_alert(self, retries: int, interval_ms: int) -> Tuple[bool, str]:
        """
        核心检测逻辑：循环轮询主文档和 iframe 中的错误元素

        Args:
            retries: 轮询次数
            interval_ms: 每轮检查间隔（毫秒）

        Returns:
            Tuple[bool, str]: (是否正常, 消息文案)
        """
        for i in range(retries):
            # 主文档检查
            hit = self._find_visible_error(self.page, _MAIN_FRAME_SELECTORS)
            if hit is not None:
                error_text = self._extract_error_text(self.page, hit)
                logger.error(f"页面主文档存在报错(selector={hit}): {error_text}")
                return False, error_text

            # iframe 检查
            frame = self._get_iframe_content()
            if frame is not None:
                hit = self._find_visible_error(frame, _IFRAME_SELECTORS)
                if hit is not None:
                    error_text = self._extract_error_text(frame, hit)
                    logger.error(f"页面 iframe 存在报错(selector={hit}): {error_text}")
                    return False, error_text

            # 本轮未发现报错，等待后重试
            logger.debug(f"第 {i + 1}/{retries} 轮未检测到 alert，等待 {interval_ms}ms 后重试")
            self.page.wait_for_timeout(interval_ms)

        return True, "页面验证正常"

    def _get_iframe_content(self) -> Optional[Frame]:
        """安全获取页面中第一个 iframe 的内容 frame"""
        try:
            iframe = self.page.locator("iframe").first
            if iframe.count() == 0:
                return None
            return iframe.content_frame
        except Exception as e:
            logger.debug(f"获取 iframe content_frame 失败，按无 iframe 处理: {e}")
            return None

    @staticmethod
    def _extract_error_text(container, selector: str) -> str:
        """读取指定错误选择器对应元素的文案"""
        try:
            if selector == _ANT_NOTIFICATION_ICON:
                msg = container.locator(_ANT_NOTIFICATION_MESSAGE).first
                return msg.inner_text() if msg.is_visible() else ""
            return container.locator(selector).first.inner_text()
        except Exception as e:
            logger.debug(f"读取错误文案失败(selector={selector}): {e}")
            return ""

    @staticmethod
    def _find_visible_error(container, selectors: List[str]) -> Optional[str]:
        """在给定容器（page 或 frame）中查找首个可见的错误元素"""
        for selector in selectors:
            try:
                if container.locator(selector).first.is_visible():
                    return selector
            except Exception as e:
                logger.debug(f"检查错误元素可见性失败(selector={selector}): {e}")
        return None

    @staticmethod
    def _wait_container_errors_hidden(container, selectors: List[str], scope: str) -> None:
        """等待某个容器内所有当前可见的错误元素消失"""
        for selector in selectors:
            try:
                locator: Locator = container.locator(selector).last
                if locator.is_visible():
                    logger.info(f"等待{scope} alert 消失(selector={selector})")
                    locator.wait_for(state="hidden")
            except Exception as e:
                logger.debug(f"等待错误元素消失失败({scope}, selector={selector}): {e}")
