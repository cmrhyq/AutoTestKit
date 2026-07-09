#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
@File internet_utils.py
@Contact cmrhyq@163.com
@License (C)Copyright 2022-2025, AlanHuang
@Modify Time 2024/5/7 下午8:12
@Author Alan Huang
@Version 0.0.1
@Description Internet Utils
"""
import random
import socket
from contextlib import closing

__all__ = [
    '_get_url_contain_params',  # 根据params组合得到包含params的url
    'tuple_or_list_params_2_dict_params',  # tuple和list类型的params转dict类型的params
    'str_cookies_2_dict',  # cookies字符串转dict
    'dict_cookies_2_str',  # dict类型cookies转str
    'driver_cookies_list_2_str',  # driver_cookies_list_2_str

    # chrome下抓包后, requests处理相关
    'chrome_copy_requests_header_2_dict_headers',  # 将直接从chrome复制的Request Headers转换为dict的headers
    'chrome_copy_query_string_parameters_2_tuple_params',  # 将直接从chrome复制的Query String Parameters转换为tuple类型的params

    'get_random_pc_ua',  # 得到一个随机pc headers
    'get_random_phone_ua',  # 得到一个随机phone headers
    'get_base_headers',  # 得到一个base headers

    # ip判断
    'is_ipv4',  # 判断是否为ipv4地址
    'is_ipv6',  # 判断是否为ipv6地址
    'get_local_free_port',  # 随机获取一个可以被绑定的空闲端口

    # html
    'html_entities_2_standard_html',  # 将html实体名称/实体编号转为html标签
    
    # 网络环境检测
    'is_ci_environment',  # 是否在 CI 环境中
    'get_network_port',  # 根据网络环境自动选择端口
]


# ==================== 网络环境检测 ====================

def is_ci_environment(ci_hostname_keywords: list = None) -> bool:
    """
    检测当前是否在 CI（持续集成）环境中运行
    
    通过主机名关键字和环境变量判断是否在 CI 环境中：
    - 检查主机名是否包含指定关键字（如 jenkins, ci, build）
    - 检查常见 CI 环境变量是否存在
    
    Args:
        ci_hostname_keywords: CI 主机名关键字列表，默认 ["jenkins", "ci", "build", "runner"]
    
    Returns:
        bool: 是否在 CI 环境中
        
    使用示例：
        if is_ci_environment():
            print("Running in CI environment")
        
        # 自定义关键字
        if is_ci_environment(["jenkins", "github-runner"]):
            print("Running in specific CI")
    """
    import os
    
    if ci_hostname_keywords is None:
        ci_hostname_keywords = ["jenkins", "ci", "build", "runner"]
    
    # 检查主机名
    hostname = socket.gethostname().lower()
    for keyword in ci_hostname_keywords:
        if keyword.lower() in hostname:
            return True
    
    # 检查常见 CI 环境变量
    ci_env_vars = [
        "CI", "JENKINS_URL", "GITHUB_ACTIONS", "GITLAB_CI",
        "TRAVIS", "CIRCLECI", "BUILD_NUMBER", "TEAMCITY_VERSION"
    ]
    for var in ci_env_vars:
        if os.environ.get(var):
            return True
    
    return False


def get_network_port(public_port: str, internal_port: str) -> str:
    """
    根据当前网络环境自动选择访问端口
    
    在 CI/内网环境中使用内网端口，在本地环境中使用公网端口。
    
    Args:
        public_port: 本地/公网访问时使用的端口
        internal_port: CI/内网环境中使用的端口
    
    Returns:
        str: 选中的端口
        
    使用示例：
        port = get_network_port(public_port="20030", internal_port="30080")
        url = f"http://api.example.com:{port}/v1"
    """
    if is_ci_environment():
        return internal_port
    return public_port


def _get_url_contain_params(url, params):
    """
    根据params组合得到包含params的url
    :param url:
    :param params:
    :return: url
    """
    return url + '?' + '&'.join([item[0] + '=' + item[1] for item in params])


def str_cookies_2_dict(str_cookies):
    """
    cookies字符串转dict
    :param str_cookies:
    :return:
    """
    _ = []
    for i in str_cookies.replace(' ', '').split(';'):
        if i != '':
            _.append((i.split('=')[0], i.split('=')[1]))

    cookies_dict = {}
    for item in _:
        cookies_dict.update({item[0]: item[1]})

    return cookies_dict


def tuple_or_list_params_2_dict_params(params):
    """
    tuple和list类型的params转dict类型的params
    :param params:
    :return:
    """
    _ = {}
    for item in params:
        _.update({
            item[0]: item[1]
        })

    return _


def chrome_copy_requests_header_2_dict_headers(copy_headers):
    """
    将直接从chrome复制的Request Headers转换为dict的headers
    :param copy_headers:
    :return: a dict
    """
    # .sub('\"\1\":\"2\"', copy_headers)
    # before_part = re.compile('^(.*):').findall(copy_headers)
    # end_part = re.compile(':(.*)$').findall(copy_headers)
    # print(before_part)
    # print(end_part)
    _ = copy_headers.split('\n')
    _ = [item.split(': ') for item in _]
    # pprint(_)

    tmp = {}
    for item in _:
        if item != ['']:
            if item[0].startswith(':'):  # 去除':authority'这些
                continue
            item_1 = item[1].replace(' ', '')
            tmp.update({item[0]: item_1})

    return tmp


def chrome_copy_query_string_parameters_2_tuple_params(copy_params):
    """
    将直接从chrome复制的Query String Parameters转换为tuple类型的params
    :param copy_params:
    :return: (('xx', 'yy'), ...)
    """
    _ = copy_params.split('\n')
    _ = [item.split(': ') for item in _]
    # pprint(_)

    tmp = []
    for item in _:
        if item != ['']:
            if len(item) == 1:
                item_1 = ''
            else:
                item_1 = item[1].replace(' ', '')
            tmp.append((item[0], item_1))

    return tuple(tmp)


def get_random_pc_ua():
    """
    随机生成PC端常见浏览器的User-Agent
    """
    # 浏览器名称和对应版本范围
    browsers = {
        "Chrome": {
            "versions": [f"{random.randint(90, 120)}.0.{random.randint(1000, 9999)}.{random.randint(10, 999)}" for _ in range(5)],
            "template": "Mozilla/5.0 (Windows NT {windows_ver}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
        },
        "Firefox": {
            "versions": [f"{random.randint(90, 110)}.0" for _ in range(5)],
            "template": "Mozilla/5.0 (Windows NT {windows_ver}; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}"
        },
        "Edge": {
            "versions": [f"{random.randint(90, 120)}.0.{random.randint(100, 999)}.{random.randint(10, 99)}" for _ in range(5)],
            "template": "Mozilla/5.0 (Windows NT {windows_ver}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Edg/{version}"
        },
        "Safari": {
            "versions": [f"{random.randint(10, 16)}.{random.randint(0, 3)}" for _ in range(5)],
            "template": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{mac_ver}_{mac_rev}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15"
        },
        "Opera": {
            "versions": [f"{random.randint(70, 100)}.0.{random.randint(1000, 9999)}.{random.randint(10, 999)}" for _ in range(5)],
            "template": "Mozilla/5.0 (Windows NT {windows_ver}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36 OPR/{version}"
        }
    }

    # 随机选择操作系统版本
    windows_versions = ["10.0", "11.0", "6.3", "6.2", "6.1"]
    windows_ver = random.choice(windows_versions)

    # 随机Mac版本
    mac_ver = random.randint(10, 15)
    mac_rev = random.randint(0, 9)

    # 随机选择浏览器
    browser_name = random.choice(list(browsers.keys()))
    browser_data = browsers[browser_name]

    # 随机选择版本
    version = random.choice(browser_data["versions"])

    # 为Opera额外添加Chrome版本
    chrome_ver = f"{random.randint(80, 120)}.0.{random.randint(1000, 9999)}.{random.randint(10, 999)}"

    # 生成User-Agent
    template = browser_data["template"]
    if browser_name == "Safari":
        user_agent = template.format(mac_ver=mac_ver, mac_rev=mac_rev, version=version)
    elif browser_name == "Opera":
        user_agent = template.format(windows_ver=windows_ver, chrome_ver=chrome_ver, version=version)
    else:
        user_agent = template.format(windows_ver=windows_ver, version=version)

    return user_agent


def get_random_phone_ua():
    """
    随机生成移动端常见浏览器的User-Agent
    """
    # 定义移动设备和操作系统版本
    user_agent = ""
    ios_devices = ["iPhone", "iPad", "iPod"]
    ios_versions = [f"{random.randint(12, 17)}_{random.randint(0, 6)}" for _ in range(5)]

    android_devices = [
        "SM-G950F", "SM-G960F", "SM-G970F", "SM-G975F", "SM-G980F", "SM-G990", "SM-G991",
        "SM-S901", "Pixel 4", "Pixel 5", "Pixel 6", "Pixel 7", "Pixel 8",
        "Redmi Note 9", "Redmi Note 10", "Redmi Note 11", "Mi 11", "Mi 12",
        "OnePlus 9", "OnePlus 10", "OnePlus 11", "ONEPLUS A5000", "ONEPLUS A6000"
    ]
    android_versions = [f"{v}.{random.randint(0, 2)}" for v in range(10, 14)]

    # 浏览器类型及模板
    browsers = {
        "iOS Safari": {
            "template": "Mozilla/5.0 ({device}; CPU OS {ios_ver} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{webkit_ver} Mobile/{mobile_ver} Safari/604.1",
            "webkit_versions": [f"{random.randint(14, 17)}.{random.randint(0, 7)}" for _ in range(3)],
            "mobile_versions": [f"15E{random.randint(100, 999)}", f"16A{random.randint(100, 999)}", f"17B{random.randint(100, 999)}"]
        },
        "Android Chrome": {
            "template": "Mozilla/5.0 (Linux; Android {android_ver}; {device}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36",
            "chrome_versions": [f"{random.randint(90, 120)}.0.{random.randint(1000, 9999)}.{random.randint(10, 200)}" for _ in range(5)]
        },
        "Android Firefox": {
            "template": "Mozilla/5.0 (Android {android_ver}; Mobile; rv:{firefox_ver}) Gecko/68.0 Firefox/{firefox_ver}",
            "firefox_versions": [f"{random.randint(90, 115)}.0" for _ in range(5)]
        },
        "Android Samsung Browser": {
            "template": "Mozilla/5.0 (Linux; Android {android_ver}; {device}) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/{sb_ver} Chrome/{chrome_ver} Mobile Safari/537.36",
            "sb_versions": [f"{random.randint(12, 20)}.0" for _ in range(5)],
            "chrome_versions": [f"{random.randint(90, 120)}.0.{random.randint(1000, 9999)}.{random.randint(10, 200)}" for _ in range(5)]
        },
        "iOS Chrome": {
            "template": "Mozilla/5.0 ({device}; CPU OS {ios_ver} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/{chrome_ver} Mobile/15E148 Safari/604.1",
            "chrome_versions": [f"{random.randint(90, 120)}.0.{random.randint(1000, 9999)}.{random.randint(10, 200)}" for _ in range(5)]
        },
        "iOS Firefox": {
            "template": "Mozilla/5.0 ({device}; CPU OS {ios_ver} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/{firefox_ver} Mobile/15E148 Safari/605.1.15",
            "firefox_versions": [f"{random.randint(90, 115)}.0" for _ in range(5)]
        }
    }

    # 随机选择浏览器类型
    browser_name = random.choice(list(browsers.keys()))
    browser_data = browsers[browser_name]

    # 生成UA字符串
    if browser_name.startswith("iOS"):
        device = random.choice(ios_devices)
        ios_ver = random.choice(ios_versions)

        if browser_name == "iOS Safari":
            webkit_ver = random.choice(browser_data["webkit_versions"])
            mobile_ver = random.choice(browser_data["mobile_versions"])
            user_agent = browser_data["template"].format(
                device=device,
                ios_ver=ios_ver,
                webkit_ver=webkit_ver,
                mobile_ver=mobile_ver
            )
        elif browser_name == "iOS Chrome":
            chrome_ver = random.choice(browser_data["chrome_versions"])
            user_agent = browser_data["template"].format(
                device=device,
                ios_ver=ios_ver,
                chrome_ver=chrome_ver
            )
        elif browser_name == "iOS Firefox":
            firefox_ver = random.choice(browser_data["firefox_versions"])
            user_agent = browser_data["template"].format(
                device=device,
                ios_ver=ios_ver,
                firefox_ver=firefox_ver
            )
    else:  # Android browsers
        device = random.choice(android_devices)
        android_ver = random.choice(android_versions)

        if browser_name == "Android Chrome":
            chrome_ver = random.choice(browser_data["chrome_versions"])
            user_agent = browser_data["template"].format(
                android_ver=android_ver,
                device=device,
                chrome_ver=chrome_ver
            )
        elif browser_name == "Android Firefox":
            firefox_ver = random.choice(browser_data["firefox_versions"])
            user_agent = browser_data["template"].format(
                android_ver=android_ver,
                firefox_ver=firefox_ver
            )
        elif browser_name == "Android Samsung Browser":
            sb_ver = random.choice(browser_data["sb_versions"])
            chrome_ver = random.choice(browser_data["chrome_versions"])
            user_agent = browser_data["template"].format(
                android_ver=android_ver,
                device=device,
                sb_ver=sb_ver,
                chrome_ver=chrome_ver
            )

    return user_agent


def get_base_headers():
    """
    得到一个基本的headers
    :return:
    """
    return {
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'user-agent': get_random_pc_ua(),
        'accept': '*/*'
    }


def dict_cookies_2_str(dict_cookies):
    """
    dict类型cookies转str
    :param dict_cookies:
    :return:
    """
    cookie = [str(key) + "=" + str(value) for key, value in dict_cookies.items()]
    str_cookies = ';'.join(item for item in cookie)

    return str_cookies


def is_ipv4(ip):
    """
    判断是否为ipv4地址
    :param ip:
    :return: bool
    """
    try:
        socket.inet_aton(ip)
    except socket.error:
        return False

    return True


def is_ipv6(ip):
    """
    判断是否为ipv6地址
    :param ip:
    :return: bool
    """
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    except socket.error:
        return False

    return True


def get_local_free_port():
    """
    随机获取一个可以被绑定的空闲端口
    :return: int
    """
    with closing(socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)) as s:
        s.bind(('127.0.0.1', 0))
        _, port = s.getsockname()

    return port


def html_entities_2_standard_html(html_body):
    """
    将html实体名称/实体编号转为html标签
    :param html_body:
    :return:
    """
    char_entities = (
        ('&nbsp;', ' '),
        ('&#160;', ' '),
        ('&lt;', '<'),
        ('&#60;', '<'),
        ('&gt;', '>'),
        ('&#62;', '>'),
        ('&amp;', '&'),
        ('&#38;', '&'),
        ('&quot;', '"'),
        ('&#34;', '"'),
    )

    for item in char_entities:
        html_body = html_body.replace(item[0], item[1])

    return html_body


def driver_cookies_list_2_str(cookies_list: list) -> str:
    """
    driver的cookies list 转 str
    :param cookies_list: eg: [{"domain":".jianshu.com", "expirationDate":1552467568.95627, ..., "name":"_m7e_session_core", ..., "value":"cc5871cc6fd05e742b83fbf476676450",}, ...]
    :return:
    """
    res = ''
    for item in cookies_list:
        name = item.get('name', '')
        value = item.get('value', '')
        if name != '':
            res += '{}={};'.format(name, value)

    return res


if __name__ == '__main__':
    print(get_random_pc_ua())