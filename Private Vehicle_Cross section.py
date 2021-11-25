import pandas as pd
import os
import re
import numpy as np
import datetime
import math
from geopy.distance import geodesic

pd.options.mode.chained_assignment = None  # default='warn'
######################校核线小客车满载率调查结果分析#########################################################

path = r"D:/调查结果数据/小客车数据（已修）/小客车数据"
files= os.listdir(path)
data=pd.DataFrame()
for file in files:
    print(file)
    data0=pd.read_excel(path+"/"+file,usecols='A:Q')
    if data0.shape[0]>55: #双方向
        row = data0.shape[0] - 56
        print('双方向', data0.columns[0], data0.iloc[row, 0])
        dir1=data0.columns[0]
        if '南向北' in dir1:
            dir1='由南向北'
        elif '北向南'in dir1:
            dir1='由北向南'
        elif '东向西' in dir1:
            dir1='由东向西'
        elif '西向东' in dir1:
            dir1='由西向东'

        dir2=data0.iloc[row, 0]
        if '南向北' in dir1:
            dir2='由南向北'
        elif '北向南'in dir1:
            dir2='由北向南'
        elif '东向西' in dir1:
            dir2='由东向西'
        elif '西向东' in dir1:
            dir2='由西向东'

        data1=data0.loc[3:,:]
        data1.columns = ['序号', '点位编号', '点位名称', '断面位置描述', '调查员姓名', '联系电话', '时间段',
                         '小汽车一人', '小汽车两人', '小汽车三人', '小汽车四人', '小汽车五人', '出租车一人',
                         '出租车两人', '出租车三人', '出租车四人', '出租车五人']
        data1['mark']=data1['点位编号'].apply(lambda x: 'N'if isinstance(x,str) else 'Y')
        data1 = data1[data1['mark']=='N'].dropna(subset=['序号', '点位编号', '点位名称', '断面位置描述']).drop(columns=['mark'])
        print(data1.shape[0])
        data1['方向']=''
        data1.loc[data1.index<list(data1[(data1['序号']==1)|(data1['时间段']=='8:00-8:15')].index)[1],'方向']=dir1
        data1.loc[data1.index >= list(data1[(data1['序号']==1)|(data1['时间段']=='8:00-8:15')].index)[1], '方向'] = dir2
    else:
        print('单方向',data0.columns[0])
        data1=data0
        data1.columns = ['序号', '点位编号', '点位名称', '断面位置描述', '调查员姓名', '联系电话', '时间段',
                         '小汽车一人', '小汽车两人', '小汽车三人', '小汽车四人', '小汽车五人', '出租车一人',
                         '出租车两人', '出租车三人', '出租车四人', '出租车五人']
        data1['mark'] = data1['点位编号'].apply(lambda x: 'N' if (isinstance(x, str))  else 'Y')
        data1 = data1[data1['mark'] == 'N'].dropna(subset=['序号', '点位编号', '点位名称', '断面位置描述']).drop(
            columns=['mark'])
        data1['方向'] = '单向'
    data=pd.concat([data,data1])
data=data.loc[(data['序号']!='序号')&(data['序号']!='序号 '),:].reset_index()
crosssection=pd.read_excel(r"D:/调查结果数据/小客车数据（已修）/小客车满载率调查点位.xlsx",sheet_name='Sheet1')
spot_district=pd.read_excel(r"D:/调查结果数据/小客车数据（已修）/小客车满载率调查点位.xlsx",sheet_name='行政区')
data=pd.merge(data,crosssection[['编号','断面位置描述','核查线']],how='left',left_on='点位编号',right_on='编号')
data=pd.merge(data,spot_district[['编号','行政区']],how='left',left_on='点位编号',right_on='编号')
data=data.drop(columns=['编号_x','编号_y', '调查员姓名', '联系电话','断面位置描述_x']).rename(columns={'断面位置描述_y':'断面位置描述'})
data_zip=data[['点位编号','行政区']].drop_duplicates()
data=data.replace(' ',0).replace('：',':')
data.to_excel(r'D:/调查结果数据/小客车数据（已修）/小客车combined.xlsx',index=False)

data=data.replace(' ',0).replace('：',':')
datan=data

for col in ['小汽车一人', '小汽车两人', '小汽车三人', '小汽车四人', '小汽车五人', '出租车一人',
                         '出租车两人', '出租车三人', '出租车四人', '出租车五人']:
    data[col]=data[col].apply(lambda x:float(x))
    datan.loc[datan['点位编号'] == 'J207', col] = datan.loc[datan['点位编号'] == 'J207', col] * 5
datan.loc[datan['点位编号']=='J115','小汽车一人']=datan.loc[datan['点位编号']=='J115','小汽车一人']*3

sum_spot=data.groupby(['点位编号', '点位名称', '断面位置描述']).agg(
    pc1=pd.NamedAgg(column='小汽车一人',aggfunc='sum'),
    pc2=pd.NamedAgg(column='小汽车两人',aggfunc='sum'),
    pc3=pd.NamedAgg(column='小汽车三人', aggfunc='sum'),
    pc4=pd.NamedAgg(column='小汽车四人',aggfunc='sum'),
    pc5=pd.NamedAgg(column='小汽车五人',aggfunc='sum'),
    tx1=pd.NamedAgg(column='出租车一人', aggfunc='sum'),
    tx2=pd.NamedAgg(column='出租车两人',aggfunc='sum'),
    tx3=pd.NamedAgg(column='出租车三人', aggfunc='sum'),
    tx4=pd.NamedAgg(column='出租车四人',aggfunc='sum'),
    tx5=pd.NamedAgg(column='出租车五人',aggfunc='sum'),
).reset_index().rename(columns={'pc1':'小汽车一人', 'pc2':'小汽车两人', 'pc3':'小汽车三人', 'pc4':'小汽车四人', 'pc5':'小汽车五人',
                                'tx1':'出租车一人','tx2':'出租车两人', 'tx3':'出租车三人', 'tx4':'出租车四人', 'tx5':'出租车五人'})

sum_spot['小汽车载客总数']=(sum_spot['小汽车一人']*1+sum_spot['小汽车两人']*2+sum_spot['小汽车三人']*3+sum_spot['小汽车四人']*4+sum_spot['小汽车五人']*5)
sum_spot['出租车载客总数']=(sum_spot['出租车两人']*1+sum_spot['出租车三人']*2+sum_spot['出租车四人']*3+sum_spot['出租车五人']*4)
sum_spot['小汽车']=sum_spot[['小汽车一人', '小汽车两人', '小汽车三人', '小汽车四人', '小汽车五人']].sum(axis=1)
sum_spot['出租车']=sum_spot[['出租车一人','出租车两人', '出租车三人', '出租车四人', '出租车五人']].sum(axis=1)
sum_spot['载客出租车']=sum_spot[['出租车两人', '出租车三人', '出租车四人', '出租车五人']].sum(axis=1)
sum_spot['小汽车载客率']=round(sum_spot['小汽车载客总数']/sum_spot['小汽车'],2)
sum_spot['出租车载客率']=round(sum_spot['出租车载客总数']/sum_spot['载客出租车'],2)

sum_spot_pct=sum_spot
for col in ['小汽车一人', '小汽车两人', '小汽车三人', '小汽车四人', '小汽车五人',
            '出租车一人','出租车两人', '出租车三人', '出租车四人', '出租车五人']:
    if '小汽车' in col:
        sum_spot_pct[col] = round(100 * sum_spot_pct[col] / sum_spot_pct['小汽车'], 2)
    elif '出租车' in col:
        sum_spot_pct[col] = round(100 * sum_spot_pct[col] / sum_spot_pct['出租车'], 2)

sum_passenger=data[['小汽车一人', '小汽车两人', '小汽车三人', '小汽车四人', '小汽车五人',
            '出租车一人','出租车两人', '出租车三人', '出租车四人', '出租车五人']].sum(axis=0).reset_index().rename(columns={'index':'载客情况',0:'总数'})
sum_passenger['比例']=0
total_pc=0
total_taxi=0
for i in sum_passenger.index:
    if '小汽车' in sum_passenger.loc[i,'载客情况']:
        sum_passenger.loc[i, '比例']=round(100*sum_passenger.loc[i, '总数']/sum_passenger.loc[0:5, '总数'].sum(),2)
        total_pc=total_pc+sum_passenger.loc[i, '总数']*(i+1)

    else:
        sum_passenger.loc[i, '比例'] = round(100 * sum_passenger.loc[i, '总数'] / sum_passenger.loc[5:, '总数'].sum(), 2)
        total_taxi = total_taxi + sum_passenger.loc[i, '总数'] * (i -5)

ave_pc=round(total_pc/sum_passenger.loc[0:4, '总数'].sum(),2)
ave_taxi=round(total_taxi/sum_passenger.loc[6:, '总数'].sum(), 2)
sum_passenger=sum_passenger.append([{'载客情况':'小汽车平均载客数', '总数':ave_pc}]).append([{'载客情况':'出租车平均载客数','总数':ave_taxi}])
print('小汽车平均载客数：{}    出租车平均载客数：{}'.format(ave_pc,ave_taxi))


sum_time=data.groupby(['时间段']).agg(
    pc1=pd.NamedAgg(column='小汽车一人',aggfunc='sum'),
    pc2=pd.NamedAgg(column='小汽车两人',aggfunc='sum'),
    pc3=pd.NamedAgg(column='小汽车三人', aggfunc='sum'),
    pc4=pd.NamedAgg(column='小汽车四人',aggfunc='sum'),
    pc5=pd.NamedAgg(column='小汽车五人',aggfunc='sum'),
    tx1=pd.NamedAgg(column='出租车一人', aggfunc='sum'),
    tx2=pd.NamedAgg(column='出租车两人',aggfunc='sum'),
    tx3=pd.NamedAgg(column='出租车三人', aggfunc='sum'),
    tx4=pd.NamedAgg(column='出租车四人',aggfunc='sum'),
    tx5=pd.NamedAgg(column='出租车五人',aggfunc='sum'),
).reset_index().rename(columns={'pc1':'小汽车一人', 'pc2':'小汽车两人', 'pc3':'小汽车三人', 'pc4':'小汽车四人', 'pc5':'小汽车五人',
                                'tx1':'出租车一人','tx2':'出租车两人', 'tx3':'出租车三人', 'tx4':'出租车四人', 'tx5':'出租车五人'})
sort_mapping=data.loc[0:51,'时间段'].reset_index().set_index('时间段')
sum_time['num'] = sum_time['时间段'].map(sort_mapping['index'])
sum_time=sum_time.sort_values('num').drop(columns=['num'])

sum_time_pct=sum_time
sum_time_pct['小汽车载客总数']=(sum_time_pct['小汽车一人']*1+sum_time_pct['小汽车两人']*2+sum_time_pct['小汽车三人']*3+sum_time_pct['小汽车四人']*4+sum_time_pct['小汽车五人']*5)
sum_time_pct['出租车载客总数']=(sum_time_pct['出租车两人']*1+sum_time_pct['出租车三人']*2+sum_time_pct['出租车四人']*3+sum_time_pct['出租车五人']*4)
sum_time_pct['小汽车']=sum_time_pct[['小汽车一人', '小汽车两人', '小汽车三人', '小汽车四人', '小汽车五人']].sum(axis=1)
sum_time_pct['出租车']=sum_time_pct[['出租车一人','出租车两人', '出租车三人', '出租车四人', '出租车五人']].sum(axis=1)
sum_time_pct['载客出租车']=sum_time_pct[['出租车两人', '出租车三人', '出租车四人', '出租车五人']].sum(axis=1)
sum_time_pct['小汽车载客率']=round(sum_time_pct['小汽车载客总数']/sum_time_pct['小汽车'],2)
sum_time_pct['出租车载客率']=round(sum_time_pct['出租车载客总数']/sum_time_pct['载客出租车'],2)
for col in ['小汽车一人', '小汽车两人', '小汽车三人', '小汽车四人', '小汽车五人',
            '出租车一人','出租车两人', '出租车三人', '出租车四人', '出租车五人']:
    if '小汽车' in col:
        sum_time_pct[col] = round(100 * sum_time_pct[col] / sum_time_pct['小汽车'], 2)
    elif '出租车' in col:
        sum_time_pct[col] = round(100 * sum_time_pct[col] / sum_time_pct['出租车'], 2)

def periodfun(x):
    x=str(x)
    if x.startswith('9'):
        return '早高峰'
    elif x.startswith('19'):
        return '晚高峰'
    elif x.startswith('1'):
        return '日间平峰'
    else:
        return '夜间平峰'
data['period']=data['时间段'].apply(lambda x:periodfun(x))
sum_period=data.groupby(['period']).agg(
    pc1=pd.NamedAgg(column='小汽车一人',aggfunc='sum'),
    pc2=pd.NamedAgg(column='小汽车两人',aggfunc='sum'),
    pc3=pd.NamedAgg(column='小汽车三人', aggfunc='sum'),
    pc4=pd.NamedAgg(column='小汽车四人',aggfunc='sum'),
    pc5=pd.NamedAgg(column='小汽车五人',aggfunc='sum'),
    tx1=pd.NamedAgg(column='出租车一人', aggfunc='sum'),
    tx2=pd.NamedAgg(column='出租车两人',aggfunc='sum'),
    tx3=pd.NamedAgg(column='出租车三人', aggfunc='sum'),
    tx4=pd.NamedAgg(column='出租车四人',aggfunc='sum'),
    tx5=pd.NamedAgg(column='出租车五人',aggfunc='sum'),
).reset_index().rename(columns={'pc1':'小汽车一人', 'pc2':'小汽车两人', 'pc3':'小汽车三人', 'pc4':'小汽车四人', 'pc5':'小汽车五人',
                                'tx1':'出租车一人','tx2':'出租车两人', 'tx3':'出租车三人', 'tx4':'出租车四人', 'tx5':'出租车五人'})
df_sort=pd.DataFrame({'period':['早高峰','日间平峰','晚高峰','晚间平峰']})
sort_mapping=df_sort.reset_index().set_index('period')
sum_period['num'] = sum_period['period'].map(sort_mapping['index'])
sum_period=sum_period.sort_values('num').drop(columns=['num'])

sum_period_pct=sum_period

sum_period_pct['小汽车载客总数']=(sum_period_pct['小汽车一人']*1+sum_period_pct['小汽车两人']*2+sum_period_pct['小汽车三人']*3+sum_period_pct['小汽车四人']*4+sum_period_pct['小汽车五人']*5)
sum_period_pct['出租车载客总数']=(sum_period_pct['出租车两人']*1+sum_period_pct['出租车三人']*2+sum_period_pct['出租车四人']*3+sum_period_pct['出租车五人']*4)
sum_period_pct['小汽车']=sum_period_pct[['小汽车一人', '小汽车两人', '小汽车三人', '小汽车四人', '小汽车五人']].sum(axis=1)
sum_period_pct['出租车']=sum_period_pct[['出租车一人','出租车两人', '出租车三人', '出租车四人', '出租车五人']].sum(axis=1)
sum_period_pct['载客出租车']=sum_period_pct[['出租车两人', '出租车三人', '出租车四人', '出租车五人']].sum(axis=1)
sum_period_pct['小汽车载客率']=round(sum_period_pct['小汽车载客总数']/sum_period_pct['小汽车'],2)
sum_period_pct['出租车载客率']=round(sum_period_pct['出租车载客总数']/sum_period_pct['载客出租车'],2)
for col in ['小汽车一人', '小汽车两人', '小汽车三人', '小汽车四人', '小汽车五人',
            '出租车一人','出租车两人', '出租车三人', '出租车四人', '出租车五人']:
    if '小汽车' in col:
        sum_period_pct[col] = round(100 * sum_period_pct[col] / sum_period_pct['小汽车'], 2)
    elif '出租车' in col:
        sum_period_pct[col] = round(100 * sum_period_pct[col] / sum_period_pct['出租车'], 2)

sum_period_pct['小汽车时辰分布']=round(sum_period_pct['小汽车']/sum_period_pct['小汽车'].sum(),4)
sum_period_pct['出租车时辰分布']=round(sum_period_pct['出租车']/sum_period_pct['出租车'].sum(),4)



sum_district=data.groupby(['行政区']).agg(
    pc1=pd.NamedAgg(column='小汽车一人',aggfunc='sum'),
    pc2=pd.NamedAgg(column='小汽车两人',aggfunc='sum'),
    pc3=pd.NamedAgg(column='小汽车三人', aggfunc='sum'),
    pc4=pd.NamedAgg(column='小汽车四人',aggfunc='sum'),
    pc5=pd.NamedAgg(column='小汽车五人',aggfunc='sum'),
    tx1=pd.NamedAgg(column='出租车一人', aggfunc='sum'),
    tx2=pd.NamedAgg(column='出租车两人',aggfunc='sum'),
    tx3=pd.NamedAgg(column='出租车三人', aggfunc='sum'),
    tx4=pd.NamedAgg(column='出租车四人',aggfunc='sum'),
    tx5=pd.NamedAgg(column='出租车五人',aggfunc='sum'),
).reset_index().rename(columns={'pc1':'小汽车一人', 'pc2':'小汽车两人', 'pc3':'小汽车三人', 'pc4':'小汽车四人', 'pc5':'小汽车五人',
                                'tx1':'出租车一人','tx2':'出租车两人', 'tx3':'出租车三人', 'tx4':'出租车四人', 'tx5':'出租车五人'})
sum_district_pct=sum_district

sum_district_pct['小汽车载客总数']=(sum_district_pct['小汽车一人']*1+sum_district_pct['小汽车两人']*2+sum_district_pct['小汽车三人']*3+sum_district_pct['小汽车四人']*4+sum_district_pct['小汽车五人']*5)
sum_district_pct['出租车载客总数']=(sum_district_pct['出租车两人']*1+sum_district_pct['出租车三人']*2+sum_district_pct['出租车四人']*3+sum_district_pct['出租车五人']*4)
sum_district_pct['小汽车']=sum_district_pct[['小汽车一人', '小汽车两人', '小汽车三人', '小汽车四人', '小汽车五人']].sum(axis=1)
sum_district_pct['出租车']=sum_district_pct[['出租车一人','出租车两人', '出租车三人', '出租车四人', '出租车五人']].sum(axis=1)
sum_district_pct['载客出租车']=sum_district_pct[['出租车两人', '出租车三人', '出租车四人', '出租车五人']].sum(axis=1)
sum_district_pct['小汽车载客率']=round(sum_district_pct['小汽车载客总数']/sum_district_pct['小汽车'],2)
sum_district_pct['出租车载客率']=round(sum_district_pct['出租车载客总数']/sum_district_pct['载客出租车'],2)
for col in ['小汽车一人', '小汽车两人', '小汽车三人', '小汽车四人', '小汽车五人',
            '出租车一人','出租车两人', '出租车三人', '出租车四人', '出租车五人']:
    if '小汽车' in col:
        sum_district_pct[col] = round(100 * sum_district_pct[col] / sum_district_pct['小汽车'], 2)
    elif '出租车' in col:
        sum_district_pct[col] = round(100 * sum_district_pct[col] / sum_district_pct['出租车'], 2)
#sum_district_pct.to_excel(r'D:/Hyder安诚/调查结果数据/小客车数据（已修）/sum_district_pct.xlsx',index=False)



writer=pd.ExcelWriter(r'D:/调查结果数据/小客车数据（已修）/小客车满载率summary_0706.xlsx')
sum_spot_pct.to_excel(writer, sheet_name='spot', startrow=0, startcol=0, index=False)
sum_time_pct.to_excel(writer,sheet_name='time', startrow=0, startcol=0, index=False)
sum_district_pct.to_excel(writer,sheet_name='District', startrow=0, startcol=0, index=False)
sum_period_pct.to_excel(writer,sheet_name='period', startrow=0, startcol=0, index=False)
sum_passenger.to_excel(writer,sheet_name='overall', startrow=0, startcol=0, index=False)
writer.save()
