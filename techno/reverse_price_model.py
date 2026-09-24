"""
反推综合电价模块：
在除综合电价以外的所有参数保持不变的前提下，
给定目标 IRR（项目税前/税后 IRR 或 资本金税前/税后 IRR，可选），
通过数值求根（二分法）反推出使该 IRR 恰好达到目标值所需的综合电价（元/kWh）。

原理：
- 综合电价同时作用于风电、光伏上网电价（与批量计算口径一致）；
- 电价越高 -> 收入越高 -> IRR 单调递增，因此适合用二分法求根；
- 每次迭代重新调用 get_financial_plan_cash_flow 完整复算财务模型。
"""

import math

import project_parameters as pp
from financial_plan_cash_flow_model import get_financial_plan_cash_flow

# 目标 IRR 类型 -> 财务模型结果中的 IRR 字段
IRR_KEYS = {
    'project_post': 'P_post_irr_result',   # 项目税后IRR
    'project_pre': 'P_pre_irr_result',     # 项目税前IRR
    'capital_post': 'C_post_irr_result',   # 资本金税后IRR
    'capital_pre': 'C_pre_irr_result',     # 资本金税前IRR
}

# 电价搜索区间 (元/kWh)
PRICE_LOW = 0.0
PRICE_HIGH_INIT = 3.0
PRICE_HIGH_MAX = 10.0


def _irr_at_price(price, irr_key, total_years):
    """
    将风/光电价设为 price 后完整复算财务模型，返回 (该电价下的目标IRR, 完整模型结果)。
    若 IRR 无法计算（npf.irr 返回 nan，即现金流无正负号变化），按 -100% 处理以便区间搜索。
    """
    pp.SELLING_PRICE_PARAMS['wind_price_per_kwh'] = price
    pp.SELLING_PRICE_PARAMS['pv_price_per_kwh'] = price
    data = get_financial_plan_cash_flow(total_years=total_years)
    irr = data['financing_cash_flow'].get(irr_key, float('nan'))
    try:
        irr = float(irr)
    except (TypeError, ValueError):
        irr = float('nan')
    if math.isnan(irr):
        irr = -1.0
    return irr, data


def solve_comprehensive_price(target_irr, irr_type='project_post', total_years=26,
                              tol=1e-8, max_iter=100):
    """
    反推使目标 IRR 达标所需的综合电价。

    Args:
        target_irr (float): 目标 IRR（小数形式，如 0.08 表示 8%）。
        irr_type (str): 'project_post' 项目税后IRR / 'project_pre' 项目税前IRR /
                        'capital_post' 资本金税后IRR / 'capital_pre' 资本金税前IRR。
        total_years (int): 计算总年数（与批量计算保持一致，默认 26）。
        tol (float): 电价求解精度（元/kWh）。
        max_iter (int): 二分法最大迭代次数。

    Returns:
        dict:
            converged (bool): 是否成功收敛。
            price (float): 反推出的综合电价（元/kWh），未收敛时为 None。
            target_irr (float): 输入的目标 IRR。
            irr_type (str): 目标 IRR 类型。
            achieved_irr (float): 求解电价下实际达到的目标 IRR（验证值）。
            P_post_irr_result (float): 求解电价下的项目税后IRR。
            P_pre_irr_result (float): 求解电价下的项目税前IRR。
            C_post_irr_result (float): 求解电价下的资本金税后IRR。
            C_pre_irr_result (float): 求解电价下的资本金税前IRR。
            LCOE (float): 求解电价下的度电成本。
            message (str): 未收敛时的原因说明。
    """
    if irr_type not in IRR_KEYS:
        raise ValueError(f"未知的 IRR 类型: {irr_type}，可选: {list(IRR_KEYS.keys())}")
    irr_key = IRR_KEYS[irr_type]

    result = {
        'converged': False,
        'price': None,
        'target_irr': target_irr,
        'irr_type': irr_type,
        'achieved_irr': None,
        'P_post_irr_result': None,
        'P_pre_irr_result': None,
        'C_post_irr_result': None,
        'C_pre_irr_result': None,
        'LCOE': None,
        'message': '',
    }

    # 保存当前电价，求解结束后恢复，避免污染全局参数状态
    original_prices = (
        pp.SELLING_PRICE_PARAMS['wind_price_per_kwh'],
        pp.SELLING_PRICE_PARAMS['pv_price_per_kwh'],
    )

    try:
        # --- 下界检查 ---
        f_low, _ = _irr_at_price(PRICE_LOW, irr_key, total_years)
        if f_low > target_irr:
            result['message'] = (
                f"目标 IRR ({target_irr:.2%}) 不高于电价下限 {PRICE_LOW} 元/kWh 对应的 IRR ({f_low:.2%})，无法反推。"
            )
            return result

        # --- 确定上界：从初始上界开始，必要时倍增扩至上限 ---
        high = PRICE_HIGH_INIT
        f_high, _ = _irr_at_price(high, irr_key, total_years)
        while f_high < target_irr and high < PRICE_HIGH_MAX:
            high = min(high * 2, PRICE_HIGH_MAX)
            f_high, _ = _irr_at_price(high, irr_key, total_years)
        if f_high < target_irr:
            result['message'] = (
                f"综合电价升至 {PRICE_HIGH_MAX:.1f} 元/kWh 仍无法达到目标 IRR "
                f"（该电价下最高约 {f_high:.2%}），请检查投资、发电量等参数。"
            )
            return result

        # --- 二分法求根：f(price) = IRR(price) - target_irr，单调递增 ---
        low = PRICE_LOW
        price = high
        for _ in range(max_iter):
            mid = (low + high) / 2
            f_mid, _ = _irr_at_price(mid, irr_key, total_years)
            if f_mid < target_irr:
                low = mid
            else:
                high = mid
            price = (low + high) / 2
            if high - low < tol:
                break

        # --- 用最终电价完整复算一次，输出验证指标 ---
        achieved_irr, data = _irr_at_price(price, irr_key, total_years)
        m = data['financing_cash_flow']
        result.update({
            'converged': True,
            'price': price,
            'achieved_irr': achieved_irr,
            'P_post_irr_result': m.get('P_post_irr_result'),
            'P_pre_irr_result': m.get('P_pre_irr_result'),
            'C_post_irr_result': m.get('C_post_irr_result'),
            'C_pre_irr_result': m.get('C_pre_irr_result'),
            'LCOE': m.get('LCOE'),
        })
        return result
    finally:
        pp.SELLING_PRICE_PARAMS['wind_price_per_kwh'] = original_prices[0]
        pp.SELLING_PRICE_PARAMS['pv_price_per_kwh'] = original_prices[1]


if __name__ == '__main__':
    # 简单自测：默认参数下反推项目税后 IRR = 8% 所需综合电价
    sol = solve_comprehensive_price(0.08, irr_type='project_post')
    if sol['converged']:
        print(f"反推综合电价: {sol['price']:.6f} 元/kWh")
        print(f"达到的项目税后IRR: {sol['achieved_irr']:.6%}")
        print(f"对应资本金税后IRR: {sol['C_post_irr_result']:.6%}")
        print(f"度电成本LCOE: {sol['LCOE']:.4f}")
    else:
        print(f"未收敛: {sol['message']}")
