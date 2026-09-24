"""
项目参数表：包含了所有基础参数和第一阶段的计算结果。
这些参数用于后续财务模型的搭建和年度计算。
主要涵盖：建设规模、投资金额、经营成本、发电参数、税费及折旧等。
"""

# ==================== 1. 基础输入参数 ====================

# C2:D5 - 分年度建设规模：定义项目的装机容量基础
PROJECT_SCALE = {
    'start_year': 2025,           # 项目启动年份
    'wind_mw': 100,               # 风电装机容量 (MW)
    'pv_mw': 100,                 # 光伏装机容量 (MW)
    'energy_storage_mwh': 50,     # 储能配置容量 (MWh)
}

# C7:C15, C18:C21 - 投资与资金参数：涵盖单瓦造价、贷款利率及还款逻辑
INVESTMENT_PARAMS = {
    'wind_unit_investment_per_w': 4,            # 风电场单位投资 (元/Wp)
    'pv_unit_investment_per_wp': 3,             # 光伏电站单位投资 (元/Wp)
    'energy_storage_unit_investment_per_wh': 0.7, # 储能单位投资 (元/Wh)
    'other_non_fixed_asset_investment_million_yuan': 0, # 其他非固定资产投资 (万元)
    'capital_ratio': 0.2,                       # 资本金比例 (通常为20%)
    'long_term_loan_rate': 0.035,               # 长期贷款年利率 (3.5%)
    'short_term_loan_rate': 0.03,               # 短期贷款年利率 (3%)
    'working_capital_per_kw': 30,               # 单位流动资金 (元/kW)
    'self_owned_working_capital_ratio': 0.3,    # 自有流动资金比例 (30%)
    'repayment_start_year': 2,                  # 开始还款年份 (运营第几年)
    'repayment_period': 7,                      # 贷款偿还期限 (年)
    'short_term_loan_rate_repayment': 0.03,     # 还款期短期利率
    'benchmark_yield': 0.06,                    # 基准收益率 (6%)
}

# C25:C30 - 经营成本参数：定义运维（O&M）支出及设备更换预案
OPERATING_COST_PARAMS = {
    'wind_unit_operating_cost_per_w': 0.05,     # 风电年运维单价 (元/W)
    'pv_unit_operating_cost_per_wp': 0.03,      # 光伏年运维单价 (元/Wp)
    'energy_storage_unit_operating_cost_per_wh': 0.02, # 储能年运维单价 (元/Wh)
    'other_operating_cost_million_yuan_per_year': 0,   # 其他年度经营成本 (万元)
    'equipment_replacement_year': 7,            # 设备第一次更换年份
    'equipment_replacement_S_year': 14,         # 设备第二次更换年份
    'equipment_replacement_unit_price_per_wh': 0.3, # 设备更换单价 (元/Wh)
}

# C34:C38 - 发电小时数与衰减：用于预测年度发电量
POWER_GENERATION_PARAMS = {
    'wind_hours': 1500,               # 风电年等效利用小时数
    'pv_first_year_hours': 1500,      # 光伏首年利用小时数
    'first_year_decline': 0.01,       # 首年衰减率
    'annual_decline': 0.004,          # 后续逐年衰减率
}

# C41:C43 - 运营年限：各类资产的经营周期
OPERATION_YEARS = {
    'wind': 20,
    'pv': 25,
    'energy_storage': 20,
}

# C46:C48 - 售电电价：收入计算的核心基准
SELLING_PRICE_PARAMS = {
    'wind_price_per_kwh': 0.33,       # 风电含税上网电价 (元/kWh)
    'pv_price_per_kwh': 0.33,         # 光伏含税上网电价 (元/kWh)
    'cost_of_electricity_discount_rate': 0.05, # 度电成本折现率
}

# C51:C58 - 税率：涉及增值税、所得税及税收优惠
TAX_RATES = {
    'vat_rate': 0.13,                         # 增值税率 (13%)
    'sales_tax_surcharge_rate': 0.1,          # 附加税率 (城市维护建设税等)
    'preferential_income_tax_rate': 0.15,     # 优惠所得税率 (如高新技术或西部大开发)
    'current_year': 2025,                     # 当前计算起始年份
    'standard_income_tax_rate': 0.25,         # 标准企业所得税率 (25%)
    'statutory_reserve_fund_ratio': 0.1,      # 法定盈余公积计提比例 (10%)
    'enterprise_development_fund_ratio': 0,   # 企业发展基金计提比例
}

# C62:C64 - 折旧率：根据各资产性质确定的年折旧比例
DEPRECIATION_RATES = {
    'wind_depreciation_rate': 0.0475,
    'pv_depreciation_rate': 0.0475,
    'energy_storage_depreciation_rate': 0.095,
}

# C67:C69 - 残值率：运营期满后的预计资产余值占比
SALVAGE_RATES = {
    'wind_salvage_rate': 0.05,
    'pv_salvage_rate': 0.05,
    'energy_storage_salvage_rate': 0.05,
}

# C16, C17 - 还款方式：0为等额本金，1为等额本息
REPAYMENT_METHOD = {
    'equal_principal_and_interest': 1,
}

# ==================== 2. 派生参数和计算 ====================
# 基于上述基础输入，通过公式自动生成用于模型的中间变量

# 光致衰减LID
POWER_GENERATION_PARAMS['photonic_decline'] = POWER_GENERATION_PARAMS['first_year_decline'] - POWER_GENERATION_PARAMS['annual_decline']

# 计算剩余税收优惠年限 (基于当前年份和政策窗口)
TAX_RATES['remaining_preferential_years'] = 2026 - TAX_RATES['current_year'] - 1

def _calculate_investments():
    """
    计算并返回各项投资成本详细拆解（单位：万元）。
    对应 Excel H列中的各项计算公式。
    """
    results = {}
    
    # 风电总投资：单价 * 规模
    results['wind_farm_investment'] = INVESTMENT_PARAMS['wind_unit_investment_per_w'] * PROJECT_SCALE['wind_mw'] * 100
    
    # 光伏总投资：单价 * 规模
    results['pv_power_plant_investment'] = INVESTMENT_PARAMS['pv_unit_investment_per_wp'] * PROJECT_SCALE['pv_mw'] * 100
    
    # 储能总投资：单价 * 规模
    results['energy_storage_investment'] = INVESTMENT_PARAMS['energy_storage_unit_investment_per_wh'] * PROJECT_SCALE['energy_storage_mwh'] * 100
    
    # 静态总投资：三者相加 + 非固定资产
    results['total_project_investment'] = (
        results['wind_farm_investment'] + 
        results['pv_power_plant_investment'] +
        results['energy_storage_investment'] + 
        INVESTMENT_PARAMS['other_non_fixed_asset_investment_million_yuan']
    )
    
    # 增值税可抵扣进项税额 (按投资额的10%估算)
    results['deductible_taxes'] = (
        results['total_project_investment'] - 
        INVESTMENT_PARAMS['other_non_fixed_asset_investment_million_yuan']
    ) * 0.1
    
    # 建设期利息：基于资本金比例和长贷利率估算
    results['construction_period_interest'] = (
        results['total_project_investment'] * (1 - INVESTMENT_PARAMS['capital_ratio']) / 
        (2 / INVESTMENT_PARAMS['long_term_loan_rate'] + INVESTMENT_PARAMS['capital_ratio'])
    )
    
    # 动态总投资：静态投资 + 建设期利息
    results['dynamic_total_investment'] = results['total_project_investment'] + results['construction_period_interest']
    
    # 初始贷款本金
    results['loan_amount'] = results['dynamic_total_investment'] * (1 - INVESTMENT_PARAMS['capital_ratio']) - results['construction_period_interest']
    
    # 流动资金需求量
    results['working_capital'] = INVESTMENT_PARAMS['working_capital_per_kw'] * (PROJECT_SCALE['wind_mw'] + PROJECT_SCALE['pv_mw']) / 10
    
    # --- 分摊固定资产原值 (用于折旧计算) ---
    # 计算逻辑：动态总投资 - 非固投 - 抵扣税额
    total_fixed_asset_original_value = results['dynamic_total_investment'] - INVESTMENT_PARAMS['other_non_fixed_asset_investment_million_yuan'] - results['deductible_taxes']
    
    sum_investments = results['wind_farm_investment'] + results['pv_power_plant_investment'] + results['energy_storage_investment']
    
    # 按投资比例将总原值分摊至风、光、储各部分
    results['wind_fixed_asset_original_value'] = total_fixed_asset_original_value * results['wind_farm_investment'] / sum_investments
    results['pv_fixed_asset_original_value'] = total_fixed_asset_original_value * results['pv_power_plant_investment'] / sum_investments
    results['energy_storage_fixed_asset_original_value'] = total_fixed_asset_original_value * results['energy_storage_investment'] / sum_investments
    
    return results

def _calculate_operating_costs():
    """
    计算并返回各项经营成本（单位：万元）。
    反映项目在运营期间的年度现金流出。
    """
    results = {}
    
    # 风电年运维成本
    results['wind_operating_cost'] = OPERATING_COST_PARAMS['wind_unit_operating_cost_per_w'] * PROJECT_SCALE['wind_mw'] * 100
    
    # 光伏年运维成本
    results['pv_operating_cost'] = OPERATING_COST_PARAMS['pv_unit_operating_cost_per_wp'] * PROJECT_SCALE['pv_mw'] * 100
    
    # 储能年运维成本
    results['energy_storage_operating_cost'] = OPERATING_COST_PARAMS['energy_storage_unit_operating_cost_per_wh'] * PROJECT_SCALE['energy_storage_mwh'] * 100
    
    # 记录更换年份
    results['replacement_year'] = OPERATING_COST_PARAMS['equipment_replacement_year']
    
    # 储能电池更换预计总费用
    results['replacement_cost'] = OPERATING_COST_PARAMS['equipment_replacement_unit_price_per_wh'] * PROJECT_SCALE['energy_storage_mwh'] * 100

    return results

# 执行计算过程，将结果实例化为常量供外部调用
INVESTMENT_RESULTS = _calculate_investments()
OPERATING_COST_RESULTS = _calculate_operating_costs()
