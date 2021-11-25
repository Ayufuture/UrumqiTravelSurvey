import numpy as np
import pandas as pd
from geopy.distance import geodesic
import datetime
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from shapely.geometry import Point,Polygon,shape
from shapely.ops import nearest_points

pd.options.mode.chained_assignment = None  # default='warn'

####load weighted data and do some calculation& transformations
rawdatafile=r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\乌鲁木齐市居民出行调查数据-0918.xlsx'
restrictionfile=r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Restrictions1109.xlsx'
hhweightfile=r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Results\results0922\df_Kid_adj.xlsx'
triptazfile=r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\出行信息.xlsx'
dfppcarfile=r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Results\results1109\dfpp_car.xlsx'
dftripforsum=r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Results\results1109\dftrip_forsummary1115_核心区duptrips.xlsx'
summarypath=r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Results\results1109'

CentralArea=gpd.read_file(r'C:\Users\yi.gu\Documents\Hyder Related\Test GIS\实体地域\实体地域范围主体420.shp')
CentralArea=CentralArea.to_crs(4326)

dfhh0 = pd.read_excel(rawdatafile, sheet_name='家庭信息')
dfhh0=dfhh0.drop(columns={'HHweight4'})
dfhhweight=pd.read_excel(hhweightfile, sheet_name='df_Kid')
dfhhw=pd.merge(dfhh0,dfhhweight[['家庭编号', 'HHweight4']],how='inner',on='家庭编号').rename(columns={'私人小客车':'私家车'})
dfwill=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\乌鲁木齐市居民出行调查数据-0630.xlsx', sheet_name='意愿信息')
dfwill=pd.merge(dfwill,dfhhw[['家庭编号','HHweight4']],how='inner',on='家庭编号')
print(dfhhw.loc[dfhhw['家庭编号']==18711,'家庭年收入'])
dfpp0 = pd.read_excel(rawdatafile, sheet_name='成员信息')


dfpp0=dfpp0[['ID', '家庭编号', '成员编号', '区域名称', '街道名称', '社区名称', '性别', '年龄', '户口登记情况',
       '乌鲁木齐户籍', '非乌鲁木齐户籍（20年初起算）', '就业就学状态', '工作状态', '工作/学校地址X', '工作/学校地址Y',
       '详细地址', '职业', '移动', '联通', '电信', '公交卡类型', '居住地-收发快递次数', '工作地-收发快递次数',
       '居住地-订外卖次数', '工作地-订外卖次数', '指定调查日是否有出行', '调查日无出行原因','年龄1','pickkid']]

dfpp0=pd.merge(dfpp0,dfhhw[['家庭编号','私家车','其中：新A', '其中：新能源']],how='left',on='家庭编号')
dfpp0['有无私家车']='无'
dfpp0.loc[dfpp0['私家车']>0,'有无私家车']='有'
if 'carweight' in dfpp0.columns:
    dfpp0 = dfpp0.drop(columns={'carweight'})
dfppweight=pd.read_excel(dfppcarfile)
dfppw=pd.merge(dfpp0,dfppweight[['成员编号','carweight']],how='inner',on='成员编号')
#dfppw=pd.merge(dfpp0,dfppweight[['成员编号','txweight']],how='inner',on='成员编号').rename(columns={'txweight':'carweight'})
dfppw['就业就学状态']=dfppw['就业就学状态'].replace(['无业','离退休再就业'],['待业','离退休'])
dfppw['年龄1']=dfppw['年龄1'].replace(['above 60', '15-59', '6-14'],['60岁及以上', '15-59岁', '6-14岁'])



dftrip0=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Results\Results1109\dftrip_forsummary1109.xlsx')
dftrip0=dftrip0.drop_duplicates(subset=['家庭编号', '成员编号', '出行编号', '出行序号', '区域名称', '街道名称', '社区名称', '出发时间', '出发X',
       '出发Y', '出发详细地址', '到达时间', '到达X', '到达Y', '到达详细地址', '出行目的','使用的主要交通方式'])
print(dftrip0.shape)

"""
dftrip0=pd.read_excel(rawdatafile, sheet_name='出行信息')
print(dftrip0.shape)
"""
dftrip0['distance0']=dftrip0.apply(lambda x: x['直线距离'] if x['TAZ_O']==x['TAZ_D'] else x['distance'], axis=1)
dftrip0 = dftrip0.replace('私人小汽车(自驾)','私家车(驾驶)')
dftrip0 = dftrip0.replace('私人小汽车(搭乘)','私家车(搭乘)')
dftrip0 = dftrip0.replace('头屯河区','经开区')
dftrip0 = dftrip0.replace('新市区','高新区')
print(dftrip0.shape)
###add repetitive trips
if ('period' in dftrip0.columns)&('pc' in dftrip0.columns):
    dftrip0_day=dftrip0[(dftrip0['period']=='Day_time')&(dftrip0['hour']>10)&(dftrip0['taxi']!=1)&(dftrip0['bus']!=1)].reset_index().drop(columns=['index'])
    day_array=np.arange(0,len(dftrip0_day),6)
    dftripadd_day=dftrip0_day[dftrip0_day.index.isin(day_array)]


    dftrip0_night = dftrip0[(dftrip0['period'] == 'Night_time')&(dftrip0['hour']!=8)&(dftrip0['taxi']!=1)&(dftrip0['bus']!=1)].reset_index().drop(columns=['index'])
    night_array = np.arange(0, len(dftrip0_night), 2)
    dftripadd_night = dftrip0_night[dftrip0_night.index.isin(night_array)]

    appendtripsr=pd.concat([dftripadd_day,dftripadd_night],ignore_index=True)
    appendtripsr.to_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Results\results1109\appendduptrips.xlsx')
    dftrip0=pd.concat([dftrip0,appendtripsr],ignore_index=True)


dftrip0 = dftrip0.replace('普通自行车', '个人自行车')
print(dftrip0.shape)


# remove trips outside of urumqi( origin and destination not in urumqi)
dftrip0['District_O']=dftrip0['District_O'].replace(['达坂城区','乌鲁木齐县'],[ 'Outside','Outside'])
dftrip0['District_D']=dftrip0['District_D'].replace(['达坂城区','乌鲁木齐县'],[ 'Outside','Outside'])
dftrip1=dftrip0[(dftrip0['District_O']!='Outside')|(dftrip0['District_D']!='Outside')]
dftrip1=dftrip1.reset_index()

origin= gpd.GeoDataFrame(dftrip1, geometry=gpd.points_from_xy(dftrip1['出发X'], dftrip1['出发Y'], crs="EPSG:4326"))
origin_central = gpd.sjoin(origin,CentralArea,how="left",op='within')
origin_central['Id']=origin_central['Id'].fillna('Outside')
origin_outside=origin_central[origin_central['Id']=='Outside'].dropna(subset=['出行编号'])
destination= gpd.GeoDataFrame(dftrip1, geometry=gpd.points_from_xy(dftrip1['到达X'], dftrip1['到达Y'], crs="EPSG:4326"))
destination_central = gpd.sjoin(destination,CentralArea,how="left",op='within')
destination_central['Id']=destination_central['Id'].fillna('Outside')
destination_outside=destination_central[destination_central['Id']=='Outside'].dropna(subset=['出行编号'])
dftrip1=dftrip1[(~dftrip1['index'].isin(origin_outside['index']) )&(~dftrip1['index'].isin(destination_outside['index']))]
print('一端在六区内',dftrip1.shape,dftrip1['carweight'].sum())
print('两端在六区内',dftrip0[(dftrip0['District_O']!='Outside')&(dftrip0['District_D']!='Outside')].shape,dftrip0.loc[(dftrip0['District_O']!='Outside')&(dftrip0['District_D']!='Outside'),'carweight'].sum())

def housesize(x):
    if x>0 and x<=50:
        return '1. 0-50平方米'
    elif x>50 and x<=100:
        return '2. 50-100平方米'
    elif x>100 and x<=150:
        return '3. 100-150平方米'
    elif x>150 and x<=200:
        return '4. 150-200平方米'
    elif x>200 :
        return '5. 200平方米以上'
dfhhw['建筑面积2']=dfhhw['房屋建筑面积'].apply(lambda x:housesize(x))

dfhhw['户规模']=dfhhw['家庭总人数'].apply(lambda x: str(x)+'人' if x<5 else '5人及以上')
dftrip1.to_excel(dftripforsum,index=False)

hhdflist=[]
hhdflistname=['分区户规模','房屋类型','住房性质','住房面积',	'户收入情况','交通工具拥有情况','户收入-私家车','本地车及新能源比例','家庭端车辆停放方式','私家车停车比例','私家车停车费用']
colnames=[['区域名称','户规模'],'房屋类型','住房性质','建筑面积2','家庭年收入']
incomelist=['2万以下', '2-3万','3-5万', '5-10万', '10-20万', '20万以上']
for col in colnames:
    sum_df=dfhhw.groupby(col)['HHweight4'].sum().reset_index()
    sum_df['pct']=round(100*sum_df['HHweight4']/sum_df['HHweight4'].sum(),1)
    if col=='家庭年收入':
        df_sort = pd.DataFrame({'家庭年收入': incomelist})
        sort_mapping = df_sort.reset_index().set_index('家庭年收入')
        sum_df['num'] = sum_df['家庭年收入'].map(sort_mapping['index'])
        sum_df= sum_df.sort_values('num').drop(columns=['num'])
    if col=='建筑面积2':
        ave_area=(dfhhw['房屋建筑面积']*dfhhw['HHweight4']).sum()/dfhhw['HHweight4'].sum()
        sum_df=sum_df.append([{'建筑面积2':'平均','pct':round(ave_area,1)}])
    if col==['区域名称','户规模']:
        sum_df=dfhhw.groupby(col)['HHweight4'].sum().reset_index()
        sum_df=sum_df.pivot(index='区域名称',columns='户规模',values='HHweight4').reset_index()
        sum_df['总户数']=sum_df[['1人', '2人', '3人', '4人', '5人及以上']].sum(axis=1)
        sum_df.loc[len(sum_df),:]=sum_df.sum(axis=0)
        sum_df.loc[len(sum_df)-1, '区域名称'] = '合计'
        for column in ['1人', '2人', '3人', '4人', '5人及以上']:
            sum_df[column]=round(100*sum_df[column]/sum_df['总户数'],1)
        df_sort = pd.DataFrame({'区域名称': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区']})
        sort_mapping = df_sort.reset_index().set_index('区域名称')
        sum_df['num'] = sum_df['区域名称'].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])

    hhdflist.append(sum_df)

#'交通工具拥有情况'
ownership=pd.DataFrame({'交通工具':['普通自行车','电动自行车','摩托车','单位配车','私家车'],'Total':0,'HHcount':0,'pct':0})

for index in ownership.index:
    col=ownership.loc[index,'交通工具']
    ownership.loc[index, 'Total'] = (dfhhw[col]*dfhhw['HHweight4']).sum()
    ownership.loc[index, 'HHcount'] = dfhhw.loc[dfhhw[col]>0,'HHweight4'].sum()
    ownership.loc[index, 'pct'] = round(100*ownership.loc[index, 'HHcount'] /dfhhw['HHweight4'].sum(),1)

ownership['平均(辆/户）']=round(ownership['Total']/ownership['HHcount'],3)
ownership['Total']=round(ownership['Total'],2)
ownership['HHcount']=round(ownership['HHcount'],2)
hhdflist.append(ownership)

#户收入和私家车的关系
dfhhw['有车']=dfhhw['私家车'].apply(lambda x: '有' if x>0 else '无')
income_veh=dfhhw.groupby(['家庭年收入','有车'])['HHweight4'].sum().reset_index()
income_veh=income_veh.pivot(index='家庭年收入',columns='有车',values='HHweight4').reset_index()
income_veh['有车比例']=round(100*(income_veh['有']/(income_veh['有']+income_veh['无'])),1)
df_sort = pd.DataFrame({'家庭年收入': incomelist})
sort_mapping = df_sort.reset_index().set_index('家庭年收入')
income_veh['num'] = income_veh['家庭年收入'].map(sort_mapping['index'])
income_veh= income_veh.sort_values('num').drop(columns=['num'])
hhdflist.append(income_veh)

#本地车，新能源比例
pcdf=pd.DataFrame(columns=['交通工具','Total','pct'])
columnlist=['私家车', '其中：新A', '其中：新能源']
for col in columnlist:
    index=len(pcdf)
    pcdf.loc[index,'交通工具']=col
    pcdf.loc[index, 'Total'] = (dfhhw[col]*dfhhw['HHweight4']).sum()

totalpc=pcdf.loc[0,'Total']
pcdf['pct']=pcdf['Total'].apply(lambda x: round(100*x/totalpc,1))
pcdf['Total']=pcdf['Total'].apply(lambda x: int(x))
hhdflist.append(pcdf)

#'家庭端车辆停放方式'
sum_df=dfhhw[dfhhw['私家车']>0].groupby(['家庭端小汽车停车场类别'])['HHweight4'].sum().reset_index()
sum_df['pct']=round(100*sum_df['HHweight4']/sum_df['HHweight4'].sum(),1)
sum_df1=dfhhw[dfhhw['私家车']>0].groupby(['家庭端小汽车停车场类别','区域名称'])['HHweight4'].sum().reset_index()
sum_df1=sum_df1.pivot(index='家庭端小汽车停车场类别',columns='区域名称',values='HHweight4').reset_index()
districtlist=['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区']
sum_df1=pd.merge(sum_df1,sum_df,how='left',on='家庭端小汽车停车场类别')
for col in ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区']:
    sum_df1[col]=round(100*sum_df1[col]/sum_df1[col].sum(),1)
sum_df1=sum_df1[['家庭端小汽车停车场类别','天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区','pct']]
hhdflist.append(sum_df1)

###家庭端小汽车停车费用
parkingdf=dfhhw.groupby('家庭端小汽车停车费用')['HHweight4'].sum().reset_index()
parkingdf['pct']=round(100*parkingdf['HHweight4']/parkingdf['HHweight4'].sum(),1)
parkingdf['averagefee']=0
def weightmean(df,col,weight):
    wm=round((df[col]*df[weight]).sum()/df[weight].sum(),2)
    return wm
parkingdf.loc[4,'averagefee']=weightmean(dfhhw[dfhhw['家庭端小汽车停车费用']=='自有停车位'],'自有停车位（管理费）:','HHweight4')
parkingdf.loc[3,'averagefee']=weightmean(dfhhw[dfhhw['家庭端小汽车停车费用']=='月租停车/停车位'],'月租停车/停车位:','HHweight4')
parkingdf.loc[0,'averagefee']=weightmean(dfhhw[dfhhw['家庭端小汽车停车费用']=='临时停车/停车位'],'临时停车/停车位:','HHweight4')
parkingdf.loc[2,'averagefee']=weightmean(dfhhw[dfhhw['家庭端小汽车停车费用']=='其他'],'其他:','HHweight4')

for  col in set(dfhhw['区域名称']):
    parkingdf[col]=0
    parkingdf.loc[4, col] = weightmean(dfhhw[(dfhhw['区域名称'] == col) &(dfhhw['家庭端小汽车停车费用']=='自有停车位')], '自有停车位（管理费）:', 'HHweight4')
    parkingdf.loc[3, col] = weightmean(dfhhw[(dfhhw['区域名称'] == col)&(dfhhw['家庭端小汽车停车费用']=='月租停车/停车位')], '月租停车/停车位:', 'HHweight4')
    parkingdf.loc[0, col] = weightmean(dfhhw[(dfhhw['区域名称'] == col)&(dfhhw['家庭端小汽车停车费用']=='临时停车/停车位')], '临时停车/停车位:', 'HHweight4')
    parkingdf.loc[2, col] = weightmean(dfhhw[(dfhhw['区域名称'] == col)&(dfhhw['家庭端小汽车停车费用']=='其他')], '其他:', 'HHweight4')
    parkingdf[col+'pct'] = 0
    parkingdf.loc[4, col+'pct'] = dfhhw.loc[(dfhhw['区域名称'] == col) & (dfhhw['家庭端小汽车停车费用'] == '自有停车位'),
                                       'HHweight4'].sum()
    parkingdf.loc[3, col+'pct'] = dfhhw.loc[(dfhhw['区域名称'] == col) & (dfhhw['家庭端小汽车停车费用'] == '月租停车/停车位'),
                                       'HHweight4'].sum()
    parkingdf.loc[0, col+'pct'] = dfhhw.loc[(dfhhw['区域名称'] == col) & (dfhhw['家庭端小汽车停车费用'] == '临时停车/停车位'),
                                       'HHweight4'].sum()
    parkingdf.loc[2, col+'pct'] = dfhhw.loc[(dfhhw['区域名称'] == col) & (dfhhw['家庭端小汽车停车费用'] == '其他'),
                                       'HHweight4'].sum()
    parkingdf.loc[1, col + 'pct'] = dfhhw.loc[(dfhhw['区域名称'] == col) & (dfhhw['家庭端小汽车停车费用'] == '免费'),
                                              'HHweight4'].sum()
    parkingdf[col+'pct']=round(100*parkingdf[col+'pct']/parkingdf[col+'pct'].sum(),1)

parkingdf=parkingdf[['家庭端小汽车停车费用', 'averagefee','天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区',
'HHweight4', 'pct','天山区pct', '沙依巴克区pct', '高新区pct', '水磨沟区pct', '经开区pct','米东区pct' ]].rename(columns={'HHweight4':'总户数','averagefee':'平均费用'})
dfhhw['park']=dfhhw[['自有停车位（管理费）:', '月租停车/停车位:', '临时停车/停车位:', '其他:']].sum(axis=1)
parkingdf.loc[len(parkingdf),:]=parkingdf.sum(axis=0)
parkingdf.loc[len(parkingdf)-1,'家庭端小汽车停车费用']='总和'

hhdflist.append(parkingdf.loc[[4,3,0,2,1,5],['家庭端小汽车停车费用','pct', '天山区pct', '沙依巴克区pct', '高新区pct', '水磨沟区pct', '经开区pct','米东区pct']])
hhdflist.append(parkingdf.loc[[4,3,0,2,1],['家庭端小汽车停车费用', '平均费用','天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区']])






willdflist=[]
willdflistname=['最近公交站','购车需求','购车原因','出行时间上限','理想出行时间','公交改善建议']
colnames=['住处距离最近的公交站的步行时间？', '您的购车意愿如何？', '什么是促成您的家庭购买小汽车的最主要因素？',
       '您认为就您目前的出行体验而言，单程出行您能忍受的出行时间上限是？','您认为就您目前的出行体验而言，单程出行最适合的出行时间范围是？',
          '您认为公交需要改善的地方是哪些？（选择无意见后无需再选）']
walklist=[ '3分钟以内', '3-5分钟', '5-10分钟','10-15分钟', '15-20分钟' ,'大于20分钟']
tolelist=[ '0-15分钟', '16-30分钟', '31-45分钟', '46-60分钟', '61-75分钟','76-90分钟','91-105分钟', '106-120分钟', '120分钟以上']
for col in colnames:
    sum_df=dfwill.groupby([col])['HHweight4'].sum().reset_index()
    sum_df['pct']=round(100*sum_df['HHweight4']/sum_df['HHweight4'].sum(),1)
    if col=='住处距离最近的公交站的步行时间？':
        df_sort = pd.DataFrame({col: walklist})
        sort_mapping = df_sort.reset_index().set_index(col)
        sum_df['num'] = sum_df[col].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])
    elif (col=='您认为就您目前的出行体验而言，单程出行您能忍受的出行时间上限是？') or (col=='您认为就您目前的出行体验而言，单程出行最适合的出行时间范围是？'):
        df_sort = pd.DataFrame({col: tolelist})
        sort_mapping = df_sort.reset_index().set_index(col)
        sum_df['num'] = sum_df[col].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])
    elif col=='您认为公交需要改善的地方是哪些？（选择无意见后无需再选）':
        sum_df=pd.DataFrame({'改善建议':['无意见','离站太远','等候太长','不能直达','票价偏高','车速较慢','换乘不便','绕道行驶','车内不舒适','站点混乱（同时到站车辆较多，标示不清等）','线路/班次信息获取不便'],'HHweight4':0,'pct':0})
        total=dfwill['HHweight4'].sum()
        for i in sum_df.index:
            comment=sum_df.loc[i,'改善建议']
            dfwill['commentflag']=dfwill[col].apply(lambda x: 1 if comment in x else 0)
            sum_df.loc[i,'HHweight4']=dfwill.loc[dfwill['commentflag']==1,'HHweight4'].sum()
            sum_df.loc[i,'pct']=round(100*sum_df.loc[i,'HHweight4']/total,1)


    willdflist.append(sum_df)


#性别,年龄,'就业就学状态','职业构成','公交卡保有情况',快递，外卖,'居住地-收发快递次数','工作地-收发快递次数','居住地-订外卖次数','工作地-订外卖次数'
ppdflist=[]
dfppw=dfppw.merge(dfhhw[['家庭编号','家庭年收入']],how='left',on='家庭编号')
dfppw['公交卡类型']=dfppw['公交卡类型'].apply(lambda x: '月票' if '月票' in x else x)
ppdfnamelist=['性别','年龄','就业就学状态','就业就学状态-性别','区域家庭就业就学人口','就业就学状态-区域','就业就学状态-家庭年收入','职业构成','公交卡保有情况','快递&外卖overall','快递&外卖按性别年龄就业就学状态等','调查日无出行原因']
colname=['性别','年龄1','就业就学状态',['就业就学状态','性别'],['就业就学状态','区域名称'],['就业就学状态','家庭年收入'],'职业','公交卡类型']
agelist=['6-14岁','15-59岁', '60岁及以上']
for col in colname:
    sum_df=dfppw.groupby(col)['carweight'].sum().reset_index()
    sum_df['pct']=round(100*sum_df['carweight']/sum_df['carweight'].sum(),1)
    if col=='年龄1':
        df_sort = pd.DataFrame({col: agelist})
        sort_mapping = df_sort.reset_index().set_index(col)
        sum_df['num'] = sum_df[col].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])
    elif col==['就业就学状态','性别']:
        sum_df=sum_df.pivot(index=col[0],columns=col[1],values='carweight').reset_index()
        for c in sum_df.columns[1:]:
            sum_df[c]=round(100*sum_df[c]/sum_df[c].sum(),1)
    elif col==['就业就学状态','区域名称']:

        hhemp=sum_df.merge(dfhhw.groupby('区域名称')['HHweight4'].sum().reset_index(),how='left',on='区域名称')
        hhemp=hhemp.pivot(index=['区域名称','HHweight4'],columns='就业就学状态',values='carweight').reset_index()
        hhemp.loc[len(hhemp), :] = hhemp.sum(axis=0)
        hhemp.loc[len(hhemp) - 1, '区域名称'] = '合计'
        hhemp['户均就学人口']=round(hhemp['就学']/hhemp['HHweight4'],2)
        hhemp['户均工作人口']=round(hhemp['工作']/hhemp['HHweight4'],2)

        ppdflist.append(hhemp[['区域名称','HHweight4','就学','户均就学人口','工作','户均工作人口']].rename(columns={'HHweight4':'总户数'}))
        sum_df=sum_df.pivot(index=col[0],columns=col[1],values='carweight').reset_index()
        for c in sum_df.columns[1:]:
            sum_df[c]=round(100*sum_df[c]/sum_df[c].sum(),1)
        sum_df=sum_df[['就业就学状态','天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区']]

    elif col==['就业就学状态','家庭年收入']:
        sum_df = sum_df.pivot(index=col[0], columns=col[1], values='carweight').reset_index()
        for c in sum_df.columns[1:]:
            sum_df[c] = round(100 * sum_df[c] / sum_df[c].sum(), 1)
        sum_df = sum_df[['就业就学状态', '2万以下', '2-3万','3-5万', '5-10万', '10-20万', '20万以上']]

    ppdflist.append(sum_df)


packagedf=pd.DataFrame({'次数':['0次','1次','2次及以上','平均'],'居住地-收发快递次数':0,'工作地-收发快递次数':0,
                        '居住地-订外卖次数':0,'工作地-订外卖次数':0})
for col in ['居住地-收发快递次数','工作地-收发快递次数','居住地-订外卖次数','工作地-订外卖次数']:
    packagedf.loc[packagedf['次数']=='0次',col]=round(100*dfppw.loc[dfppw[col]==0,'carweight'].sum()/dfppw['carweight'].sum(),1)
    packagedf.loc[packagedf['次数'] == '1次', col] = round(
        100 * dfppw.loc[dfppw[col] == 1, 'carweight'].sum() / dfppw['carweight'].sum(), 1)
    packagedf.loc[packagedf['次数'] == '2次及以上', col] = round(
        100 * dfppw.loc[dfppw[col] >1 , 'carweight'].sum() / dfppw['carweight'].sum(), 1)
    packagedf.loc[packagedf['次数'] == '平均', col]=round(
        (dfppw[col]*dfppw['carweight']).sum()/dfppw['carweight'].sum(),2)

ppdflist.append(packagedf)


packagedf2=pd.DataFrame()
for name in ['居住地-收发快递次数','工作地-收发快递次数','居住地-订外卖次数','工作地-订外卖次数']:
    sum_df=pd.DataFrame({name:['0次', '1次', '2次及以上','平均']})
    for col in ['性别','年龄1','就业就学状态', '区域名称','有无私家车']:
        sum_dfi=dfppw.groupby([name,col])['carweight'].sum().reset_index().pivot(index=name,columns=col,values='carweight')
        sum_dfi=sum_dfi.fillna(0)
        sum_dfi2=sum_dfi.loc[0:3,:]
        sum_dfi2.loc[2,:]=np.array(sum_dfi.loc[2:,:].sum(axis=0))
        sum_dfi2.index.name = 'index'
        sum_dfi2[name] = ['0次', '1次', '2次及以上','平均']
        for value in set(dfppw[col]):
            sum_dfi2[value]=round(100*sum_dfi2[value]/sum_dfi2[value].sum(),1)
            average=(dfppw.loc[dfppw[col]==value,name]*dfppw.loc[dfppw[col]==value,'carweight']).sum()/dfppw.loc[dfppw[col]==value,'carweight'].sum()
            average=round(average,2)
            sum_dfi2.loc[3,value]=average
        print(sum_dfi2)
        sum_df = pd.merge(sum_df, sum_dfi2, how='left',on=name)
    sum_df['项目']=name
    sum_df=sum_df.rename(columns={name:'次数','无':'无私家车','有':'有私家车'})
    sum_df=sum_df[['项目','次数','男', '女','6-14岁','15-59岁',  '60岁及以上', '就学', '工作', '待业',
       '离退休', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区','无私家车','有私家车']]
    packagedf2=pd.concat([packagedf2,sum_df])

ppdflist.append(packagedf2)
#调查日无出行原因
sum_df=pd.DataFrame({'调查日无出行原因':['年龄大','身体不适','在家带孩子','休假在家','天气原因','在家办公','其他',
                                 '无出行人数','占无出行人员比例','全市总人数','无出行比例']})
for col in ['性别','年龄1','就业就学状态', '区域名称','有无私家车']:
    sum_dfi=dfppw.groupby([col,'调查日无出行原因'])['carweight'].sum().reset_index().pivot(index='调查日无出行原因',columns=col,values='carweight').reset_index()
    sum_dfi=sum_dfi.fillna(0)

    for value in set(dfppw[col]):
        sum_dfi[str(value)+'pct']=round(100*sum_dfi[value]/sum_dfi[value].sum(),1)
    nrow =sum_dfi.shape[0]
    sum_dfi.loc[nrow, :] = sum_dfi.sum(axis=0)
    sum_dfi.loc[nrow, '调查日无出行原因'] = '无出行人数'
    sum_dfi.loc[nrow+1, '调查日无出行原因'] = '占无出行人员比例'
    sum_dfi.loc[nrow+2,'调查日无出行原因']='全市总人数'
    sum_dfi.loc[nrow+3, '调查日无出行原因'] = '无出行比例'
    for value in set(dfppw[col]):
        sum_dfi.loc[nrow,str(value)+'pct']=sum_dfi.loc[nrow,value]
        sum_dfi.loc[nrow+1,str(value)+'pct']=round(100*sum_dfi.loc[nrow,value]/dfppw.loc[dfppw['指定调查日是否有出行']=='无出行','carweight'].sum(),1)
        sum_dfi.loc[nrow + 2, str(value) + 'pct']=dfppw.loc[dfppw[col]==value,'carweight'].sum()
        sum_dfi.loc[nrow + 3, str(value) + 'pct'] = round(
            100 * sum_dfi.loc[nrow, str(value) + 'pct'] / sum_dfi.loc[nrow+2, str(value) + 'pct'], 1)

    sum_df=pd.merge(sum_df,sum_dfi,how='left',on='调查日无出行原因')
sum_df0=dfppw.groupby(['调查日无出行原因'])['carweight'].sum().reset_index()
sum_df0['pct']=round(100*sum_df0['carweight']/sum_df0['carweight'].sum(),1)
sum_df=sum_df.merge(sum_df0[['调查日无出行原因','pct']],how='left',on='调查日无出行原因')
sum_df_notrip=sum_df[['调查日无出行原因','男pct', '女pct','6-14岁pct', '15-59岁pct','60岁及以上pct',
                          '就学pct',  '工作pct','待业pct', '离退休pct',
                          '天山区pct', '沙依巴克区pct','高新区pct','水磨沟区pct','经开区pct', '米东区pct',
                          '无pct', '有pct','pct']]

ppdflist.append(sum_df_notrip)
print(len(ppdflist),len(ppdfnamelist))
##找每个人的出行次数
pptrip=dftrip1.groupby('成员编号')['出行序号'].count().reset_index().rename(columns={'出行序号':'出行次数'})
dfppw=pd.merge(dfppw,pptrip,how='left',on='成员编号').fillna(0)

col0='出行次数'
tripdflist=[]
tripdfnamelist=['出行次数','出行次数-性别','出行次数-年龄1','出行次数-就业就学状态','出行次数-职业', '出行次数-区域名称','出行次数-有无私家车']
for col in ['出行次数','性别','年龄1','就业就学状态','职业', '区域名称','有无私家车']:
    if col==col0:
        sum_dfx=dfppw.groupby(col)['carweight'].sum().reset_index()
        sum_dfx['pct']=round(100*sum_dfx['carweight']/sum_dfx['carweight'].sum(),1)
        sum_dfx2 = sum_dfx.loc[0:7, :]
        sum_dfx2.loc[5, :] = np.array(sum_dfx.loc[5:, :].sum(axis=0))
        sum_dfx2.index.name = 'index'
        sum_dfx2[col0] = ['0次', '1次', '2次','3次','4次','5次及以上', '平均出行次数','有出行者平均出行次数']
        sum_dfx2.loc[6,'pct']=round((dfppw['carweight']*dfppw[col0]).sum()/dfppw['carweight'].sum(),1)
        sum_dfx2.loc[7, 'pct'] = round((dfppw.loc[dfppw[col0]>0,'carweight'] * dfppw.loc[dfppw[col0]>0,col0]).sum() / dfppw.loc[dfppw[col0]>0,'carweight'].sum(), 1)
        sum_dfx2.loc[6, 'carweight'] =''
        sum_dfx2.loc[7, 'carweight'] = ''
        tripdflist.append(sum_dfx2)
    else:
        dfppw['total']=dfppw[col0]*dfppw['carweight']
        sum_df=pd.DataFrame({col:list(set(dfppw[col])),'日出行总量（人次）':0,'出行率（次/人日）':0,'有出行者出行率（次/人日）':0,'有出行人口比例（%）':0})
        for value in set(dfppw[col]):
            sum_df.loc[sum_df[col] == value, '日出行总量（人次）'] = round(dfppw.loc[dfppw[col] == value, 'total'].sum(),2)
            sum_df.loc[sum_df[col]==value,'出行率（次/人日）']=round(dfppw.loc[dfppw[col]==value,'total'].sum()/dfppw.loc[dfppw[col]==value,'carweight'].sum(),2)
            sum_df.loc[sum_df[col] == value, '有出行者出行率（次/人日）'] = round(
                dfppw.loc[(dfppw[col] == value) & (dfppw[col0]>0), 'total'].sum() / dfppw.loc[
                    (dfppw[col] == value) & (dfppw[col0]>0), 'carweight'].sum(), 2)
            sum_df.loc[sum_df[col] == value, '有出行人口比例（%）'] = round(100*
                dfppw.loc[(dfppw[col] == value) & (dfppw[col0] > 0), 'carweight'].sum() / dfppw.loc[
                    (dfppw[col] == value) , 'carweight'].sum(), 2)
        if col =='职业':
            sum_df=sum_df[sum_df[col]!=0]

        if col == '年龄1':
            df_sort = pd.DataFrame({col: agelist})
            sort_mapping = df_sort.reset_index().set_index(col)
            sum_df['num'] = sum_df[col].map(sort_mapping['index'])
            sum_df = sum_df.sort_values('num').drop(columns=['num'])
        elif col=='区域名称':
            df_sort = pd.DataFrame({col: districtlist})
            sort_mapping = df_sort.reset_index().set_index(col)
            sum_df['num'] = sum_df[col].map(sort_mapping['index'])
            sum_df = sum_df.sort_values('num').drop(columns=['num'])
        tripdflist.append(sum_df)




col0='分类'
ctgrdflist=[]
ctgrdfnamelist=['出行目的','分类','分类-性别','分类-年龄1','分类-就业就学状态','分类-就业就学-出行率', '分类-区域名称','分类-区域-出行率','分类-区内区外','分类-分行政区-区内区外','分类-有无私家车','分类-年收入','分类-主要交通工具']

if ('性别' not in dftrip1.columns) or ('年龄1'not in dftrip1.columns) or ('有无私家车' not in dftrip1.columns):
    dftrip1 = pd.merge(dftrip1, dfppw[['成员编号', '性别', '年龄1', '有无私家车']], how='left', on='成员编号')
if ('家庭年收入' not in dftrip1.columns):
    dftrip1 = pd.merge(dftrip1, dfhhw[['家庭编号', '家庭年收入']], how='left', on='家庭编号')


for col in ['出行目的','分类','性别','年龄1','就业就学状态', '就业就学状态2','区域名称','区域名称2','区内区外','有无私家车','家庭年收入','主要交通方式2']:
    if col=='出行目的':
        sum_dfx = dftrip1.groupby(col)['carweight'].sum().reset_index()
        sum_dfx['pct'] = round(100 * sum_dfx['carweight'] / sum_dfx['carweight'].sum(), 1)
        no_hometrip=dftrip1.loc[dftrip1['出行目的']!='回家','carweight'].sum()
        sum_dfx['no_home_pct']=round(100 * sum_dfx['carweight'] / no_hometrip, 1)
        sum_dfx.loc[sum_dfx[col]=='回家','no_home_pct']=sum_dfx.loc[sum_dfx[col]=='回家','pct']
        ctgrdflist.append(sum_dfx[[col,'carweight','no_home_pct']].rename(columns={'carweight':'出行量'}).sort_values(by=['no_home_pct'],ascending=False))

    elif col==col0:
        sum_dfx0=dftrip1.groupby(col0)['carweight'].sum().reset_index()
        sum_dfx0['pct']=round(100*sum_dfx0['carweight']/sum_dfx0['carweight'].sum(),1)
        df_sort = pd.DataFrame({'分类': ['基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他']})
        sort_mapping = df_sort.reset_index().set_index('分类')
        sum_dfx0['num'] = sum_dfx0['分类'].map(sort_mapping['index'])
        sum_dfx0 = sum_dfx0.sort_values('num').drop(columns=['num'])
        ctgrdflist.append(sum_dfx0)

    elif col=='就业就学状态2':
        sum_dfx=dftrip1.groupby([col0,'就业就学状态'])['carweight'].sum().reset_index().pivot(index=col0,columns='就业就学状态',values='carweight').reset_index()
        for emp in ['工作', '就学', '待业', '离退休']:
            sum_dfx[emp]=round(sum_dfx[emp]/dfppw.loc[dfppw['就业就学状态']==emp,'carweight'].sum(),1)
        df_sort = pd.DataFrame({'分类': ['基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他']})
        sort_mapping = df_sort.reset_index().set_index('分类')
        sum_dfx['num'] = sum_dfx['分类'].map(sort_mapping['index'])
        sum_dfx = sum_dfx.sort_values('num').drop(columns=['num'])
        sum_dfx.loc[len(sum_dfx), :] = sum_dfx.sum(axis=0)
        sum_dfx.loc[len(sum_dfx) - 1, '分类'] = '总和'
        ctgrdflist.append(sum_dfx[['分类', '工作', '就学', '待业', '离退休']].fillna(0))



    elif col=='区域名称2':
        sum_dfx=dftrip1.groupby([col0,'区域名称'])['carweight'].sum().reset_index().pivot(index=col0,columns='区域名称',values='carweight').reset_index()
        for dist in ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区']:
            sum_dfx[dist]=round(sum_dfx[dist]/dfppw.loc[dfppw['区域名称']==dist,'carweight'].sum(),1)
        df_sort = pd.DataFrame({'分类': ['基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他']})
        sort_mapping = df_sort.reset_index().set_index('分类')
        sum_dfx['num'] = sum_dfx['分类'].map(sort_mapping['index'])
        sum_dfx = sum_dfx.sort_values('num').drop(columns=['num'])
        sum_dfx.loc[len(sum_dfx), :] = sum_dfx.sum(axis=0)
        sum_dfx.loc[len(sum_dfx) - 1, '分类'] = '总和'
        ctgrdflist.append(sum_dfx[['分类', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区']])

    elif col=='区内区外':
        sum_dfx1=dftrip1.dropna(subset=['区内区外']).groupby([col0,col])['carweight'].sum().reset_index().pivot(index=col0,columns=col,values='carweight').reset_index()
        sum_dfx1['总体']=sum_dfx1[['区内','区外']].sum(axis=1)
        for k in ['区内','区外','总体']:
            sum_dfx1[k]=round(100*sum_dfx1[k]/sum_dfx1[k].sum(),1)
        df_sort = pd.DataFrame({'分类': ['基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他']})
        sort_mapping = df_sort.reset_index().set_index('分类')
        sum_dfx1['num'] = sum_dfx1['分类'].map(sort_mapping['index'])
        sum_dfx1 = sum_dfx1.sort_values('num').drop(columns=['num'])
        ctgrdflist.append(sum_dfx1)
        sum_dfx=dftrip1.dropna(subset=['区内区外']).groupby([col0,'区域名称',col])['carweight'].sum().reset_index().pivot(index=['区域名称',col],columns=col0,values='carweight').reset_index()
        sum_dfx=sum_dfx[['区域名称',col,'基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他']]
        df_sort = pd.DataFrame({'区域名称': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区']})
        sort_mapping = df_sort.reset_index().set_index('区域名称')
        sum_dfx['num'] = sum_dfx['区域名称'].map(sort_mapping['index'])
        sum_dfx = sum_dfx.sort_values('num').drop(columns=['num'])
        for dist in ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区']:
            for c in ['基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他']:
                tripsumdc=sum_dfx.loc[sum_dfx['区域名称']==dist,c].sum()
                sum_dfx.loc[(sum_dfx['区域名称'] == dist)&(sum_dfx[col] == '区内'), c]=round(100*sum_dfx.loc[(sum_dfx['区域名称'] == dist)&(sum_dfx[col] == '区内'), c]/tripsumdc,1)
                sum_dfx.loc[(sum_dfx['区域名称'] == dist) & (sum_dfx[col] == '区外'), c] = round(
                    100 * sum_dfx.loc[(sum_dfx['区域名称'] == dist) & (sum_dfx[col] == '区外'), c] / tripsumdc, 1)
        ctgrdflist.append(sum_dfx)


    else:
        sum_df=dftrip1.dropna(subset=[col0,col]).groupby([col0,col])['carweight'].sum().reset_index().pivot(index=col0,columns=col,values='carweight').reset_index()
        for value in set(dftrip1.dropna(subset=[col0,col])[col]):
            sum_df[value]=round(100*sum_df[value]/sum_df[value].sum(),1)
        sum_df=pd.merge(sum_df,sum_dfx0[['分类','pct']],how='left',on='分类').rename(columns={'pct':'总体'})

        df_sort = pd.DataFrame({'分类': ['基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他']})
        sort_mapping = df_sort.reset_index().set_index('分类')
        sum_df['num'] = sum_df['分类'].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])
        sum_df.loc[len(sum_df),:]=100
        sum_df.loc[len(sum_df)-1,'分类']='总和'

        if col == '年龄1':
            sum_df=sum_df[['分类','6-14岁','15-59岁', '60岁及以上','总体']]
        elif col=='区域名称':
            sum_df = sum_df[['分类', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区','米东区', '总体']]
        elif col=='家庭年收入':
            sum_df=sum_df[['分类','2万以下', '2-3万','3-5万', '5-10万', '10-20万', '20万以上','总体']]
        elif col=='主要交通方式2':
            sum_df = sum_df[['分类','全程步行', '个人自行车', '公共自行车','电动自行车', '小汽车', '单位班车','出租车', '公交车','地铁','其他','总体']]
        
        ctgrdflist.append(sum_df)

col0 = '主要交通方式2'
modedflist = []
modedfnamelist = ['主要交通方式2', '主要交通方式2-性别', '主要交通方式2-年龄1', '主要交通方式2-就业就学状态',
                  '主要交通方式2-区域名称','主要交通方式2-区内区外','主要交通方式2-分类', '主要交通方式2-有无私家车','主要交通方式2-家庭年收入']

for col in ['主要交通方式2', '性别', '年龄1', '就业就学状态', '区域名称','区内区外','分类', '有无私家车','家庭年收入']:
    if col == col0:
        sum_dfx = dftrip1.groupby(col0)['carweight'].sum().reset_index()
        sum_dfx['pct'] = round(100 * sum_dfx['carweight'] / sum_dfx['carweight'].sum(), 1)
        df_sort = pd.DataFrame(
            {'主要交通方式2': ['全程步行', '小汽车', '公交车', '地铁', '出租车', '个人自行车', '公共自行车', '电动自行车', '单位班车', '其他']})
        sort_mapping = df_sort.reset_index().set_index('主要交通方式2')
        sum_dfx['num'] = sum_dfx['主要交通方式2'].map(sort_mapping['index'])
        sum_dfx = sum_dfx.sort_values('num').drop(columns=['num'])
        sum_dfx['使用该工具的出行']=0
        sum_dfx['使用该工具的出行pct']=0
        for row in sum_dfx.index:
            mode=sum_dfx.loc[row,'主要交通方式2']
            dftrip1['modeflag']=dftrip1['modelist'].apply(lambda x: 1 if mode in x else 0)
            if (mode !='小汽车') and (mode !='公交车'):
                sum_dfx.loc[row, '使用该工具的出行'] = dftrip1.loc[dftrip1['modeflag'] == 1, 'carweight'].sum()
                sum_dfx.loc[row, '使用该工具的出行pct'] = round(100 * sum_dfx.loc[row, '使用该工具的出行'] / dftrip1['carweight'].sum(),
                                                        1)
            elif mode =='小汽车':
                sum_dfx.loc[row, '使用该工具的出行'] = dftrip1.loc[dftrip1['pc'] == 1, 'carweight'].sum()
                sum_dfx.loc[row, '使用该工具的出行pct'] = round(100 * sum_dfx.loc[row, '使用该工具的出行'] / dftrip1['carweight'].sum(),
                                                        1)
            elif mode =='公交车':
                sum_dfx.loc[row, '使用该工具的出行'] = dftrip1.loc[dftrip1['bus'] == 1, 'carweight'].sum()
                sum_dfx.loc[row, '使用该工具的出行pct'] = round(100 * sum_dfx.loc[row, '使用该工具的出行'] / dftrip1['carweight'].sum(),
                                                        1)

        modedflist.append(sum_dfx)
    else:
        if isinstance(col,str):
            grouplist=[col,col0]
        elif isinstance(col,list):
            grouplist=[col[0],col[1],col0]
        sum_df = dftrip1.dropna(subset=grouplist).groupby(grouplist)['carweight'].sum().reset_index().pivot(index=col0, columns=col,
                                                                                     values='carweight').reset_index()
        for value in set(dftrip1.dropna(subset=[col0,col])[col]):
            sum_df[value] = round(100 * sum_df[value] / sum_df[value].sum(),1)
        sum_df = pd.merge(sum_df, sum_dfx[['主要交通方式2', 'pct']], how='left', on='主要交通方式2').rename(columns={'pct': '总体'})

        df_sort = pd.DataFrame({'主要交通方式2': ['全程步行', '小汽车', '公交车', '地铁', '出租车', '个人自行车', '公共自行车', '电动自行车', '单位班车', '其他']})
        sort_mapping = df_sort.reset_index().set_index('主要交通方式2')
        sum_df['num'] = sum_df['主要交通方式2'].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])
        sum_df.loc[len(sum_df), :] = 100
        sum_df.loc[len(sum_df) - 1, '主要交通方式2'] = '总和'

        if col == '年龄1':
            sum_df = sum_df[['主要交通方式2','6-14岁','15-59岁', '60岁及以上', '总体']]
        elif col == '区域名称':
            sum_df = sum_df[['主要交通方式2', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区', '总体']]
        elif col=='分类':
            sum_df=sum_df[['主要交通方式2','基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他' , '总体']]
        elif col=='家庭年收入':
            sum_df=sum_df[['主要交通方式2','2万以下', '2-3万','3-5万', '5-10万', '10-20万', '20万以上','总体']]

        modedflist.append(sum_df)


if 'houra' not in dftrip1.columns:
    dftrip1['houra']=np.nan
    dftrip1.loc[dftrip1['出行编号'].isnull()==False, 'houra'] = dftrip1.loc[dftrip1['出行编号'].isnull()==False, '到达时间'].apply(
        lambda x: int(str(x).split(':')[0]))

col0 = 'hour'
hourdflist = []
hourdfnamelist = ['hour', 'hour-年龄1', 'hour-就业就学状态',
                  'hour-区域名称', 'hour-区内区外','hour-分类','hour-主要交通方式2','hour-机动化','高峰出行目的','高峰出行方式']
dftrip1['auto']=dftrip1['主要交通方式2'].apply(lambda x: '机动化' if x in ['其他', '公交车','单位班车', '小汽车', '地铁', '出租车'] else '非机动化')
dftrip1.loc[(dftrip1['period']=='AM_Peak')&(dftrip1['hour'].isnull()),'hour']=9
indexlist=dftrip1[(dftrip1['period']=='Day_time')&(dftrip1['hour'].isnull())].index
indexlist=list(indexlist)
hourchangedf=pd.DataFrame({'hour':[11,12,13,14,15,16,17,18],
                           'count':[440,353,359,248,235,198,254,359]})

import random
for row in hourchangedf.index:
    houri=hourchangedf.loc[row,'hour']
    counts=hourchangedf.loc[row,'count']
    if len(indexlist) > 0 and len(indexlist)>=counts:
        indexselect = random.sample(indexlist, counts)
        dftrip1.loc[indexselect, 'hour'] = houri
        indexlist = dftrip1[(dftrip1['period'] == 'Day_time') & (dftrip1['hour'].isnull())].index
        indexlist = list(indexlist)
    print(houri,len(indexlist))
print(set(dftrip1['hour']))
dftrip1.loc[(dftrip1['houra'].isnull()),'houra']=dftrip1.loc[(dftrip1['houra'].isnull()),'hour']
print(set(dftrip1['houra']))
for col in ['hour',  '年龄1', '就业就学状态', 'District_O', '区内区外','分类','主要交通方式2','auto']:
    if col == col0:
        sum_dfx = dftrip1.dropna(subset=[col0]).groupby(col0)['carweight'].sum().reset_index()
        sum_dfx['pct'] = round(100 * sum_dfx['carweight'] / sum_dfx['carweight'].sum(), 1)
        sum_dfx1=dftrip1.groupby('houra')['carweight'].sum().reset_index().rename(columns={'carweight':'到达量'})
        sum_dfx1['到达比例'] = round(100 * sum_dfx1['到达量'] / sum_dfx1['到达量'].sum(), 1)
        sum_dfx1=sum_dfx1.merge(sum_dfx,how='left',left_on='houra',right_on='hour').rename(columns={'carweight':'出发量','pct':'出发比例'})
        hourdflist.append(sum_dfx1[['hour','出发量','出发比例','到达量','到达比例']])
    else:
        sum_df = dftrip1.dropna(subset=[col,col0]).groupby([col,col0])['carweight'].sum().reset_index().pivot(index=col0, columns=col,
                                                                                     values='carweight').reset_index()
        for value in set(dftrip1.dropna(subset=[col0,col])[col]):
            sum_df[value] = round(100 * sum_df[value] / sum_df[value].sum(),1)
        sum_df = pd.merge(sum_df, sum_dfx[['hour', 'pct']], how='left', on='hour').rename(columns={'pct': '总体'})

        sum_df.loc[len(sum_df), :] = 100
        sum_df.loc[len(sum_df) - 1, 'hour'] = '总和'

        if col == '年龄1':
            sum_df = sum_df[['hour','6-14岁','15-59岁', '60岁及以上', '总体']]
        elif col == '区域名称':
            sum_df = sum_df[['hour', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区', '总体']]
        elif col=='分类':
            sum_df=sum_df[['hour','基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他' , '总体']]
        elif col == '主要交通方式2':
            sum_df = sum_df[['hour', '全程步行', '个人自行车', '公共自行车', '电动自行车', '小汽车', '单位班车', '出租车', '公交车', '地铁', '其他', '总体']]

        hourdflist.append(sum_df)

for col in ['分类','主要交通方式2']:
    sum_df=dftrip1[(dftrip1['period']=='AM_Peak')|(dftrip1['period']=='PM_Peak')].dropna(subset=[col,col0]).groupby([col,'period'])['carweight'].sum().reset_index()
    sum_df=sum_df.pivot(index=col,columns='period',values='carweight').reset_index()
    sum_df['AM_Peak'] = round(100 * sum_df['AM_Peak'] / sum_df['AM_Peak'].sum(), 1)
    sum_df['PM_Peak'] = round(100 * sum_df['PM_Peak'] / sum_df['PM_Peak'].sum(), 1)
    if col == '分类':
        df_sort = pd.DataFrame(
            {'分类': [ '基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他']})
        sort_mapping = df_sort.reset_index().set_index('分类')
        sum_df['num'] = sum_df['分类'].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])
    elif col == '主要交通方式2':
        df_sort = pd.DataFrame(
            {'主要交通方式2': ['全程步行', '小汽车', '公交车', '地铁', '出租车', '个人自行车', '公共自行车', '电动自行车', '单位班车', '其他']})
        sort_mapping = df_sort.reset_index().set_index('主要交通方式2')
        sum_df['num'] = sum_df['主要交通方式2'].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])


    hourdflist.append(sum_df)


def weightedmean(df,col,weightcol):
    return round((df[col]*df[weightcol]).sum()/df[weightcol].sum(),2)

col0 = 'duration2'
durationdflist = []
durationdfnamelist = ['duration',  'duration-年龄1', 'duration-就业就学状态',
                  'duration-区域名称','duration-区内区外', 'duration-有无私家车','duration-分类','duration-主要交通方式2']
dftrip2=dftrip1[(dftrip1['District_O']!='乌鲁木齐县')&(dftrip1['District_D']!='乌鲁木齐县')]
dftrip2=dftrip2[(dftrip2['District_O']!='达坂城区')&(dftrip2['District_D']!='达坂城区')]
dftrip2=dftrip2[(dftrip2['District_O']!='Outside')&(dftrip2['District_D']!='Outside')]
print(dftrip1.shape,dftrip2.shape)
print(weightedmean(dftrip2.dropna(subset=['duration', 'duration2']), 'duration','carweight'))
for col in ['duration', '年龄1', '就业就学状态', 'District_O', '区内区外','有无私家车','分类','主要交通方式2']:
    if col == 'duration':
        sum_dfx = dftrip1.dropna(subset=[col,col0]).groupby(col0)['carweight'].sum().reset_index()
        sum_dfx['pct'] = round(100 * sum_dfx['carweight'] / sum_dfx['carweight'].sum(), 1)
        sum_dfx.loc[len(sum_dfx),col0]='平均时耗(min)'
        sum_dfx.loc[len(sum_dfx)-1,'pct']=weightedmean(dftrip1.dropna(subset=[col,col0]),col,'carweight')
        df_sort = pd.DataFrame({'duration2': ['0-10分钟', '11-20分钟', '21-30分钟', '31-40分钟', '41-50分钟', '51-60分钟',
                                              '61-70分钟', '71-80分钟', '80分钟以上', '平均时耗(min)']})
        sort_mapping = df_sort.reset_index().set_index('duration2')
        sum_dfx['num'] = sum_dfx['duration2'].map(sort_mapping['index'])
        sum_dfx = sum_dfx.sort_values('num').drop(columns=['num'])
        durationdflist.append(sum_dfx)
    elif col=='区内区外':
        sum_dfx0=pd.DataFrame(columns=['区域名称','天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区'])
        sum_dfx0['区域名称']=['区内','区外','总体']
        for row in ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区']:
            sum_dfx0.loc[0,row]=weightmean(dftrip1[(dftrip1['District_O']==row)&(dftrip1['区内区外']=='区内')].dropna(subset=[col,col0]),'duration','carweight')
            sum_dfx0.loc[1, row] = weightmean(dftrip1[(dftrip1['District_O'] == row) & (dftrip1['区内区外'] == '区外')].dropna(subset=[col,col0]), 'duration',
                                              'carweight')
            sum_dfx0.loc[2, row] = weightmean(dftrip1[(dftrip1['District_O'] == row) ].dropna(subset=[col,col0]), 'duration', 'carweight')
        durationdflist.append(sum_dfx0)
    else:
        sum_df = dftrip1.dropna(subset=[col,col0]).groupby([col,col0])['carweight'].sum().reset_index().pivot(index=col0, columns=col,
                                                                                     values='carweight').reset_index()
        n=len(sum_df)
        sum_df.loc[n,col0]='平均时耗(min)'
        for value in set(dftrip1.dropna(subset=[col0,col])[col]):
            sum_df[value] = round(100 * sum_df[value] / sum_df[value].sum(),1)
            sum_df.loc[n,value]=weightedmean(dftrip1[dftrip1[col]==value].dropna(subset=[col,col0]),'duration','carweight')
        sum_df = pd.merge(sum_df, sum_dfx[['duration2', 'pct']], how='left', on='duration2').rename(columns={'pct': '总体'})

        df_sort = pd.DataFrame({'duration2': ['0-10分钟','11-20分钟','21-30分钟','31-40分钟','41-50分钟','51-60分钟',
                                             '61-70分钟','71-80分钟','80分钟以上','平均时耗(min)']})
        sort_mapping = df_sort.reset_index().set_index('duration2')
        sum_df['num'] = sum_df['duration2'].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])
        print(sum_df)

        if col == '年龄1':
            sum_df = sum_df[['duration2','6-14岁','15-59岁', '60岁及以上', '总体']]
        elif col == '区域名称':
            sum_df = sum_df[['duration2', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区', '总体']]
        elif col=='分类':
            sum_df=sum_df[['duration2','基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他' , '总体']]
        elif col == '主要交通方式2':
            sum_df = sum_df[['duration2', '全程步行', '个人自行车', '公共自行车', '电动自行车', '小汽车', '单位班车', '出租车', '公交车', '地铁', '其他', '总体']]

        durationdflist.append(sum_df)
        
        
col0 = 'distance2'
distancedflist = []
distancedfnamelist = ['distance',  'distance-年龄1', 'distance-就业就学状态',
                  'distance-区域名称','distance-区内区外', 'distance-有无私家车','distance-分类','distance-主要交通方式2']
#dftrip1['distance']=dftrip1['distance0']
for col in ['distance0',  '年龄1', '就业就学状态','District_O', '区内区外','有无私家车','分类','主要交通方式2']:
    if col == 'distance0':
        sum_dfx = dftrip1.dropna(subset=[col,col0]).groupby(col0)['carweight'].sum().reset_index()
        sum_dfx['pct'] = round(100 * sum_dfx['carweight'] / sum_dfx['carweight'].sum(), 1)
        sum_dfx.loc[len(sum_dfx),col0]='平均距离(km)'
        sum_dfx.loc[len(sum_dfx)-1,'pct']=weightedmean(dftrip1.dropna(subset=[col,col0]),col,'carweight')
        df_sort = pd.DataFrame(
            {'distance2': ['0-2千米', '2-4千米', '4-6千米', '6-8千米', '8-10千米', '10-15千米', '15千米以上', '平均距离(km)']})
        sort_mapping = df_sort.reset_index().set_index('distance2')
        sum_dfx['num'] = sum_dfx['distance2'].map(sort_mapping['index'])
        sum_dfx = sum_dfx.sort_values('num').drop(columns=['num'])
        distancedflist.append(sum_dfx)
    elif col=='区内区外':
        sum_dfx0=pd.DataFrame(columns=['区域名称','天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区'])
        sum_dfx0['区域名称']=['区内','区外','总体']
        for row in ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区']:
            sum_dfx0.loc[0,row]=weightmean(dftrip1[(dftrip1['District_O']==row)&(dftrip1['区内区外']=='区内')].dropna(subset=[col,col0]),'distance0','carweight')
            sum_dfx0.loc[1, row] = weightmean(dftrip1[(dftrip1['District_O'] == row) & (dftrip1['区内区外'] == '区外')].dropna(subset=[col,col0]), 'distance0',
                                              'carweight')
            sum_dfx0.loc[2, row] = weightmean(dftrip1[(dftrip1['District_O'] == row)].dropna(subset=[col,col0]), 'distance0', 'carweight')
        distancedflist.append(sum_dfx0)

    else:
        sum_df = dftrip1.dropna(subset=[col,col0]).groupby([col,col0])['carweight'].sum().reset_index().pivot(index=col0, columns=col,
                                                                                     values='carweight').reset_index()
        n=len(sum_df)
        sum_df.loc[n,col0]='平均距离(km)'
        for value in set(dftrip1.dropna(subset=[col0,col])[col]):
            sum_df[value] = round(100 * sum_df[value] / sum_df[value].sum(),1)
            sum_df.loc[n,value]=weightedmean(dftrip1[dftrip1[col]==value].dropna(subset=[col,col0]),'distance0','carweight')
        sum_df = pd.merge(sum_df, sum_dfx[['distance2', 'pct']], how='left', on='distance2').rename(columns={'pct': '总体'})

        df_sort = pd.DataFrame({'distance2': ['0-2千米','2-4千米','4-6千米','6-8千米','8-10千米','10-15千米','15千米以上','平均距离(km)']})
        sort_mapping = df_sort.reset_index().set_index('distance2')
        sum_df['num'] = sum_df['distance2'].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])

        if col == '年龄1':
            sum_df = sum_df[['distance2','6-14岁','15-59岁', '60岁及以上', '总体']]
        elif col == '区域名称':
            sum_df = sum_df[['distance2', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区', '总体']]
        elif col=='分类':
            sum_df=sum_df[['distance2','基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他' , '总体']]
        elif col == '主要交通方式2':
            sum_df = sum_df[['distance2', '全程步行', '个人自行车', '公共自行车', '电动自行车', '小汽车', '单位班车', '出租车', '公交车', '地铁', '其他', '总体']]


        distancedflist.append(sum_df)






Otherdflist=[]
otherdfnamelist=['fare','parking','parking-district','parking-ctgr','首次到达车站所花费时间（公交/地铁）','全程候车时间（公交/地铁）',
                 '最后一次下车至目的地所花费时间（公交/地铁）','此次出行换乘次数']


def faregroup(x):
    if x==0:
        return '1. 0元'
    elif x>0 and x<=5:
        return '2. 5元以内'
    elif x>5 and x<=10:
        return '3. 5-10元'
    elif x>10 and x<=20:
        return '4. 10-20元'
    elif x>20 and x<=30:
        return '5. 20-30元'
    elif x>30 and x<=50:
        return '6. 30-50元'
    elif x>50:
        return  '7. 50元以上'
dftrip1['fare']=dftrip1['此次出行总费用（不含停车费）'].apply(lambda x: faregroup(x))
dftrip1['modecount']=dftrip1['modelist'].apply(lambda x: len(x))
dftrip1['modemark']='N'
farelist= ['公共自行车', '私家车(驾驶)','私家车(搭乘)','网约车', '出租车','地铁', '公交车', '单位班车',  '黑车']
dftrip1.loc[dftrip1['modecount']==1,'modemark']=dftrip1.loc[dftrip1['modecount']==1,'使用的主要交通方式'].apply(lambda x: 'Y' if x in farelist else 'N')


faredf=dftrip1.groupby('fare')['carweight'].sum().reset_index()
faredf['pct']=round(100*faredf['carweight']/faredf['carweight'].sum(),1)
faredf.loc[len(faredf),'fare']='平均'
faredf.loc[len(faredf)-1,'pct']=round((dftrip1['此次出行总费用（不含停车费）']*dftrip1['carweight']).sum()/dftrip1['carweight'].sum(),2)
faredf2=dftrip1[dftrip1['modemark']=='Y'].groupby(['fare','使用的主要交通方式'])['carweight'].sum().reset_index()
faredf2=faredf2.pivot(index='fare',columns='使用的主要交通方式',values='carweight').reset_index()
faredf2.loc[len(faredf2),:]=0
faredf2.loc[len(faredf2)-1,'fare']='平均'

for col in faredf2.columns[1:]:
    faredf2[col]=round(100*faredf2[col]/faredf2[col].sum(),1)
    dftripi=dftrip1[(dftrip1['modemark']=='Y')&(dftrip1['使用的主要交通方式']==col)]
    ave_farei=(dftripi['此次出行总费用（不含停车费）']*dftripi['carweight']).sum()/dftripi['carweight'].sum()
    faredf2.loc[len(faredf2)-1,col]=round(ave_farei,2)

faredf=pd.merge(faredf,faredf2,how='left',on='fare').fillna(0)
Otherdflist.append(faredf)


parking_trip=dftrip1.groupby('此次停车方式（小汽车）')['carweight'].sum().reset_index()
parking_trip['pct']=round(100*parking_trip['carweight']/parking_trip['carweight'].sum(),1)
parking_trip['停车时间']=0
parking_trip['停车费用']=0
for i in parking_trip.index:
    park=parking_trip.loc[i,'此次停车方式（小汽车）']
    dftripi=dftrip1[dftrip1['此次停车方式（小汽车）']==park]
    parking_trip.loc[i, '停车时间'] = round((dftripi['carweight']*dftripi['此次停车时间（小汽车）']).sum()/dftripi['carweight'].sum(),1)
    parking_trip.loc[i, '停车费用'] = round((dftripi['carweight']*dftripi['此次停车费用（小汽车）']).sum()/dftripi['carweight'].sum(),1)
Otherdflist.append(parking_trip)

parkingft=pd.DataFrame({'行政区':['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区'],'停车时间':0,'停车费用':0})
for i in parkingft.index:
    dist=parkingft.loc[i,'行政区']
    dftripi = dftrip1[(dftrip1['District_D'] == dist)&(dftrip1['此次停车时间（小汽车）'] >0)]
    parkingft.loc[i,'停车时间']= round((dftripi['carweight']*dftripi['此次停车时间（小汽车）']).sum()/dftripi['carweight'].sum(),1)
    parkingft.loc[i, '停车时间'] = round(parkingft.loc[i, '停车时间'] / 60, 1)
    parkingft.loc[i, '停车费用'] = round((dftripi['carweight']*dftripi['此次停车费用（小汽车）']).sum()/dftripi['carweight'].sum(),1)
Otherdflist.append(parkingft)

parkingft=pd.DataFrame({'分类':['基家工作', '基家就学', '基家购物', '基家其他', '非基家商务', '非基家其他' ],'停车时间':0,'停车费用':0})
for i in parkingft.index:
    dist=parkingft.loc[i,'分类']
    dftripi = dftrip1[(dftrip1['分类'] == dist)&(dftrip1['此次停车时间（小汽车）'] >0)]
    parkingft.loc[i,'停车时间']= round((dftripi['carweight']*dftripi['此次停车时间（小汽车）']).sum()/dftripi['carweight'].sum(),1)
    parkingft.loc[i,'停车时间']=round(parkingft.loc[i,'停车时间']/60,1)
    parkingft.loc[i, '停车费用'] = round((dftripi['carweight']*dftripi['此次停车费用（小汽车）']).sum()/dftripi['carweight'].sum(),1)
Otherdflist.append(parkingft)

dftrip1_bus=dftrip1[dftrip1['bus']==1]
def timeslot(x):
    if x >= 0 and x <= 5:
        return '1. 0-5分钟'
    elif x > 5 and x <= 10:
        return '2. 5-10分钟'
    elif x > 10 and x <= 20:
        return '3. 10-20分钟'
    elif x > 20:
        return '4. 20分钟以上'

dftrip1_bus['tostop']=dftrip1_bus['首次到达车站所花费时间（公交/地铁）'].apply(lambda x: timeslot(x))
dftrip1_bus['wait']=dftrip1_bus['全程候车时间（公交/地铁）'].apply(lambda x: timeslot(x))
dftrip1_bus['fromstop']=dftrip1_bus['最后一次下车至目的地所花费时间（公交/地铁）'].apply(lambda x: timeslot(x))
collist1=['tostop','wait','fromstop','此次出行换乘次数']
collist2=['首次到达车站所花费时间（公交/地铁）','全程候车时间（公交/地铁）','最后一次下车至目的地所花费时间（公交/地铁）','此次出行换乘次数']
for i in range(len(collist1)):
    col=collist1[i]
    col2=collist2[i]
    transitdf = dftrip1_bus.groupby(col)['carweight'].sum().reset_index()
    transitdf['pct'] = round(100 * transitdf['carweight'] / transitdf['carweight'].sum(), 1)
    transitdf.loc[len(transitdf), col] = '平均'
    transitdf.loc[len(transitdf)-1, 'pct'] = round(
        (dftrip1_bus['carweight'] * dftrip1_bus[col2]).sum() / dftrip1_bus['carweight'].sum(), 1)
    Otherdflist.append(transitdf)

######################出行空间分布######################

# 各区域区内出行所占比例
dfin = dftrip1[dftrip1['区内区外'] == '区内'].groupby('District_O')['carweight'].sum().reset_index().rename(
    columns={'District_O': '区域名称'})
dftravelrate_d=dftrip1.dropna(subset=['District_O', 'District_D']).groupby('District_O')['carweight'].sum().reset_index().rename(columns={'District_O':'区域名称','carweight':'出行量（人次）'})
dfin = pd.merge(dfin, dftravelrate_d[['区域名称', '出行量（人次）']], how='left', on='区域名称')
dfin['比例(%)'] = round(100 * dfin['carweight'] / dfin['出行量（人次）'], 1)
emp_sort = pd.DataFrame({'区域名称': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区']})
sort_mapping = emp_sort.reset_index().set_index('区域名称')
dfin['emp_num'] = dfin['区域名称'].map(sort_mapping['index'])
dfin = dfin.sort_values('emp_num').drop(columns=['emp_num'])

# 全目的全方式出行OD分布（人次/日）add 2 columns to dftrip1,['District_O','District_D']
dfod = dftrip1.dropna(subset=['District_O', 'District_D']).groupby(['District_O', 'District_D'])['carweight'].sum().reset_index()
dfod = dfod.pivot(index='District_O', columns='District_D', values='carweight').reset_index().fillna(0)
emp_sort = pd.DataFrame({'District_O': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区',  'Outside']})
sort_mapping = emp_sort.reset_index().set_index('District_O')
dfod['emp_num'] = dfod['District_O'].map(sort_mapping['index'])
dfod = dfod.sort_values('emp_num').drop(columns=['emp_num'])
dfod = dfod[['District_O', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区', 'Outside']]
dfod = dfod.rename(columns={'District_O': 'OD'})

# 基家工作、基家就学区内出行所占比例
dfin_ctgr = dftrip1[dftrip1['区内区外'] == '区内'].groupby(['District_O', '分类'])['carweight'].sum().reset_index().rename(
    columns={'District_O': '区域名称'})
dfin_ctgr = dfin_ctgr.pivot(index='区域名称', columns='分类', values='carweight').reset_index()
dfin_ctgr = dfin_ctgr[['区域名称', '基家工作', '基家就学']]
dfin_ctgr = pd.merge(dfin_ctgr, dfin[['区域名称', '比例(%)']], how='left', on='区域名称')
for dist in set(dfin_ctgr['区域名称']):
    dftrip1d = dftrip1[dftrip1['District_O'] == dist]
    for ctgr in ['基家工作', '基家就学']:
        trip_dc = dftrip1d.loc[dftrip1d['分类'] == ctgr, 'carweight'].sum()
        dfin_ctgr.loc[dfin_ctgr['区域名称'] == dist, ctgr] = round(
            100 * dfin_ctgr.loc[dfin_ctgr['区域名称'] == dist, ctgr].mean() / trip_dc, 1)
emp_sort = pd.DataFrame({'区域名称': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区']})
sort_mapping = emp_sort.reset_index().set_index('区域名称')
dfin_ctgr['emp_num'] = dfin_ctgr['区域名称'].map(sort_mapping['index'])
dfin_ctgr = dfin_ctgr.sort_values('emp_num').drop(columns=['emp_num'])
dfin_ctgr = dfin_ctgr[['区域名称', '基家工作', '基家就学', '比例(%)']]
dfin_ctgr = dfin_ctgr.rename(columns={'比例(%)': '区内出行总体比例'})

# 基家工作出行矩阵（人次/日）
dfwork = dftrip1[dftrip1['分类'] == '基家工作'].dropna(subset=['District_O', 'District_D']).groupby(['District_O', 'District_D'])['carweight'].sum().reset_index()
dfwork = dfwork.pivot(index='District_O', columns='District_D', values='carweight').reset_index().fillna(0)
emp_sort = pd.DataFrame({'District_O': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区', 'Outside']})
sort_mapping = emp_sort.reset_index().set_index('District_O')
dfwork['emp_num'] = dfwork['District_O'].map(sort_mapping['index'])
dfwork = dfwork.sort_values('emp_num').drop(columns=['emp_num'])
dfwork = dfwork[['District_O', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区',  'Outside']]
dfwork = dfwork.rename(columns={'District_O': 'OD'})

# 基家就学出行矩阵（次/日）
dfschool = dftrip1[dftrip1['分类'] == '基家就学'].dropna(subset=['District_O', 'District_D']).groupby(['District_O', 'District_D'])['carweight'].sum().reset_index()
dfschool = dfschool.pivot(index='District_O', columns='District_D', values='carweight').reset_index().fillna(0)
emp_sort = pd.DataFrame({'District_O': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区',  'Outside']})
sort_mapping = emp_sort.reset_index().set_index('District_O')
dfschool['emp_num'] = dfschool['District_O'].map(sort_mapping['index'])
dfschool = dfschool.sort_values('emp_num').drop(columns=['emp_num'])
dfschool = dfschool[['District_O', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区',  'Outside']]
dfschool = dfschool.rename(columns={'District_O': 'OD'})

# 公交车、小汽车区内出行所占比例
dfin_mode = dftrip1[dftrip1['区内区外'] == '区内'].groupby(['District_O', '主要交通方式2'])['carweight'].sum().reset_index().rename(
    columns={'District_O': '区域名称'})
dfin_mode = dfin_mode.pivot(index='区域名称', columns='主要交通方式2', values='carweight').reset_index()
dfin_mode = dfin_mode[['区域名称', '公交车', '小汽车', '全程步行']]
dfin_mode = pd.merge(dfin_mode, dfin[['区域名称', '比例(%)']], how='left', on='区域名称')
for dist in set(dfin_mode['区域名称']):
    dftrip1d = dftrip1[dftrip1['District_O'] == dist]
    for mode in ['公交车', '小汽车', '全程步行']:
        trip_dc = dftrip1d.loc[dftrip1d['主要交通方式2'] == mode, 'carweight'].sum()
        dfin_mode.loc[dfin_mode['区域名称'] == dist, mode] = round(
            100 * dfin_mode.loc[dfin_mode['区域名称'] == dist, mode].mean() / trip_dc, 1)
emp_sort = pd.DataFrame({'区域名称': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区']})
sort_mapping = emp_sort.reset_index().set_index('区域名称')
dfin_mode['emp_num'] = dfin_mode['区域名称'].map(sort_mapping['index'])
dfin_mode = dfin_mode.sort_values('emp_num').drop(columns=['emp_num'])

# 公交出行矩阵（人次/日）
dfod_bus = dftrip1[dftrip1['主要交通方式2'] == '公交车'].dropna(subset=['District_O', 'District_D']).groupby(['District_O', 'District_D'])['carweight'].sum().reset_index()
dfod_bus = dfod_bus.pivot(index='District_O', columns='District_D', values='carweight').reset_index()
emp_sort = pd.DataFrame({'District_O': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区',  'Outside']})
sort_mapping = emp_sort.reset_index().set_index('District_O')
dfod_bus['emp_num'] = dfod_bus['District_O'].map(sort_mapping['index'])
dfod_bus = dfod_bus.sort_values('emp_num').drop(columns=['emp_num'])
dfod_bus = dfod_bus[['District_O', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区',  'Outside']]
dfod_bus = dfod_bus.rename(columns={'District_O': 'OD'})

# 小汽车出行矩阵（人次/日）
dfod_pc = dftrip1[dftrip1['主要交通方式2'] == '小汽车'].dropna(subset=['District_O', 'District_D']).groupby(['District_O', 'District_D'])['carweight'].sum().reset_index()
dfod_pc = dfod_pc.pivot(index='District_O', columns='District_D', values='carweight').reset_index()
emp_sort = pd.DataFrame({'District_O': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区', 'Outside']})
sort_mapping = emp_sort.reset_index().set_index('District_O')
dfod_pc['emp_num'] = dfod_pc['District_O'].map(sort_mapping['index'])
dfod_pc = dfod_pc.sort_values('emp_num').drop(columns=['emp_num'])
dfod_pc = dfod_pc[['District_O', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区', 'Outside']]
dfod_pc = dfod_pc.rename(columns={'District_O': 'OD'})

# 高峰、平峰时段区内出行所占比例
dftrip1['peak'] = dftrip1['period'].apply(lambda x: '高峰' if x in ['AM_Peak', 'PM_Peak'] else '平峰')
dfin_peak = dftrip1[dftrip1['区内区外'] == '区内'].groupby(['District_O', 'peak'])['carweight'].sum().reset_index().rename(
    columns={'District_O': '区域名称'})
dfin_peak = dfin_peak.pivot(index='区域名称', columns='peak', values='carweight')
dfin_peak = pd.merge(dfin_peak, dfin[['区域名称', '比例(%)']], how='left', on='区域名称')
for dist in set(dfin_peak['区域名称']):
    dftrip1d = dftrip1[dftrip1['区域名称'] == dist]
    for pk in ['高峰', '平峰']:
        trip_dc = dftrip1d.loc[dftrip1d['peak'] == pk, 'carweight'].sum()
        dfin_peak.loc[dfin_peak['区域名称'] == dist, pk] = round(
            100 * dfin_peak.loc[dfin_peak['区域名称'] == dist, pk].mean() / trip_dc, 1)
emp_sort = pd.DataFrame({'区域名称': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区',  'Outside']})
sort_mapping = emp_sort.reset_index().set_index('区域名称')
dfin_peak['emp_num'] = dfin_peak['区域名称'].map(sort_mapping['index'])
dfin_peak = dfin_peak.sort_values('emp_num').drop(columns=['emp_num'])

# 高峰时段出行矩阵（次/日）
dfod_peak = dftrip1[dftrip1['peak'] == '高峰'].dropna(subset=['District_O', 'District_D']).groupby(['District_O', 'District_D'])['carweight'].sum().reset_index()
dfod_peak = dfod_peak.pivot(index='District_O', columns='District_D', values='carweight').reset_index()
emp_sort = pd.DataFrame({'District_O': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区',  'Outside']})
sort_mapping = emp_sort.reset_index().set_index('District_O')
dfod_peak['emp_num'] = dfod_peak['District_O'].map(sort_mapping['index'])
dfod_peak = dfod_peak.sort_values('emp_num').drop(columns=['emp_num'])
dfod_peak = dfod_peak[['District_O', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区',  'Outside']]
dfod_peak = dfod_peak.rename(columns={'District_O': 'OD'})

# 平峰时段出行矩阵（人次/日）
dfod_nonpeak = dftrip1[dftrip1['peak'] == '平峰'].dropna(subset=['District_O', 'District_D']).groupby(['District_O', 'District_D'])['carweight'].sum().reset_index()
dfod_nonpeak = dfod_nonpeak.pivot(index='District_O', columns='District_D', values='carweight').reset_index().fillna(0)
emp_sort = pd.DataFrame({'District_O': ['天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区', 'Outside']})
sort_mapping = emp_sort.reset_index().set_index('District_O')
dfod_nonpeak['emp_num'] = dfod_nonpeak['District_O'].map(sort_mapping['index'])
dfod_nonpeak = dfod_nonpeak.sort_values('emp_num').drop(columns=['emp_num'])
dfod_nonpeak = dfod_nonpeak[['District_O', '天山区', '沙依巴克区', '高新区', '水磨沟区', '经开区', '米东区',  'Outside']]
dfod_nonpeak = dfod_nonpeak.rename(columns={'District_O': 'OD'})

dflist_dist=[dfin,dfod,dfin_ctgr,dfwork,dfschool,dfin_mode,dfod_bus,dfod_pc,dfin_peak,dfod_peak,dfod_nonpeak]
dfnamelist_dist=['各区域区内出行所占比例','全目的全方式出行OD分布（人次/日）','基家工作、基家就学区内出行所占比例','基家工作出行矩阵（人次/日）','基家就学出行矩阵（次/日）','公交车、小汽车区内出行所占比例',
            '公交出行矩阵（人次/日）','小汽车出行矩阵（人次/日）','高峰、平峰时段区内出行所占比例','高峰时段出行矩阵（次/日）','平峰时段出行矩阵（人次/日）']

print("写入文件")
writer = pd.ExcelWriter(summarypath + '\summary_1115_核心区域内dup_trips.xlsx')
### 1.家庭情况
if len(hhdflist) > 0:
    startr = 1
    rowlist = [0]
    for i in range(len(hhdflist)):
        hhdflist[i].to_excel(writer, sheet_name='households', startrow=startr, startcol=0, index=False)
        r, c = hhdflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['households']
    for i in range(len(hhdflistname)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, hhdflistname[i])

###2.意愿
if len(willdflist) > 0:
    startr = 1
    rowlist = [0]
    for i in range(len(willdflist)):
        willdflist[i].to_excel(writer, sheet_name='willing', startrow=startr, startcol=0, index=False)
        r, c = willdflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['willing']
    for i in range(len(willdflistname)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, willdflistname[i])

###3.个人情况
if len(ppdflist) > 0:
    startr = 1
    rowlist = [0]
    for i in range(len(ppdflist)):
        ppdflist[i].to_excel(writer, sheet_name='person', startrow=startr, startcol=0, index=False)
        r, c = ppdflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['person']
    for i in range(len(ppdfnamelist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, ppdfnamelist[i])

###4.出行频率
if len(tripdflist) > 0:
    startr = 1
    rowlist = [0]
    for i in range(len(tripdflist)):
        tripdflist[i].to_excel(writer, sheet_name='frequency', startrow=startr, startcol=0, index=False)
        r, c = tripdflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['frequency']
    for i in range(len(tripdfnamelist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, tripdfnamelist[i])

### 5.出行目的
if len(ctgrdflist) > 0:
    startr = 1
    rowlist = [0]
    for i in range(len(ctgrdflist)):
        ctgrdflist[i].to_excel(writer, sheet_name='purpose', startrow=startr, startcol=0, index=False)
        r, c = ctgrdflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['purpose']
    for i in range(len(ctgrdfnamelist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, ctgrdfnamelist[i])

### 6.出行方式
if len(modedflist) > 0:
    startr = 1
    rowlist = [0]
    for i in range(len(modedflist)):
        modedflist[i].to_excel(writer, sheet_name='mode', startrow=startr, startcol=0, index=False)
        r, c = modedflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['mode']
    for i in range(len(modedfnamelist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, modedfnamelist[i])

###7.出行时间
if len(hourdflist) > 0:
    startr = 1
    rowlist = [0]
    for i in range(len(hourdflist)):
        hourdflist[i].to_excel(writer, sheet_name='hour', startrow=startr, startcol=0, index=False)
        r, c = hourdflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['hour']
    for i in range(len(hourdfnamelist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, hourdfnamelist[i])

# 8.出行时耗
if len(durationdflist) > 0:
    startr = 1
    rowlist = [0]
    for i in range(len(durationdflist)):
        durationdflist[i].to_excel(writer, sheet_name='duration', startrow=startr, startcol=0, index=False)
        r, c = durationdflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['duration']
    for i in range(len(durationdfnamelist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, durationdfnamelist[i])

# 9.出行距离
if len(distancedflist) > 0:
    startr = 1
    rowlist = [0]
    for i in range(len(distancedflist)):
        distancedflist[i].to_excel(writer, sheet_name='distance', startrow=startr, startcol=0, index=False)
        r, c = distancedflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['distance']
    for i in range(len(distancedfnamelist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, distancedfnamelist[i])

# 10.其他
if len(Otherdflist) > 0:
    startr = 1
    rowlist = [0]
    for i in range(len(Otherdflist)):
        Otherdflist[i].to_excel(writer, sheet_name='other', startrow=startr, startcol=0, index=False)
        r, c = Otherdflist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['other']
    for i in range(len(otherdfnamelist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, otherdfnamelist[i])

### 11.出行空间分布
if len(dflist_dist) > 0:
    startr = 1
    rowlist = [0]
    for i in range(len(dflist_dist)):
        dflist_dist[i].to_excel(writer, sheet_name='district', startrow=startr, startcol=0, index=False)
        r, c = dflist_dist[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['district']
    for i in range(len(dfnamelist_dist)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, dfnamelist_dist[i])

writer.save()



