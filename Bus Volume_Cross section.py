import pandas as pd
import os
import numpy as np
import math
from geopy.distance import geodesic

import matplotlib.pyplot as plt
from datetime import datetime
import geopandas as gpd
from shapely import geometry
import re

plt.rcParams['font.family'] = 'simhei'
pd.options.mode.chained_assignment = None  # default='warn'
######################校核线公交满载率调查结果分析#########################################################

path = r"C:/Users/yi.gu/Documents/Hyder Related/调查结果数据/公交满载率调查结果0608/公交满载率调查数据成果"
files= os.listdir(path)
data=pd.DataFrame()
for file in files:
    data0=pd.read_excel(path+"/"+file,usecols="A:J",header=None,names=['序号', '点位编号', '点位名称', '断面位置描述', '调查员姓名', '联系电话', '观测方向', '时间', '线路号',
       '满载情况'])
    data0=data0[data0['序号']!='序号']
    data0=data0.dropna(subset=['时间', '线路号','满载情况'])
    data=pd.concat([data,data0],ignore_index=True)
    print(file,data.shape)

print(len(set(data['点位编号'])))
print(set(data['点位编号']))

data=data[['序号', '点位编号', '点位名称','断面位置描述','观测方向', '时间','线路号','满载情况']].reset_index().drop(columns='index')
crosssection=pd.read_excel(r"C:/Users/yi.gu/Documents/Hyder Related/调查结果数据/公交满载率调查结果0608/公交满载率点位.xlsx",sheet_name='公交满载率点位')
data=pd.merge(data,crosssection[['编号','核查线']],how='left',left_on='点位编号',right_on='编号').drop(columns='编号')
data=data.drop(index=data[data['点位编号']=='点位编号'].index)
data=data.dropna(subset=['点位编号','线路号','满载情况'])
data=data.replace(to_replace=['由南到北',' 由东向西',' 由南向北','南向北','北向南','自西向东','自东向西'],value=['由南向北','由东向西','由南向北','由南向北','由北向南','由西向东','由东向西'])
print(set(data['核查线']))
print(data.shape)
#data['线路号']=data['线路号'].apply(lambda x:x.replace('\n', '').replace('\r', '') if isinstance(busi, str) else str(x))
def correctbusline(x):
    if isinstance(x,str)==False:
        x=str(x)
    if isinstance(x,str):
        x=x.replace('\n', '').replace('\r', '')
    if ' ' in x:
        x=x.replace(' ','')
    if '.0' in x:
        x=x.replace('.0','')
    elif '0.' in x:
        x=x.replace('0.','')
    elif '.' in x:
        x=x.replace('.','')
    elif (x.startswith('B')) and ('BRT' not in x):
        x=x.replace('B','BRT')
    return x.upper()

data['线路号']=data['线路号'].apply(lambda x:correctbusline(x))

data['dropmark']='N'
def keyword(x):
    keywordlist=['出场','回场','教练车','故障车','应急']
    if any(s in x for s in keywordlist):
        return 'Y'
    else:
        return 'N'
data['dropmark']=data['线路号'].apply(lambda x:keyword(x))
data=data.drop(index=data[data['dropmark']=='Y'].index)
print(set(data['线路号']))
print(data.shape)
#data.groupby(['点位编号','线路号'])['时间'].count().reset_index().to_excel(r"D:/Hyder安诚/调查结果数据/公交满载率调查数据成果/线路名核查.xlsx",index=False)

def correcttime(x):
    try:
        if isinstance(x, int):
            x = str(x)
        if isinstance(x, str):
            x = x.replace(';', ':').replace('：', ':').replace('\n', '').replace('\r', '').replace(' ', '').replace('-',
                                                                                                                   '').replace(
                '.', '').replace('B', '3')
            type = len(x.split(':'))
            if type ==1 and len(x)==3:
                x=x[0]+':'+x[1:]
                x = datetime.datetime.strptime(x, '%H:%M').time()
            elif type == 1 and len(x) == 4:
                x = x[0:2] + ':' + x[2:]
                x = datetime.datetime.strptime(x, '%H:%M').time()
            elif type == 2:
                x = datetime.datetime.strptime(x, '%H:%M').time()
            elif type == 3:
                x = datetime.datetime.strptime(x, '%H:%M:%S').time()
        return x
    except:
        return "Error"



for i in data.index:
    if correcttime(data.loc[i,'时间'])=="Error":
        print(i, data.loc[i,'点位编号'], data.loc[i, '观测方向'], data.loc[i, '时间'])

data['时间']=data['时间'].apply(lambda x:correcttime(x))
data=data.replace(to_replace ="东-环西侧",value ="东一环西侧")


status=pd.read_excel(r"C:/Users/yi.gu/Documents/Hyder Related/调查结果数据/公交满载率调查结果0608/公交满载率点位.xlsx",sheet_name='Sheet1')
data=pd.merge(data,status,how='left',on='满载情况')

sum_spot=pd.DataFrame()
busroute=pd.read_excel(r"C:/Users/yi.gu/Documents/Hyder Related/调查结果数据/公交满载率调查结果0608/busnamelist.xlsx",sheet_name='Sheet2')
busroute['线路']=busroute['线路'].apply(lambda x: str(x))
for spot in set(data['点位编号']):
    spotname1=list(data.loc[data['点位编号']==spot,'点位名称'])[0]
    spotname2=list(data.loc[data['点位编号']==spot,'核查线'])[0]
    busstring=''
    for row in busroute.index:
        if spotname1 in busroute.loc[row,'途经道路']:
            if len(busstring)==0:
                busstring = str(busroute.loc[row, '线路'])
            else:
                busstring=busstring+', '+str(busroute.loc[row,'线路'])
    buscount = data.loc[data['点位编号']==spot,'线路号'].count()
    buslist = list(set(data.loc[data['点位编号']==spot,'线路号']))
    bus_text=str(buslist[0])
    for busi in buslist[1:]:
        if isinstance(busi, str) :
            if '\n' in busi:
                bus_text = bus_text + ', ' + busi.replace('\n', '').replace('\r', '')
            else:
                bus_text = bus_text + ', ' + busi

        else :
            bus_text = bus_text + ', ' +str(busi)
    print(spot,bus_text)
    sum_spot=sum_spot.append([{'点位编号':spot,'点位名称':spotname1,'核查线':spotname2,'经过线路':bus_text,'应经过线路':busstring,'实际发车数':buscount}])

#sum_spot.to_excel(r"D:/Hyder安诚/调查结果数据/公交满载率调查结果0608/cross_section_summary.xlsx",index=False)
data['hour']=0
for i in data.index:

    try:
        data.loc[i,'hour']=data.loc[i, '时间'].hour
    except:
        data.loc[i,'hour']='Error'

#data['hour']=data['时间'].apply(lambda x:x.hour)
print(data.loc[data['hour']=='Error',['点位编号','观测方向','时间']])
data_wrong=data.loc[data['hour']=='Error',['点位编号','观测方向','时间']]
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
data['period'] = data['hour'] .apply(lambda x:periodfun(x) )

data['对应乘客数']=data['对应乘客数'].apply(lambda x: float(x))
sum_hour=data.groupby(['核查线', '观测方向','hour']).agg(
    total=pd.NamedAgg(column='对应乘客数',aggfunc='sum'),
    mean=pd.NamedAgg(column='对应乘客数',aggfunc='mean'),
    count=pd.NamedAgg(column='对应乘客数',aggfunc='count'),
).reset_index()
sum_hour['满载率']=round(100*sum_hour['mean']/76,2)
sum_hour['pct']=0
for i in sum_hour.index:
    section=sum_hour.loc[i,'核查线']
    direction=sum_hour.loc[i,'观测方向']
    sum_hour.loc[i,'pct']=round(100*sum_hour.loc[i,'total']/sum_hour.loc[(sum_hour['核查线']==section) &(sum_hour['观测方向']==direction),'total'].sum(),2)


sum_hour_overall=data.groupby(['hour']).agg(
    total=pd.NamedAgg(column='对应乘客数',aggfunc='sum'),
    mean=pd.NamedAgg(column='对应乘客数',aggfunc='mean'),
    count=pd.NamedAgg(column='对应乘客数',aggfunc='count'),
).reset_index()
sum_hour_overall['pct']=round(100*sum_hour_overall['total']/sum_hour_overall['total'].sum(),2)



#sum_period=data.groupby(['period','满载情况'])['hour'].count().reset_index()
sum_period=data.groupby(['核查线', '观测方向','period']).agg(
    total=pd.NamedAgg(column='对应乘客数',aggfunc='sum'),
    average=pd.NamedAgg(column='对应乘客数',aggfunc='mean'),
).reset_index()
sum_period['满载率']=round(100*sum_period['average']/76,2)
sum_period['pct']=0
sum_period['Peak']='N'
for i in sum_period.index:
    section=sum_period.loc[i,'核查线']
    direction=sum_period.loc[i,'观测方向']
    sum_period.loc[i,'pct']=round(100*sum_period.loc[i,'total']/sum_period.loc[(sum_period['核查线']==section) &(sum_period['观测方向']==direction),'total'].sum(),2)
    if sum_period.loc[i,'average']==sum_period.loc[(sum_period['核查线']==section) &(sum_period['观测方向']==direction),'average'].max():
        sum_period.loc[i,'Peak'] = 'Y'


sum_period_overall=data.groupby(['period']).agg(
    total=pd.NamedAgg(column='对应乘客数',aggfunc='sum'),
    average=pd.NamedAgg(column='对应乘客数',aggfunc='mean'),
    count=pd.NamedAgg(column='对应乘客数',aggfunc='count'),
).reset_index()
sum_period_overall['pct']=round(100*sum_period_overall['total']/sum_period_overall['total'].sum(),2)
sum_period_overall['满载率']=round(100*sum_period_overall['average']/76,2)


writer=pd.ExcelWriter(r'C:/Users/yi.gu/Documents/Hyder Related/调查结果数据/公交满载率调查结果0608/summary.xlsx')
sum_spot.to_excel(writer, sheet_name='spot', startrow=0, startcol=0, index=False)
sum_hour.to_excel(writer,sheet_name='spot_hour', startrow=0, startcol=0, index=False)
sum_hour_overall.to_excel(writer,sheet_name='overall_hour', startrow=0, startcol=0, index=False)
sum_period.to_excel(writer,sheet_name='spot_period', startrow=0, startcol=0, index=False)
sum_period_overall.to_excel(writer,sheet_name='overall_period', startrow=0, startcol=0, index=False)
writer.save()

####画图###
#data['核查线']=data['核查线'].fillna('河滩路')

plt.rcParams['font.sans-serif'] = [u'SimHei']
plt.rcParams['axes.unicode_minus'] = False
colorlist=['red','blue','green','purple']
for sect in set(sum_hour['核查线']):
    data_sect=sum_hour[(sum_hour['核查线']==sect) & ((sum_hour['hour']==9) | (sum_hour['hour']==19))]
    data_sect['时段']=data_sect['hour'].apply(lambda x:'早高峰' if x==9 else '晚高峰')
    for i in range(len(set(data_sect['观测方向']))):
        dir=list(set(data_sect['观测方向']))[i]
        y=data_sect.loc[data_sect['观测方向']==dir,'满载率']
        x=np.arange(len(y))+0.2*i
        plt.bar(x,np.array(y),alpha=0.6, width=0.2,color=colorlist[i], label=dir)
    plt.xticks(np.arange(2)+0.2, ('早高峰', '晚高峰'), fontsize=12)
    plt.ylabel('%',fontsize=12)
    plt.legend(loc='best')
    plt.title(sect+'高峰时段满载率', fontsize=15)
    #plt.show()
    figname=r'C:/Users/yi.gu/Documents/Hyder Related/调查结果数据/公交满载率调查结果0608/校核线满载率柱状图/'+sect+'高峰时段满载率.png'
    plt.savefig(figname, bbox_inches='tight')
    plt.close()








buscountsum=data.groupby(['点位编号','点位名称','核查线', '观测方向','线路号'])['时间'].count().reset_index()
from difflib import SequenceMatcher#导入库
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()#引用ratio方法，返回序列相似性的度量
print(similarity('中国民族大学', '中国是世界上大学最多的国家'))
buslist=pd.read_excel(r"C:/Users/yi.gu/Documents/Hyder Related/调查结果数据/公交满载率调查结果0608/busnamelist.xlsx")
buslist['线名']=buslist['线名'].apply(lambda x: str(x))
buscountsum=pd.merge(buscountsum,buslist,how='left',left_on='线路号',right_on='线名')
buscountsum=buscountsum.fillna('')
buscountsum['可能正确的线名']=''
for spot in set(buscountsum['点位编号']):
    buswlisti=buscountsum.loc[(buscountsum['点位编号']==spot)&(buscountsum['线名']==''),'线路号']
    busclisti=buscountsum.loc[(buscountsum['点位编号']==spot)&(buscountsum['线名']!=''),'线路号']
    pairdf=pd.DataFrame(columns=['bus','option','similarities'])
    pairdf['option']=busclisti
    for bus in buswlisti:
        pairdf['bus']=bus
        pairdf['similarities']=pairdf['option'].apply(lambda x:similarity(bus,x))
        buscountsum.loc[(buscountsum['线路号'] == bus) & (buscountsum['点位编号'] == spot), '可能正确的线名']=','.join(list(pairdf.loc[pairdf['similarities']==max(pairdf['similarities']),'option']))

buscountsum=pd.read_excel(r"C:/Users/yi.gu/Documents/Hyder Related/调查结果数据/公交满载率调查结果0608/buscountsum.xlsx",sheet_name='Sheet1')
buscountsum=buscountsum.dropna(subset=['可能正确的线名'])
data=pd.merge(data,buscountsum[['点位编号','点位名称','观测方向','线路号','可能正确的线名']],how='left',on=['点位编号','点位名称','观测方向','线路号'])
data=data.fillna('')
def replacebusline(x0,x):
    if x!='':
        x0=str(x)
    return x0
data['线路号']=data.apply(lambda x: replacebusline(x['线路号'],x['可能正确的线名']),axis=1)
data.to_excel(r"C:/Users/yi.gu/Documents/Hyder Related/调查结果数据/公交满载率调查结果0608/公交满载率结果combined.xlsx",index=False)

data=pd.read_excel(r"C:/Users/yi.gu/Documents/Hyder Related/调查结果数据/公交满载率调查结果0608/公交满载率结果combined.xlsx",sheet_name='Sheet1')



####busline cross section volumn spatial
data=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\公交满载率调查结果0608\combined.xlsx',sheet_name='Sheet1')
data['对应乘客数']=data['对应乘客数'].fillna('NA')
data=data[data['对应乘客数']!='NA']

###whole day summary by spot
spot_sum=data.groupby( ['点位编号', '点位名称', '核查线', '观测方向']).agg(
    count=pd.NamedAgg(column='线路号',aggfunc='count'),
    sum=pd.NamedAgg(column='对应乘客数',aggfunc='sum')
).reset_index()
spot_sum['ave_psg']=spot_sum['sum']/spot_sum['count']
spot_sum['满载率']=spot_sum['ave_psg']/76
spot_sum['ave_psg']=spot_sum['ave_psg'].apply(lambda x: round(x,1))
spot_sum['满载率']=spot_sum['满载率'].apply(lambda x: round(100*x,1))

section_sum=data.groupby( ['核查线', '观测方向']).agg(
    sec_count=pd.NamedAgg(column='线路号',aggfunc='count'),
    sect_sum=pd.NamedAgg(column='对应乘客数',aggfunc='sum')
).reset_index()

spot_sum=spot_sum.merge(section_sum,how='left',on=['核查线', '观测方向'])
spot_sum['pct']=spot_sum['sum']/spot_sum['sect_sum']
spot_sum['pct']=spot_sum['pct'].apply(lambda x: round(100*x,1))



###AM period sum by spot and direction
spot_am=data[data['period']=='AM_Peak'].groupby( ['点位编号', '点位名称', '核查线', '观测方向']).agg(
    count=pd.NamedAgg(column='线路号',aggfunc='count'),
    sum=pd.NamedAgg(column='对应乘客数',aggfunc='sum')
).reset_index()
spot_am['ave_psg']=spot_am['sum']/spot_am['count']
spot_am['满载率']=spot_am['ave_psg']/76
spot_am['ave_psg']=spot_am['ave_psg'].apply(lambda x: round(x,1))
spot_am['满载率']=spot_am['满载率'].apply(lambda x: round(100*x,1))
section_am=data[data['period']=='AM_Peak'].groupby( ['核查线', '观测方向']).agg(
    sec_count=pd.NamedAgg(column='线路号',aggfunc='count'),
    sect_sum=pd.NamedAgg(column='对应乘客数',aggfunc='sum')
).reset_index()
spot_am=spot_am.merge(section_am,how='left',on=['核查线', '观测方向'])
spot_am['pct']=spot_am['sum']/spot_am['sect_sum']
spot_am['pct']=spot_am['pct'].apply(lambda x: round(100*x,1))


###PM period sum by spot and direction
spot_pm=data[data['period']=='PM_Peak'].groupby( ['点位编号', '点位名称', '核查线', '观测方向']).agg(
    count=pd.NamedAgg(column='线路号',aggfunc='count'),
    sum=pd.NamedAgg(column='对应乘客数',aggfunc='sum')
).reset_index()
spot_pm['ave_psg']=spot_pm['sum']/spot_pm['count']
spot_pm['满载率']=spot_pm['ave_psg']/76
spot_pm['ave_psg']=spot_pm['ave_psg'].apply(lambda x: round(x,1))
spot_pm['满载率']=spot_pm['满载率'].apply(lambda x: round(100*x,1))
section_pm=data[data['period']=='PM_Peak'].groupby( ['核查线', '观测方向']).agg(
    sec_count=pd.NamedAgg(column='线路号',aggfunc='count'),
    sect_sum=pd.NamedAgg(column='对应乘客数',aggfunc='sum')
).reset_index()
spot_pm=spot_pm.merge(section_am,how='left',on=['核查线', '观测方向'])
spot_pm['pct']=spot_pm['sum']/spot_pm['sect_sum']
spot_pm['pct']=spot_pm['pct'].apply(lambda x: round(100*x,1))


writer=pd.ExcelWriter(r'C:/Users/yi.gu/Documents/Hyder Related/调查结果数据/公交满载率调查结果0608/summary0817.xlsx')
spot_sum.to_excel(writer, sheet_name='spot_day', startrow=0, startcol=0, index=False)
spot_am.to_excel(writer,sheet_name='spot_am', startrow=0, startcol=0, index=False)
spot_pm.to_excel(writer,sheet_name='spot_pm', startrow=0, startcol=0, index=False)
writer.save()

spot_sum_pvt=spot_sum.pivot(index=['点位编号','点位名称', '核查线'],columns='观测方向',values='sum').reset_index()
spot_am_pvt=spot_am.pivot(index=['点位编号','点位名称', '核查线'],columns='观测方向',values='sum').reset_index()
spot_pm_pvt=spot_pm.pivot(index=['点位编号','点位名称', '核查线'],columns='观测方向',values='sum').reset_index()
dflist=[spot_sum_pvt,spot_am_pvt,spot_pm_pvt]
dfnamelist=['day','AM','PM']
for j in range(3) :
    df=dflist[j]
    name=dfnamelist[j]
    lines=['河滩路', '苏州路','克拉玛依路-南湖路', '南外环', '西一环','东一环']
    fig = plt.figure(figsize=(12,18))
    for i in range(1,7):
        ax1 = fig.add_subplot(3, 2, i)
        x_label = df.loc[df['核查线'] == lines[i-1], '点位名称']
        x=np.array(range(1,2*len(x_label)+1,2))
        ns=df.loc[df['核查线'] == lines[i-1], '由北向南']
        sn=df.loc[df['核查线'] == lines[i-1], '由南向北']
        we=df.loc[df['核查线'] == lines[i-1], '由西向东']
        ew=df.loc[df['核查线'] == lines[i-1], '由东向西']
        plt.bar(x - 0.75, sn, width=0.5, label='由南向北')
        plt.bar(x - 0.25, ns, width=0.5, label='由北向南')
        plt.bar(x + 0.25, we, width=0.5, label='由西向东')
        plt.bar(x + 0.75, ew, width=0.5, label='由东向西')
        plt.xticks(x, labels=x_label,fontsize=7,rotation=20)
        plt.ylabel(lines[i-1]+'\n客运量',fontsize=8)
    plt.legend(bbox_to_anchor=(1, -0.2), ncol = 4)
    plt.savefig(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\公交满载率调查结果0608\校核线满载率柱状图\{}点位客流量.png'.format(name), dpi=300)


hour_sum_pvt=sum_hour.pivot(index=['核查线','hour'],columns='观测方向',values='total').reset_index()
hour_sum_pvt=hour_sum_pvt[hour_sum_pvt['hour']<21]
hour_sum_pvt['hour']=hour_sum_pvt['hour'].apply(lambda x: str(x)+':00')
period_sum_pvt=sum_period.pivot(index=['核查线','period'],columns='观测方向',values='total').reset_index()
period_sum_pvt['period']=period_sum_pvt['period'].replace(['AM_Peak','Day_time','Night_time','PM_Peak'],['1.早高峰','2.日间平峰','4.夜间平峰','3.晚高峰'])
period_sum_pvt=period_sum_pvt.sort_values(by=['核查线','period'])

dflist=[hour_sum_pvt,period_sum_pvt]
dfnamelist=['hour','period']
for j in range(2) :
    df=dflist[j]
    name=dfnamelist[j]
    lines=['河滩路', '苏州路','克拉玛依路-南湖路', '南外环', '西一环','东一环']
    fig = plt.figure(figsize=(12,18))
    for i in range(1,7):
        ax1 = fig.add_subplot(3, 2, i)
        x_label = df.loc[df['核查线'] == lines[i-1], name]
        x=np.array(range(1,2*len(x_label)+1,2))
        ns=df.loc[df['核查线'] == lines[i-1], '由北向南']
        sn=df.loc[df['核查线'] == lines[i-1], '由南向北']
        we=df.loc[df['核查线'] == lines[i-1], '由西向东']
        ew=df.loc[df['核查线'] == lines[i-1], '由东向西']
        plt.bar(x-0.75,sn,width=0.5,label='由南向北')
        plt.bar(x-0.25,ns,width=0.5,label='由北向南')
        plt.bar(x + 0.25, we, width=0.5, label='由西向东')
        plt.bar(x + 0.75, ew, width=0.5, label='由东向西')
        if len(x_label)>6:
            plt.xticks(x, labels=x_label, fontsize=7, rotation=20)
        else:
            plt.xticks(x, labels=x_label, fontsize=7)
        plt.ylabel(lines[i-1]+'\n客运量',fontsize=8)
    plt.legend(bbox_to_anchor=(1, -0.15), ncol = 4)
    plt.savefig(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\公交满载率调查结果0608\校核线满载率柱状图\{}点位客流量.png'.format(name), dpi=300)




###全天客流量较大的点客流较多的公交线路
spot_sum2=spot_sum.sort_values(by=['核查线','观测方向','sum'])
max_spot=spot_sum2.drop_duplicates(keep='last',subset=['核查线','观测方向']).reset_index(drop=True)
max_spot_lines=pd.DataFrame()
for j in max_spot.index:
    spot=max_spot.loc[j,'点位编号']
    dir=max_spot.loc[j,'观测方向']
    buslines=data[(data['点位编号']==spot)&(data['观测方向']==dir)].groupby('线路号').agg(
        count=pd.NamedAgg(column='对应乘客数',aggfunc='count'),
        sum=pd.NamedAgg(column='对应乘客数',aggfunc='sum'),
    ).reset_index()
    buslines['mean']=buslines['sum']/buslines['count']
    buslines['mean']=buslines['mean'].apply(lambda x: round(x,1))
    buslines['pct']=round(100*buslines['sum']/buslines['sum'].sum(),1)
    buslines=buslines.sort_values(by=['sum','count'],ascending=False).reset_index(drop=True)
    top2=buslines.loc[0:1,:]
    top2['点位编号']=spot
    top2['观测方向']=dir
    max_spot_lines=pd.concat([max_spot_lines,top2],ignore_index=True)

max_spot_lines=max_spot_lines.merge(spot_sum2[['点位编号', '点位名称', '核查线','观测方向']],how='left',on=['点位编号','观测方向']).drop_duplicates()
max_spot_lines=max_spot_lines[['点位编号',  '点位名称', '核查线','观测方向','线路号', 'count', 'sum', 'mean', 'pct']]
max_spot_lines['载客率']=round(100*max_spot_lines['mean']/76,2)
print('all day')
print(max_spot_lines)

###早高峰客流量较大的点客流较多的公交线路
spot_sum2=spot_am.sort_values(by=['核查线','观测方向','sum'])
max_spot=spot_sum2.drop_duplicates(keep='last',subset=['核查线','观测方向']).reset_index(drop=True)
max_spot_lines=pd.DataFrame()
for j in max_spot.index:
    spot=max_spot.loc[j,'点位编号']
    dir=max_spot.loc[j,'观测方向']
    buslines=data[(data['点位编号']==spot)&(data['观测方向']==dir)&(data['period']=='AM_Peak')].groupby('线路号').agg(
        count=pd.NamedAgg(column='对应乘客数',aggfunc='count'),
        sum=pd.NamedAgg(column='对应乘客数',aggfunc='sum'),
    ).reset_index()
    buslines['mean']=buslines['sum']/buslines['count']
    buslines['mean']=buslines['mean'].apply(lambda x: round(x,1))
    buslines['pct']=round(100*buslines['sum']/buslines['sum'].sum(),1)
    buslines=buslines.sort_values(by=['sum','count'],ascending=False).reset_index(drop=True)
    top2=buslines.loc[0:1,:]
    top2['点位编号']=spot
    top2['观测方向']=dir
    max_spot_lines=pd.concat([max_spot_lines,top2],ignore_index=True)

max_spot_lines=max_spot_lines.merge(spot_sum2[['点位编号', '点位名称', '核查线','观测方向']],how='left',on=['点位编号','观测方向']).drop_duplicates()
max_spot_lines=max_spot_lines[['点位编号',  '点位名称', '核查线','观测方向','线路号', 'count', 'sum', 'mean', 'pct']]
max_spot_lines['载客率']=round(100*max_spot_lines['mean']/76,2)
print('AM')
print(max_spot_lines)

###晚高峰客流量较大的点客流较多的公交线路
spot_sum2=spot_pm.sort_values(by=['核查线','观测方向','sum'])
max_spot=spot_sum2.drop_duplicates(keep='last',subset=['核查线','观测方向']).reset_index(drop=True)
max_spot_lines=pd.DataFrame()
for j in max_spot.index:
    spot=max_spot.loc[j,'点位编号']
    dir=max_spot.loc[j,'观测方向']
    buslines=data[(data['点位编号']==spot)&(data['观测方向']==dir)&(data['period']=='PM_Peak')].groupby('线路号').agg(
        count=pd.NamedAgg(column='对应乘客数',aggfunc='count'),
        sum=pd.NamedAgg(column='对应乘客数',aggfunc='sum'),
    ).reset_index()
    buslines['mean']=buslines['sum']/buslines['count']
    buslines['mean']=buslines['mean'].apply(lambda x: round(x,1))
    buslines['pct']=round(100*buslines['sum']/buslines['sum'].sum(),1)
    buslines=buslines.sort_values(by=['sum','count'],ascending=False).reset_index(drop=True)
    top2=buslines.loc[0:1,:]
    top2['点位编号']=spot
    top2['观测方向']=dir
    max_spot_lines=pd.concat([max_spot_lines,top2],ignore_index=True)

max_spot_lines=max_spot_lines.merge(spot_sum2[['点位编号', '点位名称', '核查线','观测方向']],how='left',on=['点位编号','观测方向']).drop_duplicates()
max_spot_lines=max_spot_lines[['点位编号',  '点位名称', '核查线','观测方向','线路号', 'count', 'sum', 'mean', 'pct']]
max_spot_lines['载客率']=round(100*max_spot_lines['mean']/76,2)
print('PM')
print(max_spot_lines)


###全天分校核线客流较多的公交线路

max_section_lines=pd.DataFrame()
for j in section_sum.index:
    section=section_sum.loc[j,'核查线']
    dir=section_sum.loc[j,'观测方向']
    buslines=data[(data['核查线']==section)&(data['观测方向']==dir)].groupby('线路号').agg(
        count=pd.NamedAgg(column='对应乘客数',aggfunc='count'),
        sum=pd.NamedAgg(column='对应乘客数',aggfunc='sum'),
    ).reset_index()
    buslines['mean']=buslines['sum']/buslines['count']
    buslines['mean']=buslines['mean'].apply(lambda x: round(x,1))
    buslines['pct']=round(100*buslines['sum']/buslines['sum'].sum(),1)
    buslines=buslines.sort_values(by=['sum','count'],ascending=False).reset_index(drop=True)
    top2=buslines.loc[0:1,:]
    top2['核查线']=section
    top2['观测方向']=dir
    max_section_lines=pd.concat([max_section_lines,top2],ignore_index=True)

max_section_lines=max_section_lines[['核查线','观测方向','线路号', 'count', 'sum', 'mean', 'pct']]
max_section_lines['载客率']=round(100*max_section_lines['mean']/76,2)
print('all day')
print(max_section_lines)

###早高峰分校核线客流较多的公交线路

max_section_lines=pd.DataFrame()
for j in section_am.index:
    section=section_am.loc[j,'核查线']
    dir=section_am.loc[j,'观测方向']
    buslines=data[(data['核查线']==section)&(data['观测方向']==dir)&(data['period']=='AM_Peak')].groupby('线路号').agg(
        count=pd.NamedAgg(column='对应乘客数',aggfunc='count'),
        sum=pd.NamedAgg(column='对应乘客数',aggfunc='sum'),
    ).reset_index()
    buslines['mean']=buslines['sum']/buslines['count']
    buslines['mean']=buslines['mean'].apply(lambda x: round(x,1))
    buslines['pct']=round(100*buslines['sum']/buslines['sum'].sum(),1)
    buslines=buslines.sort_values(by=['sum','count'],ascending=False).reset_index(drop=True)
    top2=buslines.loc[0:1,:]
    top2['核查线']=section
    top2['观测方向']=dir
    max_section_lines=pd.concat([max_section_lines,top2],ignore_index=True)

max_section_lines=max_section_lines[['核查线','观测方向','线路号', 'count', 'sum', 'mean', 'pct']]
max_section_lines['载客率']=round(100*max_section_lines['mean']/76,2)
print('AM')
print(max_section_lines)

###晚高峰分校核线客流较多的公交线路

max_section_lines=pd.DataFrame()
for j in section_pm.index:
    section=section_pm.loc[j,'核查线']
    dir=section_pm.loc[j,'观测方向']
    buslines=data[(data['核查线']==section)&(data['观测方向']==dir)&(data['period']=='PM_Peak')].groupby('线路号').agg(
        count=pd.NamedAgg(column='对应乘客数',aggfunc='count'),
        sum=pd.NamedAgg(column='对应乘客数',aggfunc='sum'),
    ).reset_index()
    buslines['mean']=buslines['sum']/buslines['count']
    buslines['mean']=buslines['mean'].apply(lambda x: round(x,1))
    buslines['pct']=round(100*buslines['sum']/buslines['sum'].sum(),1)
    buslines=buslines.sort_values(by=['sum','count'],ascending=False).reset_index(drop=True)
    top2=buslines.loc[0:1,:]
    top2['核查线']=section
    top2['观测方向']=dir
    max_section_lines=pd.concat([max_section_lines,top2],ignore_index=True)

max_section_lines=max_section_lines[['核查线','观测方向','线路号', 'count', 'sum', 'mean', 'pct']]
max_section_lines['载客率']=round(100*max_section_lines['mean']/76,2)
print('PM')
print(max_section_lines)
