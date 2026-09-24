import math
from project_parameters import (
    PROJECT_SCALE,
    OPERATION_YEARS,
    POWER_GENERATION_PARAMS,
    SELLING_PRICE_PARAMS,
    TAX_RATES,
    INVESTMENT_RESULTS,
    OPERATING_COST_PARAMS
)

def calculate_annual_profit_statement(total_years=26):
    """
    计算并返回每年的销售收入、增值税及附加、所得税率等数据。

    Args:
        total_years (int): 需要计算的总年数，包括建设期。

    Returns:
        dict: 包含各年度收入和税费数据的字典。
    """
    annual_profit = {
        'total_sale_electricity_billion_kwh': [], # C101：销售电量（亿kW.h）
        'wind_generation_hours': [], # C102：风电发电小时数
        'pv_generation_hours': [], # C103：光伏发电小时数
        'sales_revenue_without_vat': [], # C104：销售收入（不含增值税）
        'vat': [], # C105：增值税
        'wind_vat': [], # C106：风电项目销售增值税
        'pv_vat': [], # C107：光伏项目销售增值税
        'sales_revenue_with_vat': [], # C108：销售收入（含增值税）
        'vat_deductible_income': [], # C109：增值税抵扣收入
        'actual_vat_paid': [], # C110：实际发生的增值税
        'sales_tax_surcharge': [], # C111：销售税金附加
        'wind_vat_rebate_income': [], # C113：营业外收入（风电增值税减半收入）
        'income_tax_rate': [],  # C117：所得税率
        'energy_change_vat':[]  # 新增储能更换增值税抵扣
    }

    # 初始化累计抵扣增值税
    cumulative_vat_deductions = 0
    total_energy_change_vat = 0
    
    # 模拟逐年计算
    for year in range(1, total_years + 1):
        # 建设期（第一年）所有收入和税费均为0
        if year == 1:
            for key in annual_profit.keys():
                annual_profit[key].append(0)
            continue

        # --- 发电量计算逻辑 ---
        # 风电发电小时数
        wind_hours = POWER_GENERATION_PARAMS['wind_hours'] if year <= OPERATION_YEARS['wind'] + 1 else 0
        annual_profit['wind_generation_hours'].append(wind_hours)
        
        # 光伏发电小时数，考虑线性衰减
        pv_hours = 0
        pv_op_years = OPERATION_YEARS['pv'] # 运营期年限 25年
        if year <= pv_op_years + 1:
            if year == 1:
                # 建设期，小时数为 0
                pv_hours = 0
            elif year == 2:
                # 运营期第1年，小时数为首年等效小时数
                pv_hours = POWER_GENERATION_PARAMS['pv_first_year_hours']
            else:
                # 运营期第2年及以后，按线性衰减计算
                first_year_decline = POWER_GENERATION_PARAMS['first_year_decline']
                annual_decline = POWER_GENERATION_PARAMS['annual_decline']
                pv_first_year_hours = POWER_GENERATION_PARAMS['pv_first_year_hours']
                
                # 计算公式: 
                # 首年等效小时数 / (1 - 首年衰减率) * (1 - 首年衰减率 - 年均衰减率 * (运营年数-1))
                # 这里的“运营年数” = year - 1
                pv_hours = (pv_first_year_hours / (1 - first_year_decline)) * (1 - first_year_decline - annual_decline * (year - 2))
                
        annual_profit['pv_generation_hours'].append(pv_hours)

        # --- 销售电量（C101） ---
        wind_power_output_billion_kwh = wind_hours * PROJECT_SCALE['wind_mw'] * 1000 / 10**8
        pv_power_output_billion_kwh = pv_hours * PROJECT_SCALE['pv_mw'] * 1000 / 10**8
        total_sale_electricity = wind_power_output_billion_kwh + pv_power_output_billion_kwh
        annual_profit['total_sale_electricity_billion_kwh'].append(total_sale_electricity)

        # --- 销售收入（含增值税） C108 ---
        sales_revenue_with_vat = (
            wind_hours * PROJECT_SCALE['wind_mw'] * 1000 * SELLING_PRICE_PARAMS['wind_price_per_kwh'] +
            pv_hours * PROJECT_SCALE['pv_mw'] * 1000 * SELLING_PRICE_PARAMS['pv_price_per_kwh']
        ) / 10000
        annual_profit['sales_revenue_with_vat'].append(sales_revenue_with_vat)

        # --- 销售收入（不含增值税） C104 ---
        vat_rate = TAX_RATES['vat_rate']
        sales_revenue_without_vat = sales_revenue_with_vat / (1 + vat_rate)
        annual_profit['sales_revenue_without_vat'].append(sales_revenue_without_vat)

        # --- 增值税（C105） ---
        vat = sales_revenue_with_vat - sales_revenue_without_vat
        annual_profit['vat'].append(vat)
        
        # 风电项目销售增值税（C106）
        wind_vat = (wind_hours * PROJECT_SCALE['wind_mw'] * 1000 * SELLING_PRICE_PARAMS['wind_price_per_kwh']) / 10000 / (1 + vat_rate) * vat_rate
        annual_profit['wind_vat'].append(wind_vat)

        # 光伏项目销售增值税（C107）
        pv_vat = (pv_hours * PROJECT_SCALE['pv_mw'] * 1000 * SELLING_PRICE_PARAMS['pv_price_per_kwh']) / 10000 / (1 + vat_rate) * vat_rate
        annual_profit['pv_vat'].append(pv_vat)

        ## 新增储能更换增加的增值税抵扣
        # 对应 Excel C149
        # 仅在设备更换年份发生
        yearly_maintenance_investment = 0
        replacement_year = OPERATING_COST_PARAMS['equipment_replacement_year']
        replacement_S_year = OPERATING_COST_PARAMS['equipment_replacement_S_year']
        if year == replacement_year :
            yearly_maintenance_investment = OPERATING_COST_PARAMS['equipment_replacement_unit_price_per_wh'] * \
                                            PROJECT_SCALE['energy_storage_mwh'] * 100
        if year == replacement_S_year :
            yearly_maintenance_investment += OPERATING_COST_PARAMS['equipment_replacement_unit_price_per_wh'] * \
                                            PROJECT_SCALE['energy_storage_mwh'] * 100
        
        energy_change_vat = yearly_maintenance_investment/(1+ TAX_RATES['vat_rate'])*TAX_RATES['vat_rate']
        annual_profit['energy_change_vat'].append(energy_change_vat)
        total_energy_change_vat += energy_change_vat
        
        # --- 增值税抵扣收入（C109） ---
        # 实际发生的增值税 = 销售增值税 - 进项税抵扣
        deductible_vat_limit = INVESTMENT_RESULTS['deductible_taxes']
        current_year_vat = annual_profit['vat'][-1]
        remaining_deductible_limit = deductible_vat_limit + total_energy_change_vat - cumulative_vat_deductions
        current_year_vat_deduction = 0
        if current_year_vat > 0 and remaining_deductible_limit > 0:
            current_year_vat_deduction = min(current_year_vat, remaining_deductible_limit)
        cumulative_vat_deductions += current_year_vat_deduction
        annual_profit['vat_deductible_income'].append(current_year_vat_deduction)

        # --- 实际发生的增值税（C110） ---
        actual_vat_paid = current_year_vat - current_year_vat_deduction
        annual_profit['actual_vat_paid'].append(actual_vat_paid)

        # --- 销售税金附加（C111） ---
        sales_tax_surcharge_rate = TAX_RATES['sales_tax_surcharge_rate']
        sales_tax_surcharge = actual_vat_paid * sales_tax_surcharge_rate
        annual_profit['sales_tax_surcharge'].append(sales_tax_surcharge)
        
        # --- 营业外收入（风电增值税减半收入） C113 暂时取消 ---
        wind_vat_rebate_income = 0
        if actual_vat_paid > 0:
            current_year_deduction = annual_profit['vat_deductible_income'][-1]
            current_year_wind_vat = annual_profit['wind_vat'][-1]
            current_year_pv_vat = annual_profit['pv_vat'][-1]
            
            # 逻辑：如果本年抵扣额小于光伏应缴增值税，则风电增值税无需抵扣，直接减半
            if current_year_deduction < current_year_pv_vat:
                wind_vat_rebate_income = current_year_wind_vat / 2
            # 否则，先用抵扣额抵扣光伏增值税，剩余部分抵扣风电增值税，然后将实际缴纳的风电增值税减半
            else:
                deducted_wind_vat = current_year_deduction - current_year_pv_vat
                actual_paid_wind_vat = current_year_wind_vat - deducted_wind_vat
                wind_vat_rebate_income = actual_paid_wind_vat / 2
        ###取消营业外收入
        wind_vat_rebate_income = 0
        annual_profit['wind_vat_rebate_income'].append(wind_vat_rebate_income)
        
        # --- 所得税率（C117） ---
        income_tax_rate = 0.0
        # 运营期年份
        operating_year = year - 1
        
        # 运营期第1-3年免税
        if operating_year >= 1 and operating_year <= 3:
            income_tax_rate = 0.0
        # 按优惠年限判断
        else:
            preferential_years = TAX_RATES.get('remaining_preferential_years', 0)
            if operating_year <= preferential_years:
                income_tax_rate = TAX_RATES['preferential_income_tax_rate']
            else:
                income_tax_rate = TAX_RATES['standard_income_tax_rate']
            # 运营期第4-6年减半征收
            if operating_year >= 4 and operating_year <= 6:
                income_tax_rate = income_tax_rate / 2

        
        annual_profit['income_tax_rate'].append(income_tax_rate)

    return annual_profit

# 示例：如何调用并打印结果
if __name__ == '__main__':
    profit_data = calculate_annual_profit_statement(total_years=26)

    # 打印部分结果
    print("年度 | 营业外收入 | 所得税率 | 增值税抵扣收入 | 销售电量 | 光伏项目销售增值税 | 储能更换增值税抵扣 ")
    print("-" * 30)
    for i, year_data in enumerate(zip(
        profit_data['wind_vat_rebate_income'],
        profit_data['income_tax_rate'],
        profit_data['vat_deductible_income'],
        profit_data['total_sale_electricity_billion_kwh'],
        profit_data['pv_vat'],
        profit_data['energy_change_vat']
    ), 1):
        print(f"年{i:<2} | {year_data[0]:<10.2f} | {year_data[1]:<8.4f} "+\
              f"| {year_data[2]:<12.4f} | {year_data[3]:<10.4f} | {year_data[4]:<12.4f} | {year_data[5]:<12.4f}")
