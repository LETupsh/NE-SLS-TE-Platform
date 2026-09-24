# 导入所需的参数和数据
from project_parameters import (
    INVESTMENT_PARAMS,
    INVESTMENT_RESULTS,
    PROJECT_SCALE,
    OPERATION_YEARS,
    SELLING_PRICE_PARAMS
)
from revenue_model import calculate_annual_profit_statement
from cost_model import get_annual_cost_statement
from cash_flow_model import calculate_annual_cash_inflow, calculate_annual_cash_outflow
from loan_repayment_summary_model import calculate_loan_repayment_summary
from capital_cash_flow_model import calculate_capital_cash_inflow,calculate_capital_cash_outflow
import numpy as np
import numpy_financial as npf

def get_financial_plan_cash_flow(total_years=26):
    """
    计算并返回财务计划现金流量表的各年度分项数据。
    本文件已包含短期贷款的计算逻辑。
    
    Args:
        total_years (int): 需要计算的总年数。
        
    Returns:
        dict: 包含各年度现金流量分项数据的字典。
    """
    # 获取所有需要的外部数据
    annual_profit_data = calculate_annual_profit_statement(total_years)
    annual_cost_data = get_annual_cost_statement(total_years)
    project_cash_inflow_data = calculate_annual_cash_inflow(total_years)
    project_cash_outflow_data = calculate_annual_cash_outflow(total_years)
    loan_repayment_data = calculate_loan_repayment_summary(total_years)
    capital_cash_inflow_data = calculate_capital_cash_inflow(total_years)
    capital_cash_outflow_data = calculate_capital_cash_outflow(total_years)

    # 初始化数据结构
    cash_flow_statement = {
        'operating_cash_flow': {
            'net_cash_flow_from_operations':[], # C251 经营活动净现金流量(1.1-1.2)
            'total_inflow':[],          #1.1 C252 现金流入
            'revenue_without_vat': [],  # 1.1.1 销售收入（不含增值税） C253
            'vat_output': [],           # 1.1.2 增值税销项税额 C254
            'other_income': [],         # 1.1.3 营业外收入 C255
            'other_inflow': [],         # 1.1.4 其他流入 C256
            'working_capital_recovery': [], # 1.1.5 回收流动资金 C257
            'financial_plan_total_outflow': [], #1.2 现金流出 C258
            'operating_costs': [],      # 1.2.1 经营成本 C259
            'vat_input': [],            # 1.2.2 增值税进项税额 C260
            'sales_tax_surcharge': [],  # 1.2.3 营业税金及附加 C261
            'vat': [],                  # 1.2.4 增值税 C262
            'other_outflow_op': [],     # 1.2.6 其他流出 C264
            'total_profit': [],         # C114：利润总额
            'loss': [],                 # C126：亏损
            'loss_make_up': [],         # C116：弥补亏损（5年以内）
            'loss_carry_forward_next_year': [],     # D115：下一年可弥补亏损
            'income_tax': [],           # C118: 所得税
            'adjusted_income_tax':[],   # C129: 调整所得税
            'total_cash_outflow': [],   # C142: 现金流出(项目财务流量)
            'capital_cash_outflow': [], # C175 现金流出（资本金流量）
            'initial_investment_cal': [],   # C202 初始投资计算流
            'annual_operating_cost_cal': [],# C204 每年经营成本计算流
            'annual_taxes_cal': []      # C207 税费成本计算流
        },
        'investment_cash_flow': {
            # 新增的投资活动净现金流量
            'net_investment_cash_flow': [], # 2. 投资活动净现金流量 C265
            'fixed_asset_salvage': [],  # 2.1.1 回收固定资产余值 C267
            'construction_investment': [], # 2.2.1 建设投资 C269
            'maintenance_investment': [],  # 2.2.2 维持运营投资 C270
            'working_capital': [],      # 2.2.3 流动资金 C271
            'other_outflow_inv': [],    # 2.2.4 其他流出 C272
        },
        'financing_cash_flow': {
            'equity_capital': [],       # 3.1.1 项目资本金投入 C275
            'construction_loan': [],    # 3.1.2 建设投资借款 C276
            'working_capital_loan': [], # 3.1.3 流动资金借款 C277
            'bonds': [],                # 3.1.4 债券 C278
            'other_inflow_fin': [],     # 3.1.6 其他流入 C280
            'total_cash_outflow_fin': [],   # 3.2 现金流出 C281 (新增)
            'interest_expense': [],     # 3.2.1 各种利息支出 C282
            'debt_principal_repayment': [], # 3.2.2 偿还债务本金 C283
            'other_outflow_fin': [],    # 3.2.4 其他流出 C284
            'net_cash_flow':[],         # 净现金流量（1+2+3） C285  
        },
        # 流动资金贷款数据结构
        'working_capital_loan_flow': {
            'WC_loan_limit': [], # C232：流动资金贷款额度
            'WC_loan_repayment': [], # C233：流动资金偿还
            'short_term_loan_interest': [] # C234：流动资金借款利息
        },
        # 短期贷款相关参数
        'short_term_loan': {
            'short_term_loan_amount': [],           # 3.1 短期贷款额度 (C227\C279)
            'short_term_loan_cumulative': [],       # 3.2 短期贷款累计 (C228)
            'short_term_loan_interest': [],         # 3.3 短期贷款利息 (C229)
            'short_term_loan_repayment': []         # 3.4 短期贷款偿还 (C230)
        },
        # 短期贷款利息和总成本费用数据结构
        'cost_and_profit': {
            'total_interest_expense': [], # C91：利息支出
            'total_cost_and_expenses': [] # C95：总成本费用
        },
        # 最终财务指标
        'final_project_metrics': {
            'project_post_tax_net_cash_flow': [],   # C150 净现金流量 (项目税后)
            'project_cumulative_net_cash_flow': [], # C151 累计净现金流量 (项目税后)
            'project_pre_tax_net_cash_flow': [],    # D159 净现金流量（项目税前）
            'project_pre_tax_cumulative_net_cash_flow': [],  #D160 累计净现金流量（项目税前）
            'capital_net_cash_flow': [],            # C189 净现金流（资本金税后）
            'capital_cumulative_net_cash_flow': [], # C189 累计净现金流（资本金税后）
            'capital_pre_tax_net_cash_flow': [],    # D197 净现金流（资本金税前）
            'capital_pre_tax_cumulative_net_cash_flow': [],  #D198 累计净现金流（资本金税前）
            'P_post_irr_result': 0, #项目税后IRR
            'P_post_npv_result': 0, #项目税后NPV
            'P_post_payback_period': 0, #项目税后回收期
            'P_pre_irr_result': 0,   #项目税前IRR
            'P_pre_npv_result': 0,   #项目税前NPV
            'P_pre_payback_period': 0,   #项目税前回收期
            'C_post_irr_result': 0, #资本金税后IRR
            'C_post_npv_result': 0, #资本金税后NPV
            'C_post_payback_period': 0, #资本金税后回收期
            'C_pre_irr_result': 0,  #资本金税前IRR
            'C_pre_npv_result': 0,  #资本金税前NPV
            'C_pre_payback_period': 0,  #资本金税前回收期
            'LOCE': 0,  #度电成本
            'G_LCOE': 0 #广义度电成本
        },
        # 新增外部数据
        'external_data': {
            'annual_profit_data': annual_profit_data,
            'annual_cost_data': annual_cost_data,
            'project_cash_inflow_data': project_cash_inflow_data,
            'project_cash_outflow_data': project_cash_outflow_data,
            'loan_repayment_data': loan_repayment_data,
            'capital_cash_inflow_data': capital_cash_inflow_data,
            'capital_cash_outflow_data': capital_cash_outflow_data,
            'INVESTMENT_PARAMS': INVESTMENT_PARAMS,
            'INVESTMENT_RESULTS': INVESTMENT_RESULTS
        }
    }
    # 用于跟踪年度亏损的私有列表，以便进行5年结转
    _annual_losses_to_carry_forward = []

    # 初始化累计值
    short_term_loan_cumulative = 0.0
    total_interest_expense = 0.0
    total_cost_and_expenses = 0.0
    total_profit = 0.0
    loss = 0.0
    loss_make_up = 0.0
    loss_carry_forward = 0.0
    income_tax = 0.0
    yearly_short_term_loan_amount = 0.0
    yearly_short_term_loan_repayment = 0.0
    yearly_short_term_loan_interest = 0.0
    short_term_loan_cumulative = 0.0
    yearly_working_capital_loan_amount = 0.0
    yearly_working_capital_repayment = 0.0
    vat_input= 0.0

    # 逐年计算各分项数据
    for year in range(total_years):
        
        # --- 1. 经营活动现金流量 ---
        cash_flow_statement['operating_cash_flow']['revenue_without_vat'].append(annual_profit_data['sales_revenue_without_vat'][year])
        cash_flow_statement['operating_cash_flow']['vat_output'].append(annual_profit_data['vat'][year])
        cash_flow_statement['operating_cash_flow']['other_income'].append(annual_profit_data['wind_vat_rebate_income'][year])
        cash_flow_statement['operating_cash_flow']['other_inflow'].append(0)
        cash_flow_statement['operating_cash_flow']['working_capital_recovery'].append(project_cash_inflow_data['working_capital_recovery'][year])
        cash_flow_statement['operating_cash_flow']['operating_costs'].append(annual_cost_data['total_operating_cost'][year])
        cash_flow_statement['operating_cash_flow']['vat_input'].append(vat_input)
        cash_flow_statement['operating_cash_flow']['sales_tax_surcharge'].append(annual_profit_data['sales_tax_surcharge'][year])
        cash_flow_statement['operating_cash_flow']['vat'].append(annual_profit_data['actual_vat_paid'][year])
        cash_flow_statement['operating_cash_flow']['other_outflow_op'].append(0)

        # --- 2. 投资活动现金流量 ---
        fixed_asset_salvage = project_cash_inflow_data['salvage_value'][year]
        construction_investment = project_cash_outflow_data['construction_investment'][year]
        maintenance_investment = project_cash_outflow_data['maintenance_investment'][year]
        working_capital = project_cash_outflow_data['working_capital'][year]
        other_outflow_inv = 0
        
        cash_flow_statement['investment_cash_flow']['fixed_asset_salvage'].append(fixed_asset_salvage)
        cash_flow_statement['investment_cash_flow']['construction_investment'].append(construction_investment)
        cash_flow_statement['investment_cash_flow']['maintenance_investment'].append(maintenance_investment)
        cash_flow_statement['investment_cash_flow']['working_capital'].append(working_capital)
        cash_flow_statement['investment_cash_flow']['other_outflow_inv'].append(other_outflow_inv)
        
        # 2. 投资活动净现金流量 (C265)
        total_inflow_inv = fixed_asset_salvage + other_outflow_inv
        total_outflow_inv = construction_investment + maintenance_investment + working_capital + other_outflow_inv
        net_investment_cash_flow = total_inflow_inv - total_outflow_inv
        cash_flow_statement['investment_cash_flow']['net_investment_cash_flow'].append(net_investment_cash_flow)

        # --- 3. 筹资活动现金流量 ---
        # 3.1.1 项目资本金投入 (C275)
        if year == 0:
            equity_capital = INVESTMENT_RESULTS['dynamic_total_investment'] * INVESTMENT_PARAMS['capital_ratio']
        elif year == 1:
            equity_capital = INVESTMENT_RESULTS['working_capital'] * INVESTMENT_PARAMS['self_owned_working_capital_ratio']
        else:
            equity_capital = 0
        
        # 3.1.2 建设投资借款 (C276)
        construction_loan = INVESTMENT_RESULTS['dynamic_total_investment'] - equity_capital if year == 0 else 0
        



        # --- 计算流动资金贷款相关的现金流 C232-C234---
        WC_loan_limit = 0.0
        WC_loan_repayment = 0.0
        interest = 0.0
        # 建设期（第1年）
        if year == 0:
            WC_loan_limit = 0.0
            WC_loan_repayment = 0.0
            interest = 0.0
        # 运营期第1年以后
        else:
            # 流动资金贷款额度 = 流动资金总额 * (1 - 自有流动资金比例)
            working_capital_per_kw = INVESTMENT_PARAMS['working_capital_per_kw']
            self_owned_ratio = INVESTMENT_PARAMS['self_owned_working_capital_ratio']
            if year < OPERATION_YEARS['wind'] + 1:
                WC_loan_limit += PROJECT_SCALE['wind_mw'] * INVESTMENT_PARAMS['working_capital_per_kw'] /10 * (1 - self_owned_ratio)
            if year < OPERATION_YEARS['pv'] + 1:
                WC_loan_limit += PROJECT_SCALE['pv_mw'] * INVESTMENT_PARAMS['working_capital_per_kw'] /10 * (1 - self_owned_ratio)
           
            # 流动资金借款利息 = 贷款额度 * 贷款利率
            interest = WC_loan_limit * INVESTMENT_PARAMS['short_term_loan_rate_repayment']
            WC_loan_repayment = WC_loan_limit
            
        # 3.1.3 流动资金借款 (C277)/流动资金贷款额度
        yearly_working_capital_loan_amount = WC_loan_limit
        yearly_working_capital_repayment = WC_loan_repayment


        # 3.1.4 债券 (C278)
        bonds = 0

        # 3.1.6 其他流入 (C280)
        other_inflow_fin = 0
        
        # 3.2.1 各种利息支出 (C282)
        # 包含长期贷款利息、流动资金借款利息和短期贷款利息
        yearly_interest_payment = loan_repayment_data['yearly_accrued_interest'][year]
        yearly_working_capital_interest = yearly_working_capital_loan_amount * INVESTMENT_PARAMS['short_term_loan_rate_repayment']


        # 3.2.4 其他流出 (C284)
        other_outflow_fin = 0


        # C91：总利息支出 = 长期贷款利息D92 + 短期贷款利息 + 流动资金借款利息D234
        if year>0:
            yearly_short_term_loan_interest = cash_flow_statement['short_term_loan']['short_term_loan_amount'][year-1] * INVESTMENT_PARAMS['short_term_loan_rate_repayment']
        total_interest_expense = loan_repayment_data['yearly_interest_payment'][year] + \
                                 yearly_short_term_loan_interest + interest

        # C95：总成本费用 = 折旧费 + 经营成本 + 利息支出  折旧费（D83）和经营成本（D87）来自 cost_model
        total_depreciation = annual_cost_data['total_depreciation'][year]
        total_operating_cost = annual_cost_data['total_operating_cost'][year]
        total_cost_and_expenses = total_depreciation + \
                                  total_operating_cost + \
                                  total_interest_expense

        # C114：利润总额 = 销售收入（不含增值税）- 销售税金附加 - 总成本费用 + 营业外收入
        # 销售收入（D104），销售税金附加（D111），营业外收入（D113）来自 revenue_model
        revenue_without_vat = annual_profit_data['sales_revenue_without_vat'][year]
        sales_tax_surcharge = annual_profit_data['sales_tax_surcharge'][year]
        wind_vat_rebate_income = annual_profit_data['wind_vat_rebate_income'][year]
        total_profit = revenue_without_vat - \
                           sales_tax_surcharge - \
                           total_cost_and_expenses + \
                           wind_vat_rebate_income

        # C126：亏损 = IF(D114<0, D114, 0)
        # 只有当利润总额小于0时，才产生亏损，否则为0
        if total_profit < 0:
            loss = total_profit
        else:
            loss = 0.0
        cash_flow_statement['operating_cash_flow']['loss'].append(loss)

        # C116：弥补亏损（5年以内）
        # 只有当利润总额大于0，且上一年有可弥补亏损时，才会进行弥补
        # 上一年可弥补亏损
        if year == 0:
            previous_loss_carry_forward =0
        else:
            previous_loss_carry_forward = cash_flow_statement['operating_cash_flow']['loss_carry_forward_next_year'][year-1]
        
        # 如果本年有利润且上一年有亏损可弥补
        if total_profit > 0 and previous_loss_carry_forward < 0:
            # 弥补亏损 = min(本年利润总额, -上一年可弥补亏损)
            # 等同于 Excel 中的 IF(E114+D115<0, E114, -D115)
            loss_make_up = min(total_profit, -previous_loss_carry_forward)
        else:
            loss_make_up = 0
        cash_flow_statement['operating_cash_flow']['loss_make_up'].append(loss_make_up)
        
        # C115：下一年可弥补亏损
        # 建设期（第1年）
        if year == 0:
            loss_carry_forward = cash_flow_statement['operating_cash_flow']['loss_make_up'][0] + cash_flow_statement['operating_cash_flow']['loss'][0]
        # 运营期1-5年（第2-6年）
        elif year > 0 and year <= 5:
            # 公式：上一年弥补亏损 + 上一年亏损 + 上一年可弥补亏损
            # 这里用本年数据计算，实际上是累加本年新发生的亏损和弥补情况
            loss_carry_forward = previous_loss_carry_forward + loss_make_up + loss
        # 运营期6年及以后（第7年及以后）
        else:
            # 倒推过去5年的亏损
            past_five_year_loss = sum(cash_flow_statement['operating_cash_flow']['loss'][year-4:year+1])
            # 公式：IF(J114<=0,SUM(F126:J126),IF(J114+I115>=0,0,IF(J114+E126<0,SUM(F126:J126),I115+J114)))
            # 简化逻辑：如果本年利润总额小于等于0，下一年可弥补亏损为过去五年的亏损总和
            if total_profit <= 0:
                loss_carry_forward = past_five_year_loss
            # 如果本年利润总额大于0
            else:
                # 如果本年利润能完全弥补上一年亏损，下一年可弥补亏损为0
                if total_profit + previous_loss_carry_forward >= 0:
                    loss_carry_forward = 0
                # 如果不能，则剩余亏损结转到下一年
                else:
                    loss_carry_forward = total_profit + previous_loss_carry_forward

        # --- 计算所得税（C118） ---
        # 应纳税所得额 = 利润总额 - 弥补亏损
        taxable_income = total_profit - loss_make_up
        if taxable_income > 0:
            # 获取本年适用的所得税率
            income_tax = taxable_income * annual_profit_data['income_tax_rate'][year]
        else:
            income_tax = 0.0
        cash_flow_statement['operating_cash_flow']['income_tax'].append(income_tax)

        #C252 现金流入
        total_inflow = cash_flow_statement['operating_cash_flow']['revenue_without_vat'][year] +\
                       cash_flow_statement['operating_cash_flow']['vat_output'][year] +\
                       cash_flow_statement['operating_cash_flow']['other_income'][year] +\
                       cash_flow_statement['operating_cash_flow']['other_inflow'][year] +\
                       cash_flow_statement['operating_cash_flow']['working_capital_recovery'][year]
        cash_flow_statement['operating_cash_flow']['total_inflow'].append(total_inflow)

        #C258 现金流出
        financial_plan_total_outflow = cash_flow_statement['operating_cash_flow']['vat_input'][year] + \
                                       cash_flow_statement['operating_cash_flow']['sales_tax_surcharge'][year] +\
                                       cash_flow_statement['operating_cash_flow']['vat'][year] +\
                                       cash_flow_statement['operating_cash_flow']['other_outflow_op'][year] +\
                                       cash_flow_statement['operating_cash_flow']['income_tax'][year] +\
                                       cash_flow_statement['operating_cash_flow']['operating_costs'][year]
        cash_flow_statement['operating_cash_flow']['financial_plan_total_outflow'].append(financial_plan_total_outflow)

        #C251 经营活动净现金流量(1.1-1.2)
        net_cash_flow_from_operations = total_inflow - financial_plan_total_outflow
        cash_flow_statement['operating_cash_flow']['net_cash_flow_from_operations'].append(net_cash_flow_from_operations)


        # 3.2.1 各种利息支出 (C282) = 本年应计利息 + 流动贷款利息 
        interest_sum = loan_repayment_data['yearly_accrued_interest'][year] + \
                       interest
            
        # 3.2.2 偿还债务本金 (C283) = 长期还本 + 短期贷款偿还 + 流动资金偿还
        if year == 0:
            debt_principal_repayment = 0
        else:            
            debt_principal_repayment = loan_repayment_data['yearly_principal_repayment'][year] + \
                                        cash_flow_statement['short_term_loan']['short_term_loan_amount'][year-1] + \
                                        WC_loan_limit
        # 3.2 现金流出 (C281) = 各种利息支出 + 偿还债务本金 + 其他流出 (新增)
        total_cash_outflow_fin = interest_sum + debt_principal_repayment + other_outflow_fin

        # --- 短期贷款计算 ---          
        if year == 0:
            # 3.1 短期贷款额度 (C227\C279):    
            yearly_short_term_loan_amount_1 = net_cash_flow_from_operations +\
                                              net_investment_cash_flow +\
                                              equity_capital + construction_loan + yearly_working_capital_loan_amount + bonds + other_inflow_fin -\
                                              total_cash_outflow_fin
            if yearly_short_term_loan_amount_1 >= 0:
                yearly_short_term_loan_amount = 0
            else:
                yearly_short_term_loan_amount = -yearly_short_term_loan_amount_1  
            short_term_loan_cumulative = 0
            yearly_short_term_loan_interest = 0
            yearly_short_term_loan_repayment = 0
        else:
            # 3.1 短期贷款额度 (C227\C279):    
            yearly_short_term_loan_amount_1 = net_cash_flow_from_operations +\
                                            net_investment_cash_flow +\
                                            equity_capital + construction_loan + yearly_working_capital_loan_amount + bonds + other_inflow_fin -\
                                            total_cash_outflow_fin +\
                                            cash_flow_statement['financing_cash_flow']['net_cash_flow'][year-1]

            
            if yearly_short_term_loan_amount_1 >= 0:
                yearly_short_term_loan_amount = 0
            else:
                yearly_short_term_loan_amount = -yearly_short_term_loan_amount_1  
            # 3.2 短期贷款累计 (C228)
            short_term_loan_cumulative = cash_flow_statement['short_term_loan']['short_term_loan_cumulative'][year-1] +\
                                         yearly_short_term_loan_amount
            # 3.3 短期贷款利息 (C229)
            yearly_short_term_loan_interest = cash_flow_statement['short_term_loan']['short_term_loan_amount'][year-1] * INVESTMENT_PARAMS['short_term_loan_rate_repayment']
            
            # 3.4 短期贷款偿还 (C230)
            yearly_short_term_loan_repayment = cash_flow_statement['short_term_loan']['short_term_loan_amount'][year-1]

            
        #净现金流量（1+2+3） C285
        net_cash_flow = net_cash_flow_from_operations +\
                        net_investment_cash_flow +\
                        yearly_short_term_loan_amount + equity_capital + construction_loan + yearly_working_capital_loan_amount + bonds + other_inflow_fin -\
                        total_cash_outflow_fin
        
        if year > 0:
            net_cash_flow = net_cash_flow + cash_flow_statement['financing_cash_flow']['net_cash_flow'][year-1]
        cash_flow_statement['financing_cash_flow']['net_cash_flow'].append(net_cash_flow)

        #调整所得税 C129
        if year < 4:
            adjusted_income_tax = 0
        elif taxable_income + total_interest_expense < 0:
            adjusted_income_tax = 0
        else:
            adjusted_income_tax = (taxable_income + total_interest_expense) * annual_profit_data['income_tax_rate'][year]
        cash_flow_statement['operating_cash_flow']['adjusted_income_tax'].append(adjusted_income_tax)
            
        #最终计算——1、项目财务现金流量表
        #C142 现金流出
        total_cash_outflow = project_cash_outflow_data['construction_investment'][year]+\
                             project_cash_outflow_data['working_capital'][year]+\
                             project_cash_outflow_data['operating_costs'][year]+\
                             project_cash_outflow_data['sales_tax_surcharge'][year]+\
                             project_cash_outflow_data['vat'][year]+\
                             project_cash_outflow_data['maintenance_investment'][year]+\
                             adjusted_income_tax
        cash_flow_statement['operating_cash_flow']['total_cash_outflow'].append(total_cash_outflow)
        
        # C150 项目税后净现金流量\C151 项目累计净现金流量
        project_post_tax_net_cash_flow = project_cash_inflow_data['total_cash_inflow'][year] - total_cash_outflow
        if year == 0:
            project_cumulative_net_cash_flow = project_post_tax_net_cash_flow
        else:
            project_cumulative_net_cash_flow = project_post_tax_net_cash_flow + cash_flow_statement['final_project_metrics']['project_cumulative_net_cash_flow'][year-1]
        cash_flow_statement['final_project_metrics']['project_post_tax_net_cash_flow'].append(project_post_tax_net_cash_flow)
        cash_flow_statement['final_project_metrics']['project_cumulative_net_cash_flow'].append(project_cumulative_net_cash_flow)

        # D159 项目税前净现金流\D160 项目累计净现金流
        project_pre_tax_net_cash_flow = project_post_tax_net_cash_flow + adjusted_income_tax
        if year == 0:
            project_pre_tax_cumulative_net_cash_flow = project_pre_tax_net_cash_flow
        else:
            project_pre_tax_cumulative_net_cash_flow = project_pre_tax_net_cash_flow + cash_flow_statement['final_project_metrics']['project_pre_tax_cumulative_net_cash_flow'][year-1]
        cash_flow_statement['final_project_metrics']['project_pre_tax_net_cash_flow'].append(project_pre_tax_net_cash_flow)
        cash_flow_statement['final_project_metrics']['project_pre_tax_cumulative_net_cash_flow'].append(project_pre_tax_cumulative_net_cash_flow)

        #资本金现金流量表 现金流出 C175
        capital_cash_outflow = (capital_cash_outflow_data['capital_investment'][year] +\
                                capital_cash_outflow_data['self_owned_working_capital'][year] +\
                                capital_cash_outflow_data['foreign_loan_principal_repayment'][year] +\
                                capital_cash_outflow_data['domestic_loan_principal_repayment'][year] +\
                                capital_cash_outflow_data['foreign_loan_interest_payment'][year] +\
                                loan_repayment_data['yearly_interest_payment'][year] +\
                                interest +\
                                yearly_short_term_loan_interest +\
                                annual_cost_data['total_operating_cost'][year] +\
                                annual_profit_data['sales_tax_surcharge'][year] +\
                                annual_profit_data['actual_vat_paid'][year] +\
                                income_tax +\
                                project_cash_outflow_data['maintenance_investment'][year]
                                )
        cash_flow_statement['operating_cash_flow']['capital_cash_outflow'].append(capital_cash_outflow)                        

        #资本金现金流量 税后净现金流量 CI-CO C189\ 累计净现金流量 C190
        capital_net_cash_flow = capital_cash_inflow_data['total_capital_inflow'][year] - capital_cash_outflow
        if year == 0:
            capital_cumulative_net_cash_flow = capital_net_cash_flow
        else:
            capital_cumulative_net_cash_flow = capital_net_cash_flow + cash_flow_statement['final_project_metrics']['capital_cumulative_net_cash_flow'][year-1]
        cash_flow_statement['final_project_metrics']['capital_net_cash_flow'].append(capital_net_cash_flow)
        cash_flow_statement['final_project_metrics']['capital_cumulative_net_cash_flow'].append(capital_cumulative_net_cash_flow)

        #资本金现金流量 税前净现金流量CI-CO C197
        capital_pre_tax_net_cash_flow = capital_net_cash_flow + income_tax
        if year == 0:
            capital_pre_tax_cumulative_net_cash_flow = capital_pre_tax_net_cash_flow
        else:
            capital_pre_tax_cumulative_net_cash_flow = capital_pre_tax_net_cash_flow + cash_flow_statement['final_project_metrics']['capital_pre_tax_cumulative_net_cash_flow'][year-1]
        cash_flow_statement['final_project_metrics']['capital_pre_tax_net_cash_flow'].append(capital_pre_tax_net_cash_flow)
        cash_flow_statement['final_project_metrics']['capital_pre_tax_cumulative_net_cash_flow'].append(capital_pre_tax_cumulative_net_cash_flow)

        #初始投资计算流C202
        initial_investment_cal = capital_cash_outflow_data['capital_investment'][year] +\
                             capital_cash_outflow_data['foreign_loan_principal_repayment'][year] +\
                             capital_cash_outflow_data['domestic_loan_principal_repayment'][year]
        cash_flow_statement['operating_cash_flow']['initial_investment_cal'].append(initial_investment_cal)

        # C204 每年经营成本计算流
        if year > 0:
            annual_operating_cost_cal =  total_interest_expense + loan_repayment_data['construction_interest'][year-1]
        else :
            annual_operating_cost_cal =  total_interest_expense
        cash_flow_statement['operating_cash_flow']['annual_operating_cost_cal'].append(annual_operating_cost_cal)

        # C207 税费成本
        annual_taxes_cal = sales_tax_surcharge + annual_profit_data['actual_vat_paid'][year] + income_tax
        cash_flow_statement['operating_cash_flow']['annual_taxes_cal'].append(annual_taxes_cal)


        # 将计算结果存储到字典中
        cash_flow_statement['financing_cash_flow']['equity_capital'].append(equity_capital)
        cash_flow_statement['financing_cash_flow']['construction_loan'].append(construction_loan)
        cash_flow_statement['financing_cash_flow']['working_capital_loan'].append(yearly_working_capital_loan_amount)
        cash_flow_statement['financing_cash_flow']['bonds'].append(bonds)
        cash_flow_statement['financing_cash_flow']['other_inflow_fin'].append(other_inflow_fin)
        cash_flow_statement['financing_cash_flow']['total_cash_outflow_fin'].append(total_cash_outflow_fin)
        cash_flow_statement['financing_cash_flow']['interest_expense'].append(interest_sum)
        cash_flow_statement['financing_cash_flow']['debt_principal_repayment'].append(debt_principal_repayment)
        cash_flow_statement['financing_cash_flow']['other_outflow_fin'].append(other_outflow_fin)
        cash_flow_statement['short_term_loan']['short_term_loan_amount'].append(yearly_short_term_loan_amount)
        cash_flow_statement['short_term_loan']['short_term_loan_cumulative'].append(short_term_loan_cumulative)
        cash_flow_statement['short_term_loan']['short_term_loan_interest'].append(yearly_short_term_loan_interest)
        cash_flow_statement['short_term_loan']['short_term_loan_repayment'].append(yearly_short_term_loan_repayment)
        cash_flow_statement['working_capital_loan_flow']['WC_loan_limit'].append(WC_loan_limit)
        cash_flow_statement['working_capital_loan_flow']['WC_loan_repayment'].append(WC_loan_repayment)
        cash_flow_statement['working_capital_loan_flow']['short_term_loan_interest'].append(interest)
        cash_flow_statement['cost_and_profit']['total_interest_expense'].append(total_interest_expense)
        cash_flow_statement['cost_and_profit']['total_cost_and_expenses'].append(total_cost_and_expenses)
        cash_flow_statement['operating_cash_flow']['total_profit'].append(total_profit)
        cash_flow_statement['operating_cash_flow']['loss_carry_forward_next_year'].append(loss_carry_forward)

    ###计算项目税前税后IRR\NPV\回收期
    def _first_payback_idx(cumulative_list):
        """累计现金流首次转正的年份下标；经营期内始终未转正时返回 None（回收期=未回收）"""
        idx_arr = np.where(np.array(cumulative_list) > 0)[0]
        return int(idx_arr[0]) if len(idx_arr) else None

    #税后
    P_post_irr_result = npf.irr(cash_flow_statement['final_project_metrics']['project_post_tax_net_cash_flow']) # C154
    P_post_npv_result = npf.npv(INVESTMENT_PARAMS['benchmark_yield'],[0] + cash_flow_statement['final_project_metrics']['project_post_tax_net_cash_flow']) #C155
    P_post_basic_period = _first_payback_idx(cash_flow_statement['final_project_metrics']['project_cumulative_net_cash_flow'])
    P_post_payback_period = P_post_basic_period + abs(np.array(cash_flow_statement['final_project_metrics']['project_cumulative_net_cash_flow'])[P_post_basic_period-1])/ \
                            np.array(cash_flow_statement['final_project_metrics']['project_post_tax_net_cash_flow'])[P_post_basic_period] if P_post_basic_period is not None else None #C157

    #税前
    P_pre_irr_result = npf.irr(cash_flow_statement['final_project_metrics']['project_pre_tax_net_cash_flow'])
    P_pre_npv_result = npf.npv(INVESTMENT_PARAMS['benchmark_yield'],[0] + cash_flow_statement['final_project_metrics']['project_pre_tax_net_cash_flow'])
    P_pre_basic_period = _first_payback_idx(cash_flow_statement['final_project_metrics']['project_pre_tax_cumulative_net_cash_flow'])
    P_pre_payback_period = P_pre_basic_period + abs(np.array(cash_flow_statement['final_project_metrics']['project_pre_tax_cumulative_net_cash_flow'])[P_pre_basic_period-1])/ \
                           np.array(cash_flow_statement['final_project_metrics']['project_pre_tax_net_cash_flow'])[P_pre_basic_period] if P_pre_basic_period is not None else None

    ###计算资本金税前税后IRR\NPV\回收期
    #税后
    C_post_irr_result = npf.irr(cash_flow_statement['final_project_metrics']['capital_net_cash_flow'])
    C_post_npv_result = npf.npv(INVESTMENT_PARAMS['benchmark_yield'],[0] + cash_flow_statement['final_project_metrics']['capital_net_cash_flow'])
    C_post_basic_period = _first_payback_idx(cash_flow_statement['final_project_metrics']['capital_cumulative_net_cash_flow'])
    C_post_payback_period = C_post_basic_period + abs(np.array(cash_flow_statement['final_project_metrics']['capital_cumulative_net_cash_flow'])[C_post_basic_period-1])/ \
                            np.array(cash_flow_statement['final_project_metrics']['capital_net_cash_flow'])[C_post_basic_period] if C_post_basic_period is not None else None

    #税前
    C_pre_irr_result = npf.irr(cash_flow_statement['final_project_metrics']['capital_pre_tax_net_cash_flow'])
    C_pre_npv_result = npf.npv(INVESTMENT_PARAMS['benchmark_yield'],[0] + cash_flow_statement['final_project_metrics']['capital_pre_tax_net_cash_flow'])
    C_pre_basic_period = _first_payback_idx(cash_flow_statement['final_project_metrics']['capital_pre_tax_cumulative_net_cash_flow'])
    C_pre_payback_period = C_pre_basic_period + abs(np.array(cash_flow_statement['final_project_metrics']['capital_pre_tax_cumulative_net_cash_flow'])[C_pre_basic_period-1])/ \
                             np.array(cash_flow_statement['final_project_metrics']['capital_pre_tax_net_cash_flow'])[C_pre_basic_period] if C_pre_basic_period is not None else None

    ###计算资本金度电成本（最终输出）
    
    cost_of_electricity_discount_rate = SELLING_PRICE_PARAMS['cost_of_electricity_discount_rate'] # C48/C205折现率
    #初始投资
    initial_investment = cash_flow_statement['operating_cash_flow']['initial_investment_cal'][0] + \
                         npf.npv(cost_of_electricity_discount_rate,[0] + cash_flow_statement['operating_cash_flow']['initial_investment_cal'][1:])

    #初始静态投资NPV 新增
    SI_npv_result = cash_flow_statement['investment_cash_flow']['construction_investment'][0] + \
                    npf.npv(cost_of_electricity_discount_rate,[0] + cash_flow_statement['investment_cash_flow']['construction_investment'][1:])

    #增值税抵扣NPV 新增
    VDI_npv_result = annual_profit_data['vat_deductible_income'][0] +\
                     npf.npv(cost_of_electricity_discount_rate,[0] + annual_profit_data['vat_deductible_income'][1:])

    #回收固定资产余值/残值 新增
    FAS_npv_result = cash_flow_statement['investment_cash_flow']['fixed_asset_salvage'][0] + \
                     npf.npv(cost_of_electricity_discount_rate,[0] + cash_flow_statement['investment_cash_flow']['fixed_asset_salvage'][1:])

    #运营成本 新增
    TOC_npv_result = annual_cost_data['total_operating_cost'][0] +\
                     npf.npv(cost_of_electricity_discount_rate,[0] + annual_cost_data['total_operating_cost'][1:])

    #上网电量NPV 新增
    TSEB_npc_result = annual_profit_data['total_sale_electricity_billion_kwh'][0] +\
                      npf.npv(cost_of_electricity_discount_rate,[0] + annual_profit_data['total_sale_electricity_billion_kwh'][1:])
    
    #每年进项抵扣（暂时空着）
    input_tax_deduction = 0
    #每年经营成本
    annual_operating_cost = cash_flow_statement['operating_cash_flow']['annual_operating_cost_cal'][0] + \
                         npf.npv(cost_of_electricity_discount_rate,[0] + cash_flow_statement['operating_cash_flow']['annual_operating_cost_cal'][1:])

    #度电成本LCOE C206
    LCOE = (SI_npv_result - VDI_npv_result - FAS_npv_result + TOC_npv_result) / TSEB_npc_result / 10000

    #税费成本
    annual_taxes = cash_flow_statement['operating_cash_flow']['annual_taxes_cal'][0] + \
                         npf.npv(cost_of_electricity_discount_rate,[0] + cash_flow_statement['operating_cash_flow']['annual_taxes_cal'][1:])

    #广义度电成本G_LCOE C208
    G_LCOE = (initial_investment - input_tax_deduction + annual_operating_cost + annual_taxes - \
            npf.npv(cost_of_electricity_discount_rate,[0] + project_cash_inflow_data['salvage_value']))/ \
            npf.npv(cost_of_electricity_discount_rate,[0] + annual_profit_data['total_sale_electricity_billion_kwh'])/10000
    
    
    cash_flow_statement['financing_cash_flow']['P_post_irr_result']= P_post_irr_result
    cash_flow_statement['financing_cash_flow']['P_post_npv_result']= P_post_npv_result
    cash_flow_statement['financing_cash_flow']['P_post_payback_period']= P_post_payback_period
    cash_flow_statement['financing_cash_flow']['P_pre_irr_result']= P_pre_irr_result
    cash_flow_statement['financing_cash_flow']['P_pre_npv_result']= P_pre_npv_result
    cash_flow_statement['financing_cash_flow']['P_pre_payback_period']= P_pre_payback_period
    cash_flow_statement['financing_cash_flow']['C_post_irr_result']= C_post_irr_result
    cash_flow_statement['financing_cash_flow']['C_post_npv_result']= C_post_npv_result
    cash_flow_statement['financing_cash_flow']['C_post_payback_period']= C_post_payback_period
    cash_flow_statement['financing_cash_flow']['C_pre_irr_result']= C_pre_irr_result
    cash_flow_statement['financing_cash_flow']['C_pre_npv_result']= C_pre_npv_result
    cash_flow_statement['financing_cash_flow']['C_pre_payback_period']= C_pre_payback_period
    cash_flow_statement['financing_cash_flow']['LCOE']= LCOE
    cash_flow_statement['financing_cash_flow']['G_LCOE']= G_LCOE

    
    return cash_flow_statement

if __name__ == '__main__':
    total_project_years = 26
    financial_data = get_financial_plan_cash_flow(total_project_years)

    # 打印部分结果以供参考
    print("财务计划现金流量表 (万元)")
    print("-" * 220)
    print(f"{'年份':<2} | {'销售收入(不含税)':<8} | {'建设投资':<8} | {'投资净流量':<8} | {'项目资本金投入':<10} | {'建设投资借款':<10} | {'短期贷款额度':<8} | {'短期贷款累计':<8} | {'短期贷款利息':<10} | {'各种利息支出':<10} | {'偿还债务本金':<10} | {'现金流出':<8}")
    for year in range(total_project_years):
        print(
            f"年{year+1:<2} | "
            f"{financial_data['operating_cash_flow']['revenue_without_vat'][year]:<15.2f} | "
            f"{financial_data['investment_cash_flow']['construction_investment'][year]:<12.2f} | "
            f"{financial_data['investment_cash_flow']['net_investment_cash_flow'][year]:<12.2f} | "
            f"{financial_data['financing_cash_flow']['equity_capital'][year]:<18.2f} | "
            f"{financial_data['financing_cash_flow']['construction_loan'][year]:<18.2f} | "
            f"{financial_data['short_term_loan']['short_term_loan_amount'][year]:<15.2f} | "
            f"{financial_data['short_term_loan']['short_term_loan_cumulative'][year]:<15.2f} | "
            f"{financial_data['short_term_loan']['short_term_loan_interest'][year]:<15.2f} | "
            f"{financial_data['financing_cash_flow']['interest_expense'][year]:<15.2f} | "
            f"{financial_data['financing_cash_flow']['debt_principal_repayment'][year]:<15.2f} | "
            f"{financial_data['financing_cash_flow']['total_cash_outflow_fin'][year]:<10.2f}"
        )
