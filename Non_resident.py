import pandas as pd
import numpy as np
from geopy.distance import geodesic
import matplotlib as mpl
import matplotlib.pyplot as plt
from datetime import datetime
import geopandas as gpd
from shapely import geometry

rawdatafile=r'C:\调查结果数据\居民出行调查\乌鲁木齐市居民出行调查数据-0630.xlsx'
non_resid=pd.read_excel(rawdatafile,sheet_name='成员信息')
non_resid['年龄1']=non_resid['年龄'].apply(lambda x: '6-14岁' if x<=14 else ( '60岁及以上'if x>=60 else '15-59岁'))
non_resid['就业就学状态']=non_resid['就业就学状态'].replace(['无业','离退休再就业'],['待业','离退休'])
non_resid=non_resid[(non_resid['户口登记情况']=='非乌鲁木齐户籍')&(non_resid['非乌鲁木齐户籍（20年初起算）']=='居住乌鲁木齐半年以下')]
non_residtrip=pd.read_excel(rawdatafile,sheet_name='出行信息')
non_residtrip=non_residtrip.merge(non_resid[['成员编号','性别','年龄1','就业就学状态']],how='inner',on='成员编号')

non_resid=non_resid.merge(non_residtrip.groupby('成员编号')['出行序号'].count().reset_index(),how='left',on='成员编号').fillna(0)
non_resid=non_resid.rename(columns={'出行序号':'出行次数'})

mode_sum=non_residtrip.groupby('使用的主要交通方式')['出行序号'].count().reset_index()
mode_sum['pct']=round(mode_sum['出行序号']/mode_sum['出行序号'].sum(),4)
print(mode_sum)

for col in ['区域名称','性别','年龄1','就业就学状态','出行次数']:
    sumdf=non_resid.groupby(col)['成员编号'].count().reset_index().rename(columns={'成员编号':'人数'})
    sumdf['pct']=sumdf['人数']/sumdf['人数'].sum()
    print(sumdf)
#流动人口规模按照街道常住人口比例

##流动人口总278690人，6月宾馆酒店1542106人，酒店宾馆停留天数3.5天
non_resid_str=non_resid.groupby('街道名称')['成员编号'].count().reset_index()
restrictionfile=r'C:\调查结果数据\居民出行调查\Restrictions0922.xlsx'
StreetN=pd.read_excel(restrictionfile, sheet_name='StreetNo')
totalnon_resi=279690-1542106*3.5/30
totalnon_resi=totalnon_resi*(StreetN['CensusPop'].sum()/(4054369-243900))


StreetN2=StreetN.merge(non_resid_str,how='left',on='街道名称')
nalist=[36,82,89,104,116]
mergelist=[37,83,20,103,74]
for i in range(5):
    val1=StreetN.loc[StreetN['扩样街道编号']==mergelist[i],'CensusPop'].iloc[0]
    val2=StreetN.loc[StreetN['扩样街道编号']==nalist[i],'CensusPop'].iloc[0]
    print(mergelist[i],val1,val1+val2)
    StreetN2.loc[StreetN2['扩样街道编号']==mergelist[i],'CensusPop']=val1+val2

StreetN2=StreetN2.dropna()
StreetN2['pct']=StreetN2['CensusPop']/StreetN2['CensusPop'].sum()
StreetN2['Non_resi']=StreetN2['pct']*totalnon_resi
StreetN2['weight']=StreetN2['Non_resi']/StreetN2['成员编号']

non_resid=non_resid.merge(StreetN2[['街道名称','weight']],how='left',on='街道名称')
non_residtrip=non_residtrip.merge(StreetN2[['街道名称','weight']],how='left',on='街道名称')


columnlist=['第一种交通方式', '第二种交通方式', '第三种交通方式', '第四种交通方式', '第五种交通方式']
non_residtrip = non_residtrip.replace('私人小汽车(自驾)','私家车(驾驶)')
non_residtrip = non_residtrip.replace('私人小汽车(搭乘)','私家车(搭乘)')
non_residtrip=non_residtrip.rename(columns={'出发时间（24小时制）':'出发时间','到达时间（24小时制）':'到达时间'})
def bustrip(df):
    if ((df['第一种交通方式'] in ['BRT','公交车','地铁']) or (df['第二种交通方式'] in ['BRT','公交车','地铁']) or (df['第三种交通方式'] in ['BRT','公交车','地铁'])
            or (df['第四种交通方式'] in ['BRT','公交车','地铁']) or (df['第五种交通方式'] in ['BRT','公交车','地铁'])):
        return 1
    else:
        return 0

def taxitrip(df):
    if ((df['第一种交通方式'] == '出租车') or (df['第二种交通方式']  == '出租车') or (df['第三种交通方式'] == '出租车')
           or (df['第四种交通方式']  == '出租车') or (df['第五种交通方式'] == '出租车')):
        return 1
    else:
        return 0

def pctrip(df):
    pclist=['私家车(驾驶)', '私家车(搭乘)', '单位小汽车',  '租赁汽车','网约车', '黑车']
    if ((df['第一种交通方式'] in pclist) or (df['第二种交通方式'] in pclist) or (df['第三种交通方式'] in pclist)
            or (df['第四种交通方式'] in pclist) or (df['第五种交通方式'] in pclist)):
        return 1
    else:
        return 0

non_residtrip['bus']=non_residtrip[columnlist].apply(lambda x: bustrip(x), axis=1)
non_residtrip['taxi']=non_residtrip[columnlist].apply(lambda x: taxitrip(x), axis=1)
non_residtrip['pc']=non_residtrip[columnlist].apply(lambda x: pctrip(x), axis=1)
def mode(x):
    if x in ['BRT','公交车']:
        return '公交车'
    elif x in ['私家车(驾驶)', '私家车(搭乘)','租赁汽车','单位小汽车','网约车','黑车']:
        return '小汽车'
    elif x in ['货车','摩托车','其他']:
        return '其他'
    else:
        return x
non_residtrip['主要交通方式2']=non_residtrip['使用的主要交通方式'].apply(lambda x:mode(x))

print('public transit',non_residtrip.loc[non_residtrip['bus']==1,'weight'].sum())
print('taxi',non_residtrip.loc[non_residtrip['taxi']==1,'weight'].sum())

mode_sum=non_residtrip.groupby('使用的主要交通方式')['weight'].sum().reset_index()
mode_sum['pct']=round(mode_sum['weight']/mode_sum['weight'].sum(),4)
mode_sum=mode_sum.rename(columns={'weight':'出行次数'})

print(mode_sum)
dflist=[mode_sum]
dfnamelist=['交通方式']
for col in ['区域名称','性别','年龄1','就业就学状态','出行次数']:
    sumdf=non_resid.groupby(col)['weight'].sum().reset_index().rename(columns={'weight':'人数'})
    sumdf['pct']=sumdf['人数']/sumdf['人数'].sum()
    print(sumdf)
    dflist.append(sumdf)
    dfnamelist.append(col)


writer=pd.ExcelWriter(r'C:\调查结果数据\居民出行调查\非酒店流动人口summary.xlsx')
### 1.家庭情况
if len(dflist)>0:
    startr = 1
    rowlist = [0]
    for i in range(len(dflist)):
        dflist[i].to_excel(writer, sheet_name='非酒店流动人口', startrow=startr, startcol=0, index=False)
        r, c = dflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['非酒店流动人口']
    for i in range(len(dfnamelist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, dfnamelist[i])
writer.save()


print((non_residtrip['此次出行换乘次数']*non_residtrip['weight']).sum()/non_residtrip['weight'].sum())
triptaz=pd.read_excel(r'C:\调查结果数据\居民出行调查\出行信息.xlsx')
non_residtrip=non_residtrip.merge(triptaz[['出行编号','TAZ_O','TAZ_D']],how='left',on='出行编号')
print(non_residtrip.loc[0,'出发时间'])

if 'hour' not in non_residtrip.columns:
    non_residtrip['hour'] = non_residtrip['出发时间'].apply(lambda x: x.hour)


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
if 'period' not in non_residtrip.columns:
    non_residtrip['period'] = non_residtrip['hour'].apply(lambda x: periodfun(x))
    
non_residtrip['TAZ_O']=non_residtrip['TAZ_O'].fillna(0)
non_residtrip['TAZ_D']=non_residtrip['TAZ_D'].fillna(0)
car_taz_matrix=non_residtrip[non_residtrip['pc']==1].dropna(subset=['TAZ_O','TAZ_D']).groupby(['TAZ_O','TAZ_D'])['weight'].sum().reset_index()
car_taz_matrix=car_taz_matrix.sort_values(by=['TAZ_O','TAZ_D'])
car_AM_matrix=non_residtrip[(non_residtrip['pc']==1)&(non_residtrip['period']=='AM_Peak')].dropna(subset=['TAZ_O','TAZ_D']).groupby(['TAZ_O','TAZ_D'])['weight'].sum().reset_index()
car_AM_matrix=car_AM_matrix.sort_values(by=['TAZ_O','TAZ_D'])
car_PM_matrix=non_residtrip[(non_residtrip['pc']==1)&(non_residtrip['period']=='PM_Peak')].dropna(subset=['TAZ_O','TAZ_D']).groupby(['TAZ_O','TAZ_D'])['weight'].sum().reset_index()
car_PM_matrix=car_PM_matrix.sort_values(by=['TAZ_O','TAZ_D'])
writer=pd.ExcelWriter(r'C:\调查结果数据\居民出行调查\car_taz_非酒店宾馆的流动人口.xlsx')
car_taz_matrix.to_excel(writer,sheet_name='entireday', startrow=0, startcol=0, index=False)
car_AM_matrix.to_excel(writer,sheet_name='AM_Peak', startrow=0, startcol=0, index=False)
car_PM_matrix.to_excel(writer,sheet_name='PM_Peak', startrow=0, startcol=0, index=False)
writer.save()


#酒店流动人口taz
visitortrip=pd.read_excel(r'C:\调查结果数据\流动人口出行信息.xlsx')
if 'period' not in visitortrip.columns:
    visitortrip['period'] = visitortrip['hour'].apply(lambda x: periodfun(x))
for col in ['15(私人小汽车（自驾）)','15(私人小汽车（搭乘）)','15(租赁汽车)','15(黑车)','15(单位小汽车)']:
    visitortrip[col] = visitortrip[col].fillna(0)
visitortrip['pc']=visitortrip['15(私人小汽车（自驾）)']+visitortrip['15(私人小汽车（搭乘）)']+visitortrip['15(租赁汽车)']+visitortrip['15(黑车)']+visitortrip['15(单位小汽车)']
visitortrip['pc']=visitortrip['pc'].apply(lambda x:1 if x>0 else 0)
visitortrip['weight']=80.3898
car_taz_matrix1=visitortrip[visitortrip['pc']==1].dropna(subset=['TAZ_O','TAZ_D']).groupby(['TAZ_O','TAZ_D'])['weight'].sum().reset_index()
car_taz_matrix1=car_taz_matrix1.sort_values(by=['TAZ_O','TAZ_D'])
car_AM_matrix1=visitortrip[(visitortrip['pc']==1)&(visitortrip['period']=='AM_Peak')].dropna(subset=['TAZ_O','TAZ_D']).groupby(['TAZ_O','TAZ_D'])['weight'].sum().reset_index()
car_AM_matrix1=car_AM_matrix1.sort_values(by=['TAZ_O','TAZ_D'])
car_PM_matrix1=visitortrip[(visitortrip['pc']==1)&(visitortrip['period']=='PM_Peak')].dropna(subset=['TAZ_O','TAZ_D']).groupby(['TAZ_O','TAZ_D'])['weight'].sum().reset_index()
car_PM_matrix1=car_PM_matrix1.sort_values(by=['TAZ_O','TAZ_D'])


car_taz_matrix0=car_taz_matrix.merge(car_taz_matrix1,how='outer',on=['TAZ_O','TAZ_D'])
car_taz_matrix0=car_taz_matrix0.fillna(0)
car_taz_matrix0['trips']=car_taz_matrix0['weight_x']+car_taz_matrix0['weight_y']

car_AM_matrix0=car_AM_matrix.merge(car_AM_matrix1,how='outer',on=['TAZ_O','TAZ_D'])
car_AM_matrix0=car_AM_matrix0.fillna(0)
car_AM_matrix0['trips']=car_AM_matrix0['weight_x']+car_AM_matrix0['weight_y']

car_PM_matrix0=car_PM_matrix.merge(car_PM_matrix1,how='outer',on=['TAZ_O','TAZ_D'])
car_PM_matrix0=car_PM_matrix0.fillna(0)
car_PM_matrix0['trips']=car_PM_matrix0['weight_x']+car_PM_matrix0['weight_y']

writer=pd.ExcelWriter(r'C:\调查结果数据\car_taz_流动人口.xlsx')
car_taz_matrix0[['TAZ_O','TAZ_D','trips']].to_excel(writer,sheet_name='entireday', startrow=0, startcol=0, index=False)
car_AM_matrix0[['TAZ_O','TAZ_D','trips']].to_excel(writer,sheet_name='AM_Peak', startrow=0, startcol=0, index=False)
car_PM_matrix0[['TAZ_O','TAZ_D','trips']].to_excel(writer,sheet_name='PM_Peak', startrow=0, startcol=0, index=False)
writer.save()
