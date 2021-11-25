import pandas as pd
import os
import re
import numpy as np
import datetime
import math
from geopy.distance import geodesic

pd.options.mode.chained_assignment = None  # default='warn'
######################快速路小汽车时辰分布#########################################################

path = r"D:/Hyder安诚/调查结果数据/道路流量数据/15小时断面/快速路"
files= os.listdir(path)
data=pd.DataFrame()
for file in files:
    print(file)
    data0=pd.read_excel(path+"/"+file,usecols='A:L')
    data = pd.concat([data, data0], ignore_index=True)
data=data.fillna(0)
data['调查时段']=data['调查时段'].replace(['22:15-22;30','22;45-23;00'],['22:15-22:30','22:45-23:00'])
data=data[data['调查时段']!=' ']
data['hour']=data['调查时段'].apply(lambda x: int(x[0:2]))
def periodfun(hour):
    if int(hour) ==9:
        return 'AM_Peak'
    elif int(hour) ==19:
        return 'PM_Peak'
    elif (int(hour) >19 or int(hour) <9):
        return 'Night_time'
    elif (int(hour) >9 and int(hour) <19):
        return 'Day_time'
    else:
        return 'Unknown'

data['period'] = data['hour'].apply(lambda x:periodfun(x) )
data_period=data.groupby('period')['小客车'].sum().reset_index()
data_period['pct']=round(data_period['小客车']/data_period['小客车'].sum(),4)
data_hour=data.groupby('hour')['小客车'].sum().reset_index()
data_hour['pct']=round(data_hour['小客车']/data_hour['小客车'].sum(),4)

data_hour.to_excel(r'D:/Hyder安诚/调查结果数据/道路流量数据/15小时快速路hour.xlsx',index=False)
data_period.to_excel(r'D:/Hyder安诚/调查结果数据/道路流量数据/15小时快速路period.xlsx',index=False)