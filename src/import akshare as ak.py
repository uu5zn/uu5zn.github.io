import akshare as ak
import pandas as pd
data = ak.macro_china_shibor_all()
print(data.head())
data['日期'] = pd.to_datetime(data['日期'], errors='coerce', format='%Y-%m-%d')
data = data.set_index('日期')
series_data = data['1M-定价'].iloc[-300:]
print(series_data.head())