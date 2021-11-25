import numpy as np
import pandas as pd
import os
from geopy.distance import geodesic
import datetime

pd.options.mode.chained_assignment = None  # default='warn'
###load and combine metro volume data
path=r'C:/Users/yi.gu/Documents/2020乌鲁木齐交通调查任务书/各单位调研材料/地铁城轨集团/地铁数据-2021年5月和6月/数据'
files = os.listdir(path)
ODdf=pd.DataFrame()
enterdf=pd.DataFrame()
exitdf=pd.DataFrame()
for file in files:
    if 'OD记录' in file:
        ODdf1=pd.read_csv(path+'/'+file,header=0)
        ODdf1=ODdf1.dropna()
        ODdf=pd.concat([ODdf,ODdf1],ignore_index=True)
        print(file,ODdf.shape)
    elif '进站记录' in file:
        enterdf1=pd.read_csv(path+'/'+file,header=0)
        enterdf1=enterdf1.dropna()
        enterdf=pd.concat([enterdf,enterdf1],ignore_index=True)
        print(file, enterdf.shape)
    elif '出站记录' in file:
        exitdf1=pd.read_csv(path+'/'+file,header=0)
        exitdf1=exitdf1.dropna()
        exitdf=pd.concat([exitdf,exitdf1],ignore_index=True)
        print(file,exitdf.shape)


enterdf['year']=enterdf['ENTRY_DATETIME'].apply(lambda x: str(x)[0:4] )
enterdf['month']=enterdf['ENTRY_DATETIME'].apply(lambda x: str(x)[5:7])
enterdf2021=enterdf[(enterdf['year']=='2021')&((enterdf['month']=='05')|(enterdf['month']=='06'))]
enterdf2021['day']=enterdf['ENTRY_DATETIME'].apply(lambda x: str(x)[8:10])
print(enterdf.shape,enterdf2021.shape)
enterday_sum=enterdf2021.groupby(['year','month','day'])['TR_TYPE'].count().reset_index()
print(enterday_sum['TR_TYPE'].mean())
exitdf['year']=exitdf['DEAL_DATETIME'].apply(lambda x: str(x)[0:4] )
exitdf['month']=exitdf['DEAL_DATETIME'].apply(lambda x: str(x)[5:7])
exitdf2021=exitdf[(exitdf['year']=='2021')&((exitdf['month']=='05')|(exitdf['month']=='06'))]
exitdf2021['day']=exitdf['DEAL_DATETIME'].apply(lambda x: str(x)[8:10])
print(exitdf.shape,exitdf2021.shape)
exitday_sum=exitdf2021.groupby(['year','month','day'])['TR_TYPE'].count().reset_index()
print(exitday_sum['TR_TYPE'].mean())

ODdf['year']=ODdf['ENTRY_DATETIME'].apply(lambda x: str(x)[0:4] )
ODdf['month']=ODdf['ENTRY_DATETIME'].apply(lambda x: str(x)[5:7])
ODdf2021=ODdf[(ODdf['year']=='2021')&((ODdf['month']=='05')|(ODdf['month']=='06'))]
ODdf2021['day']=ODdf['ENTRY_DATETIME'].apply(lambda x: str(x)[8:10])
ODdf2021['mark']=ODdf['ENTRY_DATETIME'].apply(lambda x: 'Y'if len(str(x))<18 else 'N') #'Y' datetime wrong
ODdf2021=ODdf2021[ODdf2021['mark']=='N']
ODdf2021['mark']=ODdf['DEAL_DATETIME'].apply(lambda x: 'Y'if len(str(x))<18 else 'N') #'Y' datetime wrong
ICOD=ODdf2021[ODdf2021['mark']=='N']

stat_dist=pd.read_excel(r'C:\Users\yi.gu\Documents\2020乌鲁木齐交通调查任务书\各单位调研材料\地铁城轨集团\刷卡数据、站间OD-5月1日当天\站间距.xlsx')
stat_dist=stat_dist.iloc[0:21,:]

stat_od_dist=pd.DataFrame(columns=stat_dist.columns)
for i in range(1,22):
    for j in range(1,22):
        if i < j:
            stati = list(stat_dist.loc[stat_dist['起点序号'] == i, '起点站名'])[0]
            statj = list(stat_dist.loc[stat_dist['起点序号'] == j, '起点站名'])[0]
            stati_AMD=list(stat_dist.loc[stat_dist['起点序号'] == i, '起点行政区'])[0]
            statj_AMD = list(stat_dist.loc[stat_dist['起点序号'] == j, '起点行政区'])[0]

            dist = stat_dist.loc[(stat_dist['起点序号'] < j) & (stat_dist['起点序号'] >= i), '站间距'].sum()
            stat_od_dist = stat_od_dist.append([{'起点序号': i, '起点站名': stati, '终点序号': j, '终点站名': statj,
                                                 '站间距': dist,'起点行政区':stati_AMD,'终点行政区':statj_AMD}])
        elif i > j:
            stati = list(stat_dist.loc[stat_dist['起点序号'] == i, '起点站名'])[0]
            statj = list(stat_dist.loc[stat_dist['起点序号'] == j, '起点站名'])[0]
            stati_AMD = list(stat_dist.loc[stat_dist['起点序号'] == i, '起点行政区'])[0]
            statj_AMD = list(stat_dist.loc[stat_dist['起点序号'] == j, '起点行政区'])[0]
            dist = stat_dist.loc[(stat_dist['起点序号'] < i) & (stat_dist['起点序号'] >= j), '站间距'].sum()
            stat_od_dist = stat_od_dist.append([{'起点序号': i, '起点站名': stati, '终点序号': j, '终点站名': statj,
                                                 '站间距': dist,'起点行政区':stati_AMD,'终点行政区':statj_AMD}])
        elif i == j:
            stati = list(stat_dist.loc[stat_dist['起点序号'] == i, '起点站名'])[0]
            stati_AMD = list(stat_dist.loc[stat_dist['起点序号'] == i, '起点行政区'])[0]
            stat_od_dist = stat_od_dist.append([{'起点序号': i, '起点站名': stati, '终点序号': i, '终点站名': stati,
                                                 '站间距': 0,'起点行政区':stati_AMD,'终点行政区':stati_AMD}])

#stat_od_dist.to_excel(r'C:\Users\yi.gu\Documents\2020乌鲁木齐交通调查任务书\各单位调研材料\地铁城轨集团\刷卡数据、站间OD-5月1日当天\OD站间距.xlsx',index=False)


def durationfun(start,end):

    t0=datetime.datetime.strptime(str(start),"%Y-%m-%d %H:%M:%S")
    t1=datetime.datetime.strptime(str(end),"%Y-%m-%d %H:%M:%S")
    duration=int((t1-t0).seconds/60)
    return duration

ICOD['Duration']=ICOD.apply(lambda x:durationfun(x['ENTRY_DATETIME'],x['DEAL_DATETIME']),axis=1 )



ICOD=pd.merge(ICOD,stat_od_dist[['起点站名', '终点站名','站间距']],how='left',left_on=['CHINESE_NAME','CHINESE_NAME.1'],right_on=['起点站名','终点站名'])
ICOD['Distance']=ICOD['站间距']/1000

ICOD=ICOD[(ICOD['Distance']>0)&(ICOD['Duration']>0)]

ICOD['hour']=ICOD['ENTRY_DATETIME'].apply(lambda x:datetime.datetime.strptime(str(x),"%Y-%m-%d %H:%M:%S").hour)
ICOD['dayoweek']=ICOD['ENTRY_DATETIME'].apply(lambda x:datetime.datetime.strptime(str(x),"%Y-%m-%d %H:%M:%S").weekday())
ICOD['dayoweek']=ICOD['dayoweek'].replace([0,1,2,3,4,5,6],['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
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

ICOD['period']= ICOD['hour'] .apply(lambda x:periodfun(x))
#daily volume
ICOD_Daily=ICOD.groupby(['month','day','dayoweek'])['TR_TYPE'].count().reset_index().rename(columns={'TR_TYPE':'trip'})
ICOD_Daily=ICOD_Daily.sort_values(by=['month','day'])

ICOD_Daily.plot()
# summarize volume by hour and period
weekdaycount=ICOD[(ICOD['dayoweek']!='Sun')&(ICOD['dayoweek']!='Sat')].drop_duplicates(subset=['month','day']).shape[0]
weekendcount=ICOD[(ICOD['dayoweek']=='Sun')|(ICOD['dayoweek']=='Sat')].drop_duplicates(subset=['month','day']).shape[0]
ICOD_wd_hour=ICOD[(ICOD['dayoweek']!='Sun')&(ICOD['dayoweek']!='Sat')].groupby('hour')['TR_TYPE'].count().reset_index().rename(columns={'TR_TYPE':'trip'})
ICOD_wd_hour['pct']=round(100*ICOD_wd_hour['trip']/ICOD_wd_hour['trip'].sum(),2)
ICOD_wd_hour['trip']=round(ICOD_wd_hour['trip']/weekdaycount,1)
ICOD_wn_hour=ICOD[(ICOD['dayoweek']=='Sun')|(ICOD['dayoweek']=='Sat')].groupby('hour')['TR_TYPE'].count().reset_index().rename(columns={'TR_TYPE':'trip'})
ICOD_wn_hour['pct']=round(100*ICOD_wn_hour['trip']/ICOD_wn_hour['trip'].sum(),2)
ICOD_wn_hour['trip']=round(ICOD_wn_hour['trip']/weekendcount,1)
ICOD_wd_hour.plot()
ICOD_wn_hour.plot()

ICOD_hour=ICOD.groupby('hour')['TR_TYPE'].count().reset_index().rename(columns={'TR_TYPE':'trip'})
ICOD_hour['pct']=round(100*ICOD_hour['trip']/ICOD_hour['trip'].sum(),2)
ICOD_hour['trip']=round(ICOD_hour['trip']/(weekendcount+weekdaycount),1)


ICOD_period=ICOD.groupby('period')['TR_TYPE'].count().reset_index()
ICOD_period=ICOD_period.rename(columns={'TR_TYPE':'trip'})
ICOD_period['pct']=round(100*ICOD_period['trip']/ICOD_period['trip'].sum(),2)
ICOD_period['trip']=round(ICOD_period['trip']/(weekendcount+weekdaycount),1)
sort=pd.DataFrame({'period':['AM_Peak', 'PM_Peak', 'Day_time','Night_time']})
sort_mapping = sort.reset_index().set_index('period')
ICOD_period['num'] = ICOD_period['period'].map(sort_mapping['index'])
ICOD_period=ICOD_period.sort_values('num').drop(columns=['num'])


# summarize volume by station
ICOD_enter=ICOD.groupby('CHINESE_NAME')['TR_TYPE'].count().reset_index()
ICOD_enter=ICOD_enter.rename(columns={'CHINESE_NAME':'enter_station','TR_TYPE':'enter_trip'})
ICOD_enter=pd.merge(ICOD_enter,stat_dist[['起点站名','起点序号']],how='left',left_on='enter_station',right_on='起点站名')
ICOD_enter['enter_pct']=round(100*ICOD_enter['enter_trip']/ICOD_enter['enter_trip'].sum(),2)
ICOD_enter['enter_trip']=round(ICOD_enter['enter_trip']/(weekendcount+weekdaycount),1)
ICOD_enter=ICOD_enter.sort_values(by='起点序号')
ICOD_enter=ICOD_enter[['起点序号','enter_station', 'enter_trip',  'enter_pct']]

ICOD_exit=ICOD.groupby('CHINESE_NAME.1')['TR_TYPE'].count().reset_index()
ICOD_exit=ICOD_exit.rename(columns={'CHINESE_NAME.1':'exit_station','TR_TYPE':'exit_trip'})
ICOD_exit['exit_pct']=round(100*ICOD_exit['exit_trip']/ICOD_exit['exit_trip'].sum(),2)
ICOD_exit['exit_trip']=round(ICOD_exit['exit_trip']/(weekendcount+weekdaycount),1)
ICOD_station=pd.merge(ICOD_enter,ICOD_exit,how='left',left_on='enter_station',right_on='exit_station')
ICOD_station=ICOD_station.rename(columns={'起点序号':'序号'})
ICOD_station=ICOD_station[['序号', 'enter_station', 'enter_trip', 'enter_pct',  'exit_trip', 'exit_pct']]

ICOD_station2=ICOD.groupby(['CHINESE_NAME','CHINESE_NAME.1']).agg(
    trip=pd.NamedAgg(column='TR_TYPE',aggfunc='count'),
).reset_index()
ICOD_station2['trip']=round(ICOD_station2['trip']/(weekendcount+weekdaycount),1)
ICOD_station2=pd.merge(ICOD_station2,stat_od_dist[['起点序号', '起点站名', '终点序号', '终点站名', '站间距']],how='left',left_on=['CHINESE_NAME','CHINESE_NAME.1'],right_on=['起点站名','终点站名'])

ICOD_station2=ICOD_station2[['起点序号', 'CHINESE_NAME', '终点序号', 'CHINESE_NAME.1', 'trip','站间距']].sort_values(by=['起点序号', '终点序号'])
ICOD_station2=ICOD_station2.rename(columns={'站间距':'distance'})

# summarize volume by district
ICOD=pd.merge(ICOD,stat_dist[['起点站名','起点序号','起点行政区']],how='left',left_on='CHINESE_NAME',right_on='起点站名')
ICOD=pd.merge(ICOD,stat_dist[['起点站名','起点序号','起点行政区']],how='left',left_on='CHINESE_NAME.1',right_on='起点站名')
ICOD=ICOD[['起点序号_x','CHINESE_NAME', 'ENTRY_DATETIME', '起点序号_y','CHINESE_NAME.1', 'DEAL_DATETIME',
       'CARD_SUB_NAME', 'CARD_LOGICAL_ID', 'TR_TYPE', 'Duration', 'Distance',
       'hour', 'period',  '起点行政区_x',  '起点行政区_y']]
ICOD=ICOD.rename(columns={'起点序号_x':'起点序号','起点序号_y':'终点序号','起点行政区_x':'起点行政区','起点行政区_y':'终点行政区'})
ICOD_adm=ICOD.groupby(['起点行政区','终点行政区']).agg(
    trip=pd.NamedAgg(column='TR_TYPE',aggfunc='count'),
    ave_distance=pd.NamedAgg(column='Distance',aggfunc='sum'),
).reset_index()
ICOD_adm['ave_distance']=round(ICOD_adm['ave_distance']/ICOD_adm['trip'],2)
ICOD_adm['trip']=round(ICOD_adm['trip']/(weekendcount+weekdaycount),1)
#passenger flow 客流断面
flowdf=stat_dist[['起点序号', '起点站名']]
flowdf['下行']=0
flowdf['上行']=0
for i in ICOD_station2.index:
    start=ICOD_station2.loc[i,'起点序号']
    end=ICOD_station2.loc[i,'终点序号']
    flow=ICOD_station2.loc[i,'trip']
    if start<=end:
        flowdf.loc[(flowdf['起点序号'] >= start) & (flowdf['起点序号'] <= end),'下行']=\
            flowdf.loc[(flowdf['起点序号'] >= start) & (flowdf['起点序号'] <= end),'下行']+flow
    else:
        flowdf.loc[(flowdf['起点序号'] <= start) & (flowdf['起点序号'] >= end), '上行'] = \
            flowdf.loc[(flowdf['起点序号'] <= start) & (flowdf['起点序号'] >= end), '上行'] + flow

flowdf['KD']=flowdf.apply(lambda x: max(x['下行'],x['上行'])/(x['下行']+x['上行']), axis=1)

#other performance indicators:客运量，客流强度即每日每公里所运输的旅客人数，平均运距，客流时辰分布
totaltrips=round(ICOD['TR_TYPE'].count()/(weekendcount+weekdaycount),1)
avedistance=ICOD['Distance'].mean()
intensity=ICOD['TR_TYPE'].count()/ICOD['Distance'].max()


## export to excel
writer=pd.ExcelWriter(r'C:/Users/yi.gu/Documents/2020乌鲁木齐交通调查任务书/各单位调研材料/地铁城轨集团/地铁数据-2021年5月和6月/summary_MayJune.xlsx')
ICOD_Daily.to_excel(writer,sheet_name='Daily',startrow=0,startcol=0,index=False)
ICOD_wn_hour.to_excel(writer,sheet_name='weekend_hour',startrow=0,startcol=0,index=False)
ICOD_wd_hour.to_excel(writer,sheet_name='weekday_hour',startrow=0,startcol=0,index=False)
ICOD_hour.to_excel(writer, sheet_name='hour & period', startrow=0, startcol=0, index=False)
ICOD_period.to_excel(writer, sheet_name='hour & period', startrow=ICOD_hour.shape[0]+3, startcol=0, index=False)
ICOD_station.to_excel(writer, sheet_name='station', startrow=0, startcol=0, index=False)
ICOD_station2.to_excel(writer, sheet_name='station', startrow=ICOD_station.shape[0]+3, startcol=0, index=False)

flowdf.to_excel(writer,sheet_name='passengerflow',startrow=0,startcol=0,index=False)
ICOD_adm.to_excel(writer, sheet_name='other', startrow=0, startcol=0, index=False)

sheet1 = writer.sheets['other']
startrv = ICOD_adm.shape[0] + 3
namelist=['客运量(人/日)','客流强度(人/km)','平均运距km']
varlist=[totaltrips,intensity,avedistance]
for j in range(len(varlist)):
        sheet1.write(startrv, 1, varlist[j])
        sheet1.write(startrv, 0, namelist[j])
        startrv += 1
writer.save()


ICOD_AM=ICOD[(ICOD['dayoweek']!='Sun')&(ICOD['dayoweek']!='Sat')&(ICOD['period']=='AM_Peak')]
ICOD_PM=ICOD[(ICOD['dayoweek']!='Sun')&(ICOD['dayoweek']!='Sat')&(ICOD['period']=='PM_Peak')]
ICOD_NonPeak=ICOD[(ICOD['dayoweek']!='Sun')&(ICOD['dayoweek']!='Sat')&(ICOD['period']!='PM_Peak')&(ICOD['period']!='AM_Peak')]
ICODlist=[ICOD_AM,ICOD_PM,ICOD_NonPeak]
totaldaylist=[weekdaycount,weekendcount]
file1=r'C:/Users/yi.gu/Documents/2020乌鲁木齐交通调查任务书/各单位调研材料/地铁城轨集团/地铁数据-2021年5月和6月/summary_MayJune_AM.xlsx'
file2=r'C:/Users/yi.gu/Documents/2020乌鲁木齐交通调查任务书/各单位调研材料/地铁城轨集团/地铁数据-2021年5月和6月/summary_MayJune_PM.xlsx'
file3=r'C:/Users/yi.gu/Documents/2020乌鲁木齐交通调查任务书/各单位调研材料/地铁城轨集团/地铁数据-2021年5月和6月/summary_MayJune_NonPeak.xlsx'

filenamelist=[file1,file2,file3]
for i in range(3):
    ICODi=ICODlist[i]
    totalday=totaldaylist[1]
    filename=filenamelist[i]

    # summarize volume by station
    ICOD_enter = ICODi.groupby('CHINESE_NAME')['TR_TYPE'].count().reset_index()
    ICOD_enter = ICOD_enter.rename(columns={'CHINESE_NAME': 'enter_station', 'TR_TYPE': 'enter_trip'})
    ICOD_enter = pd.merge(ICOD_enter, stat_dist[['起点站名', '起点序号']], how='left', left_on='enter_station', right_on='起点站名')
    ICOD_enter['enter_pct'] = round(100 * ICOD_enter['enter_trip'] / ICOD_enter['enter_trip'].sum(), 2)
    ICOD_enter['enter_trip'] = round(ICOD_enter['enter_trip'] /totalday, 1)
    ICOD_enter = ICOD_enter.sort_values(by='起点序号')
    ICOD_enter = ICOD_enter[['起点序号', 'enter_station', 'enter_trip', 'enter_pct']]

    ICOD_exit = ICODi.groupby('CHINESE_NAME.1')['TR_TYPE'].count().reset_index()
    ICOD_exit = ICOD_exit.rename(columns={'CHINESE_NAME.1': 'exit_station', 'TR_TYPE': 'exit_trip'})
    ICOD_exit['exit_pct'] = round(100 * ICOD_exit['exit_trip'] / ICOD_exit['exit_trip'].sum(), 2)
    ICOD_exit['exit_trip'] = round(ICOD_exit['exit_trip'] /totalday, 1)
    ICOD_station = pd.merge(ICOD_enter, ICOD_exit, how='left', left_on='enter_station', right_on='exit_station')
    ICOD_station = ICOD_station.rename(columns={'起点序号': '序号'})
    ICOD_station = ICOD_station[['序号', 'enter_station', 'enter_trip', 'enter_pct', 'exit_trip', 'exit_pct']]

    ICOD_station2 = ICODi.groupby(['CHINESE_NAME', 'CHINESE_NAME.1']).agg(
        trip=pd.NamedAgg(column='TR_TYPE', aggfunc='count'),
    ).reset_index()
    ICOD_station2['trip'] = round(ICOD_station2['trip'] /totalday, 1)
    ICOD_station2 = pd.merge(ICOD_station2, stat_od_dist[['起点序号', '起点站名', '终点序号', '终点站名', '站间距']], how='left',
                             left_on=['CHINESE_NAME', 'CHINESE_NAME.1'], right_on=['起点站名', '终点站名'])

    ICOD_station2 = ICOD_station2[['起点序号', 'CHINESE_NAME', '终点序号', 'CHINESE_NAME.1', 'trip', '站间距']].sort_values(
        by=['起点序号', '终点序号'])
    ICOD_station2 = ICOD_station2.rename(columns={'站间距': 'distance'})

    # summarize volume by district
    ICODi = pd.merge(ICODi,stat_dist[['起点站名', '起点序号', '起点行政区']], how='left', left_on='CHINESE_NAME', right_on='起点站名')
    ICODi = pd.merge(ICODi,stat_dist[['起点站名', '起点序号', '起点行政区']], how='left', left_on='CHINESE_NAME.1', right_on='起点站名')
    ICODi = ICODi[['起点序号_x', 'CHINESE_NAME', 'ENTRY_DATETIME', '起点序号_y', 'CHINESE_NAME.1', 'DEAL_DATETIME',
                 'CARD_SUB_NAME', 'CARD_LOGICAL_ID', 'TR_TYPE', 'Duration', 'Distance',
                 'hour', 'period', '起点行政区_x', '起点行政区_y']]
    ICODi = ICODi.rename(columns={'起点序号_x': '起点序号', '起点序号_y': '终点序号', '起点行政区_x': '起点行政区', '起点行政区_y': '终点行政区'})
    ICOD_adm = ICODi.groupby(['起点行政区', '终点行政区']).agg(
        trip=pd.NamedAgg(column='TR_TYPE', aggfunc='count'),
        ave_distance=pd.NamedAgg(column='Distance', aggfunc='sum'),
    ).reset_index()
    ICOD_adm['ave_distance'] = round(ICOD_adm['ave_distance'] / ICOD_adm['trip'], 2)
    ICOD_adm['trip'] = round(ICOD_adm['trip'] /totalday, 1)
    # passenger flow 客流断面
    flowdf = stat_dist[['起点序号', '起点站名']]
    flowdf['下行'] = 0
    flowdf['上行'] = 0
    for i in ICOD_station2.index:
        start = ICOD_station2.loc[i, '起点序号']
        end = ICOD_station2.loc[i, '终点序号']
        flow = ICOD_station2.loc[i, 'trip']
        if start <= end:
            flowdf.loc[(flowdf['起点序号'] >= start) & (flowdf['起点序号'] <= end), '下行'] = \
                flowdf.loc[(flowdf['起点序号'] >= start) & (flowdf['起点序号'] <= end), '下行'] + flow
        else:
            flowdf.loc[(flowdf['起点序号'] <= start) & (flowdf['起点序号'] >= end), '上行'] = \
                flowdf.loc[(flowdf['起点序号'] <= start) & (flowdf['起点序号'] >= end), '上行'] + flow

    flowdf['KD'] = flowdf.apply(lambda x: max(x['下行'], x['上行']) / (x['下行'] + x['上行']), axis=1)

    # other performance indicators:客运量，客流强度即每日每公里所运输的旅客人数，平均运距，客流时辰分布
    totaltrips = round(ICODi['TR_TYPE'].count() /totalday, 1)
    avedistance = ICODi['Distance'].mean()
    intensity = ICODi['TR_TYPE'].count() / ICODi['Distance'].max()

    ## export to excel
    writer = pd.ExcelWriter(filename)

    ICOD_station.to_excel(writer, sheet_name='station', startrow=0, startcol=0, index=False)
    ICOD_station2.to_excel(writer, sheet_name='station', startrow=ICOD_station.shape[0] + 3, startcol=0, index=False)

    flowdf.to_excel(writer, sheet_name='passengerflow', startrow=0, startcol=0, index=False)
    ICOD_adm.to_excel(writer, sheet_name='other', startrow=0, startcol=0, index=False)

    sheet1 = writer.sheets['other']
    startrv = ICOD_adm.shape[0] + 3
    namelist = ['客运量(人/日)', '客流强度(人/km)', '平均运距km']
    varlist = [totaltrips, intensity, avedistance]
    for j in range(len(varlist)):
        sheet1.write(startrv, 1, varlist[j])
        sheet1.write(startrv, 0, namelist[j])
        startrv += 1
    writer.save()


import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from shapely import geometry
plt.rcParams['font.family'] = 'simhei'
centroiddf=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\Test GIS\District\District_Centroid.xls')
centroiddf['District']=centroiddf['District'].replace('高新区','新市区')
Region = gpd.read_file(r'C:\Users\yi.gu\Documents\Hyder Related\Test GIS\District\District.shp', encoding='gbk')
Region = Region.to_crs(4326)
Region = Region.loc[0:5, :]
Region=Region[Region['District']!='米东区']

file=r'C:\Users\yi.gu\Documents\2020乌鲁木齐交通调查任务书\各单位调研材料\地铁城轨集团\地铁数据-2021年5月和6月\period_district_od.xlsx'
xl=pd.ExcelFile(file)
for sheet in xl.sheet_names:
    df1=pd.read_excel(file,sheet_name=sheet)
    df1=pd.merge(df1,centroiddf[['District','CentroidX','CentroidY']],how='left',left_on='起点行政区',right_on='District').rename(columns={'CentroidX':'O_X','CentroidY':'O_Y'})
    df1 = pd.merge(df1, centroiddf[['District', 'CentroidX', 'CentroidY']], how='left', left_on='终点行政区',
                   right_on='District').rename(columns={'CentroidX': 'D_X', 'CentroidY': 'D_Y'})
    linelist = []
    for i in df1.index:
        line = geometry.LineString([(df1.loc[i, 'O_X'], df1.loc[i, 'O_Y']),
                                    (df1.loc[i, 'D_X'], df1.loc[i, 'D_Y'])])
        linelist.append(line)
    polylines = gpd.GeoSeries(linelist, crs='EPSG:4326', index=df1['trip'])
    polylines.to_file(r'C:\Users\yi.gu\Documents\2020乌鲁木齐交通调查任务书\各单位调研材料\地铁城轨集团\地铁数据-2021年5月和6月\district_od_{}.shp'.format(sheet), encoding='utf-8')

    fig = plt.figure()
    ax = plt.subplot(111)
    plt.sca(ax)
    Region.plot(ax=ax,edgecolor=(0,0,0,1),facecolor=(0,0,0,0),linewidths=0.25)

    vmax = df1['trip'].max()
    norm = mpl.colors.Normalize(vmin=0, vmax=vmax)
    cmapname = 'autumn_r'
    cmap = mpl.cm.get_cmap(cmapname)

    # plot OD
    # for loop
    for i in range(len(df1)):
        # color and linewidth
        color_i = cmap(norm(df1['trip'].iloc[i]))
        linewidth_i = norm(df1['trip'].iloc[i]) * 5
        # plot
        plt.plot([df1['O_X'].iloc[i], df1['D_X'].iloc[i]],
                 [df1['O_Y'].iloc[i], df1['D_Y'].iloc[i]], color=color_i,
                 linewidth=linewidth_i)


    for i in centroiddf.index:
        if centroiddf.loc[i, 'District'] == '天山区':
            plt.text(centroiddf.loc[i, 'CentroidX'], centroiddf.loc[i, 'CentroidY'] - 0.05,
                     centroiddf.loc[i, 'District'],
                     fontsize=6, horizontalalignment="center")  # 标注位置X，Y，标注内容
        else:
            plt.text(centroiddf.loc[i, 'CentroidX'], centroiddf.loc[i, 'CentroidY'], centroiddf.loc[i, 'District'],
                     fontsize=6, horizontalalignment="center")  # 标注位置X，Y，标注内容
    # no axis
    plt.axis('off')
    # set xlim ylim
    plt.show()
    plt.title('{}_地铁OD分布图'.format(sheet), fontsize=18, fontweight='bold')
    plt.savefig(r'C:\Users\yi.gu\Documents\2020乌鲁木齐交通调查任务书\各单位调研材料\地铁城轨集团\地铁数据-2021年5月和6月\地铁OD_matrix_{}.png'.format(sheet), dpi=300)

#########早晚高峰时段公共交通平均拥挤度,地铁一节车厢额定载客量310，6节车厢，高峰发车间隔6分（1小时10班）
ICOD=ICOD.rename(columns={'CHINESE_NAME':'起点站名','CHINESE_NAME.1':'终点站名'})
ICOD=ICOD[ICOD['起点站名']!=ICOD['终点站名']]
ICOD=ICOD.merge(stat_dist[['起点站名','起点序号']],how='left',on='起点站名')
ICOD=ICOD.merge(stat_dist[['终点站名','终点序号']],how='left',on='终点站名')
ICOD.loc[ICOD['终点站名']=='三屯碑','终点序号']=1
ICOD['direction']=ICOD.apply(lambda x: '下行'if x['起点序号']<x['终点序号'] else '上行',axis=1)
ICOD['deal_hour']=ICOD['DEAL_DATETIME'].apply(lambda x:datetime.datetime.strptime(str(x),"%Y-%m-%d %H:%M:%S").hour)
ICOD_AM=ICOD[(ICOD['hour']==9)|(ICOD['deal_hour']==9)]
ICOD_AM=ICOD_AM[(ICOD_AM['dayoweek']!='Sat')&(ICOD_AM['dayoweek']!='Sun')]
ICOD_AM_AVG=ICOD_AM.groupby(['month','day','起点站名','起点序号','终点站名','终点序号','direction'])['TR_TYPE'].count().reset_index()
ICOD_AM_AVG=ICOD_AM_AVG.groupby(['起点站名','起点序号','终点站名','终点序号','direction'])['TR_TYPE'].mean().reset_index()
ICOD_PM=ICOD[(ICOD['hour']==19)|(ICOD['deal_hour']==19)]
ICOD_PM=ICOD_PM[(ICOD_PM['dayoweek']!='Sat')&(ICOD_PM['dayoweek']!='Sun')]
ICOD_PM_AVG=ICOD_PM.groupby(['month','day','起点站名','起点序号','终点站名','终点序号','direction'])['TR_TYPE'].count().reset_index()
ICOD_PM_AVG=ICOD_PM_AVG.groupby(['起点站名','起点序号','终点站名','终点序号','direction'])['TR_TYPE'].mean().reset_index()
for df in [ICOD_AM_AVG,ICOD_PM_AVG]:
    #下行
    enter=df[df['direction']=='下行'].groupby(['起点站名','起点序号'])['TR_TYPE'].sum().reset_index().rename(columns={'TR_TYPE':'下行_上车人数'})
    exit=df[df['direction']=='下行'].groupby(['终点站名','终点序号'])['TR_TYPE'].sum().reset_index().rename(columns={'TR_TYPE':'下行_下车人数'})
    crosssection=stat_dist[['起点序号','起点站名']].merge(enter[['起点站名','起点序号','下行_上车人数']],how='left',on=['起点序号','起点站名'])
    crosssection = crosssection.merge(exit[['终点站名','终点序号', '下行_下车人数']], how='left',left_on=['起点序号','起点站名'],right_on=['终点序号', '终点站名'])
    crosssection[['下行_上车人数','下行_下车人数']]=crosssection[['下行_上车人数','下行_下车人数']].fillna(0)
    crosssection.loc[crosssection['起点序号']==1,'断面客流']=crosssection.loc[crosssection['起点序号']==1,'下行_上车人数']
    crosssection=crosssection.sort_values(by=['起点序号'])
    for i in range(1,len(crosssection)):
        #print(crosssection.at[i-1,'断面客流']+crosssection.at[i,'下行_上车人数']-crosssection.at[i,'下行_下车人数'])
        volume=round(crosssection.at[i-1,'断面客流']+crosssection.at[i,'下行_上车人数']-crosssection.at[i,'下行_下车人数'],1)
        crosssection.loc[i, '断面客流']=volume
    print('下行',crosssection['断面客流'].max(),crosssection['断面客流'].max()/(310*6*10))
    #上行
    enter = df[df['direction'] == '上行'].groupby(['起点站名', '起点序号'])['TR_TYPE'].sum().reset_index().rename(
        columns={'TR_TYPE': '上行_上车人数'})
    exit = df[df['direction'] == '上行'].groupby(['终点站名', '终点序号'])['TR_TYPE'].sum().reset_index().rename(
        columns={'TR_TYPE': '上行_下车人数'})
    crosssection = stat_dist[['起点序号', '起点站名']].merge(enter[['起点站名', '起点序号', '上行_上车人数']], how='left',
                                                     on=['起点序号', '起点站名'])
    crosssection = crosssection.merge(exit[['终点站名', '终点序号', '上行_下车人数']], how='left', left_on=['起点序号', '起点站名'],
                                      right_on=['终点序号', '终点站名'])
    crosssection[['上行_上车人数', '上行_下车人数']] = crosssection[['上行_上车人数', '上行_下车人数']].fillna(0)
    crosssection.loc[crosssection['起点序号'] == 21, '断面客流'] = crosssection.loc[crosssection['起点序号'] == 21, '上行_上车人数']
    crosssection = crosssection.sort_values(by=['起点序号'],ascending=False).reset_index().drop(columns=['index'])
    for i in range(1,len(crosssection) ):
        #print(crosssection.at[i - 1, '断面客流'] + crosssection.at[i, '上行_上车人数'] - crosssection.at[i, '上行_下车人数'])
        volume = round(crosssection.at[i - 1, '断面客流'] + crosssection.at[i, '上行_上车人数'] - crosssection.at[i, '上行_下车人数'],
                       1)
        crosssection.loc[i, '断面客流'] = volume
    print('上行',crosssection['断面客流'].max(), crosssection['断面客流'].max() / (310 * 6 * 10))






