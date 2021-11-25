
###轨道站点800米范围内的轨道交通通勤量占城市总通勤量百分比
import numpy as np
import pandas as pd
from geopy.distance import geodesic
import matplotlib.pyplot as plt
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point,Polygon,shape
from shapely.ops import nearest_points

pd.options.mode.chained_assignment = None  # default='warn'
plt.rcParams['font.family'] = 'simhei'
summarypath=r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Results\Results1109'
dfhhw=pd.read_excel(summarypath+'\household_forsummary1109.xlsx')
dfppw=pd.read_excel(summarypath+'\person_forsummary1109.xlsx')
dftripw=pd.read_excel(summarypath+'\dftrip_forsummary1109_duptrips.xlsx')
dftripw['duration']=dftripw['duration'].apply(lambda x: 1440+x if x<0 else x)
def dur_slot(x):
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
dftripw.loc[dftripw['出行编号'].isnull()==False,'duration2']=dftripw.loc[dftripw['出行编号'].isnull()==False,'duration'].apply(lambda x:dur_slot(x))
def weightmean(df,col,weight):
    wm=round((df[col]*df[weight]).sum()/df[weight].sum(),2)
    return wm



dfppw=dfppw.merge(dftripw.groupby('成员编号')['出行序号'].count().reset_index(),how='left',on='成员编号')
dfppw['wght_ct']=dfppw['carweight']*dfppw['出行序号']
age_sum=dfppw.groupby('年龄').agg(
    wght=pd.NamedAgg(column='carweight',aggfunc='sum'),
wght_ct=pd.NamedAgg(column='wght_ct',aggfunc='sum'),
).reset_index()
age_sum['ave_trip']=age_sum['wght_ct']/age_sum['wght']
plt.scatter(x=np.array(age_sum['年龄']),y=np.array(age_sum['ave_trip']))
age_sum.to_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Results\Results0922\age_trip_sum.xlsx')
metrostation=gpd.read_file(r'C:\Users\yi.gu\Documents\Hyder Related\Test GIS\Subway Station.shp')
metrostation=metrostation.to_crs(3857)
metrobuffer=gpd.GeoDataFrame({'Id':metrostation['Id'],'Sta_Name':metrostation['Sta_Name'],'geometry':metrostation.buffer(800)})
metrobuffer=metrobuffer.to_crs(4326)

metro_union=metrostation.geometry.unary_union

home=gpd.GeoDataFrame(dfhhw, geometry=gpd.points_from_xy(dfhhw['家庭X'], dfhhw['家庭Y'], crs="EPSG:4326"))
school=gpd.GeoDataFrame(dfppw, geometry=gpd.points_from_xy(dfppw['工作/学校地址X'], dfppw['工作/学校地址Y'], crs="EPSG:4326"))
homemetro=gpd.sjoin(home,metrobuffer,how="inner",op='within').dropna(subset=['Sta_Name']).drop_duplicates(['家庭编号'])
schoolmetro=gpd.sjoin(school,metrobuffer,how="inner",op='within').dropna(subset=['Sta_Name']).drop_duplicates(['成员编号'])
print(homemetro['Sta_Name'].dropna(),(homemetro['HHweight4']*homemetro['家庭总人数']).sum()/(home['HHweight4']*home['家庭总人数']).sum())
print(schoolmetro['Sta_Name'].dropna(),schoolmetro['carweight'].sum()/school['carweight'].sum())
#people live or work close to metro station

dfppw['metro']='N'
dfppw.loc[dfppw['成员编号'].isin(list(schoolmetro['成员编号'])),'metro']='Y'
dfppw.loc[dfppw['家庭编号'].isin(list(homemetro['家庭编号'])),'metro']='Y'
print(dfppw.groupby('metro')['carweight'].sum())
metro_potential=dfppw.groupby('metro')['carweight'].sum().loc['Y']
print(round(metro_potential,0))
columnlist=['第一种交通方式', '第二种交通方式', '第三种交通方式', '第四种交通方式', '第五种交通方式']
def metrotrip(df):
    if ((df['第一种交通方式'] =='地铁') or (df['第二种交通方式'] =='地铁') or (df['第三种交通方式'] =='地铁')
            or (df['第四种交通方式']=='地铁') or (df['第五种交通方式'] =='地铁')):
        return 1
    else:
        return 0
dftripw['metrotrip']=dftripw[columnlist].apply(lambda x:metrotrip(x), axis=1)
dfppw=dfppw.merge(dftripw.groupby('成员编号')['metrotrip'].sum().reset_index(),how='left',on='成员编号')
dfppw['metrotrip']=dfppw['metrotrip'].fillna(0)
metro_passenger=dfppw.loc[dfppw['metrotrip']>0,'carweight'].sum()
print('住在地铁附近或学校/单位附近有地铁的居民',round(metro_passenger,0))
#住在地铁附近或学校/单位附近有地铁的居民中会使用地铁的比例
print('住在地铁附近或学校/单位附近有地铁的居民中会使用地铁的比例',round(metro_passenger/metro_potential,4))

dfppw=dfppw.merge(dftripw[(dftripw['分类']=='基家工作')|(dftripw['分类']=='基家就学')].groupby('成员编号')['metrotrip'].sum().reset_index().rename(columns={'metrotrip':'metro_commute'}),how='left',on='成员编号')
dfppw['metro_commute']=dfppw['metro_commute'].fillna(0)
metro_commute=dfppw.loc[dfppw['metro_commute']>0,'carweight'].sum()
print(round(metro_commute,0))
#住在地铁附近或学校/单位附近有地铁的居民中会使用地铁通勤的比例
print(round(metro_commute/metro_potential,4))

#dftrip_commute=dftripw[(dftripw['分类']=='基家就学')|(dftripw['分类']=='基家工作')]
dftrip_commute=dftripw[(dftripw['出行目的']=='上班')|(dftripw['出行目的']=='上学')]

dftrip_commute=dftrip_commute.reset_index()

print(dfppw.loc[dfppw['']])
print('5公里内的通勤出行占所有通勤出行的比例')
print(dftrip_commute.loc[dftrip_commute['distance0']<=5,'carweight'].sum()/dftrip_commute['carweight'].sum())
print('通勤5公里内的人占全部通勤人口的比例')
commutepp5=dftrip_commute[dftrip_commute['distance0']<=5].drop_duplicates(subset=['成员编号'])['carweight'].sum()
print('通勤5公里内的人',commutepp5)
commutepp=dfppw.loc[(dfppw['就业就学状态']=='工作')|(dfppw['就业就学状态']=='就学'),'carweight'].sum()
#commutepp=dftrip_commute.drop_duplicates(subset=['成员编号'])['carweight'].sum()
print('需要通勤总人口',round(commutepp,1))


print('通勤5公里内的人占全部通勤人口的比例',round(commutepp5/commutepp,4))
commutepp45=dftrip_commute[dftrip_commute['duration']<=45].drop_duplicates(subset=['成员编号'])['carweight'].sum()
print('通勤45分钟内的人',round(commutepp45,1))
print('通勤45分钟内的人占全部通勤人口的比例',round(commutepp45/commutepp,4))
for purp in ['上班','上学']:
    print(purp)
    print('平均距离', weightmean(dftrip_commute[dftrip_commute['出行目的']==purp], 'distance0', 'carweight'))
    print('平均时耗', weightmean(dftrip_commute[dftrip_commute['出行目的']==purp], 'duration', 'carweight'))
print('平均通勤距离',weightmean(dftrip_commute,'distance0','carweight'))
print('平均通勤时耗',weightmean(dftrip_commute,'duration','carweight'))
commute_o=gpd.GeoDataFrame(dftrip_commute, geometry=gpd.points_from_xy(dftrip_commute['出发X'], dftrip_commute['出发Y'], crs="EPSG:4326"))
commute_d=gpd.GeoDataFrame(dftrip_commute, geometry=gpd.points_from_xy(dftrip_commute['到达X'], dftrip_commute['到达Y'], crs="EPSG:4326"))
commute_ometro=gpd.sjoin(commute_o,metrobuffer,how="inner",op='within').dropna(subset=['Sta_Name']).drop_duplicates(['index'])
commute_dmetro=gpd.sjoin(commute_d,metrobuffer,how="inner",op='within').dropna(subset=['Sta_Name']).drop_duplicates(['index'])
print('通勤起点在地铁站800m内，通勤终点在地铁站800m内')
print(commute_ometro.carweight.sum(),commute_dmetro.carweight.sum())
dftrip_commute['closemetro']='N'
dftrip_commute['closemetro']=dftrip_commute['index'].apply(lambda x: 'Y' if (x in list(commute_ometro['index'])) or (x in list(commute_dmetro['index'])) else 'N')

print('通勤起点或终点在地铁站800m内',dftrip_commute.loc[dftrip_commute['closemetro']=='Y','carweight'].sum())
print('通勤起点或终点在地铁站800m内的地铁出行',dftrip_commute.loc[(dftrip_commute['closemetro']=='Y')&(dftrip_commute['metrotrip']==1),'carweight'].sum())
print('通勤起点或终点在地铁站800m内的地铁出行占通勤总量的比例',dftrip_commute.loc[(dftrip_commute['closemetro']=='Y')&(dftrip_commute['metrotrip']==1),'carweight'].sum()/dftrip_commute['carweight'].sum())

distancesum=dftrip_commute.groupby('distance2')['carweight'].sum().reset_index()
distancesum['pct_total']=round(100*distancesum['carweight']/distancesum['carweight'].sum(),1)
distancesum['carweight']=round(distancesum['carweight'],0)

distancesum_work=dftrip_commute[dftrip_commute['出行目的']=='上班'].groupby('distance2')['carweight'].sum().reset_index()
distancesum_work['pct_work']=round(100*distancesum_work['carweight']/distancesum_work['carweight'].sum(),1)
distancesum_work['carweight']=round(distancesum_work['carweight'],0)

distancesum_study=dftrip_commute[dftrip_commute['出行目的']=='上学'].groupby('distance2')['carweight'].sum().reset_index()
distancesum_study['pct_study']=round(100*distancesum_study['carweight']/distancesum_study['carweight'].sum(),1)
distancesum_study['carweight']=round(distancesum_study['carweight'],0)

distancesum=distancesum.merge(distancesum_work,how='left',on='distance2').merge(distancesum_study,how='left',on='distance2')
distancesum=distancesum.rename(columns={'carweight_x':'通勤量','carweight_y':'上班出行量','carweight':'上学出行量'})
print(distancesum)

durationsum=dftrip_commute.groupby('duration2')['carweight'].sum().reset_index()
durationsum['pct_total']=round(100*durationsum['carweight']/durationsum['carweight'].sum(),1)
durationsum['carweight']=round(durationsum['carweight'],0)

durationsum_work=dftrip_commute[dftrip_commute['出行目的']=='上班'].groupby('duration2')['carweight'].sum().reset_index()
durationsum_work['pct_work']=round(100*durationsum_work['carweight']/durationsum_work['carweight'].sum(),1)
durationsum_work['carweight']=round(durationsum_work['carweight'],0)

durationsum_study=dftrip_commute[dftrip_commute['出行目的']=='上学'].groupby('duration2')['carweight'].sum().reset_index()
durationsum_study['pct_study']=round(100*durationsum_study['carweight']/durationsum_study['carweight'].sum(),1)
durationsum_study['carweight']=round(durationsum_study['carweight'],0)

durationsum=durationsum.merge(durationsum_work,how='left',on='duration2').merge(durationsum_study,how='left',on='duration2')
durationsum=durationsum.rename(columns={'carweight_x':'通勤量','carweight_y':'上班出行量','carweight':'上学出行量'})
print(durationsum)


for purp in set(dftripw['分类']):
    print(purp)
    print('平均距离', weightmean(dftripw[dftripw['分类']==purp], 'distance', 'carweight'))
    print('平均时耗', weightmean(dftripw[dftripw['分类']==purp], 'duration', 'carweight'))

metrotripdf=dftripw[dftripw['metrotrip']==1].groupby(['modelist'])['carweight'].sum().reset_index()
def tometrofun(x):
    x=x.strip("[]").replace("'","").replace(", ",",").split(',')
    if x[0]=='公交车':
        return '公交车'
    elif x[0]=='出租车':
        return '出租车'
    elif x[0] in ['私家车(搭乘)','私家车(驾驶)','租赁汽车','黑车','网约车','单位小汽车']:
        return '小汽车'
    elif x[0]=='地铁':
        return '步行'
    else:
        return '其他'

def frommetrofun(x):
    x=x.strip("[]").replace("'","").replace(", ",",").split(',')
    if x[-1]=='公交车':
        return '公交车'
    elif x[-1]=='出租车':
        return '出租车'
    elif x[-1] in ['私家车(搭乘)','私家车(驾驶)','租赁汽车','黑车','网约车','单位小汽车']:
        return '小汽车'
    elif x[-1]=='地铁':
        return '步行'
    else:
        return '其他'

metrotripdf['tometro']=metrotripdf['modelist'].apply(lambda x: tometrofun(x))
metrotripdf['frommetro']=metrotripdf['modelist'].apply(lambda x: frommetrofun(x))
metroshuttle=pd.DataFrame({'交通方式':['公交车','步行','出租车','小汽车','其他'],
                           '出发地到地铁站使用该方式的比例(%)':0,
                           '地铁站到目的地使用该方式的比例(%)':0})
for row in metroshuttle.index:
    mode=metroshuttle.loc[row,'交通方式']
    metroshuttle.loc[row,'出发地到地铁站使用该方式的比例(%)']=metrotripdf.loc[metrotripdf['tometro']==mode,'carweight'].sum()
    metroshuttle.loc[row, '地铁站到目的地使用该方式的比例(%)'] = metrotripdf.loc[metrotripdf['frommetro'] == mode, 'carweight'].sum()
metroshuttle['出发地到地铁站使用该方式的比例(%)']=round(100*metroshuttle['出发地到地铁站使用该方式的比例(%)']/metroshuttle['出发地到地铁站使用该方式的比例(%)'].sum(),1)
metroshuttle['地铁站到目的地使用该方式的比例(%)']=round(100*metroshuttle['地铁站到目的地使用该方式的比例(%)']/metroshuttle['地铁站到目的地使用该方式的比例(%)'].sum(),1)

print(metroshuttle)