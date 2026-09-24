import math
from project_parameters import (
    PROJECT_SCALE,
    OPERATION_YEARS,
    INVESTMENT_RESULTS,
    DEPRECIATION_RATES,
    SALVAGE_RATES,
    TAX_RATES,
    OPERATING_COST_PARAMS
)

def calculate_depreciation(asset_name, year, current_year_cumulative_depreciation):
    """
    计算特定资产在给定年份的折旧费用。
    
    逻辑关系：折旧费用 = (固定资产原值 - 预计净残值) / 折旧年限
    这里采用直线法折旧，并确保年度折旧额不超过剩余可折旧额。
    
    Args:
        asset_name (str): 资产名称 ('wind', 'pv', 'energy_storage').
        year (int): 当前计算的年份.
        current_year_cumulative_depreciation (dict): 包含当前年份前所有累计折旧的字典。

    Returns:
        float: 该年应计提的折旧费用（万元）。
    """
    # 获取参数
    # 固定资产原值，对应 Excel 表格中的 H7, H8, H9
    fixed_asset_original_value = INVESTMENT_RESULTS.get(f'{asset_name}_fixed_asset_original_value')
    # 残值率，对应 Excel 表格中的 C34, C35, C36
    salvage_rate = SALVAGE_RATES.get(f'{asset_name}_salvage_rate')
    # 折旧年限率，对应 Excel 表格中的 C31, C32, C33
    depreciation_rate = DEPRECIATION_RATES.get(f'{asset_name}_depreciation_rate')

    # 获取之前年份的累计折旧
    cumulative_depreciation = current_year_cumulative_depreciation.get(asset_name, 0)
    if asset_name == 'energy_storage':
        cumulative_depreciation = current_year_cumulative_depreciation.get('energy_storage_0', 0)

    # 理论可折旧总额 = 原值 * (1 - 残值率)
    depreciable_total = fixed_asset_original_value * (1 - salvage_rate)

    # 正常年度折旧额 = 原值 / 折旧年限
    annual_depreciation_amount = fixed_asset_original_value / (1 / depreciation_rate)

    # 剩余可折旧额
    remaining_depreciation = depreciable_total - cumulative_depreciation

    # 计算本年折旧
    if remaining_depreciation <= 0:
        return 0
    else:
        # 如果剩余可折旧额小于本年应提折旧额，则只提剩余部分
        return min(annual_depreciation_amount, remaining_depreciation)

def calculate_storage_replacement_depreciation(asset_name, current_year,current_year_cumulative_depreciation):
    """
    计算储能设备第一次更换后，当年应计提的折旧费用。
    逻辑基于提供的 Excel 公式：严格控制累计折旧不超过 (不含税原值 * (1 - 残值率))。

    Args:
        current_year (int): 当前计算的年份
        replacement_year (int): 储能设备第一次更换年份 
        cumulative_depreciation (float): 到上一年末的累计已提折旧 
        unit_price_yuan_per_wh (float): 更换单价 (元/Wh) 
        capacity_mwh (float): 储能容量 (MWh) 
        vat_rate (float): 增值税率 
        depreciation_rate (float): 折旧率 
        salvage_rate (float): 残值率

    Returns:
        float: 该年应计提的折旧费用（单位与输入原值单位保持一致）。
    """
    cumulative_depreciation = current_year_cumulative_depreciation[asset_name]
    if asset_name == 'energy_storage_1':
        replacement_year = OPERATING_COST_PARAMS['equipment_replacement_year']
    elif asset_name == 'energy_storage_2':
        replacement_year = OPERATING_COST_PARAMS['equipment_replacement_S_year']
    # 1. Excel 公式中的第一个 IF：检查是否需要考虑更换
    if replacement_year == 0:
        return 0.0

    # 2. Excel 公式中的第二个 IF：检查是否已达到更换年份
    if replacement_year > current_year :
        return 0.0

    # --- 开始计算折旧（已达到更换年份） ---
    # 辅助计算项：资产成本的关键乘积 (C31 * C5 * 100)
    asset_cost_product = OPERATING_COST_PARAMS['equipment_replacement_unit_price_per_wh'] * PROJECT_SCALE['energy_storage_mwh'] * 100 
    
    # 理论可折旧总额 (Depreciable Total): (不含税原值) * (1 - 残值率)
    # 对应 Excel: ($C$31*$C$5*100/(1+$C$52))*(1-$C$70)
    # 不含税原值 = asset_cost_product / (1 + vat_rate)
    depreciable_total = (asset_cost_product / (1.0 + TAX_RATES['vat_rate'])) * (1.0 - SALVAGE_RATES['energy_storage_salvage_rate'])

    # 正常年度折旧额 (Annual Depreciation Amount)
    # 对应 Excel: ($C$31*$C$5*100)*$C$65  <- 注意：这里使用的是含税成本乘积
    annual_depreciation_amount = asset_cost_product * DEPRECIATION_RATES['energy_storage_depreciation_rate']
    
    # 剩余可折旧额 (Remaining Depreciable Amount)
    remaining_depreciation = depreciable_total - cumulative_depreciation

    # 3. 折旧控制逻辑（对应 Excel 的内部 IF 结构）
    
    # 检查累计折旧是否已达到上限
    if remaining_depreciation <= 0.0:
        # 累计已足额，返回 0 (对应 Excel 最内部 IF 的 False 结果和最外部 IF 的 False 结果)
        return 0.0
    else:
        # 累计未足额，取两者最小值
        # 对应 Excel 的 IF(条件)<(SUM+Annual), 剩余额, Annual
        current_year_depreciation = min(annual_depreciation_amount, remaining_depreciation)
        return current_year_depreciation

def calculate_operating_costs(asset_name, year):
    """
    计算特定资产在给定年份的经营成本，并考虑运营年限。
    
    逻辑关系：经营成本 = 项目规模 * 单位经营成本
    
    Args:
        asset_name (str): 资产名称 ('wind', 'pv', 'energy_storage').
        year (int): 当前计算的年份.

    Returns:
        float: 该年应计提的经营成本（万元）。
    """
    # 运营年限
    max_operation_year = OPERATION_YEARS.get(asset_name)

    # 运营期判断：假设第一年为建设期，且年份不能超过运营年限
    if year > 1 and max_operation_year and year <= max_operation_year + 1:
        if asset_name == 'wind':
            # 对应 Excel 表格中的 C25, C3
            return OPERATING_COST_PARAMS['wind_unit_operating_cost_per_w'] * PROJECT_SCALE['wind_mw'] * 100
        elif asset_name == 'pv':
            # 对应 Excel 表格中的 C26, C4
            return OPERATING_COST_PARAMS['pv_unit_operating_cost_per_wp'] * PROJECT_SCALE['pv_mw'] * 100
        elif asset_name == 'energy_storage':
            # 对应 Excel 表格中的 C27, C5
            base_cost = OPERATING_COST_PARAMS['energy_storage_unit_operating_cost_per_wh'] * PROJECT_SCALE['energy_storage_mwh'] * 100
            
            # 设备重置费用，对应 Excel 表格中的 C29, C30
            replacement_year = OPERATING_COST_PARAMS['equipment_replacement_year']
            replacement_cost = OPERATING_COST_PARAMS['equipment_replacement_unit_price_per_wh'] * PROJECT_SCALE['energy_storage_mwh'] * 100
            
            # 同样考虑建设期，更换年份对应 year == replacement_year + 1
            if year == replacement_year + 1:
                return base_cost ###+ replacement_cost
            else:
                return base_cost
    
    # 建设期或超过运营年限，成本为0
    return 0

def get_annual_cost_statement(total_years=26):
    """
    生成一个包含所有年份成本费用的报表。
    此表用于汇总所有与运营相关的成本（不包括融资成本）。
    
    Args:
        total_years (int): 需要计算的总年数，包括建设期。

    Returns:
        dict: 包含各年度成本数据的字典。
    """
    annual_costs = {
        'total_depreciation': [],             # 总折旧，对应 Excel C83
        'wind_depreciation': [],              # 风电折旧，对应 Excel C84
        'pv_depreciation': [],                # 光伏折旧，对应 Excel C85
        'energy_storage_depreciation': [],    # 储能折旧，对应 Excel C86
        'total_operating_cost': [],           # 总经营成本，对应 Excel C87
        'wind_operating_cost': [],            # 风电经营成本，对应 Excel C88
        'pv_operating_cost': [],              # 光伏经营成本，对应 Excel C89
        'energy_storage_operating_cost': [],  # 储能经营成本，对应 Excel C90
        # 备注：长期贷款利息 (C92) 和流动资金贷款利息 (C94) 属于融资成本，
        # 它们的计算逻辑在(C246) 和(C234)  financial_plan_cash_flow_model.py中。
    }
    
    # 初始化累计折旧字典
    cumulative_depreciation = {'wind': 0, 'pv': 0, 'energy_storage': 0, 'energy_storage_0': 0, 'energy_storage_1': 0, 'energy_storage_2': 0}

    for year in range(1, total_years + 1):
        # 建设期（第一年）成本为 0
        if year == 1:
            annual_costs['total_depreciation'].append(0)
            annual_costs['wind_depreciation'].append(0)
            annual_costs['pv_depreciation'].append(0)
            annual_costs['energy_storage_depreciation'].append(0)
            annual_costs['total_operating_cost'].append(0)
            annual_costs['wind_operating_cost'].append(0)
            annual_costs['pv_operating_cost'].append(0)
            annual_costs['energy_storage_operating_cost'].append(0)
            continue

        # 运营期计算
        # 计算年度折旧
        wind_depreciation = calculate_depreciation('wind', year, cumulative_depreciation)
        pv_depreciation = calculate_depreciation('pv', year, cumulative_depreciation)
        energy_storage_depreciation_0 = calculate_depreciation('energy_storage', year, cumulative_depreciation)
        energy_storage_depreciation_1 = calculate_storage_replacement_depreciation('energy_storage_1', year, cumulative_depreciation)
        energy_storage_depreciation_2 = calculate_storage_replacement_depreciation('energy_storage_2', year, cumulative_depreciation)
        energy_storage_depreciation = energy_storage_depreciation_0 +\
                                      energy_storage_depreciation_1 +\
                                      energy_storage_depreciation_2
        

        # 更新累计折旧
        cumulative_depreciation['wind'] += wind_depreciation
        cumulative_depreciation['pv'] += pv_depreciation
        cumulative_depreciation['energy_storage'] += energy_storage_depreciation
        cumulative_depreciation['energy_storage_0'] += energy_storage_depreciation_0
        cumulative_depreciation['energy_storage_1'] += energy_storage_depreciation_1
        cumulative_depreciation['energy_storage_2'] += energy_storage_depreciation_2
        
        # 计算年度经营成本
        wind_operating_cost = calculate_operating_costs('wind', year)
        pv_operating_cost = calculate_operating_costs('pv', year)
        energy_storage_operating_cost = calculate_operating_costs('energy_storage', year)
        
        # 存储本年数据
        annual_costs['wind_depreciation'].append(wind_depreciation)
        annual_costs['pv_depreciation'].append(pv_depreciation)
        annual_costs['energy_storage_depreciation'].append(energy_storage_depreciation)
        annual_costs['total_depreciation'].append(wind_depreciation + pv_depreciation + energy_storage_depreciation)

        annual_costs['wind_operating_cost'].append(wind_operating_cost)
        annual_costs['pv_operating_cost'].append(pv_operating_cost)
        annual_costs['energy_storage_operating_cost'].append(energy_storage_operating_cost)
        annual_costs['total_operating_cost'].append(wind_operating_cost + pv_operating_cost + energy_storage_operating_cost)
        
    return annual_costs

# 示例：如何调用并打印结果
if __name__ == '__main__':
    cost_data = get_annual_cost_statement(total_years=26)

    print("总成本费用表 (万元)")
    print("-" * 60)
    print("年份 | 总折旧 | 风电折旧 | 光伏折旧 | 储能折旧 | 总经营成本")
    for year, (total_d, wind_d, pv_d, es_d, total_o) in enumerate(zip(
        cost_data['total_depreciation'],
        cost_data['wind_depreciation'],
        cost_data['pv_depreciation'],
        cost_data['energy_storage_depreciation'],
        cost_data['total_operating_cost']
    ), 1):
        print(
            f"年{year:<2} | {total_d:<6.2f} | {wind_d:<8.2f} | {pv_d:<8.2f} | {es_d:<8.2f} | {total_o:<12.2f}")
