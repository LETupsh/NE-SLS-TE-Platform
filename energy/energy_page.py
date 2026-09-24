"""
储能源荷储匹配分析——页面模块（UI 主体）。
从 energy_app.py 抽出，供独立版 (energy_app.py) 与综合版 (integrated_app.py) 共用。
不包含登录逻辑，登录由宿主 App 负责。
"""

import datetime

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from energy_model import (
    calculate_single_case,
    generate_8760_month_array,
    parse_batch_input,
    parse_time_slot_input,
    perform_batch_calculation,
    write_batch_results_to_excel,
    write_hourly_data_to_excel,
)


def init_session_state():
    if 'monthly_config_data' not in st.session_state:
        st.session_state.monthly_config_data = {
            m: {'尖峰': '19-21', '峰': '12-14, 17-18, 22-23', '平': '7-11, 15-16', '谷': '0-5', '深谷': '6-6'}
            for m in range(1, 13)
        }
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = []
    if 'discharge_allowed' not in st.session_state:
        st.session_state.discharge_allowed = {'尖峰': True, '峰': True, '平': True, '谷': True, '深谷': True}
    if 'price_mode' not in st.session_state:
        st.session_state.price_mode = 'period'
    if 'hourly_self_prices' not in st.session_state:
        st.session_state.hourly_self_prices = None
    if 'hourly_on_grid_prices' not in st.session_state:
        st.session_state.hourly_on_grid_prices = None
    if 'csv_discharge_str' not in st.session_state:
        st.session_state.csv_discharge_str = '0-23'


def get_final_map():
    final_map = {}
    for month in range(1, 13):
        h_map = {h: '平' for h in range(24)}
        for period in ['深谷', '谷', '平', '峰', '尖峰']:
            slots = parse_time_slot_input(st.session_state.monthly_config_data[month][period])
            if slots:
                for s, e in slots:
                    hrs = range(s, e+1) if s <= e else list(range(s, 24)) + list(range(0, e+1))
                    for h in hrs:
                        h_map[h] = period
        for h, p in h_map.items():
            final_map[f"{h}_{month}"] = p
    return final_map


def color_time_periods(val):
    color_map = {
        '尖峰': 'background-color: #ff6347; color: white',
        '峰':   'background-color: #ffd700; color: black',
        '平':   'background-color: #90ee90; color: black',
        '谷':   'background-color: #add8e6; color: black',
        '深谷': 'background-color: #4682b4; color: white',
    }
    return color_map.get(val, '')


def render_energy_page():
    """储能源荷储匹配分析页面主体（UI + 计算 + 导出）"""
    init_session_state()
    tab1, tab2 = st.tabs(["计算与分析", "电价与时段配置"])

    # ========== tab2：电价与时段配置 ==========
    with tab2:
        st.subheader("1. 电价模式选择")
        price_mode = st.radio(
            "选择电价模式",
            options=['period', 'csv'],
            format_func=lambda x: '分时段电价（默认）' if x == 'period' else 'CSV 逐时电价',
            horizontal=True,
            key="price_mode_radio"
        )
        st.session_state.price_mode = price_mode
        prices = {'Curtailment': st.number_input("折损/弃电电价 (元/kWh)", value=0.0, format="%.4f")}
        periods = ['尖峰', '峰', '平', '谷', '深谷']

        # ---- CSV 模式 ----
        if price_mode == 'csv':
            st.info("请上传包含 **8760 行** 逐时电价数据的 CSV 文件，需包含两列：**自用电价** 和 **上网电价**（单位：元/kWh）")
            csv_price_file = st.file_uploader("上传逐时电价 CSV", type="csv", key="price_csv_uploader")
            if csv_price_file is not None:
                try:
                    price_df = pd.read_csv(csv_price_file)
                    if len(price_df) != 8760:
                        st.error(f"CSV 文件行数必须为 8760，当前为 {len(price_df)} 行。")
                        st.session_state.hourly_self_prices = None
                        st.session_state.hourly_on_grid_prices = None
                    else:
                        cols = price_df.columns.tolist()
                        st.success(f"已读取 {len(price_df)} 行数据，列名：{cols}")
                        c1, c2 = st.columns(2)
                        with c1:
                            self_col = st.selectbox("自用电价对应列", cols, index=0, key="self_col_select")
                        with c2:
                            on_grid_col = st.selectbox("上网电价对应列", cols, index=min(1, len(cols)-1), key="on_grid_col_select")
                        st.session_state.hourly_self_prices = price_df[self_col].values.astype(float)
                        st.session_state.hourly_on_grid_prices = price_df[on_grid_col].values.astype(float)
                        st.markdown("**逐时电价预览（前 24 小时）：**")
                        preview_df = pd.DataFrame({
                            "小时": range(1, 25),
                            "自用电价 (元/kWh)": st.session_state.hourly_self_prices[:24],
                            "上网电价 (元/kWh)": st.session_state.hourly_on_grid_prices[:24]
                        })
                        st.dataframe(preview_df, height=(len(preview_df)+1)*35+3, use_container_width=True)
                except Exception as e:
                    st.error(f"解析 CSV 文件失败：{e}")
                    st.session_state.hourly_self_prices = None
                    st.session_state.hourly_on_grid_prices = None
            else:
                st.session_state.hourly_self_prices = None
                st.session_state.hourly_on_grid_prices = None
            for p in periods:
                prices[p] = {'self': 0.0, 'on_grid': 0.0}

        # ---- 分时段模式 ----
        if price_mode == 'period':
            st.subheader("时段电价")
            header_cols = st.columns([0.8] + [1]*5)
            with header_cols[0]:
                st.markdown("**时段 →**")
            for i, p in enumerate(periods):
                with header_cols[i+1]:
                    st.markdown(f"**{p}**")
            row1_cols = st.columns([0.8] + [1]*5)
            with row1_cols[0]:
                st.markdown("**自用电价**")
            for i, p in enumerate(periods):
                with row1_cols[i+1]:
                    prices[p] = prices.get(p, {})
                    prices[p]['self'] = st.number_input(
                        label="", value=0.3 if p == '深谷' else (1.2 if i < 2 else 0.6),
                        format="%.4f", key=f"s_{p}", label_visibility="collapsed"
                    )
            row2_cols = st.columns([0.8] + [1]*5)
            with row2_cols[0]:
                st.markdown("**上网电价**")
            for i, p in enumerate(periods):
                with row2_cols[i+1]:
                    prices[p]['on_grid'] = st.number_input(
                        label="", value=0.38, format="%.4f", key=f"o_{p}", label_visibility="collapsed"
                    )

        # ---- 允许放电时段 ----
        st.markdown("---")
        st.subheader("2. 允许放电时段")
        if price_mode == 'csv':
            st.caption("输入允许放电的小时范围（0–23），多个时段用逗号分隔，适用于全年每日")
            csv_discharge_input = st.text_input(
                "允许放电时段",
                value=st.session_state.csv_discharge_str,
                placeholder="例：7-22 或 0-5, 19-23",
                key="csv_discharge_text"
            )
            st.session_state.csv_discharge_str = csv_discharge_input
            try:
                allowed_set = set()
                for part in csv_discharge_input.replace(' ', '').split(','):
                    if not part: continue
                    if '-' in part:
                        s, e = part.split('-')
                        for h in range(int(s), int(e)+1):
                            if 0 <= h <= 23: allowed_set.add(h)
                    else:
                        h = int(part)
                        if 0 <= h <= 23: allowed_set.add(h)
                st.session_state.discharge_allowed = {h: (h in allowed_set) for h in range(24)}
                st.caption(f"已解析：允许放电 {len(allowed_set)} 小时 → {sorted(allowed_set)}")
            except:
                st.warning("格式解析失败，请检查输入。当前默认全部允许。")
                st.session_state.discharge_allowed = {h: True for h in range(24)}
        else:
            if any(isinstance(k, int) for k in st.session_state.discharge_allowed.keys()):
                st.session_state.discharge_allowed = {'尖峰': True, '峰': True, '平': True, '谷': True, '深谷': True}
            row3_cols = st.columns([0.8] + [1]*5)
            with row3_cols[0]:
                st.markdown("**允许放电**")
            for i, p in enumerate(periods):
                with row3_cols[i+1]:
                    st.session_state.discharge_allowed[p] = st.checkbox(
                        label="", value=st.session_state.discharge_allowed.get(p, True),
                        key=f"d_{p}", label_visibility="collapsed"
                    )

        # ---- 月度时段详细配置（CSV 模式隐藏） ----
        if price_mode != 'csv':
            st.markdown("---")
            st.subheader("3. 月度时段详细配置")
            st.info("格式: 开始-结束 (0-23)，多个时段用逗号分隔。优先级：尖峰 > 峰 > 平 > 谷 > 深谷")
            edit_col1, _ = st.columns([1, 2])
            with edit_col1:
                month = st.selectbox("当前编辑月份", range(1, 13))
            m_cols = st.columns(5)
            temp_inputs = {}
            for i, p in enumerate(['尖峰', '峰', '平', '谷', '深谷']):
                temp_inputs[p] = m_cols[i].text_input(
                    f"{p}时段定义",
                    value=st.session_state.monthly_config_data[month][p],
                    key=f"input_{month}_{p}"
                )
                st.session_state.monthly_config_data[month][p] = temp_inputs[p]
            with st.expander("批量复制当前月份配置到其他月份"):
                target_months = st.multiselect("选择目标月份", [m for m in range(1, 13) if m != month])
                if st.button("执行批量同步"):
                    if target_months:
                        for tm in target_months:
                            st.session_state.monthly_config_data[tm] = temp_inputs.copy()
                        st.success(f"已成功将 {month} 月配置同步至 {target_months} 月")
                        st.rerun()
                    else:
                        st.warning("请先选择目标月份")

        # ---- 4. 全年日均逐时电价趋势（Altair 静态图） ----
        st.markdown("---")
        st.subheader("4. 全年日均逐时电价趋势")
        if (st.session_state.price_mode == 'csv'
                and st.session_state.hourly_self_prices is not None
                and st.session_state.hourly_on_grid_prices is not None):
            hourly_prices_self = np.zeros(24)
            hourly_prices_on_grid = np.zeros(24)
            for h in range(24):
                hourly_prices_self[h] = np.mean(st.session_state.hourly_self_prices[h::24])
                hourly_prices_on_grid[h] = np.mean(st.session_state.hourly_on_grid_prices[h::24])
        else:
            f_map = get_final_map()
            hourly_prices_self = np.zeros(24)
            hourly_prices_on_grid = np.zeros(24)
            for h in range(24):
                total_self = 0.0
                total_on_grid = 0.0
                for m in range(1, 13):
                    period = f_map.get(f"{h}_{m}", "平")
                    total_self += prices[period]['self']
                    total_on_grid += prices[period]['on_grid']
                hourly_prices_self[h] = total_self / 12
                hourly_prices_on_grid[h] = total_on_grid / 12

        chart_data = pd.DataFrame({
            "小时": [f"{h:02d}:00" for h in range(24)],
            "日均自用电价 (元/kWh)": hourly_prices_self,
            "日均上网电价 (元/kWh)": hourly_prices_on_grid
        })

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**日均自用电价趋势**")
            alt_self = alt.Chart(chart_data).mark_line(color="#ff6347").encode(
                x=alt.X("小时", sort=None),
                y=alt.Y("日均自用电价 (元/kWh)", scale=alt.Scale(padding=50))
            ).properties(height=300)
            st.altair_chart(alt_self, use_container_width=True)

        with c2:
            st.markdown("**日均上网电价趋势**")
            alt_ongrid = alt.Chart(chart_data).mark_line(color="#1f77b4").encode(
                x=alt.X("小时", sort=None),
                y=alt.Y("日均上网电价 (元/kWh)", scale=alt.Scale(padding=50))
            ).properties(height=300)
            st.altair_chart(alt_ongrid, use_container_width=True)

    # ========== tab1：计算与分析 ==========
    with tab1:
        st.title("新能源项目源荷储匹配分析平台")
        f = st.file_uploader("上传 8760 逐时数据 (CSV)", type="csv")
        if f:
            df = pd.read_csv(f)
            c1, c2 = st.columns(2)
            eff = c1.number_input("储能往返效率 (P3)", value=0.85, max_value=1.0)
            dep = c2.number_input("储能放电深度 (P2)", value=0.9, max_value=1.0)

            st.markdown("---")
            st.subheader("批量计算参数设置")
            st.caption("格式：单个数字 (例: 1) 或 范围步长 (例: 1,4,1 代表从1到4，步长1)")
            bc1, bc2, bc3, bc4 = st.columns(4)
            with bc1:
                pv_raw = st.text_input("光伏容量 (MW)", value="5")
            with bc2:
                wi_raw = st.text_input("风电容量 (MW)", value="2")
            with bc3:
                p_raw = st.text_input("储能功率 (MW)", value="2,4,1")
            with bc4:
                d_raw = st.text_input("储能时长 (h)", value="1,4,1")

            pv_list = parse_batch_input(pv_raw)
            wi_list = parse_batch_input(wi_raw)
            p_list = parse_batch_input(p_raw)
            d_list = parse_batch_input(d_raw)

            if st.button("开始执行模拟计算", type="primary"):
                if None in [pv_list, wi_list, p_list, d_list]:
                    st.error("输入格式有误，请检查是否使用了英文逗号且格式正确。")
                else:
                    total_scenarios = len(pv_list) * len(wi_list) * len(p_list) * len(d_list)
                    st.info(f"即将计算 {total_scenarios} 组方案...")
                    params = {
                        "pv_list": pv_list, "wind_list": wi_list,
                        "power_list": p_list, "duration_list": d_list,
                        "efficiency": eff, "depth": dep,
                        "peak_valley_map": get_final_map(),
                        "prices": prices,
                        "discharge_allowed": st.session_state.discharge_allowed,
                        "hourly_self_prices": st.session_state.hourly_self_prices,
                        "hourly_on_grid_prices": st.session_state.hourly_on_grid_prices
                    }
                    with st.spinner("正在进行计算..."):
                        st.session_state.batch_results = perform_batch_calculation(
                            df["PV_Unit_Output(kWh)"].values,
                            df["Wind_Unit_Output(kWh)"].values,
                            df["Load(kWh)"].values,
                            params, generate_8760_month_array()
                        )
                    st.session_state.last_params = params
                    st.success("计算完成！")

            if st.session_state.batch_results:
                res_df = pd.DataFrame(st.session_state.batch_results)
                cols_drop = ["尖峰消纳 (%)", "峰消纳 (%)", "平消纳 (%)", "谷消纳 (%)", "深谷消纳 (%)"]
                res_df = res_df.drop(columns=[c for c in cols_drop if c in res_df.columns])
                n_rows = len(res_df)
                table_height = (n_rows + 1) * 35 + 3
                st.dataframe(res_df.style.format({
                    "光伏容量 (MW)": "{:.2f}", "风电容量 (MW)": "{:.2f}",
                    "储能功率 (MW)": "{:.2f}", "储能时长 (h)": "{:.1f}",
                    "储能容量 (MWh)": "{:.2f}",
                    "加权自用电价": "{:.4f}", "加权上网电价": "{:.4f}", "综合电价": "{:.4f}",
                    "总发电量 (kWh)": "{:.2f}", "总消纳电量 (kWh)": "{:.2f}",
                    "总上网电量 (kWh)": "{:.2f}", "总折损电量 (kWh)": "{:.2f}",
                    "自用比例 (%)": "{:.2f}", "绿电占用电比例 (%)": "{:.2f}",
                    "光伏利用小时数 (h)": "{:.1f}", "风电利用小时数 (h)": "{:.1f}",
                    "储能等效循环次数": "{:.2f}"
                }), height=table_height, use_container_width=True)

                ex_data = write_batch_results_to_excel(st.session_state.batch_results, st.session_state.last_params)
                st.download_button(
                    label="下载 Excel 完整报表",
                    data=ex_data,
                    file_name=f"能源模拟分析_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width='stretch'
                )

                scheme_options = [
                    f"方案{idx}：光伏{res['光伏容量 (MW)']}MW_风电{res['风电容量 (MW)']}MW_储能{res['储能功率 (MW)']}MWx{res['储能时长 (h)']}h"
                    for idx, res in enumerate(st.session_state.batch_results, 1)
                ]
                selected_scheme_idx = st.selectbox(
                    "选择方案导出逐时数据",
                    range(len(scheme_options)),
                    format_func=lambda i: scheme_options[i],
                    key="scheme_selector"
                )

                if st.button("计算该方案 8760 逐时过程量", width='stretch', key="export_hourly"):
                    with st.spinner("正在重新计算逐时数据并生成 Excel..."):
                        selected = st.session_state.batch_results[selected_scheme_idx]
                        pv_unit = df["PV_Unit_Output(kWh)"].values
                        wind_unit = df["Wind_Unit_Output(kWh)"].values
                        load = df["Load(kWh)"].values
                        month_arr = generate_8760_month_array()
                        hourly_res = calculate_single_case(
                            pv_unit, wind_unit, load,
                            selected['光伏容量 (MW)'], selected['风电容量 (MW)'],
                            selected['储能功率 (MW)'], selected['储能时长 (h)'],
                            st.session_state.last_params['efficiency'],
                            st.session_state.last_params['depth'],
                            st.session_state.last_params['peak_valley_map'],
                            st.session_state.last_params['prices'],
                            month_arr,
                            st.session_state.last_params['discharge_allowed'],
                            return_hourly=True,
                            hourly_self_prices=st.session_state.last_params.get('hourly_self_prices'),
                            hourly_on_grid_prices=st.session_state.last_params.get('hourly_on_grid_prices')
                        )
                        hourly_excel = write_hourly_data_to_excel(hourly_res["hourly_data"], selected)
                        st.download_button(
                            label="点击下载逐时过程量 Excel",
                            data=hourly_excel,
                            file_name=f"8760逐时过程量_方案{selected_scheme_idx+1}_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            width='stretch', key="download_hourly"
                        )

                        # ===== 逐日发电量与逐日负荷（Altair 双线静态图） =====
                        st.markdown("---")
                        st.subheader("日发电量与日用电量曲线")
                        hourly_gen = hourly_res["hourly_data"]["total_generation_kwh"]
                        hourly_load_arr = hourly_res["hourly_data"]["load_kwh"]
                        hourly_cons = hourly_res["hourly_data"]["consumption_kwh"]
                        daily_gen = np.sum(hourly_gen.reshape(-1, 24), axis=1)
                        daily_load = np.sum(hourly_load_arr.reshape(-1, 24), axis=1)
                        days = np.arange(1, 366)

                        df_daily = pd.DataFrame({
                            "天数": days,
                            "逐日发电量 (kWh)": daily_gen,
                            "逐日负荷 (kWh)": daily_load
                        })
                        df_daily_long = df_daily.melt(id_vars=["天数"], var_name="指标", value_name="kWh")
                        alt_daily = alt.Chart(df_daily_long).mark_line().encode(
                            x=alt.X("天数", title="天数", scale=alt.Scale(domain=[0, 370])),
                            y=alt.Y("kWh", title="kWh"),
                            color=alt.Color("指标", scale=alt.Scale(
                                domain=["逐日发电量 (kWh)", "逐日负荷 (kWh)"],
                                range=["#ff6347", "#1f77b4"]
                            ), legend=alt.Legend(orient="top"))
                        ).properties(height=350)
                        st.altair_chart(alt_daily, use_container_width=True)

                        # ===== 每日自用比例 + 新能源占负荷比例（Altair 静态图） =====
                        daily_cons = np.sum(hourly_cons.reshape(-1, 24), axis=1)
                        daily_self_ratio = np.round(np.clip(
                            np.divide(daily_cons, daily_gen, where=daily_gen > 0, out=np.zeros_like(daily_gen)) * 100,
                            0, 100
                        ), 2)
                        daily_renewable_ratio = np.round(np.divide(daily_cons, daily_load,
                            where=daily_load > 0, out=np.zeros_like(daily_load)) * 100, 2)

                        c3, c4 = st.columns(2)
                        with c3:
                            st.markdown("**每日自用比例（消纳/发电）**")
                            df_self = pd.DataFrame({"天数": days, "每日自用比例 (%)": daily_self_ratio})
                            alt_self2 = alt.Chart(df_self).mark_line(color="#ff6347").encode(
                                x=alt.X("天数", scale=alt.Scale(domain=[0, 370])), y="每日自用比例 (%)"
                            ).properties(height=300)
                            st.altair_chart(alt_self2, use_container_width=True)

                        with c4:
                            st.markdown("**每日新能源占负荷用电比例（消纳/负荷）**")
                            df_renew = pd.DataFrame({"天数": days, "每日新能源占负荷用电比例 (%)": daily_renewable_ratio})
                            alt_renew = alt.Chart(df_renew).mark_line(color="#1f77b4").encode(
                                x=alt.X("天数", scale=alt.Scale(domain=[0, 370])), y="每日新能源占负荷用电比例 (%)"
                            ).properties(height=300)
                            st.altair_chart(alt_renew, use_container_width=True)
