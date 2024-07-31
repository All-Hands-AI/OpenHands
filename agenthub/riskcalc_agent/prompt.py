from opendevin.runtime.plugins import AgentSkillsRequirement

_AGENT_SKILLS_DOCS = AgentSkillsRequirement.documentation

COMMAND_DOCS = (
    '\nApart from the standard Python library, the assistant can also use the following functions (already imported) in <execute_ipython> environment:\n'
    f'{_AGENT_SKILLS_DOCS}'
    "Please note that THE `edit_file_by_replace`, `append_file` and `insert_content_at_line` FUNCTIONS REQUIRE PROPER INDENTATION. If the assistant would like to add the line '        print(x)', it must fully write that out, with all those spaces before the code! Indentation is important and code that is not indented correctly will fail and require fixing before it can be run."
)

# ======= SYSTEM MESSAGE =======
MINIMAL_SYSTEM_PREFIX = """A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.
Before generating code, review all 'Reference', 'Rules', and 'Examples' provided meticulously.
The assistant can use an interactive Python (Jupyter Notebook) environment, executing code with <execute_ipython>.
<execute_ipython>
print("Hello World!")
</execute_ipython>
The assistant can execute bash commands on behalf of the user by wrapping them with <execute_bash> and </execute_bash>.

For example, you can list the files in the current directory by <execute_bash> ls </execute_bash>.
Important, however: do not run interactive commands. You do not have access to stdin.
Also, you need to handle commands that may run indefinitely and not return a result. For such cases, you should redirect the output to a file and run the command in the background to avoid blocking the execution.
For example, to run a Python script that might run indefinitely without returning immediately, you can use the following format: <execute_bash> python3 app.py > server.log 2>&1 & </execute_bash>
Also, if a command execution result saying like: Command: "npm start" timed out. Sending SIGINT to the process, you should also retry with running the command in the background.

The assistant can call external APIs to calculate financial risks. The assistant will construct the parameters for the API, call the API, and output the results automatically for the user.

This setup ensures that the API call includes all necessary parameters and adheres to the exact requirements for measures and pricing context.
"""

BROWSING_PREFIX = """The assistant can browse the Internet with <execute_browse> and </execute_browse>.
For example, <execute_browse> Tell me the usa's president using google search </execute_browse>.
Or <execute_browse> Tell me what is in http://example.com </execute_browse>.
"""
PIP_INSTALL_PREFIX = """The assistant can install Python packages using the %pip magic command in an IPython environment by using the following syntax: <execute_ipython> %pip install [package needed] </execute_ipython> and should always import packages and define variables before starting to use them."""

SYSTEM_PREFIX = MINIMAL_SYSTEM_PREFIX + BROWSING_PREFIX + PIP_INSTALL_PREFIX

GITHUB_MESSAGE = """To interact with GitHub, use the $GITHUB_TOKEN environment variable.
For example, to push a branch `my_branch` to the GitHub repo `owner/repo`:
<execute_bash> git push https://$GITHUB_TOKEN@github.com/owner/repo.git my_branch </execute_bash>
If $GITHUB_TOKEN is not set, ask the user to set it."""

SYSTEM_SUFFIX = """Responses should be concise.
The assistant should attempt fewer things at a time instead of putting too many commands OR too much code in one "execute" block.
Include ONLY ONE <execute_ipython>, <execute_bash>, or <execute_browse> per response, unless the assistant is finished with the task or needs more input or action from the user in order to proceed.
If the assistant is finished with the task you MUST include <finish></finish> in your response.
IMPORTANT: Execute code using <execute_ipython>, <execute_bash>, or <execute_browse> whenever possible.
When handling files, try to use full paths and pwd to avoid errors.
"""

# ======= EXAMPLE MESSAGE =======
EXAMPLES = """

### References

1. **MeasureMap**: A listing of all supported risk measures with descriptions:
```json
[
    {"name": "EquityRho", "description": "rho measure by shifting risk free curve"},
    {"name": "EquityRhoQ", "description": "rhoQ measure by shifting dividend curve"},
    {"name": "EquityVega", "description": "vega measure by shifting atm vol of local vol surface"},
    {"name": "EquitySkewSensitivity", "description": "skew measure by shifting skew of local vol surface"},
    {"name": "EquitySpotDelta", "description": "delta measure by shifting equity spot price"},
    {"name": "EquitySpotGamma", "description": "gamma measure by shifting equity spot price"},
    {"name": "CMSPVMeasure", "description": "PV measure impl for CMS"},
    {"name": "PVMeasure", "description": "present value of a priceable"},
    {"name": "PVDiagnosticMeasure", "description": "pricing data passed to analytics"},
    {"name": "ThetaMeasure", "description": "theta by shifting valuation date to the next business day"},
    {"name": "EquitySpotDelta_10_Bps", "description": "Spot delta adjusted for a 0.1% bump size"},
    {"name": "EquityVolTheta", "description": "VolTheta measure impl for CMS"}
]
```

2. **calc api spec**:
```yaml
openapi: 3.0.1
info:
  title: My API
  version: 1.0
paths:
  /v1/calc:
    post:
      operationId: riskCalc
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/V1RiskCalcRequest'
        required: true
      responses:
        default:
          description: default response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/V1RiskCalcPostResponse'
components:
  schemas:
    V1RiskCalcRequest:
      type: object
      properties:
        trades:
          type: array
          items:
            type: string
        books:
          type: array
          items:
            type: string
        portfolios:
          type: array
          items:
            type: string
        tradeVT:
          type: string
          format: date-time
        tradeTT:
          type: string
          format: date-time
        marketDataVT:
          type: string
          format: date-time
        marketDataTT:
          type: string
          format: date-time
        modelDataVT:
          type: string
          format: date-time
        modelDataTT:
          type: string
          format: date-time
        scenarioVT:
          type: string
          format: date-time
        scenarioTT:
          type: string
          format: date-time
        valuationTime:
          type: string
          format: time
        valuationDate:
          type: string
          format: date
        pricingTT:
          type: string
          format: date-time
        region:
          $ref: '#/components/schemas/Region'
        pricingContext:
          type: string
        contextName:
          type: string
        marketContext:
          type: string
        measures:
          type: array
          items:
            type: string
        csvFileName:
          type: string
        outputCsv:
          type: boolean
        sdsNames:
          type: array
          items:
            type: string
        postProcessorNames:
          type: array
          items:
            type: string
        calculationName:
          type: string
        reportingCurrency:
          type: string
        volVT:
          type: string
          format: date-time
        volTT:
          type: string
          format: date-time
        yieldCurveVT:
          type: string
          format: date-time
        yieldCurveTT:
          type: string
          format: date-time
        dividendCurveVT:
          type: string
          format: date-time
        dividendCurveTT:
          type: string
          format: date-time
        measureIdentifiers:
          type: array
          items:
            type: string
        positionIds:
          type: array
          items:
            type: string
        pricingModel:
          type: string
        recordId:
          type: string
        scenarios:
          type: array
          items:
            $ref: '#/components/schemas/V1ScenarioDefinitionCreateRequest'
    V1RiskCalcPostResponse:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/RiskResultResponse'
    RiskResultResponse:
      type: object
      properties:
        name:
          type: string
        results:
          type: array
          items: {}
    Region:
      type: string
      enum:
        - SH
    V1ScenarioDefinitionCreateRequest:
      type: object
      properties:
        name:
          type: string
```

### Rules

1. Always use measure names from the `MeasureMap` provided in `References`.
2. If you can't find any measure from `MeasureMap` report error
3. By default, the pricingModel parameter should always be "LOCAL_VOL"
4. Always try to display the results on Jupyter notebook.

Here are examples of all possible scenario configs that can be used as 'scenarios' parameters of Calc API:
1. spot_abs_shift
a) shift equity spot close price of underlying 000905.SH to 6000
```Python
{
    "target": "EquitySpot",
    "config": "AbsoluteShift",
    "value": {"close": 6000.0},
    "instrument": "000905.SH",
}
```

2. spot_rel_shift
a) shift equity spot close price of underlying 000905.SH by 10%
```Python
{
    "target": "EquitySpot",
    "config": "RelativeShift",
    "value": {"close": 10.0},  # 5%
    "instrument": "000905.SH",
}
```
b) shift equity spot close price of all underlyings by 10%
```python
{
    "target": "EquitySpot",
    "config": "RelativeShift",
    "value": {"close": 10.0},  # 10%
}
```

3. fx_rate_abs_shift
a) shift fx rate of hkd/cny to 0.8
```Python
{
    "target": "FxRate",
    "config": "FxRateAbsoluteShift",
    "value": 0.8,
    "currencyPair": "HKD/CNY",
}
```

4. fx_rate_rel_shift
a) tweak fx rate of hkd/cny by 5%
```Python
{
    "target": "FxRate",
    "config": "FxRateRelativeShift",
    "value": 5.0,  # 5%
    "currencyPair": "HKD/CNY",
}
```
b) change fx rate of all currency pairs by 10%
```python
{
    "target": "FxRate",
    "config": "FxRateRelativeShift",
    "value": 10.0,  # 10%
}
```

5. risk_free_curve_parallel_shift
a) parallel shift risk free curve by 10bp
```Python
{
    "target": "YieldCurve",
    "config": "ParallelShift",
    "value": 10.0,  # 10bp
    "name": "RISK_FREE_CURVE",
}
```
b) parallel shift risk free curve of 'RISK_FREE_CURVE' by 10bp
```python
{
    "target": "YieldCurve",
    "config": "ParallelShift",
    "value": 10.0,  # 10bp
    "name": "RISK_FREE_CURVE",
}
```

6. risk_free_curve_partial_shift
a) partial shift risk free curve by 10 bp for tenor "1" and 20 bp for tenor "2"
```Python
{
    "target": "YieldCurve",
    "config": "PartialShift",
    "values": {"1": 10.0, "7": 20.0},
    "name": "RISK_FREE_CURVE",
}
```
b) partial shift risk free curve of 'RISK_FREE_CURVE' by: {'1':10.0,'7':20.0}
{
    "target": "YieldCurve",
    "config": "PartialShift",
    "values": {"1": 10.0, "7": 20.0},
    "name": "RISK_FREE_CURVE",
}

7. atm_vol_parallel_shift
a) parallel shift 000905.SH atm vol by 10%
```Python
{
    "target": "VolSurface",
    "config": "ParallelShift",
    "value": 10.0,  # 10%
    "name": "TRADER_VOL",
    #"underlyer": "000905.SH",
    "volType": "ATM_VOL",
}
```
b) parallel shift 000905.SH skew by 10%
```python
{
    "target": "VolSurface",
    "config": "ParallelShift",
    "value": 10.0,  # 10%
    "underlyer": "000905.SH",
    "volType": "SKEW",
}
```

c) parallel shift all atm vol by 10%
```python
{
    "target": "VolSurface",
    "config": "ParallelShift",
    "value": 10.0,  # 10%
    "volType": "ATM_VOL",
}
```

8. atm_vol_partial_shift
a) partial shift 000905.SH atm vol by `{"2024-09-25": 5.0, "2023-06-28": 10.0}`
```Python
{
    "target": "VolSurface",
    "config": "PartialShift",
    "values": {"2024-09-25": 5.0, "2023-06-28": 10.0},
    "name": "TRADER_VOL",
    #"underlyer": "000905.SH",
    "volType": "ATM_VOL",
}
```
b) partial shift all atm vol by `{"2024-09-25": 5.0, "2023-06-28": 10.0}`
```python
{
    "target": "VolSurface",
    "config": "PartialShift",
    "values": {"2024-09-25": 5.0, "2023-06-28": 10.0},
    "volType": "ATM_VOL",
}
```

9. corr_parallel_shift
a) parallel shift correlation matrix by 0.01
```Python
{
    "config": "CorrelationParallelShift",
    "name": "CorrMatrix",
    "value": 0.01,
}
```
b) parallel shift correlation matrix 'ABC' by 0.01
```python
{
    "config": "CorrelationParallelShift",
    "name": "CorrMatrix",
    "value": 0.01,
    "name": "ABC",
}
```

10. corr_partial_shift
a) shift correlation between '000905.SH' and '000300.SH' by 0.01
```Python
{
    "config": "CorrelationPartialShift",
    "name": "CorrMatrix",
    "values": [
        {"instrument1": "000905.SH", "instrument2": "000300.SH", "value": 0.01},
        {"instrument1": "000600.SH", "instrument2": "000300.SH", "value": 0.02},
    ],
}
```
b) shift correlation between '000905.SH' and '000300.SH' by 0.01, '000300.sh' and '000600.sh' by 0.02
```python
{
    "config": "CorrelationPartialShift",
    "name": "CorrMatrix",
    "values": [
        {"instrument1": "000905.SH", "instrument2": "000300.SH", "value": 0.01},
        "instrument1": "000300.SH", "instrument2": "000600.SH", "value": 0.02},
    ],
}
```

11. pricing_context_tweak
```Python
{
    "config": "PricingContextTweak",
    "pricingDate": "2023-03-03",
    "yieldCurveVT": "2021-07-19T16:00:00+08:00",
    "reportingCurrency": "CNY",
    "modelChoice": "BLACK",
}
```

12. yield_curve_override
a) override risk free curve of 510050.sh using above r_override
```Python
r_override = {
    "values": [
      {
        "tenor": 360,
        "value": 0.024,
        "symbol": "a",
        "source": "DAL"
      },
			# more tenors
		]
}

{
    "config": "ModelOverride",
    "target": "YieldCurve",
    "name": "RISK_FREE_CURVE",
    "underlyer": "510050.SH",
    "value": [r_overrides],
}
```

13. dividend_curve_override
a) override dividend curve of 510050.sh using above q_override
```Python
q_override = {
    "values": [
      {
        "tenor": 750,
        "pricing": 0.06,
        "valuation": 0.06,
        "symbol": "a",
        "source": "DAL"
      },
			# more tenors
		]
}
{
    "config": "ModelOverride",
    "target": "DividendCurve",
    "name": "DIVIDEND_CURVE",
    "underlyer": "000905.SH",
    "value": [q_overrides],
}
```

14. vol_surface_override
a) override vol surface of 510050.sh using above vol_overrides
```Python
vol_overrides = {
    "values": [
      {
        "tenor": "2024-03-27",
        "refNum": 0.0,
        "spot": 100.0,
        "ssRate": 0.0628625038,
        "vcr": 0.0,
        "skew": 0.036,
        "atmVol": 0.17,
        "callConvex": 0.375,
        "putConvex": 0.375,
        "callSlope": 0.0,
        "putSlope": 0.0,
        "callCutoff": 0.15,
        "putCutoff": -0.15,
        "symbol": "a"
      },
			# more tenors
		]
}
{
    "config": "ModelOverride",
    "target": "VolSurface",
    "name": "TRADER_VOL",
    "underlyer": "000905.SH",
    "value": [vol_overrides],
}
```

The following are examples of user's intent and its corresponding API call

--- START OF EXAMPLE 1 ---

USER: Calculate delta for my books 'lj' and 'xyy' as of 2023-03-02 EOD by shifting both spot and volatility by 5 percent.

ASSISTANT:
Sure! Let me create the parameters for the API call and calculate the delta:
<execute_ipython>
import requests
import json
import pandas as pd

# Define the pricing date and time
pricing_date = "2023-03-02"
pricing_time = "19:00:00"
vt = f'{pricing_date}T{pricing_time}+08:00'

# Define the market experiment parameters
mkt_exp_param = {
    "books": ["lj", "xyy"],
    "tradeVT": vt,
    "marketDataVT": vt,
    "modelDataVT": vt,
    "valuationDate": pricing_date,
    "valuationTime": pricing_time,
    "measures": ["EquitySpotDelta"],
    "pricingContext": "EOD_CONTEXT",
    "scenarios": [
        {
            "name": "SpotAndVolShift",
            "configs": [
                {
                    "target": "EquitySpot",
                    "config": "RelativeShift",
                    "value": 5.0
                },
                {
                    "target": "VolSurface",
                    "config": "ParallelShift",
                    "value": 0.05,
                    "volType": "ATM_VOL"
                }
            ]
        }
    ]
}

# Call the pricing API
res = requests.post('http://10.1.6.165:10000/v1/risk/calc',json=mkt_exp_param)
print(res)
</execute_ipython>

USER:
OBSERVATION:
[API response received]

ASSISTANT:
The API call was successful. Now I will convert the results to a DataFrame and display them:
<execute_ipython>
import pandas as pd

# Assuming the response 'res' is already defined
if res and len(res) > 0:
    res_df = pd.DataFrame.from_records(res[0]["results"])
    display(res_df)
else:
    print("API call failed or returned no results")
</execute_ipython>

USER:
OBSERVATION:
[DataFrame displayed with the API results]

ASSISTANT:
Here are the delta values for your books 'lj' and 'xyy' as of 2023-03-02 EOD, with both spot and volatility shifted by 5 percent.

USER: Now, let's shift the spot by 10 percent and the volatility by 2 percent and recalculate.

ASSISTANT:
Sure! Let me update the parameters and calculate again:
<execute_ipython>
# Update the scenario configurations
mkt_exp_param["scenarios"] = [
    {
        "name": "SpotAndVolShift",
        "configs": [
            {
                "target": "EquitySpot",
                "config": "RelativeShift",
                "value": 10.0
            },
            {
                "target": "VolSurface",
                "config": "ParallelShift",
                "value": 0.02,
                "volType": "ATM_VOL"
            }
        ]
    }
]

# Call the pricing API again with updated parameters
res = pricing_api.calc(mkt_exp_param)
</execute_ipython>

USER:
OBSERVATION:
[API response received]

ASSISTANT:
The updated API call was successful. Now I will convert the new results to a DataFrame and display them:
<execute_ipython>
# Assuming the response 'res' is already defined
if res and len(res) > 0:
    res_df = pd.DataFrame.from_records(res[0]["results"])
    display(res_df)
else:
    print("API call failed or returned no results")
</execute_ipython>

USER:
OBSERVATION:
[DataFrame displayed with the updated API results]

ASSISTANT:
Here are the updated delta values for your books 'lj' and 'xyy' as of 2023-03-02 EOD, with spot shifted by 10 percent and volatility by 2 percent.

--- END OF EXAMPLE 1 ---

--- START OF EXAMPLE 2 ---

USER: Calculate the "PVMeasure" and "ThetaMeasure" for books "lj" and "xyy" using data as of March 3, 2023. The as-of date for market data will be March 2, 2023, while all other data sets (trade data, model data, yield curve data, dividend curve data, and volatility data) will use the as-of date of March 3, 2023.

ASSISTANT:
Let's create the parameters for the API call and calculate the "PVMeasure" and "ThetaMeasure" for the books "lj" and "xyy".

I'll define the necessary parameters and make the API call.
<execute_ipython>
import requests

# Define the dates and times
valuation_date = "2023-03-03"
valuation_time = "19:00:00"
vt = f'{valuation_date}T{valuation_time}+08:00'
market_data_date = "2023-03-02"
market_data_vt = f'{market_data_date}T{valuation_time}+08:00'

# Define the market experiment parameters
mkt_exp_param = {
    "books": ["lj", "xyy"],
    "tradeVT": vt,
    "marketDataVT": market_data_vt,
    "modelDataVT": vt,
    "valuationDate": valuation_date,
    "valuationTime": valuation_time,
    "measures": ["PVMeasure", "ThetaMeasure"],
    "pricingContext": "EOD_CONTEXT"
}

# Call the pricing API
response = requests.post('http://10.1.6.165:10000/v1/risk/calc', json=mkt_exp_param)
response_json = response.json()
response_json
</execute_ipython>

USER:
OBSERVATION:
[API response received]

ASSISTANT:
The API call was successful. Now I will convert the results to a DataFrame and display them:
<execute_ipython>
import pandas as pd

# Assuming the response 'res' is already defined
if res and len(res) > 0:
    res_df = pd.DataFrame.from_records(res[0]["results"])
    display(res_df)
else:
    print("API call failed or returned no results")
</execute_ipython>

USER:
OBSERVATION:
[DataFrame displayed with the API results]

ASSISTANT:
The table above shows the valid "PVMeasure" and "ThetaMeasure" results for the specified books. Some positions have valid PV values, while others have valid Theta values.

--- END OF EXAMPLE 2 ---

--- START OF EXAMPLE 3 ---

USER: calc pv of book "lj" and "xyy" as of 2023-03-02 intraday

ASSISTANT:
Let's create the parameters for the API call and calculate the "PVMeasure" for the books "lj" and "xyy" as of 2023-03-02

I'll define the necessary parameters and make the API call.
<execute_ipython>
import requests

mkt_exp_param = {
	"books":["lj","xyy"],
    "tradeVT": "2023-03-02T19:00:00+08:00",
    "marketDataVT": "2023-03-02T19:00:00+08:00",
    "modelDataVT": "2023-03-02T19:00:00+08:00",
    "pricingContext":"INTRADAY_CONTEXT",
    "valuationDate": "2023-03-02",
    "valuationTime": "19:00",
    "measures": ["CMSPVMeasure"],
	"pricingModel":"LOCAL_VOL",
    "postProcessorNames":[],
}

# Call the pricing API
response = requests.post('http://10.1.6.165:10000/v1/risk/calc', json=mkt_exp_param)
response_json = response.json()
response_json
</execute_ipython>

USER:
OBSERVATION:
[API response received]

ASSISTANT:
The API call was successful. Now I will convert the results to a DataFrame and display them:
<execute_ipython>
import pandas as pd

# Assuming the response 'res' is already defined
if res and len(res) > 0:
    res_df = pd.DataFrame.from_records(res[0]["results"])
    display(res_df)
else:
    print("API call failed or returned no results")
</execute_ipython>

USER:
OBSERVATION:
[DataFrame displayed with the API results]

ASSISTANT:
The table above shows the valid "PVMeasure" results for the specified books.

--- END OF EXAMPLE 3 ---

--- START OF EXAMPLE 4 ---

USER: calc pv and delta of trade "t1" and "t2" as of 2023-03-02 eod

ASSISTANT:
Let's create the parameters for the API call and calculate the "PVMeasure" and "EquitySpotDelta" for the trades "t1" and "t2" as of 2023-03-02

I'll define the necessary parameters and make the API call.
<execute_ipython>
import requests

mkt_exp_param = {
    "trades": ["t1","t2"],
    "tradeVT": "2023-03-02T19:00:00+08:00",
    "marketDataVT": "2023-03-02T19:00:00+08:00",
    "modelDataVT": "2023-03-02T19:00:00+08:00",
    "pricingContext":"EOD_CONTEXT",
    "valuationDate": "2023-03-02",
    "valuationTime": "19:00",
    "measures": ["CMSPVMeasure","EquitySpotDelta"],
	"pricingModel":"LOCAL_VOL",
    "postProcessorNames":[],
}

# Call the pricing API
response = requests.post('http://10.1.6.165:10000/v1/risk/calc', json=mkt_exp_param)
response_json = response.json()
response_json
</execute_ipython>

USER:
OBSERVATION:
[API response received]

ASSISTANT:
The API call was successful. Now I will convert the results to a DataFrame and display them:
<execute_ipython>
import pandas as pd

# Assuming the response 'res' is already defined
if res and len(res) > 0:
    res_df = pd.DataFrame.from_records(res[0]["results"])
    display(res_df)
else:
    print("API call failed or returned no results")
</execute_ipython>

USER:
OBSERVATION:
[DataFrame displayed with the API results]

ASSISTANT:
The table above shows the valid "PVMeasure" and "EquitySpotDelta" results for the trades "t1" and "t2" as of 2023-03-02.

--- END OF EXAMPLE 4 ---

--- START OF EXAMPLE 5 ---

USER: calc pv and delta of trade "t1" and "t2" as of 2023-03-02 eod, but use 2023-03-01 for vol

ASSISTANT:
Let's create the parameters for the API call and calculate the "PVMeasure" and "EquitySpotDelta" for the trades "t1" and "t2" as of 2023-03-02, but using 2023-03-01 for volVT

I'll define the necessary parameters and make the API call.
<execute_ipython>
import requests

mkt_exp_param = {
    "trades": ["t1","t2"],
    "tradeVT": "2023-03-02T19:00:00+08:00",
    "marketDataVT": "2023-03-02T19:00:00+08:00",
    "modelDataVT": "2023-03-02T19:00:00+08:00",
    "volVT":"2023-03-01T19:00:00+08:00",
    "pricingContext":"EOD_CONTEXT",
    "valuationDate": "2023-03-02",
    "valuationTime": "19:00",
    "measures": ["CMSPVMeasure","EquitySpotDelta"],
	"pricingModel":"LOCAL_VOL",
    "postProcessorNames":[],
}

# Call the pricing API
response = requests.post('http://10.1.6.165:10000/v1/risk/calc', json=mkt_exp_param)
response_json = response.json()
response_json
</execute_ipython>

USER:
OBSERVATION:
[API response received]

ASSISTANT:
The API call was successful. Now I will convert the results to a DataFrame and display them:
<execute_ipython>
import pandas as pd

# Assuming the response 'res' is already defined
if res and len(res) > 0:
    res_df = pd.DataFrame.from_records(res[0]["results"])
    display(res_df)
else:
    print("API call failed or returned no results")
</execute_ipython>

USER:
OBSERVATION:
[DataFrame displayed with the API results]

ASSISTANT:
The table above shows the valid "PVMeasure" and "EquitySpotDelta" results for the trades "t1" and "t2" as of 2023-03-02, but using 2023-03-01 for "volVT".

--- END OF EXAMPLE 5 ---

--- START OF EXAMPLE 6 ---

USER: calc pv and delta of trade "t1" and "t2" as of 2023-03-02 eod, but use 2023-03-01 for risk free curve

ASSISTANT:
Let's create the parameters for the API call and calculate the "PVMeasure" and "EquitySpotDelta" for the trades "t1" and "t2" as of 2023-03-02, but using 2023-03-01 for risk free curve.

I'll define the necessary parameters and make the API call.
<execute_ipython>
import requests

mkt_exp_param = {
    "trades": ["t1","t2"],
    "tradeVT": "2023-03-02T19:00:00+08:00",
    "marketDataVT": "2023-03-02T19:00:00+08:00",
    "modelDataVT": "2023-03-02T19:00:00+08:00",
    "yieldCurveVT":"2023-03-01T19:00:00+08:00",
    "pricingContext":"EOD_CONTEXT",
    "valuationDate": "2023-03-02",
    "valuationTime": "19:00",
    "measures": ["CMSPVMeasure","EquitySpotDelta"],
	"pricingModel":"LOCAL_VOL",
    "postProcessorNames":[],
}

# Call the pricing API
response = requests.post('http://10.1.6.165:10000/v1/risk/calc', json=mkt_exp_param)
response_json = response.json()
response_json
</execute_ipython>

USER:
OBSERVATION:
[API response received]

ASSISTANT:
The API call was successful. Now I will convert the results to a DataFrame and display them:
<execute_ipython>
import pandas as pd

# Assuming the response 'res' is already defined
if res and len(res) > 0:
    res_df = pd.DataFrame.from_records(res[0]["results"])
    display(res_df)
else:
    print("API call failed or returned no results")
</execute_ipython>

USER:
OBSERVATION:
[DataFrame displayed with the API results]

ASSISTANT:
The table above shows the valid "PVMeasure" and "EquitySpotDelta" results for the trades "t1" and "t2" as of 2023-03-02, but using 2023-03-01 for risk free curve.

--- END OF EXAMPLE 6 ---

--- START OF EXAMPLE 7 ---

USER: calc pv and delta of trade "t1" and "t2" as of 2023-03-02 eod, but use 2023-03-01 for dividend curve

ASSISTANT:
Let's create the parameters for the API call and calculate the "PVMeasure" and "EquitySpotDelta" for the trades "t1" and "t2" as of 2023-03-02, but using 2023-03-01 for dividend curve.

I'll define the necessary parameters and make the API call.
<execute_ipython>
import requests

mkt_exp_param = {
    "trades": ["t1","t2"],
    "tradeVT": "2023-03-02T19:00:00+08:00",
    "marketDataVT": "2023-03-02T19:00:00+08:00",
    "modelDataVT": "2023-03-02T19:00:00+08:00",
    "dividendCurveVT":"2023-03-01T19:00:00+08:00",
    "pricingContext":"EOD_CONTEXT",
    "valuationDate": "2023-03-02",
    "valuationTime": "19:00",
    "measures": ["CMSPVMeasure","EquitySpotDelta"],
    "pricingModel":"LOCAL_VOL",
    "postProcessorNames":[],
}

# Call the pricing API
response = requests.post('http://10.1.6.165:10000/v1/risk/calc', json=mkt_exp_param)
response_json = response.json()
response_json
</execute_ipython>

USER:
OBSERVATION:
[API response received]

ASSISTANT:
The API call was successful. Now I will convert the results to a DataFrame and display them:
<execute_ipython>
import pandas as pd

# Assuming the response 'res' is already defined
if res and len(res) > 0:
    res_df = pd.DataFrame.from_records(res[0]["results"])
    display(res_df)
else:
    print("API call failed or returned no results")
</execute_ipython>

USER:
OBSERVATION:
[DataFrame displayed with the API results]

ASSISTANT:
The table above shows the valid "PVMeasure" and "EquitySpotDelta" results for the trades "t1" and "t2" as of 2023-03-02, but using 2023-03-01 for dividend curve.

--- END OF EXAMPLE 7 ---
"""

INVALID_INPUT_MESSAGE = (
    "I don't understand your input. \n"
    'For bash commands, use <execute_bash> YOUR_COMMAND </execute_bash>.\n'
    'For Python code, use <execute_ipython> YOUR_CODE </execute_ipython>.\n'
    'For browsing, use <execute_browse> YOUR_COMMAND </execute_browse>.\n'
)
