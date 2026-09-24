"""
风光储一体化综合分析平台（统合版）
=================================
将「储能源荷储匹配分析」(储能分析/) 与「技经批量计算」(技经批量计算/) 两个模型
整合为一个应用，通过侧边栏换页完成全部操作：

  1. ⚡ 储能源荷储分析 —— 上传 8760 逐时数据，配置电价/时段，批量模拟源荷储匹配，
     结果保存在 st.session_state.batch_results；
  2. 💰 技经批量计算 —— 新增「储能分析结果传入」输入模式，直接读取上一步的批量结果
     （容量、利用小时数、综合电价），无需再导出/导入 Excel，一键完成 IRR/LCOE 批量
     计算或反推综合电价；表格上传与手动步长模式保持不变。

登录机制与两个独立版 App 共用（Cookie 前缀一致、secrets 配置一致）。
"""

import os
import sys

import streamlit as st

# ===================== 兼容性补丁  =====================
# 解决 streamlit-cookies-manager 内部调用已弃用/移除的 st.cache 问题
if not hasattr(st, "cache"):
    st.cache = st.cache_data

# ===================== 将两个子模块目录加入 import 路径 =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "energy"))
sys.path.insert(0, os.path.join(BASE_DIR, "techno"))

from energy_page import render_energy_page          # noqa: E402  (储能模块 energy/)
from techno_page import render_techno_page          # noqa: E402  (技经模块 techno/)
from streamlit_cookies_manager import EncryptedCookieManager  # noqa: E402

# ===================== 用户数据库（已迁移到 Streamlit secrets，请勿在代码中硬编码密码）=====================
try:
    USER_CREDENTIALS = dict(st.secrets["users"])
except Exception:
    # secrets 未配置 [users] 段时安全兜底：所有账号都无法登录（fail-closed）
    USER_CREDENTIALS = {}

# 设置页面配置
st.set_page_config(page_title="风光储一体化综合分析平台", layout="wide")

# ===================== 登录与 Cookie =====================
try:
    _cookie_password = st.secrets["cookie_password"]
except Exception as e:
    raise RuntimeError(
        "缺少登录配置：请在 .streamlit/secrets.toml 中配置 cookie_password 和 [users]"
        "（可参考 技经批量计算/.streamlit/secrets.toml）"
    ) from e

cookies = EncryptedCookieManager(
    prefix="energy-app/",
    password=_cookie_password
)
if not cookies.ready():
    st.stop()


def check_login():
    """多用户验证逻辑（基于浏览器 Cookie 保持登录态）"""
    if cookies.get("auth_status") == "logged_in":
        return True

    st.title("风光储一体化综合分析平台 - 身份验证")

    with st.form("login_form"):
        user_input = st.text_input("账号")
        pw_input = st.text_input("密码", type="password")
        submit = st.form_submit_button("登录")

        if submit:
            if user_input in USER_CREDENTIALS and USER_CREDENTIALS[user_input] == pw_input:
                cookies["auth_status"] = "logged_in"
                cookies["current_user"] = user_input
                cookies.save()
                st.success(f"欢迎回来，{user_input}！正在进入系统...")
                st.rerun()
                return True
            else:
                st.error("账号或密码不正确，请重试")
    return False


def logout():
    """登出逻辑 - 显示在侧边栏顶部"""
    current_user = cookies.get("current_user", "未知用户")
    st.sidebar.write(f"**当前用户**: {current_user}")
    if st.sidebar.button("退出登录", use_container_width=True):
        cookies["auth_status"] = "logged_out"
        cookies["current_user"] = ""
        cookies.save()
        st.rerun()
    st.sidebar.markdown("---")


if not check_login():
    st.stop()

logout()


# ===================== 页面包装 =====================
def _energy_page():
    """储能源荷储分析页（页面自带标题与双 Tab）"""
    render_energy_page()


def _techno_page():
    """技经批量计算页"""
    st.title("风光储系统经济性评价平台 · 技经批量计算")
    st.markdown("---")
    render_techno_page()


# ===================== 换页导航 =====================
page = st.navigation([
    st.Page(_energy_page, title="储能源荷储分析", icon="⚡", default=True),
    st.Page(_techno_page, title="技经批量计算", icon="💰"),
])
page.run()
