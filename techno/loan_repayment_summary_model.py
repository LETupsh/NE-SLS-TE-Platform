# 该文件合并了 loan_repayment_summary_model.py 和 loan_model.py 的全部功能。
# 本文件现在专注于长期贷款的还本付息计算及相关数据的汇总。
# 短期贷款和流动资金贷款的计算逻辑已移至 financial_plan_cash_flow_model.py

# 导入所需的参数和数据
from project_parameters import (
    INVESTMENT_PARAMS,
    INVESTMENT_RESULTS,
    TAX_RATES,
    REPAYMENT_METHOD,
    OPERATION_YEARS
)
import math
# 从其他模型导入必要的函数
from cost_model import get_annual_cost_statement
from revenue_model import calculate_annual_profit_statement

def pmt(rate, nper, pv):
    """
    [来自 loan_model.py]
    计算等额本息还款的每期支付金额。
    遵循Excel PMT函数逻辑，返回正数。

    Args:
        rate (float): 每期利率。
        nper (int): 还款总期数。
        pv (float): 贷款总额（现值），传入正数。

    Returns:
        float: 每期支付金额，返回正数。
    """
    if rate == 0:
        return pv / nper

    return rate * pv / (1 - (1 + rate)**-nper)

def calculate_loan_repayment_plan():
    """
    [来自 loan_model.py]
    计算长期贷款在建设期和运营期内的还本付息计划。

    返回:
        dict: 包含各年度还本、付息等数据的字典。
              - year: 年度
              - year_start_balance: 年初本金 (C242)
              - yearly_accrued_interest: 本年应计利息 (C243)
              - yearly_total_repayment: 还本付息合计 (C244)
              - yearly_principal_repayment: 本年还本 (C245)
              - yearly_interest_payment: 本年付息 (C246)
    """
    # 获取参数
    long_term_loan_rate = INVESTMENT_PARAMS['long_term_loan_rate']
    repayment_period = INVESTMENT_PARAMS['repayment_period']
    repayment_start_year = INVESTMENT_PARAMS['repayment_start_year']

    # 贷款总额（万元），对应 Excel 中的 H14
    total_loan_amount = INVESTMENT_RESULTS['loan_amount']

    # 确定还款方式
    is_equal_principal_and_interest = (REPAYMENT_METHOD['equal_principal_and_interest'] == 1)

    # 初始化数据结构
    repayment_plan = {
        'year': [],
        'year_start_balance': [],
        'yearly_accrued_interest': [],
        'yearly_total_repayment': [],
        'yearly_principal_repayment': [],
        'yearly_interest_payment': []
    }

    # 初始化年末贷款余额（正数表示欠款），对应 Excel 中的 C241
    end_of_year_balance = 0

    # 假设运营年限为25年，加上1年建设期
    total_project_years = OPERATION_YEARS['pv'] + 1

    # 预先计算建设期末的贷款余额，作为还款期现值
    construction_period_interest = (total_loan_amount / 2) * long_term_loan_rate
    end_of_construction_balance = total_loan_amount + construction_period_interest

    # 预先计算等额本息还款额或等额本金还本额
    if is_equal_principal_and_interest:
        fixed_yearly_payment = pmt(long_term_loan_rate, repayment_period, end_of_construction_balance)
    else:
        fixed_yearly_principal = end_of_construction_balance / repayment_period

    # --- 逐年计算 (从项目第1年开始) ---
    for year in range(1, total_project_years + 1):
        repayment_plan['year'].append(year)

        # 年初本金余额 = 上一年末本金余额
        year_start_balance = end_of_year_balance
        repayment_plan['year_start_balance'].append(year_start_balance)

        # 统一将所有还款项初始化为0，确保未发生时为0
        yearly_accrued_interest = 0
        yearly_principal_repayment = 0
        yearly_total_repayment = 0

        # --- 建设期计算（第1年） ---
        if year < repayment_start_year:
            # 建设期只产生应计利息，不进行还本付息
            if year == 1:
                yearly_accrued_interest = construction_period_interest
                end_of_year_balance = end_of_construction_balance
            
        # --- 运营期还款计算 ---
        else:
            # 判断是否在还款期内
            is_in_repayment_period = (year >= repayment_start_year) and (year <= (repayment_start_year + repayment_period - 1))

            if is_in_repayment_period:
                # 在还款期内
                yearly_accrued_interest = year_start_balance * long_term_loan_rate

                if is_equal_principal_and_interest:
                    # 等额本息
                    yearly_total_repayment = fixed_yearly_payment
                    yearly_principal_repayment = yearly_total_repayment - yearly_accrued_interest
                else:
                    # 等额本金
                    yearly_principal_repayment = fixed_yearly_principal
                    yearly_total_repayment = yearly_principal_repayment + yearly_accrued_interest

                end_of_year_balance = year_start_balance - yearly_principal_repayment

                # 检查年末余额是否为负，并进行调整（最后一年）
                if end_of_year_balance < 0:
                    yearly_principal_repayment += end_of_year_balance
                    yearly_total_repayment = yearly_principal_repayment + yearly_accrued_interest
                    end_of_year_balance = 0

            else:
                # 还款期已结束
                end_of_year_balance = 0
                
        repayment_plan['yearly_accrued_interest'].append(yearly_accrued_interest)
        repayment_plan['yearly_total_repayment'].append(yearly_total_repayment)
        repayment_plan['yearly_principal_repayment'].append(yearly_principal_repayment)
        
        # 付息 (C246) 在建设期为0，运营期为应计利息
        if year < repayment_start_year:
            repayment_plan['yearly_interest_payment'].append(0)
        else:
            repayment_plan['yearly_interest_payment'].append(yearly_accrued_interest)
    
    return repayment_plan

def calculate_loan_repayment_summary(total_years=26):
    """
    [来自 loan_repayment_summary_model.py]
    计算并返回每年的长期借款还本付息汇总表数据。
    本函数不包含短期贷款和流动资金贷款相关计算。

    Args:
        total_years (int): 需要计算的总年数，通常为项目运营年限+建设期。

    Returns:
        dict: 包含各年度借款还本付息数据的字典。
              - beginning_long_term_principal: 1.1.1 年初本金 (C217)
              - construction_interest: 1.1.2 建设期利息 (C218)
              - yearly_new_loan: 1.2 本年借款 (C219)
              - yearly_accrued_interest: 1.3 本年应计利息 (C220)
              - yearly_principal_repayment: 1.4 本年还本 (C221)
              - yearly_interest_payment: 1.5 本年付息 (C222)
              - funds_for_repayment: 2 偿还本金的资金来源 (C223)
              - profit_for_repayment: 2.1 可用于还本的利润 (C224)
              - depreciation: 2.2 折旧 (C225)
              - total_long_term_loan_summary: (留空待计算)
              - funds_for_repayment: (留空待计算)
    """
    # 获取所需的外部数据，直接调用合并后的文件内的函数
    loan_repayment_plan = calculate_loan_repayment_plan()
    annual_cost_data = get_annual_cost_statement(total_years)
    annual_profit_data = calculate_annual_profit_statement(total_years)

    # 初始化数据结构
    loan_summary = {
        'total_long_term_loan_summary': [],
        'beginning_long_term_principal': [],
        'construction_interest': [],
        'yearly_new_loan': [],
        'yearly_accrued_interest': [],
        'yearly_principal_repayment': [],
        'yearly_interest_payment': [],
        'funds_for_repayment': [],
        'profit_for_repayment': [],
        'depreciation': [],
    }

    # 逐年计算
    for year in range(1, total_years + 1):
        # 统一将所有项初始化为0
        yearly_new_loan = 0
        yearly_construction_interest = 0

        # --- 1. 人民币借款及还本付息 ---
        # 1.1.1 年初本金 (C217): 在 loan_model.py 中已计算，这里直接引用
        beginning_long_term_principal = loan_repayment_plan['year_start_balance'][year - 1]

        # 1.1.2 建设期利息 (C218): H12
        if year == 1:
            yearly_construction_interest = INVESTMENT_RESULTS['construction_period_interest']

        # 1.2 本年借款 (C219): H14
        if year == 1:
            yearly_new_loan = INVESTMENT_RESULTS['loan_amount']

        # 1.3 本年应计利息 (C220): C243
        yearly_accrued_interest = loan_repayment_plan['yearly_accrued_interest'][year - 1]

        # 1.4 本年还本 (C221): C245
        yearly_principal_repayment = loan_repayment_plan['yearly_principal_repayment'][year - 1]

        # 1.5 本年付息 (C222)
        # 运营期为本年应计利息，建设期为应计利息减去已资本化的建设期利息
        if year >= INVESTMENT_PARAMS['repayment_start_year']:
            yearly_interest_payment = yearly_accrued_interest
        else:
            yearly_interest_payment = yearly_accrued_interest - yearly_construction_interest

        # --- 2. 偿还本金的资金来源 ---
        # 2.1 可用于还本的利润 (C224)
        # IF((D119-D122-D123)>0,D119-D122-D123,0)
        # 利润总额 (D119) 减去所得税 (D122) 和应付利润 (D123)
        # 注意: revenue_model.py 中目前没有 D119, D122, D123 等数据
        profit_for_repayment = 0 # 留空待补充

        # 2.2 折旧 (C225): D83
        depreciation = annual_cost_data['total_depreciation'][year - 1]

        # 将计算结果存储到字典中
        loan_summary['beginning_long_term_principal'].append(beginning_long_term_principal)
        loan_summary['construction_interest'].append(yearly_construction_interest)
        loan_summary['yearly_new_loan'].append(yearly_new_loan)
        loan_summary['yearly_accrued_interest'].append(yearly_accrued_interest)
        loan_summary['yearly_principal_repayment'].append(yearly_principal_repayment)
        loan_summary['yearly_interest_payment'].append(yearly_interest_payment)
        loan_summary['profit_for_repayment'].append(profit_for_repayment)
        loan_summary['depreciation'].append(depreciation)

        # 留空：总数计算
        loan_summary['total_long_term_loan_summary'].append(0)
        loan_summary['funds_for_repayment'].append(0)

    return loan_summary

if __name__ == '__main__':
    # 示例运行逻辑，与原 loan_repayment_summary_model.py 的 main 部分一致
    total_project_years = 26 # 1年建设期+还款年限
    loan_data = calculate_loan_repayment_summary(total_project_years)

    # 打印部分结果以供参考
    print("借款还本付息计算表 (万元)")
    print("-" * 120)
    print(f"{'年份':<4} | {'年初本金':<10} | {'本年新借':<10} | {'应计利息':<10} | {'还本':<10} | {'付息':<10} | {'折旧':<10}")
    for year in range(total_project_years):
        print(
            f"年{year+1:<5} | "
            f"{loan_data['beginning_long_term_principal'][year]:<14.2f} | "
            f"{loan_data['yearly_new_loan'][year]:<14.2f} | "
            f"{loan_data['yearly_accrued_interest'][year]:<12.2f} | "
            f"{loan_data['yearly_principal_repayment'][year]:<12.2f} | "
            f"{loan_data['yearly_interest_payment'][year]:<10.2f} | "
            f"{loan_data['depreciation'][year]:<10.2f}"
        )

    # 示例运行逻辑，与原 loan_model.py 的 main 部分一致
    print("\n" + "="*60)
    print("长期贷款还本付息计划 (万元)")
    print("="*60)
    loan_plan = calculate_loan_repayment_plan()
    # 打印前几年的结果
    print("年度 | 年初本金 | 本年应计利息 | 还本付息合计 | 还本 | 付息")
    print("-" * 60)
    for i in range(1, 27):
        # 考虑到列表索引从0开始，而年份从1开始
        if i - 1 < len(loan_plan['year']):
            print(
                f"年{loan_plan['year'][i-1]:<2} | {loan_plan['year_start_balance'][i-1]:<8.2f} | "
                f"{loan_plan['yearly_accrued_interest'][i-1]:<10.2f} | "
                f"{loan_plan['yearly_total_repayment'][i-1]:<12.2f} | "
                f"{loan_plan['yearly_principal_repayment'][i-1]:<6.2f} | "
                f"{loan_plan['yearly_interest_payment'][i-1]:<6.2f}"
            )
