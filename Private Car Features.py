import requests
import pandas as pd
import numpy as np
import json
import re
import time
from bs4 import BeautifulSoup
import math
from geopy.distance import geodesic
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from shapely.geometry import Point,Polygon,shape
pd.options.mode.chained_assignment = None  # default='warn'
"""
小客车出行调查summary

（二） 使用特征
1. 本地/外地比例及空间分布
2.车辆属性
3.停车位置（夜间、工作）
4.停车费用（夜间、工作）
5.使用频率与用途
6.买车意愿
（三）出行特征
1.出行强度
2.时间分布
3.空间分布
4.出行目的
5.出行时耗
6.出行距离
7.同行人数
"""


cars = pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\小客车出行特征数据库2021.07.16-提交.xlsx', sheet_name='小汽车基本信息')
cartrips = pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\小客车出行特征数据库2021.07.16-提交.xlsx', sheet_name='小汽车出行信息')
import datetime
cars['days']=0
cars['distancedaily']=0
for i in cars.index:
    if isinstance(cars.loc[i,'提交答卷时间'],str):
        cars.loc[i, '提交答卷时间']=datetime.datetime.strptime(cars.loc[i, '提交答卷时间'],"%Y/%m/%d %H:%M:%S")
    if isinstance(cars.loc[i,'提交答卷时间'],str):
        cars.loc[i, '您的车购买时间'] = datetime.datetime.strptime(cars.loc[i, '您的车购买时间'], "%Y/%m/%d %H:%M:%S")
    cars.loc[i,'days']=(cars.loc[i,'提交答卷时间']-cars.loc[i,'您的车购买时间']).days
    if cars.loc[i,'days']>0:
        cars.loc[i, 'distancedaily']=cars.loc[i,'车辆总里程_万公里']*10000/(cars.loc[i,'days'])






cars['本地'] = 'N'
cars.loc[(cars['您的车辆号牌前两位市：汉字'] == '新') & (cars['您的车辆号牌前两位市：首位字母'] == 'A'), '本地'] = 'Y'
cars['age'] = cars['您的车购买时间'].apply(lambda x: 2021 - x.year)
cartrips = pd.merge(cartrips, cars[['车辆序号', '本地', '您的监测站地点']], how='left', on='车辆序号')
cartrips['hour'] = cartrips['出发时间'].apply(lambda x: int(str(x)[0:2]))
cartrips['出行编号'] = range(1, len(cartrips) + 1)

###transfer coordinates to wgs1984
x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 偏心率平方


def out_of_china(lng, lat):
    """
    判断是否在国内，不在国内不做偏移
    """
    return not (lng > 73.66 and lng < 135.05 and lat > 3.86 and lat < 53.55)
def bd09_to_gcj02(bd_lon, bd_lat):
    """
    百度坐标系(BD-09)转火星坐标系(GCJ-02),same with wgs_1984
    """
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gg_lng = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return [gg_lng, gg_lat]
cartrips['coord_wgs']=cartrips.apply(lambda x:bd09_to_gcj02(x['出发X（百度）'], x['出发Y（百度）']),axis=1)
cartrips['出发x_wgs']=cartrips['coord_wgs'].apply(lambda x: x[0])
cartrips['出发y_wgs']=cartrips['coord_wgs'].apply(lambda x: x[1])
cartrips['coord_wgs']=cartrips.apply(lambda x:bd09_to_gcj02(x['到达X（百度）'], x['到达Y（百度）']),axis=1)
cartrips['到达x_wgs']=cartrips['coord_wgs'].apply(lambda x: x[0])
cartrips['到达y_wgs']=cartrips['coord_wgs'].apply(lambda x: x[1])
cartrips=cartrips.drop(columns=['coord_wgs'])
cartrips.to_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\cartrips_wgs.xlsx',index=False)
###spatial join
##run saved trip dataframe in 'Spatial Join.py'
cartrips=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\cartrips.xlsx',sheet_name='Sheet1')

cardistance=cartrips.groupby('车辆序号')['distance'].sum().reset_index()
cars=cars.merge(cardistance,how='left',on='车辆序号')





def checkdistrict(adds_text,dist_sj,city):
    # adds_text: address in text, dist_sj: district from spatial join
    if dist_sj =='Outside':
        if '乌鲁木齐市' in adds_text and '区' in str(adds_text):
            return re.split('[区县]',str(adds_text[5:]))[0]+'区'
        elif '乌鲁木齐市' in adds_text and '县' in str(adds_text):
            return re.split('[区县]',str(adds_text[5:]))[0]+'县'
        elif '乌鲁木齐市' not in adds_text:
            return city
    elif dist_sj in adds_text:
        return dist_sj
    elif dist_sj not in adds_text:
        if '乌鲁木齐市' in adds_text and '区' in str(adds_text):
            return re.split('[区县]',str(adds_text[5:]))[0]+'区'
        elif '乌鲁木齐市' in adds_text and '县' in str(adds_text):
            return re.split('[区县]',str(adds_text[5:]))[0]+'县'
        elif '乌鲁木齐市' not in adds_text:
            return city

cartrips['district_o2']=cartrips.apply(lambda x:checkdistrict(x['出发详细地址'],x['District_O'],x['City_O']),axis=1)
cartrips['district_d2']=cartrips.apply(lambda x:checkdistrict(x['到达详细地址'],x['District_D'],x['City_D']),axis=1)

"""
使用特征: 1. 本地/外地比例 2.车辆属性 3.停车位置（夜间、工作） 4.停车费用（夜间、工作） 5.使用频率与用途 6.买车意愿

"""
#1. 本地/外地比例
car_sum_local = cars.groupby(['本地'])['车辆序号'].count().reset_index().rename(columns={'车辆序号': '数量'})
car_sum_local['percent'] = round(100 * car_sum_local['数量'] / car_sum_local['数量'].sum(), 2)
#2.车辆属性
cars['您的车辆属性是']=cars['您的车辆属性是'].replace([1,2,3],['自有','单位车辆','其他'])
car_sum_own = cars.groupby(['您的车辆属性是'])['车辆序号'].count().reset_index().rename(columns={'车辆序号': '数量'})
car_sum_own['percent'] = round(100 * car_sum_own['数量'] / car_sum_own['数量'].sum(), 2)
#3.停车位置（夜间、工作）
car_sum_park1 = cars.groupby(['您的车辆夜间一般停放在什么地方？']).agg(
    count=pd.NamedAgg(column='车辆序号', aggfunc='count'),
    ave_fee=pd.NamedAgg(column='夜间停车费大约是多少元/月？', aggfunc='mean'),
).reset_index().rename(columns={'count': '数量', 'ave_fee': '平均停车费（元/月）'})
car_sum_park1['Pct_night'] = round(100 * car_sum_park1['数量'] / car_sum_park1['数量'].sum(), 2)
car_sum_park1['平均停车费（元/月）'] = round(car_sum_park1['平均停车费（元/月）'], 2)
car_sum_park1['您的车辆夜间一般停放在什么地方？'] = ['①住宅区划线停车位', '②住宅区非划线区域', '③单位划线停车位', '④单位非划线区域', '⑤路边划线停车位', '⑥路边非划线区域', '⑦公共停车场',
                                     '⑧其他位置（建筑门前、人行道、空地等）']

car_sum_park2 = cars.groupby(['您上班（去工作地）开车一般车辆停在什么地方？ ']).agg(
    count=pd.NamedAgg(column='车辆序号', aggfunc='count'),
    ave_fee=pd.NamedAgg(column='上班停车费大约是多少元/月？', aggfunc='mean'),
).reset_index().rename(columns={'count': '数量', 'ave_fee': '平均停车费（元/月）'})
car_sum_park2['Pct_work'] = round(100 * car_sum_park2['数量'] / car_sum_park2['数量'].sum(), 2)
car_sum_park2['平均停车费（元/月）'] = round(car_sum_park2['平均停车费（元/月）'], 2)
car_sum_park2['您上班（去工作地）开车一般车辆停在什么地方？ '] = ['①基本不开车上班', '②单位划线停车位', '③单位非划线区域', '④路边划线停车位', '⑤路边非划线区域', '⑥公共停车场',
                                            '⑦其他位置（建筑门前、人行道、空地等）']
#4.停车费用（夜间、工作）
car_sum_parkfee=pd.DataFrame([{'夜间停车平均费用':round(cars['夜间停车费大约是多少元/月？'].mean(),2),
                               '夜间停车最高费用':cars['夜间停车费大约是多少元/月？'].max(),
                               '夜间停车最低费用':cars['夜间停车费大约是多少元/月？'].min(),
                               '上班停车平均费用': round(cars['上班停车费大约是多少元/月？'].mean(), 2),
                               '上班停车最高费用': cars['上班停车费大约是多少元/月？'].max(),
                               '上班停车最低费用': cars['上班停车费大约是多少元/月？'].min(),
                               }])

car_sum_parkfee['夜间停车免费比例'] = round(100 * cars.loc[cars['夜间停车费大约是多少元/月？'] == 0, '车辆序号'].count() / cars['车辆序号'].count(),
                                    2)
car_sum_parkfee['上班停车免费比例'] = round(100 * cars.loc[cars['上班停车费大约是多少元/月？'] == 0, '车辆序号'].count() / cars['车辆序号'].count(),
                                    2)
#5.车龄
def age_group_func(age):
    if age <= 6:
        return '6年以内'
    elif age > 6 and age <= 10:
        return '6年以上，10年以内'
    elif age > 10 and age <= 15:
        return '10年以上，15年以内'
    elif age > 15:
        return '15年以上'
cars['age_group'] = cars['age'].apply(lambda x: age_group_func(x))
car_sum_age = cars.groupby('age_group')['车辆序号'].count().reset_index().rename(columns={'车辆序号': '数量','age_group':'车龄'})
car_sum_age['Percent'] = round(100 * car_sum_age['数量'] / car_sum_age['数量'].sum(), 2)
df_sort=pd.DataFrame({'车龄':[ '6年以内','6年以上，10年以内', '10年以上，15年以内','15年以上']})
sort_mapping = df_sort.reset_index().set_index('车龄')
car_sum_age['num'] = car_sum_age['车龄'].map(sort_mapping['index'])
car_sum_age=car_sum_age.sort_values('num').drop(columns=['num'])

#6.总里程
def mileage_group_func(mileage):
    if mileage<= 5:
        return '5万公里以内'
    elif mileage> 5 and mileage<= 10:
        return '5万公里以上，10万公里以内'
    elif mileage> 10 and mileage<= 15:
        return '10万公里以上，15万公里以内'
    elif mileage> 15:
        return '15万公里以上'
cars['mileage_group'] = cars['age'].apply(lambda x: mileage_group_func(x))
car_sum_mileage= cars.groupby('mileage_group')['车辆序号'].count().reset_index().rename(columns={'车辆序号': '数量','mileage_group':'总里程'})
car_sum_mileage['Percent'] = round(100 * car_sum_mileage['数量'] / car_sum_mileage['数量'].sum(), 2)
df_sort=pd.DataFrame({'总里程':[ '5万公里以内','5万公里以上，10万公里以内', '10万公里以上，15万公里以内','15万公里以上']})
sort_mapping = df_sort.reset_index().set_index('总里程')
car_sum_mileage['num'] = car_sum_mileage['总里程'].map(sort_mapping['index'])
car_sum_mileage=car_sum_mileage.sort_values('num').drop(columns=['num'])

#7.油耗
def gasoline_group_func(gasoline):
    if gasoline<= 5:
        return '5L以内'
    elif gasoline> 5 and gasoline<= 10:
        return '5L以上，10L以内'
    elif gasoline> 10 and gasoline<= 15:
        return '10L以上，15L以内'
    elif gasoline> 15:
        return '15L以上'
cars['gasoline_group'] = cars['age'].apply(lambda x: gasoline_group_func(x))
car_sum_gasoline= cars.groupby('gasoline_group')['车辆序号'].count().reset_index().rename(columns={'车辆序号': '数量','gasoline_group':'百公里油耗（L）'})
car_sum_gasoline['Percent'] = round(100 * car_sum_gasoline['数量'] / car_sum_gasoline['数量'].sum(), 2)
df_sort=pd.DataFrame({'百公里油耗（L）':[ '5L以内','5L以上，10L以内', '10L以上，15L以内','15L以上']})
sort_mapping = df_sort.reset_index().set_index('百公里油耗（L）')
car_sum_gasoline['num'] = car_sum_gasoline['百公里油耗（L）'].map(sort_mapping['index'])
car_sum_gasoline=car_sum_gasoline.sort_values('num').drop(columns=['num'])



#8.使用频率
car_sum_freq=cars.groupby('平均下来，您的车辆每周使用多少天？')['车辆序号'].count().reset_index().rename(columns={'车辆序号': '数量'})
car_sum_freq['Percent'] = round(100 * car_sum_freq['数量'] / car_sum_freq['数量'].sum(), 2)
car_sum_freq=car_sum_freq.append([{'平均下来，您的车辆每周使用多少天？':'平均每周使用天数','数量':round(cars['平均下来，您的车辆每周使用多少天？'].mean(),2)}])

#9.用途
car_sum_purp=pd.DataFrame({'使用目的':['总数','比例'],
    '工作相关':[cars['11(日常上班和工作业务)'].sum(),round(100*cars['11(日常上班和工作业务)'].sum()/len(cars),1)],
                               '小孩相关':[cars['11(接送小孩及其他与小孩有关的出行)'].sum(),round(100*cars['11(接送小孩及其他与小孩有关的出行)'].sum()/len(cars),1)],
                               '娱乐活动': [cars['11(游玩、自驾游等 娱乐活动)'].sum(),round(100*cars['11(游玩、自驾游等 娱乐活动)'].sum()/len(cars),1)],
                               '购物餐饮': [cars['11(购物、餐饮等休闲活动)'].sum(),round(100*cars['11(购物、餐饮等休闲活动)'].sum()/len(cars),1)],
                               '其他': [cars['11(其他)'].sum(),round(100*cars['11(其他)'].sum()/len(cars),1)]
                               })


#10.买车意愿
car_sum_will=cars.groupby('近3年内，你的家庭是否会新增小汽车？')['车辆序号'].count().reset_index().rename(columns={'车辆序号': '数量'})
car_sum_will['近3年内，你的家庭是否会新增小汽车？']=['①不会','②会','③说不清楚']
car_sum_will['Percent'] = round(100 * car_sum_will['数量'] / car_sum_will['数量'].sum(), 2)



"""
出行特征: 1.出行强度 2.时间分布 3.空间分布 4.出行目的 5.出行时耗 6.出行距离 7.同行人数
"""

#1.出行强度
cartrip_sum_freq=cartrips.groupby(['车辆序号'] )['您的监测站地点'].count().reset_index().rename(columns={'您的监测站地点':'trips'}).groupby('trips')['车辆序号'].count().reset_index().rename(columns={'车辆序号': '数量'})
cartrip_sum_freq['Percent'] = round(100 * cartrip_sum_freq['数量'] / cartrip_sum_freq['数量'].sum(), 2)
cartrip_sum_freq=cartrip_sum_freq.append([{'trips':'平均','数量':round(cartrips.groupby(['车辆序号'])['您的监测站地点'].count().mean(),2)}])
#2.时间分布
cartrip_sum_hour=cartrips.groupby('hour')['您的监测站地点'].count().reset_index().rename(columns={'您的监测站地点':'trips'})
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
cartrips['period'] = cartrips['hour'] .apply(lambda x:periodfun(x) )
cartrip_sum_hour['Pct']=round(100*cartrip_sum_hour['trips']/cartrip_sum_hour['trips'].sum(),2)
cartrip_sum_period=cartrips.groupby('period')['您的监测站地点'].count().reset_index().rename(columns={'您的监测站地点':'trips'})
cartrip_sum_period['Pct']=round(100*cartrip_sum_period['trips']/cartrip_sum_period['trips'].sum(),2)

#3.空间分布
cartrips.loc[cartrips['district_o2']=='安置小区','district_o2']=cartrips.loc[cartrips['district_o2']=='安置小区','District_O']
cartrips.loc[cartrips['district_d2']=='安置小区','district_d2']=cartrips.loc[cartrips['district_d2']=='安置小区','District_D']
districtlist=['天山区', '头屯河区', '新市区', '水磨沟区','沙依巴克区', '米东区', '乌鲁木齐县','达坂城区','昌吉回族自治州','五家渠市']
cartrips['district_o2']=cartrips['district_o2'].apply(lambda x: x if x in districtlist else '其他')
cartrips['district_d2']=cartrips['district_d2'].apply(lambda x: x if x in districtlist else '其他')
cartrip_sum_od=cartrips.groupby(['district_o2','district_d2'])['您的监测站地点'].count().reset_index().pivot(index='district_o2',columns='district_d2',values='您的监测站地点').reset_index().fillna(0)
cartrip_sum_od=cartrip_sum_od[['district_o2', '天山区', '头屯河区', '新市区', '水磨沟区','沙依巴克区', '米东区', '乌鲁木齐县','达坂城区', '昌吉回族自治州','五家渠市','其他']]
df_sort=pd.DataFrame({'district_o2':['天山区','头屯河区','新市区','水磨沟区','沙依巴克区','米东区','乌鲁木齐县','达坂城区','昌吉回族自治州','五家渠市','其他']})
sort_mapping = df_sort.reset_index().set_index('district_o2')
cartrip_sum_od['num'] = cartrip_sum_od['district_o2'].map(sort_mapping['index'])
cartrip_sum_od=cartrip_sum_od.sort_values('num').drop(columns=['num'])

#4.出行目的
cartrip_sum_purp=cartrips.groupby('出行目的')['您的监测站地点'].count().reset_index().rename(columns={'您的监测站地点':'trips'})
cartrip_sum_purp['出行目的']=['①上班','②上学','③回家','④购物','⑤休闲娱乐','⑥就餐','⑦就医','⑧探亲访友','⑨公务业务','⑩个人业务','⑪回单位','⑫接送人','⑬接送货','⑭其他' ]
cartrip_sum_purp['Percent']=round(100*cartrip_sum_purp['trips']/cartrip_sum_purp['trips'].sum(),2)

#5.同行人数
cartrip_sum_comp=cartrips.groupby('同行人数（含自己）')['您的监测站地点'].count().reset_index().rename(columns={'您的监测站地点':'trips'})
cartrip_sum_comp['Percent']=round(100*cartrip_sum_comp['trips']/cartrip_sum_comp['trips'].sum(),2)
cartrip_sum_comp=cartrip_sum_comp.append([{'同行人数（含自己）':'平均同行人数','trips':round(cartrips['同行人数（含自己）'].mean(),2)}])


#6.出行时耗
def durationfun(start,end):
    if isinstance(start,str):
        start=time.strptime(start,'%H:%M:%S')
    if isinstance(end,str):
        end=time.strptime(end,'%H:%M:%S')
    x=end.tm_hour*60+end.tm_min-start.tm_hour*60-start.tm_min
    return x

def durationfun2(x):
    if x >=0 and x<=10:
        return '0-10分钟'
    elif x>10 and x <=20:
        return '11-20分钟'
    elif x>20 and x<=30:
        return '21-30分钟'
    elif x>30 and x<=40:
        return '31-40分钟'
    elif x>40 and x<=50:
        return '41-50分钟'
    elif x>50 and x<=60:
        return '51-60分钟'
    elif x>60 and x<=70:
        return '61-70分钟'
    elif x>70 and x<=80:
        return '71-80分钟'
    elif x>80:
        return '80分钟以上'
cartrips['duration'] = cartrips.apply(lambda x:durationfun(x['出发时间'],x['到达时间']),axis=1 )
cartrips['duration2'] = cartrips.apply(lambda x:durationfun2(x['duration']),axis=1 )
cartrip_sum_dur=cartrips.groupby('duration2')['您的监测站地点'].count().reset_index().rename(columns={'您的监测站地点':'trips'})
cartrip_sum_dur['Percent']=round(100*cartrip_sum_dur['trips']/cartrip_sum_dur['trips'].sum(),2)
cartrip_sum_dur=cartrip_sum_dur.append([{'duration2':'平均时耗','trips':round(cartrips['duration'].mean(),2)}])

#7.出行距离
def distancefun2(x):
    if x >= 0 and x <= 5:
        return '0-5千米'
    elif x > 5 and x <= 10:
        return '5-10千米'
    elif x > 10 and x <= 20:
        return '10-20千米'
    elif x > 20 and x <= 30:
        return '20-30千米'
    elif x > 30 and x <= 50:
        return '30-50千米'
    elif x > 50 and x <= 100:
        return '50-100千米'
    elif np.isinf(x) == False and x > 15000:
        return '15千米以上'
    elif np.isinf(x) == True:
        return '乌鲁木齐市外'

cartrips['distance2'] = cartrips.apply(lambda x:distancefun2(x['distance']),axis=1 )
cartrip_sum_dist=cartrips.groupby('distance2')['您的监测站地点'].count().reset_index().rename(columns={'您的监测站地点':'trips'})
cartrip_sum_dist['Percent']=round(100*cartrip_sum_dist['trips']/cartrip_sum_dist['trips'].sum(),2)
cartrip_sum_dist=cartrip_sum_dist.append([{'distance2':'平均出行距离','trips':round(cartrips['distance'].mean(),2)}])

# save to excel
cardflist=[car_sum_local,car_sum_own,car_sum_park1,car_sum_park2,car_sum_parkfee,car_sum_age,car_sum_mileage,car_sum_gasoline,car_sum_freq,car_sum_purp,car_sum_will]
cardfnamelist=['车牌来源地','车辆属性','夜间停车点','上班停车点','停车费用','车龄','总里程','油耗','每周使用频率','使用目的','买车意愿']

cartripdflist=[cartrip_sum_freq,cartrip_sum_hour,cartrip_sum_period,cartrip_sum_od,cartrip_sum_purp,cartrip_sum_comp,cartrip_sum_dur,cartrip_sum_dist]
cartripdfnamelist=['出行强度','时辰分布按小时','时辰分布按时段','空间分布','出行目的','同行人数','出行时耗','出行距离']


writer=pd.ExcelWriter(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\小客车出行特征private_car_summary.xlsx')
### 1.车辆信息
if len(cardflist)>0:
    startr = 1
    rowlist = [0]
    for i in range(len(cardflist)):
        cardflist[i].to_excel(writer, sheet_name='车辆信息', startrow=startr, startcol=0, index=False)
        r, c = cardflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['车辆信息']
    for i in range(len(cardflist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, cardfnamelist[i])
###2.小汽车出行信息
if len(cartripdflist)>0:
    startr = 1
    rowlist = [0]
    for i in range(len(cartripdflist)):
        cartripdflist[i].to_excel(writer, sheet_name='出行信息', startrow=startr, startcol=0, index=False)
        r, c = cartripdflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['出行信息']
    for i in range(len(cartripdfnamelist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, cartripdfnamelist[i])

writer.save()


"""
sum_bycar=cartrips.groupby(['','车辆序号'] ).agg(
    trips=pd.NamedAgg(column='出行编号',aggfunc='count'),
    totalpp=pd.NamedAgg(column='同行人数（含自己）',aggfunc='sum'),
    totaldistance=pd.NamedAgg(column='distance_TAZ',aggfunc='sum'),
).reset_index()
sum_bycar['ave_pp']=round(sum_bycar['totalpp']/sum_bycar['trips'],2)
sum_bycar['ave_distance']=round(sum_bycar['totaldistance']/sum_bycar['trips'],2)


import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = [u'SimHei']
plt.rcParams['axes.unicode_minus'] = False

sum_bycar.hist(column='trips',by='您的监测站地点')
figname=r'C:\Users\yi.gu\Documents\Hyder Related\2020乌鲁木齐交通调查任务书\小客车出行特征\出行强度.png'
plt.savefig(figname, bbox_inches='tight')
sum_bycar.hist(column='ave_pp',by='您的监测站地点')
figname=r'C:\Users\yi.gu\Documents\Hyder Related\2020乌鲁木齐交通调查任务书\小客车出行特征\同行人数.png'
plt.savefig(figname, bbox_inches='tight')
sum_bycar.hist(column='ave_distance',by='您的监测站地点')
figname=r'C:\Users\yi.gu\Documents\Hyder Related\2020乌鲁木齐交通调查任务书\小客车出行特征\出行距离.png'
plt.savefig(figname, bbox_inches='tight')

sum_bystation=sum_bycar.groupby('您的监测站地点').agg(
    car_count=pd.NamedAgg(column='车辆序号',aggfunc='count'),
totaltrips=pd.NamedAgg(column='trips',aggfunc='sum'),
    totalpp=pd.NamedAgg(column='totalpp',aggfunc='sum'),
    totaldistance=pd.NamedAgg(column='totaldistance',aggfunc='sum'),
).reset_index()
sum_bystation['ave_trips']=round(sum_bystation['totaltrips']/sum_bystation['car_count'],2)
sum_bystation['ave_pp']=round(sum_bystation['totalpp']/sum_bystation['totaltrips'],2)
sum_bystation['ave_distance']=round(sum_bystation['totaldistance']/sum_bystation['totaltrips'],2)

sum_bystation.to_excel(r'C:\Users\yi.gu\Documents\Hyder Related\2020乌鲁木齐交通调查任务书\小客车出行特征\summary.xlsx',index=False)

sum_bydistance=cartrips.groupby(['您的监测站地点','distance_func']).agg(
    trips=pd.NamedAgg(column='出行编号',aggfunc='count'),
    totalpp=pd.NamedAgg(column='同行人数（含自己）',aggfunc='sum'),
    totaldistance=pd.NamedAgg(column='distance_TAZ',aggfunc='sum'),
).reset_index()
sum_bydistance['ave_pp']=round(sum_bydistance['totalpp']/sum_bydistance['trips'],2)
sum_bydistance['ave_distance']=round(sum_bydistance['totaldistance']/sum_bydistance['trips'],2)
sum_bydistance.to_excel(r'C:\Users\yi.gu\Documents\Hyder Related\2020乌鲁木齐交通调查任务书\小客车出行特征\summary2.xlsx',index=False)


### select 10 trips per location randomly and find the coordinates of origins & destinations from amap（高德地图）,
### calculate the coordinate difference between original coordinates and amap coordinates
import random
selecttriplist=[]
cartrips['flag']='N'
for ind in cartrips.index:
    if cartrips.loc[ind,'distance_func']=='Euclidean':
        cartrips.loc[ind,'flag']='Y'
    # urumqi longitude around 86.63-88.97 latitude 42.75-44.13
    if (cartrips.loc[ind,'出发X（百度）']>=88 or cartrips.loc[ind,'出发X（百度）']<=87 or cartrips.loc[ind,'出发Y（百度）']>=44 or cartrips.loc[ind,'出发Y（百度）']<=43) and '乌鲁木齐' in cartrips.loc[ind,'出发详细地址']:
        cartrips.loc[ind, 'flag'] = 'Y'
    if (cartrips.loc[ind,'到达X（百度）']>=88 or cartrips.loc[ind,'到达X（百度）']<=87 or cartrips.loc[ind,'到达Y（百度）']>=44 or cartrips.loc[ind,'到达Y（百度）']<=43) and '乌鲁木齐' in cartrips.loc[ind,'到达详细地址']:
        cartrips.loc[ind, 'flag'] = 'Y'


for i in range(1,16):
    cartripsi=cartrips[(cartrips['您的监测站地点']==i)]
    listi = list(cartripsi['出行编号'])
    slice = random.sample(listi, 10)
    print(slice)
    selecttriplist.append(slice)

selecttriplist=np.array(selecttriplist).flatten()
#selecttriplist=np.array(cartrips.loc[cartrips['flag']=='Y', '出行编号'])
selecttripdf=pd.DataFrame(columns=[ '出行编号','出发X（高德）', '出发Y（高德）', '到达X（高德）', '到达Y（高德）'])
for t in selecttriplist[182:-1]:
    origin=list(cartrips.loc[cartrips['出行编号']==t,'出发详细地址'])[0]
    destin=list(cartrips.loc[cartrips['出行编号']==t,'到达详细地址'])[0]
    url = 'https://restapi.amap.com/v3/place/text?keywords={}&city=%E4%B9%8C%E9%B2%81%E6%9C%A8%E9%BD%90&offset=20&page=1&key=3a54f278f73608bb1e859f3249e94eef&extensions=base'.format(
        origin)
    r = requests.get(url, verify=False).text
    rt = json.loads(r)
    if (rt['status'] == '1') and (rt['count']!='0'):
        print(origin, rt['pois'][0]['location'])
        locastr= rt['pois'][0]['location']
        long0=float(locastr.split(',')[0])
        lat0=float(locastr.split(',')[1])
    else:
        print(origin, 'NA')
        long0 = 87
        lat0 = 43

    url = 'https://restapi.amap.com/v3/place/text?keywords={}&city=%E4%B9%8C%E9%B2%81%E6%9C%A8%E9%BD%90&offset=20&page=1&key=3a54f278f73608bb1e859f3249e94eef&extensions=base'.format(
        destin)
    r = requests.get(url, verify=False).text
    rt = json.loads(r)
    if (rt['status'] == '1') and (rt['count']!='0'):
        print(destin, rt['pois'][0]['location'])
        locastr = rt['pois'][0]['location']
        long1 = float(locastr.split(',')[0])
        lat1 = float(locastr.split(',')[1])
    else:
        print(destin, 'NA')
        long1 = 87
        lat1 = 43

    selecttripdf = selecttripdf.append([{'出行编号':t, '出发X（高德）':long0, '出发Y（高德）':lat0, '到达X（高德）':long1, '到达Y（高德）':lat1}])

selecttripdf=pd.merge(selecttripdf,cartrips[['出行编号', '您的监测站地点','出发X（百度）', '出发Y（百度）', '出发详细地址', '到达X（百度）',
       '到达Y（百度）', '到达详细地址']],how='left',on=['出行编号'])

def distancefun2(lat1,long1,lat2,long2):
        try:
            lat1 = float(lat1)
            long1 = float(long1)
            lat2 = float(lat2)
            long2 = float(long2)
            distance = geodesic((lat1, long1), (lat2, long2)).m  # 计算两个坐标直线距离
            return round(distance/1000, 2)
        except:
            return float("inf")


selecttripdf['distance_o']= selecttripdf.apply(lambda x:distancefun2(x['出发Y（百度）'],x['出发X（百度）'], x['出发Y（高德）'],x['出发X（高德）']),axis=1 )
selecttripdf['distance_d']= selecttripdf.apply(lambda x:distancefun2(x['到达Y（百度）'],x['到达X（百度）'], x['到达Y（高德）'],x['到达X（高德）']),axis=1 )

selecttripdf.to_excel(r'C:\Users\yi.gu\Documents\Hyder Related\2020乌鲁木齐交通调查任务书\coord_accurateness_test2.xlsx',index=False)


#request coordinates using address(text) from amap API
#http://restapi.amap.com/v3/place/text?key=3a54f278f73608bb1e859f3249e94eef&keywords={}&city=乌鲁木齐&children=1&offset=20&page=1&extensions=all



#request driving distance between two coordinates from amap API,no more than 6 digits, limit 2k per day
#https://restapi.amap.com/v3/distance?key=3a54f278f73608bb1e859f3249e94eef&origins=116.481028,39.989643&destination=114.465302,40.004717&type=1&output=json
#https://restapi.amap.com/v3/distance?key=3a54f278f73608bb1e859f3249e94eef&origins=87.298477,44.017088&destination=87.593462,43.843248&type=1
#jsontext['results'][0]['distance']

"""
#####weighted car OD
cars = pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\小客车出行特征数据库2021.07.16-提交.xlsx', sheet_name='小汽车基本信息')
cartrips=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\cartrips.xlsx',sheet_name='Sheet1')

"""
locationdf=pd.DataFrame({'您的监测站地点':[1,3,5,6,7,8,9,11,12,13,15],'监测站':['Y','Y','Y','Y','Y','Y','Y','Y','Y','Y','Y']})
cars=cars.merge(locationdf,how='left',on='您的监测站地点').dropna(subset=['监测站'])
cartrips=cartrips.merge(locationdf,how='left',on='您的监测站地点').dropna(subset=['监测站'])
"""

def checkdistrict(adds_text,dist_sj,city):
    # adds_text: address in text, dist_sj: district from spatial join
    if dist_sj =='Outside':
        if '乌鲁木齐市' in adds_text and '区' in str(adds_text):
            return re.split('[区县]',str(adds_text[5:]))[0]+'区'
        elif '乌鲁木齐市' in adds_text and '县' in str(adds_text):
            return re.split('[区县]',str(adds_text[5:]))[0]+'县'
        elif '乌鲁木齐市' not in adds_text:
            return city
    elif dist_sj in adds_text:
        return dist_sj
    elif dist_sj not in adds_text:
        if '乌鲁木齐市' in adds_text and '区' in str(adds_text):
            return re.split('[区县]',str(adds_text[5:]))[0]+'区'
        elif '乌鲁木齐市' in adds_text and '县' in str(adds_text):
            return re.split('[区县]',str(adds_text[5:]))[0]+'县'
        elif '乌鲁木齐市' not in adds_text:
            return city

cartrips['district_o2']=cartrips.apply(lambda x:checkdistrict(x['出发详细地址'],x['District_O'],x['City_O']),axis=1)
cartrips['district_d2']=cartrips.apply(lambda x:checkdistrict(x['到达详细地址'],x['District_D'],x['City_D']),axis=1)
cartrips.loc[cartrips['district_o2']=='安置小区','district_o2']=cartrips.loc[cartrips['district_o2']=='安置小区','District_O']
cartrips.loc[cartrips['district_d2']=='安置小区','district_d2']=cartrips.loc[cartrips['district_d2']=='安置小区','District_D']
districtlist=['天山区', '头屯河区', '新市区', '水磨沟区','沙依巴克区', '米东区', '乌鲁木齐县','达坂城区','昌吉回族自治州','五家渠市']
cartrips['district_o2']=cartrips['district_o2'].apply(lambda x: x if x in districtlist else '其他')
cartrips['district_d2']=cartrips['district_d2'].apply(lambda x: x if x in districtlist else '其他')

Region=gpd.read_file(r'C:\Users\yi.gu\Documents\Hyder Related\Test GIS\District\District.shp',encoding='gbk')
Region=Region.to_crs(4326)
Parking= gpd.GeoDataFrame(cars, geometry=gpd.points_from_xy(cars[ '车辆夜间一般停放地点X(百度）'], cars['车辆夜间一般停放地点Y（百度）'], crs="EPSG:4326"))
Parking_Region = gpd.sjoin(Parking,Region,how="left",op='within')

Parking_region_sum=Parking_Region.groupby('District')['车辆序号'].count().reset_index()
dfhhw=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Results\Results0922\df_Kid_adj.xlsx')
dfhhw['total']=dfhhw['私家车']*dfhhw['HHweight4']
cardf=dfhhw.groupby('行政区')['total'].sum().reset_index()
cardf['行政区']=cardf['行政区'].replace(['经开区','高新区'],['头屯河区','新市区'])
Parking_region_sum=Parking_region_sum.merge(cardf,how='left',left_on='District',right_on='行政区')
Parking_region_sum['weight1']=Parking_region_sum['total']/Parking_region_sum['车辆序号']
Parking_region_sum['weight2']=Parking_region_sum['total'].sum()/Parking_region_sum['车辆序号'].sum()
cars=cars.merge(Parking_Region[['车辆序号','District']],how='left',on='车辆序号')
cars=cars.merge(Parking_region_sum[['District','weight1','weight2']],how='left',on='District')
cartrips=cartrips.merge(cars[['车辆序号','weight1','weight2']],how='left',on='车辆序号')
"""
cartrips['distance0']=cartrips['distance'].apply(lambda x: round(x,0))
import seaborn as sns
dftrip1=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Results\Results0922\dftrip_forsummary.xlsx')
dftrip1['distance0']=dftrip1['distance'].apply(lambda x: round(x,0))
dftrip1['modecount']=dftrip1['modelist'].apply(lambda x: len(x.split(',')))


dftrip2=dftrip1[(dftrip1['pc']==1)&(dftrip1['modecount']==1)]
dftrip2=dftrip2[(dftrip2['TAZ_O']>0)&(dftrip2['TAZ_D']>0)]
avetrip_dist3=(dftrip2['distance']*dftrip2['carweight']).sum()/dftrip2['carweight'].sum()
print(round(avetrip_dist3,3))

dftrip_dist3=dftrip2.groupby('distance0')['carweight'].sum().reset_index().rename(columns={'carweight':'count'}).sort_values(by='distance0')
dftrip_dist3['pct']=dftrip_dist3['count']/dftrip_dist3['count'].sum()

dftrip_dist=dftrip1[(dftrip1['pc']==1)&(dftrip1['modecount']==1)].groupby('distance0')['carweight'].sum().reset_index().rename(columns={'carweight':'count'}).sort_values(by='distance0')
dftrip_dist['pct']=dftrip_dist['count']/dftrip_dist['count'].sum()
ave_dist1=(dftrip1.loc[(dftrip1['pc']==1)&(dftrip1['modecount']==1),'distance']*dftrip1.loc[(dftrip1['pc']==1)&(dftrip1['modecount']==1),'carweight']).sum()/dftrip1.loc[(dftrip1['pc']==1)&(dftrip1['modecount']==1),'carweight'].sum()

cartrip_dist=cartrips.groupby('distance0')['index'].count().reset_index().rename(columns={'index':'count'}).sort_values(by='distance0')
cartrip_dist['pct']=cartrip_dist['count']/cartrip_dist['count'].sum()
ave_dist2=(cartrips['distance']*cartrips['weight1']).sum()/cartrips['weight1'].sum()
print('居民出行调查仅使用小汽车的出行平均距离：',round(ave_dist1,2),'小汽车调查出行平均距离：',round(ave_dist2,2))
plt.plot(dftrip_dist['distance0'],dftrip_dist['pct'],color='red',label='travel survey')
plt.plot(cartrip_dist['distance0'],cartrip_dist['pct'],color='blue',label='private car survey')
plt.legend()
"""

#1.出行强度

cartrips_sum=cartrips.groupby('车辆序号').agg(
    count=pd.NamedAgg(column='您的监测站地点',aggfunc='count'),
    weight1=pd.NamedAgg(column='weight1',aggfunc='mean'),
    weight2=pd.NamedAgg(column='weight2',aggfunc='mean'),
).reset_index()
freq1=(cartrips_sum['count']*cartrips_sum['weight1']).sum()/cartrips_sum['weight1'].sum()
freq2=(cartrips_sum['count']*cartrips_sum['weight2']).sum()/cartrips_sum['weight2'].sum()
print(round(freq1,2),round(freq2,2))
cartrip_sum_freq=cartrips_sum.groupby('count').agg(
    weight1=pd.NamedAgg(column='weight1',aggfunc='sum'),
    weight2=pd.NamedAgg(column='weight2',aggfunc='sum'),
).reset_index()
cartrip_sum_freq['pct1']=round(100*cartrip_sum_freq['weight1']/cartrip_sum_freq['weight1'].sum(),1)
cartrip_sum_freq['pct2']=round(100*cartrip_sum_freq['weight2']/cartrip_sum_freq['weight2'].sum(),1)
#

#3.空间分布

cartrip_sum_od=cartrips.groupby(['district_o2','district_d2'])['weight1'].sum().reset_index().pivot(index='district_o2',columns='district_d2',values='weight1').reset_index().fillna(0)
cartrip_sum_od=cartrip_sum_od[['district_o2', '天山区', '头屯河区', '新市区', '水磨沟区','沙依巴克区', '米东区', '乌鲁木齐县','达坂城区', '昌吉回族自治州','五家渠市','其他']]
df_sort=pd.DataFrame({'district_o2':['天山区','头屯河区','新市区','水磨沟区','沙依巴克区','米东区','乌鲁木齐县','达坂城区','昌吉回族自治州','五家渠市','其他']})
sort_mapping = df_sort.reset_index().set_index('district_o2')
cartrip_sum_od['num'] = cartrip_sum_od['district_o2'].map(sort_mapping['index'])
cartrip_sum_od=cartrip_sum_od.sort_values('num').drop(columns=['num'])


cartrip_sum_od2=cartrips.groupby(['district_o2','district_d2'])['weight2'].sum().reset_index().pivot(index='district_o2',columns='district_d2',values='weight2').reset_index().fillna(0)
cartrip_sum_od2=cartrip_sum_od2[['district_o2', '天山区', '头屯河区', '新市区', '水磨沟区','沙依巴克区', '米东区', '乌鲁木齐县','达坂城区', '昌吉回族自治州','五家渠市','其他']]
df_sort=pd.DataFrame({'district_o2':['天山区','头屯河区','新市区','水磨沟区','沙依巴克区','米东区','乌鲁木齐县','达坂城区','昌吉回族自治州','五家渠市','其他']})
sort_mapping = df_sort.reset_index().set_index('district_o2')
cartrip_sum_od2['num'] = cartrip_sum_od2['district_o2'].map(sort_mapping['index'])
cartrip_sum_od2=cartrip_sum_od2.sort_values('num').drop(columns=['num'])

#4.出行目的
cartrip_sum_purp=cartrips.groupby('出行目的').agg(
    weight1=pd.NamedAgg(column='weight1',aggfunc='sum'),
    weight2=pd.NamedAgg(column='weight2',aggfunc='sum'),
).reset_index()

cartrip_sum_purp['pct1']=round(100*cartrip_sum_purp['weight1']/cartrip_sum_purp['weight1'].sum(),1)
cartrip_sum_purp['pct2']=round(100*cartrip_sum_purp['weight2']/cartrip_sum_purp['weight2'].sum(),1)
cartrip_sum_purp['出行目的']=['①上班','②上学','③回家','④购物','⑤休闲娱乐','⑥就餐','⑦就医','⑧探亲访友','⑨公务业务','⑩个人业务','⑪回单位','⑫接送人','⑬接送货','⑭其他' ]



#6.出行时耗

def durationfun2(x):
    if x >=0 and x<=10:
        return '0-10分钟'
    elif x>10 and x <=20:
        return '11-20分钟'
    elif x>20 and x<=30:
        return '21-30分钟'
    elif x>30 and x<=40:
        return '31-40分钟'
    elif x>40 and x<=50:
        return '41-50分钟'
    elif x>50 and x<=60:
        return '51-60分钟'
    elif x>60 and x<=70:
        return '61-70分钟'
    elif x>70 and x<=80:
        return '71-80分钟'
    elif x>80:
        return '80分钟以上'

cartrips['duration2'] = cartrips.apply(lambda x:durationfun2(x['duration']),axis=1 )
cartrip_sum_dur=cartrips.groupby('duration2').agg(
    weight1=pd.NamedAgg(column='weight1',aggfunc='sum'),
weight2=pd.NamedAgg(column='weight2',aggfunc='sum'),
).reset_index()
cartrip_sum_dur['Pct1']=round(100*cartrip_sum_dur['weight1']/cartrip_sum_dur['weight1'].sum(),2)
cartrip_sum_dur['Pct2']=round(100*cartrip_sum_dur['weight2']/cartrip_sum_dur['weight2'].sum(),2)
ave_dur1=(cartrips['weight1']*cartrips['duration']).sum()/cartrips['weight1'].sum()
ave_dur2=(cartrips['weight2']*cartrips['duration']).sum()/cartrips['weight2'].sum()
cartrip_sum_dur=cartrip_sum_dur.append([{'duration2':'平均时耗','Pct1':round(ave_dur1,2),'Pct2':round(ave_dur2,2)}])

#7.出行距离
def distancefun2(x):
    if x >= 0 and x <= 5:
        return '0-5千米'
    elif x > 5 and x <= 10:
        return '5-10千米'
    elif x > 10 and x <= 15:
        return '10-15千米'
    elif x > 15 and x <= 20:
        return '15-20千米'
    elif np.isinf(x) == False and x > 20:
        return '20千米以上'
    elif np.isinf(x) == True:
        return '乌鲁木齐市外'

cartrips['distance2'] = cartrips.apply(lambda x:distancefun2(x['distance']),axis=1 )
cartrip_sum_dist=cartrips.groupby('distance2').agg(
    weight1=pd.NamedAgg(column='weight1',aggfunc='sum'),
weight2=pd.NamedAgg(column='weight2',aggfunc='sum'),
).reset_index()
cartrip_sum_dist['Pct1']=round(100*cartrip_sum_dist['weight1']/cartrip_sum_dist['weight1'].sum(),2)
cartrip_sum_dist['Pct2']=round(100*cartrip_sum_dist['weight2']/cartrip_sum_dist['weight2'].sum(),2)
ave_dist1=(cartrips['weight1']*cartrips['distance']).sum()/cartrips['weight1'].sum()
ave_dist2=(cartrips['weight2']*cartrips['distance']).sum()/cartrips['weight2'].sum()
cartrip_sum_dist=cartrip_sum_dist.append([{'distance2':'平均时耗','Pct1':round(ave_dist1,2),'Pct2':round(ave_dist2,2)}])

###穿越核查线
IOTAZ=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\crosssection volume\TAZ with crosssection.xls')
cartrips=cartrips.merge(IOTAZ[['TAZ','环路']],how='left',left_on='TAZ_O',right_on='TAZ').rename(columns={'环路':'环路_O'})
cartrips=cartrips.merge(IOTAZ[['TAZ','环路']],how='left',left_on='TAZ_D',right_on='TAZ').rename(columns={'环路':'环路_D'})
cartrips=cartrips.drop(columns=['TAZ_x','TAZ_y'])
cartrips[['环路_O','环路_D']]=cartrips[['环路_O','环路_D']].fillna('环外')
def direction(x1,y1,x2,y2):
    if x2>x1 and y2>y1:
        return '东北方向'
    elif x2>x1 and y2<y1:
        return '东南方向'
    elif x2<x1 and y2>y1:
        return '西北方向'
    elif x2<x1 and y2<y1:
        return '西南方向'
cartrips['direction']=cartrips.apply(lambda x: direction(x['出发x_wgs'],x['出发y_wgs'],x['到达x_wgs'],x['到达y_wgs']),axis=1)

circle=cartrips.groupby(['环路_O','环路_D']).agg(
    weight1=pd.NamedAgg(column='weight1',aggfunc='sum'),
weight2=pd.NamedAgg(column='weight2',aggfunc='sum'),
).reset_index()
Lines=gpd.read_file(r'C:\Users\yi.gu\Documents\Hyder Related\Test GIS\公交满载率调查点位图层\New_Shapefile.shp',encoding='UTF-8')
Lines=Lines.to_crs(4326)

from shapely import geometry
linelist=[]
for i in cartrips.index:
        line=geometry.LineString([(cartrips.loc[i, '出发x_wgs'],cartrips.loc[i, '出发y_wgs']),(cartrips.loc[i, '到达x_wgs'],cartrips.loc[i, '到达y_wgs'])])
        linelist.append(line)
polylines=gpd.GeoSeries(linelist,crs='EPSG:4326',index=cartrips['index'])
triplines=gpd.GeoDataFrame()
triplines['geometry']=polylines
triplines['index']=cartrips['index']
triplines['weight1']=cartrips['weight1']
triplines['weight2']=cartrips['weight2']
triplines['direction']=cartrips['direction']
for j in Lines.index:
    name=Lines.loc[j,'SectionNam']
    triplines[name]=triplines['geometry'].intersects(Lines.loc[j,'geometry'])
sum_df0=pd.DataFrame()
for col1 in ['河滩路', '东一环', '西一环']:
    triplines2=triplines[triplines[col1]==True]
    triplines2['direction']=triplines['direction'].replace(['西南方向', '东南方向', '西北方向', '东北方向'],['由东向西', '由西向东', '由东向西', '由西向东'])
    sum_df=triplines2.groupby('direction').agg(
        weight1=pd.NamedAgg(column='weight1',aggfunc='sum'),
        weight2=pd.NamedAgg(column='weight2', aggfunc='sum'),
    ).reset_index()
    sum_df['section']=col1
    sum_df0=pd.concat([sum_df0,sum_df],ignore_index=True)
for col1 in ['克拉玛依路-南湖路','苏州路', '南外环']:
    triplines2=triplines[triplines[col1]==True]
    triplines2['direction']=triplines['direction'].replace(['西南方向', '东南方向', '西北方向', '东北方向'],['由北向南', '由北向南', '由南向北', '由南向北'])
    sum_df=triplines2.groupby('direction').agg(
        weight1=pd.NamedAgg(column='weight1',aggfunc='sum'),
        weight2=pd.NamedAgg(column='weight2', aggfunc='sum'),
    ).reset_index()
    sum_df['section']=col1
    sum_df0=pd.concat([sum_df0,sum_df],ignore_index=True)


IOdf=pd.DataFrame({'section':['东一环', '西一环','苏州路', '南外环','东一环', '西一环','苏州路', '南外环'],
                   'direction':['由东向西','由西向东','由北向南','由南向北','由西向东','由东向西','由南向北','由北向南'],
                   '进出城':['进城','进城','进城','进城','出城','出城','出城','出城']})
sum_df0=sum_df0.merge(IOdf,how='left',on=['section','direction']).fillna('NA')
#进城
print(sum_df0.loc[sum_df0['进出城']=='进城','weight1'].sum())
print(sum_df0.loc[sum_df0['进出城']=='进城','weight2'].sum())
#出城
print(sum_df0.loc[sum_df0['进出城']=='出城','weight1'].sum())
print(sum_df0.loc[sum_df0['进出城']=='出城','weight2'].sum())




# save to excel
cartripdflist=[cartrip_sum_freq,cartrip_sum_od,cartrip_sum_od2,cartrip_sum_dur,cartrip_sum_dist,sum_df0]
cartripdfnamelist=['出行强度','空间分布-分区加权','空间分布-不分区加权','出行时耗','出行距离','校核线']


writer=pd.ExcelWriter(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\小客车出行特征private_car_summary_weighted.xlsx')

if len(cartripdflist)>0:
    startr = 1
    rowlist = [0]
    for i in range(len(cartripdflist)):
        cartripdflist[i].to_excel(writer, sheet_name='出行信息', startrow=startr, startcol=0, index=False)
        r, c = cartripdflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['出行信息']
    for i in range(len(cartripdfnamelist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, cartripdfnamelist[i])

writer.save()

##### find the taz matrics
from shapely.ops import nearest_points
from shapely.geometry import Point


TAZ = gpd.read_file(r'C:\Users\yi.gu\Documents\Hyder Related\Test GIS\TAZ\TAZ.shp',encoding='gbk')
TAZ=TAZ.to_crs(4326)
TAZ_centroid=gpd.GeoDataFrame(TAZ[['ID','TAZ']],geometry=TAZ['geometry'].centroid,crs="EPSG:4326")
TAZ_centroid=TAZ_centroid.to_crs(4326)
TAZ_union=TAZ_centroid.geometry.unary_union

cartrips['keep']=1
cartrips.loc[(cartrips['City_O']!='乌鲁木齐市')&(cartrips['City_D']!='乌鲁木齐市'),'keep']=0
cartrips=cartrips[cartrips['keep']==1]
origin = gpd.GeoDataFrame(
    cartrips[['index', '车辆序号', '出行序号', '出发x_wgs', '出发y_wgs',
       'TAZ_O']], geometry = gpd.points_from_xy(cartrips['出发x_wgs'], cartrips['出发y_wgs'], crs="EPSG:4326"))
desti = gpd.GeoDataFrame(
    cartrips[['index', '车辆序号', '出行序号', '到达x_wgs', '到达y_wgs',
       'TAZ_D']], geometry = gpd.points_from_xy(cartrips['到达x_wgs'], cartrips['到达y_wgs'], crs="EPSG:4326"))
Origin_TAZ = gpd.sjoin(origin,TAZ,how="left",op='within')
Desti_TAZ = gpd.sjoin(desti,TAZ,how="left",op='within')


def near(point, pts=TAZ_union):
    # find the nearest point and return the corresponding Place value
    nearest = TAZ_centroid.geometry == nearest_points(point, pts)[1]
    return list(TAZ_centroid[nearest].TAZ)[0]


Origin_TAZ.loc[Origin_TAZ['TAZ_O']==0,'TAZ_O'] = Origin_TAZ[Origin_TAZ['TAZ_O']==0].apply(lambda row: near(row.geometry), axis=1)
Origindf=Origin_TAZ[['index','TAZ_O']]
Desti_TAZ.loc[Desti_TAZ['TAZ_D']==0,'TAZ_D'] = Desti_TAZ[Desti_TAZ['TAZ_D']==0].apply(lambda row: near(row.geometry), axis=1)
Destidf=Desti_TAZ[['index','TAZ_D']]
cartrips['TAZ_O']=cartrips['index'].map(Origindf['TAZ_O'])
cartrips['TAZ_D']=cartrips['index'].map(Destidf['TAZ_D'])

TAZ_OD1=cartrips.groupby(['TAZ_O','TAZ_D'])['weight1'].sum().reset_index().pivot(index='TAZ_O',columns='TAZ_D',values='weight1').reset_index()
TAZ_OD2=cartrips.groupby(['TAZ_O','TAZ_D'])['weight2'].sum().reset_index().pivot(index='TAZ_O',columns='TAZ_D',values='weight2').reset_index()

writer=pd.ExcelWriter(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\小汽车出行特征OD_weighted.xlsx')
TAZ_OD1.to_excel(writer, sheet_name='权重分区', startrow=0, startcol=0, index=False)
TAZ_OD2.to_excel(writer, sheet_name='权重不分区', startrow=0, startcol=0, index=False)
writer.save()

