from enum import Enum


class WaitUntil(Enum):
    """
    wait_until: 等待条件，可选值：
    - load = 'load': 等待 load 事件触发
    - dom = 'domcontentloaded': 等待 DOMContentLoaded 事件触发（默认）
    - net = 'networkidle': 等待网络空闲
    - commit = 'commit': 等待网络响应接收完成
    """
    load = "load"
    dom = "domcontentloaded"
    net = "networkidle"
    commit = "commit"

class ElementState(Enum):
    """
    state: 元素状态，可选值：
    - 'attached': 元素已附加到 DOM
    - 'detached': 元素已从 DOM 分离
    - 'visible': 元素可见（默认）
    - 'hidden': 元素隐藏
    """
    attached = "attached"
    detached = "detached"
    visible = "visible"
    hidden = "hidden"

class LoadState(Enum):
    """
    state: 加载状态，可选值：
    - load = 'load': 等待 load 事件
    - dom = 'domcontentloaded': 等待 DOMContentLoaded 事件
    - net = 'networkidle': 等待网络空闲
    """
    load = "load"
    dom = "domcontentloaded"
    net = "networkidle"