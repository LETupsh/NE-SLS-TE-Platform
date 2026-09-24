# NE-SLS-TE-Platform · 风光储一体化综合分析平台

将 **源荷储匹配分析（储能）** 与 **技经批量计算** 两个模型整合为一个 Streamlit 应用，
通过侧边栏换页完成全部操作，两个模块之间**内置数据直通**，无需导出/导入 Excel 文件。

> 独立版储能模型见 [NE-SLS-Platform](https://github.com/LETupsh/NE-SLS-Platform)。

## 功能总览

### ⚡ 页面一：储能源荷储匹配分析
- 上传 8760 逐时数据（光伏出力 / 风电出力 / 负荷，CSV），批量模拟源荷储匹配；
- 电价模式二选一：**分时段电价**（尖峰/峰/平/谷/深谷，逐月可配置、支持批量同步）
  或 **CSV 逐时电价**（自用电价 + 上网电价两列）；
- 批量遍历光伏容量 / 风电容量 / 储能功率 / 储能时长，输出综合电价、加权自用/上网电价、
  消纳率、绿电占用电比例、储能等效循环次数等指标；
- 任意方案可复算 8760 逐时过程量并导出 Excel，附逐日发电/负荷/自用比例曲线。

### 💰 页面二：技经批量计算
- 三种输入模式：**表格上传** / **手动步长遍历** / **储能分析结果直通**（本整合版新增）；
- 正向计算：综合电价 → 项目税前/税后 IRR、资本金税前/税后 IRR、NPV、回收期、LCOE；
- **反推综合电价**：给定目标 IRR（项目/资本金 × 税前/税后，四选一），
  数值求解使该指标恰好达标所需的综合电价（二分法，精度 ~1e-9 元/kWh）；
- 财务模型覆盖：增值税进项抵扣与更换设备抵扣、所得税"三免三减半"、
  长期贷款（等额本息/等额本金）、流动资金贷款、短期融资平衡、折旧与残值回收。

## 数据直通（两页联动）

```
⚡ 储能页批量模拟
   └─ 结果存入会话状态 (容量 / 利用小时数 / 综合电价 …)
          │  换页，无需导出文件
          ▼
💰 技经页「储能分析结果传入」模式
   └─ 勾选参与计算的方案 → 自动构建技经方案 → 批量 IRR / LCOE 或反推综合电价
```

## 快速开始

```bash
# 1. 安装依赖（Python 3.10+）
pip install -r requirements.txt

# 2. 配置登录凭据（真实 secrets 只保存在本地，已被 .gitignore 排除）
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
#    编辑 .streamlit/secrets.toml，填入 cookie_password 与 [users] 账号密码

# 3. 启动
streamlit run integrated_app.py
#    Windows 下也可直接双击 run_integrated.bat
```

> 提示：需自备 8760 行逐时数据 CSV（列：`PV_Unit_Output(kWh)`, `Wind_Unit_Output(kWh)`, `Load(kWh)`）；
> 技经表格上传模式的必需列：风电容量 (MW)、光伏容量 (MW)、风电利用小时数 (h)、
> 光伏利用小时数 (h)、储能容量 (MWh)、综合电价。

## 项目结构

```
NE-SLS-TE-Platform/
├── integrated_app.py            # 统一入口：登录 + 侧边栏换页导航
├── run_integrated.bat           # Windows 一键启动
├── requirements.txt
├── .streamlit/
│   └── secrets.toml.example     # 登录凭据模板（真实文件不入库）
├── energy/                      # 储能模块
│   ├── energy_model.py          #   纯计算：8760 逐时模拟、批量方案、Excel 导出
│   └── energy_page.py           #   页面 UI（双 Tab：计算与分析 / 电价与时段配置）
└── techno/                      # 技经模块
    ├── techno_page.py           #   页面 UI（正算 + 反推，三种输入模式）
    ├── project_parameters.py    #   全局参数与派生投资/成本计算
    ├── financial_plan_cash_flow_model.py  # 财务计划现金流量表 + IRR/NPV/回收期/LCOE
    ├── cash_flow_model.py       #   项目财务现金流量表
    ├── capital_cash_flow_model.py         # 资本金现金流量表
    ├── loan_repayment_summary_model.py    # 长期贷款还本付息
    ├── cost_model.py            #   成本费用（折旧、运维、更换）
    └── reverse_price_model.py   #   反推综合电价求解器（二分法）
```

## 反推综合电价模块说明

- 固定除综合电价外的全部参数，将风、光上网电价视为同一综合电价；
- 电价越高 IRR 单调越高，采用二分法求根，每次迭代完整复算财务模型，与正向计算完全同源；
- 搜索区间 0 ~ 10 元/kWh（自动扩界），结果输出反推电价及全部四项 IRR 的验证值；
- 目标不可达（如 IRR 高于电价上限所能达到的值）时给出明确提示而非报错。

## 登录说明

- 多用户 Cookie 登录（加密存储，浏览器关闭后保持登录态）；
- 凭据配置在 `.streamlit/secrets.toml`，**切勿提交真实文件**；
- 未配置 `[users]` 时所有账号均无法登录（fail-closed）。
