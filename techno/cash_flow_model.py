# 导入所需的参数和数据
from project_parameters import (
    PROJECT_SCALE,
    OPERATION_YEARS,
    INVESTMENT_PARAMS,
    INVESTMENT_RESULTS,
    DEPRECIATION_RATES,
    SALVAGE_RATES,
    REPAYMENT_METHOD,
    TAX_RATES,
    OPERATING_COST_PARAMS
)
from cost_model import get_annual_cost_statement
from revenue_model import calculate_annual_profit_statement

def calculate_annual_cash_inflow(total_years=26):
    """
    计算并返回每年的现金流入。

    Args:
        total_years (int): 需要计算的总年数，包括建设期。

    Returns:
        dict: 包含各年度现金流入分项数据的字典。
    """
    # 获取年度收入和成本数据，这些数据已在其他模型中计算好
    annual_profit_data = calculate_annual_profit_statement(total_years)
    
    # 初始化现金流入数据结构
    cash_inflow = {
        'total_cash_inflow': [],        # 现金流入 C135
        'sales_revenue_with_vat': [], # 1.1 销售收入（含增值税） C138
        'other_income': [], # 1.2 营业外收入 C139
        'salvage_value': [], # 1.3 回收固定资产余值 C140
        'working_capital_recovery': [] # 1.4 回收流动资金 C141
    }
    
    # 逐年计算
    for year in range(1, total_years + 1):
        # 统一将所有现金流入项初始化为0
        yearly_sales_revenue_with_vat = 0
        yearly_other_income = 0
        yearly_salvage_value = 0
        yearly_working_capital_recovery = 0

        # --- 1.1 销售收入（含增值税） ---
        # 对应 Excel C138
        # D104 (销售收入不含税) + D105 (增值税销项税额)
        yearly_sales_revenue_with_vat = annual_profit_data['sales_revenue_without_vat'][year - 1] + \
                                        annual_profit_data['vat'][year - 1]
        
        # --- 1.2 营业外收入（风电增值税减半返还收入） ---
        # 对应 Excel C139
        # 计算!D113*(1+计算!$C$51)
        yearly_other_income = annual_profit_data['wind_vat_rebate_income'][year - 1] * (1 + TAX_RATES['vat_rate'])
        
        # --- 1.3 回收固定资产余值 ---
        # 对应 Excel C140
        # IF(D134=($C$41+1),计算!$C$69*$H$17,0)+...
        # 仅在运营年限结束后的第一年发生回收
        if year == OPERATION_YEARS['wind'] + 1:
            # 回收风电部分
            yearly_salvage_value += SALVAGE_RATES['wind_salvage_rate'] * INVESTMENT_RESULTS['wind_fixed_asset_original_value']
        
        if year == OPERATION_YEARS['pv'] + 1:
            # 回收光伏部分
            yearly_salvage_value += SALVAGE_RATES['pv_salvage_rate'] * INVESTMENT_RESULTS['pv_fixed_asset_original_value']

        if year == OPERATION_YEARS['energy_storage'] + 1:
            # 回收储能部分
            yearly_salvage_value += SALVAGE_RATES['energy_storage_salvage_rate'] * INVESTMENT_RESULTS['energy_storage_fixed_asset_original_value']

        # --- 1.4 回收流动资金 ---
        # 对应 Excel C141
        # IF(D134=($C$41+1),$C$3*$C$14/10,0)+...
        # 在风电和光伏运营期结束时回收
        if year == OPERATION_YEARS['wind'] + 1:
            yearly_working_capital_recovery = INVESTMENT_PARAMS['working_capital_per_kw'] * PROJECT_SCALE['wind_mw'] / 10
        if year == OPERATION_YEARS['pv'] + 1:
            yearly_working_capital_recovery = yearly_working_capital_recovery + INVESTMENT_PARAMS['working_capital_per_kw'] * PROJECT_SCALE['pv_mw'] / 10
        # 将计算结果存储到字典中
        cash_inflow['sales_revenue_with_vat'].append(yearly_sales_revenue_with_vat)
        cash_inflow['other_income'].append(yearly_other_income)
        cash_inflow['salvage_value'].append(yearly_salvage_value)
        cash_inflow['working_capital_recovery'].append(yearly_working_capital_recovery)
        
        # 计算年度总现金流入
        total_inflow = yearly_sales_revenue_with_vat + yearly_other_income + \
                       yearly_salvage_value + yearly_working_capital_recovery
        cash_inflow['total_cash_inflow'].append(total_inflow)

    return cash_inflow
    
def calculate_annual_cash_outflow(total_years=26):
    """
    计算并返回每年的现金流出。
    
    Args:
        total_years (int): 需要计算的总年数，包括建设期。
        
    Returns:
        dict: 包含各年度现金流出分项数据的字典。
    """
    # 获取年度收入和成本数据
    annual_profit_data = calculate_annual_profit_statement(total_years)
    annual_cost_data = get_annual_cost_statement(total_years)
    
    # 初始化现金流出数据结构
    cash_outflow = {
        'construction_investment': [], # 2.1 建设投资 C143
        'working_capital': [], # 2.2 流动资金 C144
        'operating_costs': [], # 2.3 经营成本 C145
        'sales_tax_surcharge': [], # 2.4 销售税金及附加 C146
        'vat': [], # 2.5 增值税 C147
        'income_tax_adjustment': [], # 2.6 调整所得税 C148
        'maintenance_investment': [] # 2.7 维持运营投资 C149
    }

    for year in range(1, total_years + 1):
        # 统一将所有现金流出项初始化为0
        yearly_construction_investment = 0
        yearly_working_capital = 0
        yearly_operating_costs = 0
        yearly_sales_tax_surcharge = 0
        yearly_vat = 0
        yearly_income_tax_adjustment = 0
        yearly_maintenance_investment = 0
        
        # --- 2.1 建设投资 ---
        # 对应 Excel C143, 仅在项目第一年发生
        # H10
        if year == 1:
            yearly_construction_investment = INVESTMENT_RESULTS['total_project_investment']
            
        # --- 2.2 流动资金 ---
        # 对应 Excel C144, 运营期第一年（项目第二年）投入
        # H15
        if year == 2:
            yearly_working_capital = INVESTMENT_RESULTS['working_capital']
            
        # --- 2.3 经营成本 ---
        # 对应 Excel C145
        # D87
        yearly_operating_costs = annual_cost_data['total_operating_cost'][year - 1]
        
        # --- 2.4 销售税金及附加 ---
        # 对应 Excel C146
        # 计算!D111
        yearly_sales_tax_surcharge = annual_profit_data['sales_tax_surcharge'][year - 1]
        
        # --- 2.5 增值税 ---
        # 对应 Excel C147
        # D110
        yearly_vat = annual_profit_data['actual_vat_paid'][year - 1]
        
        # --- 2.6 调整所得税 ---
        # 对应 Excel C148
        # 计算!D129, 此处暂时用占位符
        yearly_income_tax_adjustment = 0 # 后续代码进行计算
        
        # --- 2.7 维持运营投资 ---
        # 对应 Excel C149
        # 仅在设备更换年份发生
        replacement_year = OPERATING_COST_PARAMS['equipment_replacement_year']
        replacement_S_year = OPERATING_COST_PARAMS['equipment_replacement_S_year']
        if year == replacement_year :
            yearly_maintenance_investment = OPERATING_COST_PARAMS['equipment_replacement_unit_price_per_wh'] * \
                                            PROJECT_SCALE['energy_storage_mwh'] * 100
        if year == replacement_S_year :
            yearly_maintenance_investment = yearly_maintenance_investment + OPERATING_COST_PARAMS['equipment_replacement_unit_price_per_wh'] * \
                                            PROJECT_SCALE['energy_storage_mwh'] * 100

        # 将计算结果存储到字典中
        cash_outflow['construction_investment'].append(yearly_construction_investment)
        cash_outflow['working_capital'].append(yearly_working_capital)
        cash_outflow['operating_costs'].append(yearly_operating_costs)
        cash_outflow['sales_tax_surcharge'].append(yearly_sales_tax_surcharge)
        cash_outflow['vat'].append(yearly_vat)
        cash_outflow['income_tax_adjustment'].append(yearly_income_tax_adjustment)
        cash_outflow['maintenance_investment'].append(yearly_maintenance_investment)
        
    return cash_outflow

if __name__ == '__main__':
    total_years = OPERATION_YEARS['pv'] + 1 # 项目总年限，包括1年建设期
    
    cash_inflow_data = calculate_annual_cash_inflow(total_years)
    cash_outflow_data = calculate_annual_cash_outflow(total_years)
    
    # 打印现金流入表
    print("项目财务现金流量表 - 现金流入 (万元)")
    print("-" * 100)
    print(f"{'年份':<4} | {'总现金流入':<10} | {'销售收入(含税)':<15} | {'营业外收入':<10} | {'回收余值':<10} | {'回收流动资金':<15}")
    for year in range(total_years):
        print(
            f"年{year+1:<2} | "
            f"{cash_inflow_data['total_cash_inflow'][year]:<12.2f} | "
            f"{cash_inflow_data['sales_revenue_with_vat'][year]:<15.2f} | "
            f"{cash_inflow_data['other_income'][year]:<12.2f} | "
            f"{cash_inflow_data['salvage_value'][year]:<10.2f} | "
            f"{cash_inflow_data['working_capital_recovery'][year]:<15.2f}"
        )
    print("\n")
    
    # 打印现金流出表
    print("项目财务现金流量表 - 现金流出 (万元)")
    print("-" * 120)
    print(f"{'年份':<4} | {'建设投资':<10} | {'流动资金':<10} | {'经营成本':<10} | {'销售税金及附加':<15} | {'增值税':<10} | {'所得税':<10} | {'维持运营投资':<15}")
    for year in range(total_years):
        print(
            f"年{year+1:<2} | "
            f"{cash_outflow_data['construction_investment'][year]:<12.2f} | "
            f"{cash_outflow_data['working_capital'][year]:<10.2f} | "
            f"{cash_outflow_data['operating_costs'][year]:<12.2f} | "
            f"{cash_outflow_data['sales_tax_surcharge'][year]:<15.2f} | "
            f"{cash_outflow_data['vat'][year]:<10.2f} | "
            f"{cash_outflow_data['income_tax_adjustment'][year]:<10.2f} | "
            f"{cash_outflow_data['maintenance_investment'][year]:<15.2f}"
        )
