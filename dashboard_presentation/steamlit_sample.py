# First Author: Angus Au-Yeung
# Second Author: Lee Yat Shun, Jasper
# Copyright (c) 2023 Angus Au-Yeung, Lee Yat Shun, Jasper. All rights reserved.

import pandas as pd
import numpy as np
import streamlit as st  # pip install streamlit
import yfinance as yf   # pip install yfinance
from stocknews import StockNews # pip install stocknews
import plotly.express as px #!pip install pip install plotly-express
from alpha_vantage.fundamentaldata import FundamentalData #pip install alpha-vantage

from datetime import datetime, timedelta 
import matplotlib.pyplot as plt
from scipy.stats import norm
from arch import arch_model
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import vartests

# call the package from _test.py
from var_tests import binomial_test, kupiec_pof_test, christoffersen_test, traffic_light_test
from caviar import CaviarModel

#side bar

st.title('Stock Dashboard')
ticker = st.sidebar.text_input('Ticker')
#start_date = st.sidebar.date_input('Start date')
#end_date = st.sidebar.date_input('End date')

start_date = datetime(2015,1,1)
end_date = datetime.today()
obs_day = end_date - timedelta(days=252*2)
forecast_day = obs_day + timedelta(days=1)
data = yf.download(ticker, start=start_date, end=end_date)
returns = data['Adj Close'].pct_change().dropna()
returns = returns.apply(lambda x: x*100)

option = st.selectbox("CARViar model",("adaptive", "symmetric", "asymmetric", "igarch"))
method = ['mle', 'RQ']
quantile = 0.05

caviar = CaviarModel(quantile, model=option, method=method[0])

caviar.fit(returns.loc[:obs_day])
c_VaRs = caviar.predict(returns.loc[forecast_day:], caviar.VaR0_out)
current_CVaRs = round(c_VaRs[-1],4)
previous_CVaRs = round(c_VaRs[-2],4)
st.metric(label="Current_VaRs_CARViar", value=current_CVaRs, delta= round(previous_CVaRs - current_CVaRs,4), delta_color='inverse')

#GARCH model
result = []
for i in range(1,3):
  for j in range(1,3):
    am = arch_model(returns, vol='Garch', mean="Zero", p=i, q=j)
    res = am.fit(disp='off', last_obs=obs_day)
    result.append({'mod':res, 'aic':res.aic})

result = sorted(result, key=lambda x: x['aic'])
res = result[0]['mod']

forecasts = res.forecast(start = forecast_day, reindex=False)
cond_mean = forecasts.mean
cond_var = forecasts.variance
q = am.distribution.ppf([0.01, 0.05])
value_at_risk = np.sqrt(cond_var).values*q[None,:]
value_at_risk = pd.DataFrame(value_at_risk, columns=['1%','5%'],index=cond_var.index)
VaRs = value_at_risk['5%']
current_GVaRs = round(VaRs[-1],4)
previous_GVaRs = round(VaRs[-2],4)
st.metric(label="Current_VaRs_GARCH", value=current_GVaRs, delta= round(previous_GVaRs - current_GVaRs,4), delta_color='inverse')

#download and plot chart

#st.metric("VaR:", VaR_indicator[:-1])
fig = px.line(data, x=data.index, y=data['Adj Close'], title=ticker)
#fig.add_scatter(x=data.index, y=c_VaRs[:-1], title="5% quantile")
st.plotly_chart(fig)

#run test to ensure model significant
b = binomial_test(returns.loc[forecast_day:], VaRs, quantile)
t, _, _ = traffic_light_test(returns.loc[forecast_day:], VaRs, quantile, num_obs=250, baseline=3)
k = kupiec_pof_test(returns.loc[forecast_day:], VaRs, quantile)
c = christoffersen_test(returns.loc[forecast_day:], VaRs)

st.header("Test for GARCH")
col1, col2, col3, col4 = st.columns(4)
col1.metric("binomial", round(b,4))
col2.metric("traffic_light", t)
col3.metric("kupiec", k)
col4.metric("christoffersen", round(c,4))

#run test to ensure model significant
bi = binomial_test(returns.loc[forecast_day:], c_VaRs[:-1], caviar.quantile)
dq = caviar.dq_test(returns.loc[forecast_day:], 'out')
ku = kupiec_pof_test(returns.loc[forecast_day:], c_VaRs[:-1], caviar.quantile)
ch = christoffersen_test(returns.loc[forecast_day:], c_VaRs[:-1])
tr, _, _ = traffic_light_test(returns.loc[forecast_day:], c_VaRs[:-1], caviar.quantile, num_obs=250, baseline=3)

st.header("Test for CARViaR")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("DQ test", round(dq,4))
col2.metric("binomial", round(bi,4))
col3.metric("traffic light", tr)
col4.metric("kupiec", ku)
col5.metric("christoffersen", round(ch,4))

#select CAViaR model by p-value
#c_beta_p = caviar.beta_pvals

#display inf
pricing_data, fundamental_data, news = st.tabs(["Price", "Fundamental Data", "Top 10 news"])
trading_date = 252

with pricing_data:
  st.header("Price Movements")
  data2 = data
  data2["% change"] = data["Adj Close"]/data["Adj Close"].shift(1) - 1
  data2.dropna(inplace=True)
  st.write(data2)
  annual_return = data2["% change"].mean()*trading_date*100
  st.write("Annual_return:", annual_return,"%")
  stdev = np.std(data2['% change'])*np.sqrt(trading_date)
  st.write("Standard Deviation:", stdev*100,"%")
  st.write("1-year-return mean:", data2["% change"].mean())
  st.write("Risk Adjusted return:", annual_return/(stdev*100))

with news:
  st.header(f"News of {ticker}")
  sn = StockNews(ticker, save_news=False)
  df_news = sn.read_rss()
  for i in range(10):
    st.subheader(f'News {i+1}')
    st.write(df_news['published'][i])
    st.write(df_news['title'][i])
    st.write(df_news['summary'][i])
    title_sentiment = df_news['sentiment_title'][i]
    st.write(f'Title Sentiment {title_sentiment}')
    news_sentiment = df_news['sentiment_summary'][i]
    st.write(f'News Sentiment {news_sentiment}')

with fundamental_data:
  key = "43OTW409OLX93FWD"  #get a key here: https://www.alphavantage.co/support/#api-key #43OTW409OLX93FWD
  fd = FundamentalData(key, output_format = "pandas")
  st.subheader("Balance Sheet")
  balance_sheet = fd.get_balance_sheet_annual(ticker)[0]
  bs = balance_sheet.T[2:]
  bs.columns = list(balance_sheet.T.iloc[0])
  st.write(bs)
  st.subheader('Income Statement')
  income_statement = fd.get_income_statement_annual(ticker)[0]
  is1 = income_statement.T[2:]
  is1.columns = list(income_statement.T.iloc[0])
  st.write(is1)
  st.subheader("Cash Flow Statement")
  cash_flow = fd.get_cash_flow_annual(ticker)[0]
  cf = cash_flow.T[2:]
  cf.colums = list(cash_flow.T.iloc[0])
  st.write(cf)