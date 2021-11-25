import pandas as pd
import numpy as np
import re


pd.options.mode.chained_assignment = None  # default='warn'
######################公交满意度调查结果分析#########################################################
data=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\地铁满意度\乌鲁木齐市轨道客流满意度调查数据库-11.17.xlsx',sheet_name='Sheet1')
stationlist=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\地铁满意度\轨道客流出行特征和满意度调查数据06.19提交.xlsx',sheet_name='站点')
dictionary=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\地铁满意度\轨道客流出行特征和满意度调查数据06.19提交.xlsx',sheet_name='代号')
colnamelist=dictionary.columns[1:]
def satisfscore(x):
    if x==1 or x==2:
        return 1
    elif x==3:
        return 0.5
    elif x==4 or x==5:
        return 0
for colname in colnamelist:
    data=pd.merge(data,dictionary[['代号',colname]],how='left',left_on=colname,right_on='代号').drop(columns=['代号',colname+'_x'])
    data=data.rename(columns={colname+'_y':colname})
for colname in data.columns:
    if colname.startswith('19、'):
        data[colname]=data[colname].apply(lambda x: satisfscore(x))


"""
性别，年龄，收入，职业，月乘坐地铁次数，支付方式
目的结构，总体及分站点的接驳方式，耗时
整体满意度，子项目满意度，分性别、年龄、职业的满意度

"""




#乘客个人特征
passengerdf=[]
passengerdfname=['各站点受调查人数','性别','是否为本市户籍','职业','月收入','乘车频率','年龄','乘车时段']
colnamelistp=['2、站点名称', '15、您的性别：', '16、您的户籍', '17、您的职业是', '18、您每月的收入水平是','12、您每月乘坐地铁的次数是']

for i in range(len(colnamelistp)) :
    colname=colnamelistp[i]
    colname2=passengerdfname[i]
    sum_df=data.groupby(colname)['序号'].count().reset_index().rename(columns={'序号':'人数',colname:colname2})
    sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
    if colname in dictionary.columns:
        df_sort = pd.DataFrame({colname2: list(dictionary[colname].dropna())})
        sort_mapping = df_sort.reset_index().set_index(colname2)
        sum_df['num'] = sum_df[colname2].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])
    print(sum_df)
    passengerdf.append(sum_df)

def age_group(x):
    if x>=6 and x<=18:
        return '6-18'
    elif x>=19 and x<=33:
        return '19-33'
    elif x>=34 and x<=48:
        return '34-48'
    elif x>=49 and x<=63:
        return '49-63'
    elif x>=64:
        return 'above 64'
    else:
        return 'under 6'

data['年龄'] =data['14、您的年龄'].apply(lambda x:age_group(x))
sum_df=data.groupby('年龄')['序号'].count().reset_index().rename(columns={'序号':'人数'})
sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
age_sort=pd.DataFrame({'年龄':['6-18', '19-33', '34-48','49-63','above 64']})
sort_mapping = age_sort.reset_index().set_index('年龄')
sum_df['age_num'] = sum_df['年龄'].map(sort_mapping['index'])
sum_df=sum_df.sort_values('age_num').drop(columns=['age_num'])
print(sum_df)
passengerdf.append(sum_df)

sum_df=pd.DataFrame({'时段':['工作日早/晚高峰', '工作日平峰', '休息日'],'人数':list(data[['13、(工作日早/晚高峰)', '13、(工作日平峰)', '13、(休息日)']].count(axis=0))})
sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
passengerdf.append(sum_df)

for colname in ['13、(工作日早/晚高峰)', '13、(工作日平峰)', '13、(休息日)']:
    data[colname]=data[colname].fillna(0)
    data[colname]=data[colname].apply(lambda x:int(x))
data['pattern']=data.apply(lambda x:str(x['13、(工作日早/晚高峰)'])+str(x['13、(工作日平峰)'])+str(x['13、(休息日)']),axis=1)
patterndf=data.groupby('pattern')['序号'].count().reset_index().rename(columns={'序号':'人数'})
patterndf['pattern']=patterndf['pattern'].replace(to_replace=['003', '020', '023', '100', '103', '120', '123'],value=[
    '仅休息日','仅工作日平峰','工作日平峰及休息日','仅工作日早晚高峰','工作日早晚高峰及休息日','工作日早晚高峰及平峰','所有时段'
])
patterndf['pct']=round(100*patterndf['人数']/patterndf['人数'].sum(),2)
passengerdf.append(patterndf)
passengerdfname.append('pattern')


#乘客出行特征

tripdf=[]
tripdfname=['本次支付方式','出行目的','起点站','终点站']
colnamelistt=['11、本次出行费用支付方式','3、出行目的', '6、首先使用的站点', '7、最终离开的站名' ]
for i in range(len(colnamelistt)) :
    colname=colnamelistt[i]
    colname2=tripdfname[i]
    sum_df=data.groupby(colname)['序号'].count().reset_index().rename(columns={'序号':'人数',colname:colname2})
    sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
    if colname in dictionary.columns:
        df_sort = pd.DataFrame({colname2: list(dictionary[colname].dropna())})
        sort_mapping = df_sort.reset_index().set_index(colname2)
        sum_df['num'] = sum_df[colname2].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])
    else:
        df_sort = pd.DataFrame({colname2: list(stationlist['站点名称'])})
        sort_mapping = df_sort.reset_index().set_index(colname2)
        sum_df['num'] = sum_df[colname2].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])
    print(sum_df)
    tripdf.append(sum_df)


###从起点到车站和从车站到目的地的时间
def transfer_group(x):
    if  x<=10:
        return '<10min'
    elif x>10 and x<=20:
        return '10〜20min'
    elif x>20 :
        return '>20min'


data['出发地到车站'] =data['10、出发地到轨道车站的时耗'].apply(lambda x:transfer_group(x))
data['车站到目的地'] =data['10、轨道车站到目的地的时耗'].apply(lambda x:transfer_group(x))
data['mark']='N'
data.loc[(data['4.起点X']>=88)|(data['4.起点X']<=87)|(data['4.起点Y']>=44)|(data['4.起点Y']<=43),'mark']='Y'
data.loc[(data['5.终点X']>=88)|(data['5.终点X']<=87)|(data['5.终点Y']>=44)|(data['5.终点Y']<=43),'mark']='Y'
for colname in ['出发地到车站','车站到目的地']:
    sum_df = data[data['mark']=='N'].groupby(colname)['序号'].count().reset_index().rename(columns={'序号': '人数'})
    sum_df['pct'] = round(100 * sum_df['人数'] / sum_df['人数'].sum(), 2)
    df_sort = pd.DataFrame({colname: ['<10min', '10〜20min', '>20min']})
    sort_mapping = df_sort.reset_index().set_index(colname)
    sum_df['num'] = sum_df[colname].map(sort_mapping['index'])
    sum_df = sum_df.sort_values('num').drop(columns=['num'])
    print(sum_df)
    tripdf.append(sum_df)
    tripdfname.append(colname)

sum_df=data[data['mark']=='N'].groupby(['6、首先使用的站点'])['10、出发地到轨道车站的时耗'].mean().reset_index().rename(columns={'6、首先使用的站点':'上车站点','10、出发地到轨道车站的时耗':'到车站时耗'})
sum_df['到车站时耗']=round(sum_df['到车站时耗'],2)
df_sort=pd.DataFrame({'上车站点':list(stationlist['站点名称'])})
sort_mapping = df_sort.reset_index().set_index('上车站点')
sum_df['num'] = sum_df['上车站点'].map(sort_mapping['index'])
sum_df=sum_df.sort_values('num').drop(columns=['num'])
sum_df = sum_df.append([{'上车站点': '平均（min）', '到车站时耗': round(data['10、出发地到轨道车站的时耗'].mean(), 2)}])
print(sum_df)
tripdf.append(sum_df)
tripdfname.append('分站点起点到车站时耗')

sum_df=data[data['mark']=='N'].groupby(['7、最终离开的站名'])['10、轨道车站到目的地的时耗'].mean().reset_index().rename(columns={'7、最终离开的站名':'下车站点','10、轨道车站到目的地的时耗':'下车到目的地时耗'})
sum_df['下车到目的地时耗']=round(sum_df['下车到目的地时耗'],2)
df_sort=pd.DataFrame({'下车站点':list(stationlist['站点名称'])})
sort_mapping = df_sort.reset_index().set_index('下车站点')
sum_df['num'] = sum_df['下车站点'].map(sort_mapping['index'])
sum_df=sum_df.sort_values('num').drop(columns=['num'])
sum_df = sum_df.append([{'下车站点': '平均（min）', '下车到目的地时耗': round(data['10、轨道车站到目的地的时耗'].mean(), 2)}])
print(sum_df)
tripdf.append(sum_df)
tripdfname.append('分站点下车到目的地时耗')

###到地铁站的距离
from geopy.distance import geodesic
data_trip=data[['序号',  '4.起点X', '4.起点Y',  '5.终点X', '5.终点Y',  '6、首先使用的站点', '7、最终离开的站名','mark']]
data_trip=data_trip[data_trip['mark']=='N']
def distancetostation(long1,lat1,station):
    try:
        long1 = float(long1)
        lat1 = float(lat1)
        long2 = float(stationlist.loc[stationlist['站点名称'] == station, 'X百度'])
        lat2 = float(stationlist.loc[stationlist['站点名称'] == station, 'Y百度'])
        distance = geodesic((lat1, long1), (lat2, long2)).m  # 计算两个坐标直线距离
        return round(distance, 1)
    except:
        return float("inf")
data_trip['distance_o']=data_trip.apply(lambda x:distancetostation(x['4.起点X'],x['4.起点Y'],x['6、首先使用的站点']),axis=1)
data_trip['distance_d']=data_trip.apply(lambda x:distancetostation(x['5.终点X'],x['5.终点Y'],x['7、最终离开的站名']),axis=1)
def distance_group(x):
    if x >=0 and x<=500:
        return '0-0.5千米'
    elif x>500 and x <=1000:
        return '0.5-1千米'
    elif x>1000 and x<=1500:
        return '1-1.5千米'
    elif x>1500 and x<=2000:
        return '1.5-2千米'
    elif np.isinf(x)==False and x>2000:
        return '2千米以上'
    elif np.isinf(x)==True:
        return '乌鲁木齐市外'
data_trip['distance_o2']=data_trip['distance_o'].apply(lambda x:distance_group(x))
data_trip['distance_d2']=data_trip['distance_d'].apply(lambda x:distance_group(x))
sum_df_o=data_trip.groupby(['distance_o2'])['distance_o'].count().reset_index().rename(columns={'distance_o':'人数'})
sum_df_o['pct']=round(100*sum_df_o['人数']/sum_df_o['人数'].sum(),1)
sum_df_o=sum_df_o.append([{'distance_o2':'平均','人数':data_trip['distance_o'].mean()}])
sum_df_os=data_trip.groupby(['6、首先使用的站点','distance_o2'])['distance_o'].count().reset_index().rename(columns={'distance_o':'人数'})
sum_df_os=sum_df_os.pivot(index='6、首先使用的站点',columns='distance_o2',values='人数').reset_index().fillna(0)
sum_df_os['sum']=sum_df_os.sum(axis=1)
sum_df_os['mean_distance']=0
for row in sum_df_os.index:
    sum_df_os.loc[row,'mean_distance']=round(data_trip.loc[data_trip['6、首先使用的站点']==sum_df_os.loc[row,'6、首先使用的站点'],'distance_o'].mean(),2)
for col in sum_df_os.columns[1:-2]:
    sum_df_os[col]=round(100*sum_df_os[col]/sum_df_os['sum'],1)
df_sort=stationlist[['站点编号','站点名称']]
sort_mapping=df_sort.reset_index().set_index('站点名称')
sum_df_os['num']=sum_df_os['6、首先使用的站点'].map(sort_mapping['站点编号'])
sum_df_os=sum_df_os.sort_values('num').drop(columns=['num'])
tripdf.append(sum_df_o)
tripdf.append(sum_df_os)
tripdfname.append('起点到车站的距离分布')
tripdfname.append('分站点起点到车站的距离分布')
sum_df_d=data_trip.groupby(['distance_d2'])['distance_d'].count().reset_index().rename(columns={'distance_d':'人数'})
sum_df_d['pct']=round(100*sum_df_d['人数']/sum_df_d['人数'].sum(),1)
sum_df_d=sum_df_d.append([{'distance_d2':'平均','人数':data_trip['distance_d'].mean()}])
sum_df_ds=data_trip.groupby(['7、最终离开的站名','distance_d2'])['distance_d'].count().reset_index().rename(columns={'distance_d':'人数'})
sum_df_ds=sum_df_ds.pivot(index='7、最终离开的站名',columns='distance_d2',values='人数').reset_index().fillna(0)
sum_df_ds['sum']=sum_df_ds.sum(axis=1)
sum_df_ds['mean_distance']=0
for row in sum_df_ds.index:
    sum_df_ds.loc[row,'mean_distance']=round(data_trip.loc[data_trip['7、最终离开的站名']==sum_df_ds.loc[row,'7、最终离开的站名'],'distance_d'].mean(),2)
for col in sum_df_ds.columns[1:-2]:
    sum_df_ds[col]=round(100*sum_df_ds[col]/sum_df_ds['sum'],1)
df_sort=stationlist[['站点编号','站点名称']]
sort_mapping=df_sort.reset_index().set_index('站点名称')
sum_df_ds['num']=sum_df_ds['7、最终离开的站名'].map(sort_mapping['站点编号'])
sum_df_ds=sum_df_ds.sort_values('num').drop(columns=['num'])
tripdf.append(sum_df_d)
tripdf.append(sum_df_ds)
tripdfname.append('车站到终点的距离分布')
tripdfname.append('分站点车站到终点的距离分布')


data=data.drop(columns=['mark'])

####接驳方式
transfer_from_o=data.groupby('6、首先使用的站点').agg(
walk=pd.NamedAgg(column='8、(全程步行)',aggfunc=sum),
    brt=pd.NamedAgg(column='8、(BRT)', aggfunc=sum),
    bus=pd.NamedAgg(column='8、(公共汽电车)', aggfunc=sum),
    bike=pd.NamedAgg(column='8、(非机动车)', aggfunc=sum),
    motor=pd.NamedAgg(column='8、(摩托车)', aggfunc=sum),
    taxi=pd.NamedAgg(column='8、(出租车)', aggfunc=sum),
    pc=pd.NamedAgg(column='8、(私人小汽车)',aggfunc=sum),
    illegal=pd.NamedAgg(column='8、(黑车)',aggfunc=sum),
    other=pd.NamedAgg(column='8、(其他)',aggfunc=sum),
).reset_index().rename(columns={'6、首先使用的站点':'上车站点','walk':'全程步行','brt':'BRT','bus':'公共汽电车','bike':'非机动车','motor':'摩托车',
                                'taxi':'出租车','pc': '私人小汽车','illegal':'黑车','other': '其他'})

transfer_from_o['sum']=transfer_from_o.sum(axis=1)
transfer_from_o.loc[len(transfer_from_o),:]=np.array(transfer_from_o.sum(axis=0))
transfer_from_o.iloc[len(transfer_from_o)-1,0]='总计'
for colname in transfer_from_o.columns[1:-1]:
    transfer_from_o[colname]=round(100* transfer_from_o[colname]/transfer_from_o['sum'],2)
df_sort=pd.DataFrame({'上车站点':list(stationlist['站点名称']+['总计'])})
sort_mapping = df_sort.reset_index().set_index('上车站点')
transfer_from_o['num'] = transfer_from_o['上车站点'].map(sort_mapping['index'])
transfer_from_o=transfer_from_o.sort_values('num').drop(columns=['num'])

tripdf.append(transfer_from_o)
tripdfname.append('分站点接驳方式（起点）')


transfer_to_d=data.groupby('7、最终离开的站名').agg(
walk=pd.NamedAgg(column='9、(全程步行)',aggfunc=sum),
    brt=pd.NamedAgg(column='9、(BRT)', aggfunc=sum),
    bus=pd.NamedAgg(column='9、(公共汽电车)', aggfunc=sum),
    bike=pd.NamedAgg(column='9、(非机动车)', aggfunc=sum),
    motor=pd.NamedAgg(column='9、(摩托车)', aggfunc=sum),
    taxi=pd.NamedAgg(column='9、(出租车)', aggfunc=sum),
    pc=pd.NamedAgg(column='9、(私人小汽车)',aggfunc=sum),
    illegal=pd.NamedAgg(column='9、(黑车)',aggfunc=sum),
    other=pd.NamedAgg(column='9、(其他)',aggfunc=sum),
).reset_index().rename(columns={'7、最终离开的站名':'下车站点','walk':'全程步行','brt':'BRT','bus':'公共汽电车','bike':'非机动车','motor':'摩托车',
                                'taxi':'出租车','pc': '私人小汽车','illegal':'黑车','other': '其他'})

transfer_to_d['sum']=transfer_to_d.sum(axis=1)
transfer_to_d.loc[len(transfer_to_d),:]=np.array(transfer_to_d.sum(axis=0))
transfer_to_d.iloc[len(transfer_to_d)-1,0]='总计'
for colname in transfer_to_d.columns[1:-1]:
    transfer_to_d[colname]=round(100* transfer_to_d[colname]/transfer_to_d['sum'],2)
df_sort=pd.DataFrame({'下车站点':list(stationlist['站点名称']+['总计'])})
sort_mapping = df_sort.reset_index().set_index('下车站点')
transfer_to_d['num'] = transfer_to_d['下车站点'].map(sort_mapping['index'])
transfer_to_d=transfer_to_d.sort_values('num').drop(columns=['num'])

tripdf.append(transfer_to_d)
tripdfname.append('分站点接驳方式（终点）')


###行政区OD###
def districtfunc(address):
    if '乌鲁木齐市' in str(address) and '区' in str(address):
        district=re.split('[区县]',str(address[5:]))[0]+'区'
    else:
        district='其他'
    return district

data['出发行政区']=data['4.起点详细地址'].apply(lambda x:districtfunc(x))
data['到达行政区']=data['5.终点详细地址'].apply(lambda x:districtfunc(x))
sum_od=data.groupby(['出发行政区','到达行政区'])['序号'].count().reset_index().rename(columns={'序号':'人数'}).pivot(index='出发行政区',columns='到达行政区',values='人数').reset_index().fillna(0)
sum_od=sum_od[['出发行政区', '天山区',  '新市区', '水磨沟区','沙依巴克区', '米东区']]
df_sort=pd.DataFrame({'出发行政区':['天山区','头屯河区','新市区','水磨沟区','沙依巴克区','米东区']})
sort_mapping = df_sort.reset_index().set_index('出发行政区')
sum_od['num'] = sum_od['出发行政区'].map(sort_mapping['index'])
sum_od=sum_od.sort_values('num').drop(columns=['num'])
print(sum_od)
tripdf.append(sum_od)
tripdfname.append('行政区OD')


###站间OD####
station_od=data.groupby(['6、首先使用的站点', '7、最终离开的站名'])['序号'].count().reset_index().rename(columns={'序号':'人数','6、首先使用的站点':'上车站名','7、最终离开的站名':'下车站名'})
station_od=station_od.pivot(index='上车站名',columns='下车站名',values='人数').reset_index().fillna(0)

station_od=station_od[['上车站名']+list(stationlist['站点名称'])]
df_sort=pd.DataFrame({'上车站名':list(stationlist['站点名称'])})
sort_mapping = df_sort.reset_index().set_index('上车站名')
station_od['num'] = station_od['上车站名'].map(sort_mapping['index'])
station_od=station_od.sort_values('num').drop(columns=['num'])
print(station_od)
tripdf.append(station_od)
tripdfname.append('站点OD')

###计算运距###
stat_dist=pd.read_excel(r'D:\Hyder安诚\2020乌鲁木齐交通调查任务书\各单位调研材料\地铁城轨集团\刷卡数据、站间OD-5月1日当天\OD站间距.xlsx')
data=pd.merge(data,stat_dist[['起点站名', '终点站名', '站间距']],how='left',left_on=['6、首先使用的站点', '7、最终离开的站名'],right_on=['起点站名', '终点站名'])
data['站间距']=data['站间距'].fillna(-1)
print(data.loc[data['站间距']==-1,['6、首先使用的站点', '7、最终离开的站名', '站间距']])
print('平均运距km：{}'.format(round(data['站间距'].mean()/1000,2)))

####计算上下行横断面流量#####
data_trip=data[['序号','提交答卷时间','6、首先使用的站点', '7、最终离开的站名']]
df_sort=stationlist[['站点编号','站点名称']]
sort_mapping=df_sort.reset_index().set_index('站点名称')
data_trip['index_o']=data_trip['6、首先使用的站点'].map(sort_mapping['站点编号'])
data_trip['index_d']=data_trip['7、最终离开的站名'].map(sort_mapping['站点编号'])
data_trip['direction']=data_trip['index_o']-data_trip['index_d']
data_trip['direction']=data_trip['direction'].apply(lambda x: '下行'if x <0 else '上行')
stationlist['下行断面客流']=0
stationlist['上行断面客流']=0
for i in data_trip.index:
    stationo=data_trip.loc[i,'index_o']
    stationd=data_trip.loc[i,'index_d']
    if data_trip.loc[i,'direction']=='下行':
        stationlist.loc[(stationlist['站点编号']>=stationo) &(stationlist['站点编号']<=stationd),'下行断面客流']=\
            stationlist.loc[(stationlist['站点编号']>=stationo) &(stationlist['站点编号']<=stationd),'下行断面客流']+1
    elif data_trip.loc[i,'direction']=='上行':
        stationlist.loc[(stationlist['站点编号']>=stationd) &(stationlist['站点编号']<=stationo),'上行断面客流']=\
            stationlist.loc[(stationlist['站点编号']>=stationd) &(stationlist['站点编号']<=stationo),'上行断面客流']+1

def directionf(x,y):
    return round(max(x,y)/(x+y),2)
stationlist['Dfactor']=stationlist.apply(lambda x: directionf(x['下行断面客流'],x['上行断面客流']),axis=1)

##########满意度#######
satislist=['4、乘客满意度调查—进出站标识、标志、广播指引等信息全面清晰醒目', '4、购票、检票支付方式以及下载使用相关APP方便快捷',
       '4、安检工作规范有序、通过顺畅', '4、环境整洁、通风良好、温度适宜及空气质量良好',
       '4、候车乘车秩序良好，无乞讨卖艺、散发小广告等行为', '4、乘客信息服务（比如列车内的报站信息）清晰',
       '4、电（扶）梯等服务设施完好、使用正常', '4、列车运行准时、平稳、噪声低', '4、无障碍和人性化设施（比如直梯）完备、运行良好',
       '4、换乘方便快捷（地铁换乘其他交通工具）、换乘标识清晰、秩序良好', '4、工作人员态度友好、答复准确',
       '4、投诉渠道畅通，回复及时满意', '4、进出站、候车、乘车等全过程感觉安全可靠', '4、对列车候车时间是否满意',
       '4、对进出站闸机工作状态是否满意', '4、对周边地标指引标识是否满意',
       '4、对车内设施满意度评价，包括车载广播、电视播报系统，车内环境、通风、空调，座椅扶手安全牢靠等',
       '4、对车门/屏蔽门开关安全无故障满意度评价', '4、对站内逃生疏散通道了解情况']

weightdf=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\地铁满意度\乌鲁木齐市轨道客流满意度调查数据库-11.17.xlsx',sheet_name='满意度')

#二级指标（19项分类别平均得分）
for colname in ['3、出行目的',  '12、您每月乘坐地铁的次数是', '15、您的性别：', '16、您的户籍', '17、您的职业是', '18、您每月的收入水平是',
       '年龄' ]:
    varlist=set(data[colname])
    for var in varlist:
        for satis in satislist:
            weightdf.loc[weightdf['评价内容']==satis,var]=data.loc[data[colname]==var,satis].mean()



for colname in weightdf.columns[4:]:
    weightdf[colname]=round(weightdf[colname]*weightdf['分值'],1)

weightdf.loc[len(weightdf),:]=weightdf.sum(axis=0)
weightdf.iloc[-1,0]='总计'

#一级指标平均分数
scoredf=pd.DataFrame({'评价指标':list(set(weightdf['评价指标']))})
for colname in ['3、出行目的',  '12、您每月乘坐地铁的次数是', '15、您的性别：', '16、您的户籍', '17、您的职业是', '18、您每月的收入水平是',
       '年龄' ]:
    varlist=set(data[colname])
    for var in varlist:
        for satis2 in set(weightdf['评价指标']):
            scoredf.loc[scoredf['评价指标']==satis2,var]=weightdf.loc[weightdf['评价指标']==satis2,var].sum()

scoredf.loc[len(scoredf),:]=scoredf.sum(axis=0)
scoredf.iloc[-1,0]='总计'

weightdf.loc[0:18,'总体']=list(data[satislist].mean(axis=0))
weightdf['总体']=round(weightdf['总体']*weightdf['分值'],1)
weightdf.loc[19,'总体']=weightdf.loc[0:18,'总体'].sum()
writer=pd.ExcelWriter(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\地铁满意度\地铁满意度summary1122.xlsx')
### 1.乘客个人信息
if len(passengerdf)>0:
    startr = 1
    rowlist = [0]
    for i in range(len(passengerdf)):
        passengerdf[i].to_excel(writer, sheet_name='passenger', startrow=startr, startcol=0, index=False)
        r, c = passengerdf[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['passenger']
    for i in range(len(passengerdf)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, passengerdfname[i])

###2.出行信息
if len(tripdf)>0:
    startr = 1
    rowlist = [0]
    for i in range(len(tripdf)):
        tripdf[i].to_excel(writer, sheet_name='trip', startrow=startr, startcol=0, index=False)
        r, c = tripdf[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['trip']
    for i in range(len(tripdf)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, tripdfname[i])


###3.满意度
weightdf=weightdf[['序号', '评价内容', '评价指标', '分值', '接送人', '文化体育娱乐休闲', '就医', '上学',
       '乘坐飞机/火车等去外地', '业务', '回宾馆', '上班', '回家', '日常生活','小于5次','5-20次','21-40次','40次以上','男', '女',
                   '本市户籍', '非本市户籍居住满半年', '非本市户籍居住不满半年', '6-18', '19-33','34-48', '49-63', 'above 64',
                   '小学生', '工人', '医护人员', '自由职业者', '中学生', '大专院校学生', '公务员', '教育工作者',
                   '公司企业管理者', '事业单位人员', '科技人员', '专职司机（除公交、出租车司机以外）', '军人/警察', '个体/私营户',
                   '农林牧渔生产者', '服务业人员', '公司职员','其他','2000元以下','2000-5000元', '5001-8000元','8000元以上','总体']]
scoredf=scoredf[['评价指标', '接送人', '文化体育娱乐休闲', '就医', '上学',
       '乘坐飞机/火车等去外地', '业务', '回宾馆', '上班', '回家', '日常生活','小于5次','5-20次','21-40次','40次以上','男', '女',
                   '本市户籍', '非本市户籍居住满半年', '非本市户籍居住不满半年', '6-18', '19-33','34-48', '49-63', 'above 64',
                   '小学生', '工人', '医护人员', '自由职业者', '中学生', '大专院校学生', '公务员', '教育工作者',
                   '公司企业管理者', '事业单位人员', '科技人员', '专职司机（除公交、出租车司机以外）', '军人/警察', '个体/私营户',
                   '农林牧渔生产者', '服务业人员', '公司职员','其他','2000元以下','2000-5000元', '5001-8000元','8000元以上']]
weightdf.to_excel(writer,sheet_name='satisfaction', startrow=0, startcol=0, index=False)
rown=weightdf.shape[0]+2
scoredf.to_excel(writer,sheet_name='satisfaction', startrow=rown, startcol=3, index=False)

sheet1.write(rown+scoredf.shape[0]+3,0,'平均运距：')
sheet1.write(rown+scoredf.shape[0]+3,1,round(data['站间距'].mean()/1000,2))
sheet1.write(rown+scoredf.shape[0]+4,1,stationlist)

writer.save()

#################################################2021 November Data ##########################################
data=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\地铁满意度\乌鲁木齐市轨道客流满意度调查数据库-11.17.xlsx',sheet_name='Sheet1')
if 'Unnamed: 26' in data.columns:
    data=data.drop(columns=[ 'Unnamed: 25', 'Unnamed: 26'])
weightdf = pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\地铁满意度\乌鲁木齐市轨道客流满意度调查数据库-11.17.xlsx',
                         sheet_name='满意度')
satislist = ['4、乘客满意度调查—进出站标识、标志、广播指引等信息全面清晰醒目', '4、购票、检票支付方式以及下载使用相关APP方便快捷',
             '4、安检工作规范有序、通过顺畅', '4、环境整洁、通风良好、温度适宜及空气质量良好',
             '4、候车乘车秩序良好，无乞讨卖艺、散发小广告等行为', '4、乘客信息服务（比如列车内的报站信息）清晰',
             '4、电（扶）梯等服务设施完好、使用正常', '4、列车运行准时、平稳、噪声低', '4、无障碍和人性化设施（比如直梯）完备、运行良好',
             '4、换乘方便快捷（地铁换乘其他交通工具）、换乘标识清晰、秩序良好', '4、工作人员态度友好、答复准确',
             '4、投诉渠道畅通，回复及时满意', '4、进出站、候车、乘车等全过程感觉安全可靠', '4、对列车候车时间是否满意',
             '4、对进出站闸机工作状态是否满意', '4、对周边地标指引标识是否满意',
             '4、对车内设施满意度评价，包括车载广播、电视播报系统，车内环境、通风、空调，座椅扶手安全牢靠等',
             '4、对车门/屏蔽门开关安全无故障满意度评价', '4、对站内逃生疏散通道了解情况']

data['avg_level']=round(data[satislist].mean(axis=1),0)
scorelvl=data.groupby('avg_level')['序号'].count().reset_index().rename(columns={'序号':'count'})
scorelvl['pct']=round(100*scorelvl['count']/scorelvl['count'].sum(),1)
print(scorelvl)

def satisfscore(x):
    if x == 1 or x == 2:
        return 1
    elif x == 3:
        return 0.5
    elif x == 4 or x == 5:
        return 0


for colname in data.columns:
    if colname.startswith('4、'):
        data[colname] = data[colname].apply(lambda x: satisfscore(x))

for satis in satislist:
    weightdf.loc[weightdf['评价内容'] == satis, 'pct'] = data[satis].mean()
weightdf['score'] = round(weightdf['pct'] * weightdf['分值'], 2)
for colname in ['2、站点名称', '3、调查日类型']:
    varlist=set(data[colname])
    for var in varlist:
        for satis in satislist:
            weightdf.loc[weightdf['评价内容']==satis,var]=data.loc[data[colname]==var,satis].mean()
        weightdf[var]=round(weightdf[var]*weightdf['分值'],2)

weightdf.loc[len(weightdf), :] = weightdf.sum(axis=0)
weightdf.iloc[-1, 0] = '总计'
weightdf.iloc[-1,1:3]=''
data['score']=0
for satis in satislist:
    data['score']=data['score']+data[satis]*weightdf.loc[weightdf['评价内容']==satis,'分值'].iloc[0]

scoredf=pd.DataFrame({'评价指标':list(set(weightdf['评价指标']))})
for colname in ['2、站点名称', '3、调查日类型']:
    varlist=set(data[colname])
    for var in varlist:
        for satis2 in set(weightdf['评价指标']):
            scoredf.loc[scoredf['评价指标']==satis2,var]=weightdf.loc[weightdf['评价指标']==satis2,var].sum()

scoredf.loc[len(scoredf),:]=scoredf.sum(axis=0)
scoredf.iloc[-1,0]='总计'


scoredf2=weightdf[weightdf['评价指标']!=''].groupby(['评价指标']).agg(
    分值=pd.NamedAgg(column='分值',aggfunc='sum'),
得分=pd.NamedAgg(column='score',aggfunc='sum'),
).reset_index()
scoredf2['pct']=round(100*scoredf2['得分']/scoredf2['分值'],2)
scoredf2=scoredf2.merge(scoredf,how='left',on='评价指标')

writer=pd.ExcelWriter(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\地铁满意度\地铁满意度summary1122.xlsx')
weightdf.to_excel(writer,sheet_name='satisfaction', startrow=0, startcol=0, index=False)
rown=weightdf.shape[0]+2
scoredf2.to_excel(writer,sheet_name='satisfaction', startrow=rown, startcol=0, index=False)
rown=rown+scoredf.shape[0]+2
scorelvl.to_excel(writer,sheet_name='satisfaction', startrow=rown, startcol=0, index=False)
writer.save()