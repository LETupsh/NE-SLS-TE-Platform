# 导入所需的参数和数据
from project_parameters import (
    INVESTMENT_PARAMS,
    INVESTMENT_RESULTS
)
from cash_flow_model import calculate_annual_cash_inflow, calculate_annual_cash_outflow
from loan_repayment_summary_model import calculate_loan_repayment_plan

def calculate_capital_cash_inflow(total_years=26):
    """
    计算并返回每年的资本金财务现金流入。

    Args:
        total_years (int): 需要计算的总年数，包括建设期。

    Returns:
        dict: 包含各年度现金流入分项数据的字典。
    """
    # 引用项目财务现金流量表中的数据
    project_cash_flow_in = calculate_annual_cash_inflow(total_years)

    # 初始化资本金现金流入数据结构
    capital_inflow = {
        'total_capital_inflow': [],    #1 现金流入 C168
        'sales_revenue_with_vat': [],  # 1.1 销售收入（含增值税），对应 Excel C171
        'other_income': [],            # 1.2 营业外收入，对应 Excel C172
        'salvage_value': [],           # 1.3 回收固定资产余值，对应 Excel C173
        'working_capital_recovery': [] # 1.4 回收流动资金，对应 Excel C174
    }

    # 直接引用项目现金流量表中的计算结果
    capital_inflow['sales_revenue_with_vat'] = project_cash_flow_in['sales_revenue_with_vat']
    capital_inflow['other_income'] = project_cash_flow_in['other_income']
    capital_inflow['salvage_value'] = project_cash_flow_in['salvage_value']
    capital_inflow['working_capital_recovery'] = project_cash_flow_in['working_capital_recovery']
    
    # 计算年度总现金流入
    for year in range(total_years):
        total_inflow = (
            capital_inflow['sales_revenue_with_vat'][year] +
            capital_inflow['other_income'][year] +
            capital_inflow['salvage_value'][year] +
            capital_inflow['working_capital_recovery'][year]
        )
        capital_inflow['total_capital_inflow'].append(total_inflow)
    
    return capital_inflow

def calculate_capital_cash_outflow(total_years=26):
    """
    计算并返回每年的资本金财务现金流出。

    Args:
        total_years (int): 需要计算的总年数。

    Returns:
        dict: 包含各年度现金流出分项数据的字典。
    """
    # 获取所需的外部数据
    project_cash_flow_out = calculate_annual_cash_outflow(total_years)
    loan_repayment_plan = calculate_loan_repayment_plan()
    
    # 初始化资本金现金流出数据结构
    capital_outflow = {
        'capital_investment': [],             # 2.1 项目资本金，对应 Excel C176
        'self_owned_working_capital': [],     # 2.2 流动资金中自有资金，对应 Excel C177
        'foreign_loan_principal_repayment': [], # 2.3 国外借款本金偿还，对应 Excel C178
        'domestic_loan_principal_repayment': [], # 2.4 国内借款本金偿还，对应 Excel C179
        'foreign_loan_interest_payment': [],   # 2.5 国外借款利息支付，对应 Excel C180
        'operating_costs': [],                # 经营成本
        'sales_tax_surcharge': [],            # 销售税金及附加
        'vat': [],                            # 增值税
        'income_tax_adjustment': [],          # 调整所得税
        'maintenance_investment': []          # 维持运营投资
    }

    for year in range(1, total_years + 1):
        # 统一将所有现金流出项初始化为0
        yearly_capital_investment = 0
        yearly_self_owned_working_capital = 0
        yearly_foreign_loan_principal = 0
        yearly_domestic_loan_principal = 0
        yearly_foreign_loan_interest = 0
        
        # --- 2.1 项目资本金 ---
        # 对应 Excel C176。H13 * C11
        # 仅在项目第一年（建设期）投入
        if year == 1:
            yearly_capital_investment = INVESTMENT_RESULTS['dynamic_total_investment'] * INVESTMENT_PARAMS['capital_ratio']
        
        # --- 2.2 流动资金中自有资金 ---
        # 对应 Excel C177。H15 * C15
        # 仅在运营期第一年（项目第二年）投入
        if year == 2:
            yearly_self_owned_working_capital = INVESTMENT_RESULTS['working_capital'] * INVESTMENT_PARAMS['self_owned_working_capital_ratio']

        # --- 2.3 国外借款本金偿还 ---
        # 对应 Excel C178。您提供的表格显示为0。
        yearly_foreign_loan_principal = 0
        
        # --- 2.4 国内借款本金偿还 ---
        # 对应 Excel C179。D245
        # 引用 loan_model.py 的计算结果
        yearly_domestic_loan_principal = loan_repayment_plan['yearly_principal_repayment'][year - 1]
        
        # --- 2.5 国外借款利息支付 ---
        # 对应 Excel C180。您提供的表格显示为0。
        yearly_foreign_loan_interest = 0
        
        # 将计算结果存储到字典中
        capital_outflow['capital_investment'].append(yearly_capital_investment)
        capital_outflow['self_owned_working_capital'].append(yearly_self_owned_working_capital)
        capital_outflow['foreign_loan_principal_repayment'].append(yearly_foreign_loan_principal)
        capital_outflow['domestic_loan_principal_repayment'].append(yearly_domestic_loan_principal)
        capital_outflow['foreign_loan_interest_payment'].append(yearly_foreign_loan_interest)
        
    # 直接引用项目现金流出表中已计算的数据
    capital_outflow['operating_costs'] = project_cash_flow_out['operating_costs']
    capital_outflow['sales_tax_surcharge'] = project_cash_flow_out['sales_tax_surcharge']
    capital_outflow['vat'] = project_cash_flow_out['vat']
    capital_outflow['income_tax_adjustment'] = project_cash_flow_out['income_tax_adjustment']
    capital_outflow['maintenance_investment'] = project_cash_flow_out['maintenance_investment']    
    return capital_outflow


if __name__ == '__main__':
    # 假设项目运营20年，加上1年建设期，总共21年
    total_project_years = 21

    cash_inflow_data = calculate_capital_cash_inflow(total_project_years)
    cash_outflow_data = calculate_capital_cash_outflow(total_project_years)
    
    # 打印资本金现金流入表
    print("资本金财务现金流量表 - 现金流入 (万元)")
    print("-" * 100)
    print(f"{'年份':<4} | {'总现金流入':<10} | {'销售收入(含税)':<15} | {'营业外收入':<10} | {'回收余值':<10} | {'回收流动资金':<15}")
    for year in range(total_project_years):
        print(
            f"年{year+1:<2} | "
            f"{cash_inflow_data['total_capital_inflow'][year]:<12.2f} | "
            f"{cash_inflow_data['sales_revenue_with_vat'][year]:<15.2f} | "
            f"{cash_inflow_data['other_income'][year]:<12.2f} | "
            f"{cash_inflow_data['salvage_value'][year]:<10.2f} | "
            f"{cash_inflow_data['working_capital_recovery'][year]:<15.2f}"
        )
    
    print("\n")
    
    # 打印资本金现金流出表
    print("资本金财务现金流量表 - 现金流出 (万元)")
    print("-" * 120)
    print(f"{'年份':<4} | {'总现金流出':<10} | {'项目资本金':<10} | {'自有流动资金':<15} | {'国内借款还本':<15} | {'经营成本':<10} | {'维持运营投资':<15}")
    for year in range(total_project_years):
        print(
            f"年{year+1:<2} | "
            f"{cash_outflow_data['capital_investment'][year]:<12.2f} | "
            f"{cash_outflow_data['self_owned_working_capital'][year]:<15.2f} | "
            f"{cash_outflow_data['domestic_loan_principal_repayment'][year]:<15.2f} | "
            f"{cash_outflow_data['operating_costs'][year]:<10.2f} | "
            f"{cash_outflow_data['maintenance_investment'][year]:<15.2f}"
        )
