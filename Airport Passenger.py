import pandas as pd
import re
pd.options.mode.chained_assignment = None  # default='warn'
######################客运站满意度调查结果分析#########################################################
"""
客运站旅客个人信息	根据客流规模扩样，性别/年龄/来自哪里
客运站旅客出行信息	根据客流规模扩样，起终点/到达客运站的交通方式/时耗/出行目的/候机时间/同行人数
客运站旅客出行意愿信息	根据客流规模扩样，乘车频率/选择乘车的理由
客运站满意度	根据客流规模扩样，总体/分项目
"""
data=pd.read_excel(r'D:\Hyder安诚\调查结果数据\枢纽调查\乌鲁木齐市地窝堡机场交通调查问卷数据库07.07.xlsx',sheet_name='机场数据')
dictionary=pd.read_excel(r'D:\Hyder安诚\调查结果数据\枢纽调查\乌鲁木齐市地窝堡机场交通调查问卷数据库07.07.xlsx',sheet_name='代号')
#data['mark']='N'
#data.loc[(data['您此次出行的起点（1城区内，2城区外）：']==2) &(data['您此次出行的终点（1城区内，2城区外）：']==2) & (data['出行的交通方式：']==12),'mark']='Y'
#data=data[data['mark']=='N'].drop(columns=['mark'])
passengerdf=[]
passengerdfname=['性别','职业','籍贯','出行方式','出行目的','乘机频率','选择飞机的原因','同行人数','进入候机厅人数','候机时间','起终点','到机场时耗','分地区到机场时耗','航空公司偏好']
for i in range(1,8):
    colname=dictionary.columns[i]
    colname2=passengerdfname[i-1]
    data=pd.merge(data,dictionary[['代号',colname]],how='left',left_on=colname,right_on='代号').drop(columns=['代号',colname+'_x'])
    data=data.rename(columns={colname+'_y':colname})
    sum_df=data.groupby(colname)['序号'].count().reset_index().rename(columns={'序号':'人数'})
    sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
    if colname in dictionary.columns:
        df_sort = pd.DataFrame({colname2: list(dictionary[colname].dropna())})
        sort_mapping = df_sort.reset_index().set_index(colname2)
        sum_df['num'] = sum_df[colname].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])
        print(sum_df)

    passengerdf.append(sum_df)
for colname in ['18、(1)您从起点到机场，同行有___人（包括本人），', '18、(2)您的同伴中总共有___人进入候车厅']:
    data[colname]=data[colname].apply(lambda x: '>=5人' if x>=5 else str(x)+'人')
    sum_df=data.groupby(colname)['序号'].count().reset_index().rename(columns={'序号':'人数'})
    sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
    passengerdf.append(sum_df)

##候机时间
def waitingfun(x):
    if x<=30:
        return '30min以内'
    elif x>30 and x<=60:
        return '30-60min'
    elif x>60 and x<=90:
        return '60-90min'
    elif x>90 and x<=120:
        return '90-120min'
    elif x>120:
        return '120min以上'
data['候机时间']=data['14、您从进安检开始总共要等候多久，才可以登机？（分钟）'].apply(lambda x: waitingfun(x))
sum_df=data.groupby('候机时间')['序号'].count().reset_index().rename(columns={'序号':'人数'})
sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
df_sort = pd.DataFrame({'候机时间': ['30min以内','30-60min','60-90min','90-120min','120min以上']})
sort_mapping = df_sort.reset_index().set_index('候机时间')
sum_df['num'] = sum_df['候机时间'].map(sort_mapping['index'])
sum_df = sum_df.sort_values('num').drop(columns=['num'])
sum_df=sum_df.append([{'候机时间':'平均（min）','人数':round(data['14、您从进安检开始总共要等候多久，才可以登机？（分钟）'].mean(),1)}])
passengerdf.append(sum_df)

##起终点


import geopandas as gpd
Province=gpd.read_file(r'D:/Hyder安诚/全国区划/省.shp')
Province=Province.to_crs(4326)
Region=gpd.read_file(r'D:/Hyder安诚/Test GIS/District/District.shp',encoding='gbk')
Region=Region.to_crs(4326)
origin = gpd.GeoDataFrame(data, geometry = gpd.points_from_xy(data['出行起点X'], data['出行起点Y'], crs="EPSG:4326"))
desti = gpd.GeoDataFrame(data, geometry = gpd.points_from_xy(data['出行终点X'], data['出行终点Y'], crs="EPSG:4326"))


Origin_Province = gpd.sjoin(origin,Province,how="left",op='within')
Origin_Reg=gpd.sjoin(origin,Region,how='left',op='within')
Origin_Province_Reg=pd.merge(Origin_Province,Origin_Reg[['序号','District']],how='left',on='序号')
Origin_Province_Reg=Origin_Province_Reg[['序号','出行起点X', '出行起点Y', 'geometry','省','District']]
Origin_Province_Reg['省']=Origin_Province_Reg['省'].fillna('NA').replace('新疆维吾尔自治区','新疆其他地区')
Origin_Province_Reg['District']=Origin_Province_Reg['District'].fillna('新疆其他地区')
Origin_Province_Reg=Origin_Province_Reg.rename(columns={'省':'Province_O','District':'District_O'})

Desti_Province = gpd.sjoin(desti,Province,how="left",op='within')
Desti_Reg=gpd.sjoin(desti,Region,how='left',op='within')
Desti_Province_Reg=pd.merge(Desti_Province,Desti_Reg[['序号','District']],how='left',on='序号')
Desti_Province_Reg=Desti_Province_Reg[['序号','出行终点X', '出行终点Y', 'geometry','省','District']]
Desti_Province_Reg['省']=Desti_Province_Reg['省'].fillna('NA').replace('新疆维吾尔自治区','新疆其他地区')
Desti_Province_Reg['District']=Desti_Province_Reg['District'].fillna('新疆其他地区')
Desti_Province_Reg=Desti_Province_Reg.rename(columns={'省':'Province_D','District':'District_D'})

data=pd.merge(data,Origin_Province_Reg[['序号','Province_O','District_O']],how='left',on='序号')
data=pd.merge(data,Desti_Province_Reg[['序号','Province_D','District_D']],how='left',on='序号')


data['起点地区']=''
data['终点地区']=''

for i in data.index:
    if data.loc[i,'5、您此次出行的起点（1城区内，2城区外）：']==1:
            data.loc[i, '起点地区'] ='乌鲁木齐市'
    elif data.loc[i,'5、您此次出行的起点（1城区内，2城区外）：']==2:
        if data.loc[i,'Province_O']!='NA':
            data.loc[i, '起点地区'] = data.loc[i,'Province_O']
        elif '省' in data.loc[i,'出行起点详细地址']:
            data.loc[i, '起点地区'] = re.split('[省]', data.loc[i,'出行起点详细地址'])[0] + '省'


    if data.loc[i,'10、您此次出行的终点（1城区内，2城区外）：']==1:
            data.loc[i, '终点地区'] = '乌鲁木齐市'

    elif data.loc[i,'10、您此次出行的终点（1城区内，2城区外）：']==2:
        if data.loc[i,'Province_D']!='NA':
            data.loc[i, '终点地区'] = data.loc[i,'Province_D']
        elif  '省' in data.loc[i,'出行终点详细地址']:
            data.loc[i, '终点地区'] = re.split('[省]', data.loc[i,'出行终点详细地址'])[0] + '省'

print(set(data['起点地区']),set(data['终点地区']))

sum_od=data.groupby(['起点地区','终点地区'])['序号'].count().reset_index().rename(columns={'序号':'人数'}).pivot(index='起点地区',columns='终点地区',values='人数').reset_index().fillna(0)
print(sum_od)
passengerdf.append(sum_od)
####画OD Plot
import matplotlib as mpl
import matplotlib.pyplot as plt
from shapely.geometry import Point,Polygon,shape


Province_point = Province.copy()
Province_point['geometry'] = Province.centroid
Province_point.to_excel(r'D:/Hyder安诚/全国区划/Province_Centroid.xlsx',index=False)
centroid=pd.read_excel(r'D:/Hyder安诚/全国区划/Province_Centroid.xlsx')
sum_odplot=data.groupby(['起点地区','终点地区'])['序号'].count().reset_index().rename(columns={'序号':'人数'})
sum_odplot=pd.merge(sum_odplot,centroid,how='left',left_on='起点地区',right_on='省').rename(columns={'Long':'Long_x','Lat':'Lat_x'})
sum_odplot=pd.merge(sum_odplot,centroid,how='left',left_on='终点地区',right_on='省').rename(columns={'Long':'Long_y','Lat':'Lat_y'})
fig = plt.figure()
ax = plt.subplot(111)
plt.sca(ax)
# plot administration shp
Province.plot(ax=ax, edgecolor=(0, 0, 0, 1), facecolor=(0, 0, 0, 0), linewidths=0.5)

# colormap
vmax = sum_odplot['人数'].max()
norm = mpl.colors.Normalize(vmin=0, vmax=vmax)
cmapname = 'autumn_r'
cmap = mpl.cm.get_cmap(cmapname)

# plot OD
# for loop
for i in range(len(sum_odplot)):
    # color and linewidth
    color_i = cmap(norm(sum_odplot['人数'].iloc[i]))
    linewidth_i = norm(sum_odplot['人数'].iloc[i]) * 5
    # plot
    plt.plot([sum_odplot['Long_x'].iloc[i], sum_odplot['Long_y'].iloc[i]], [sum_odplot['Lat_x'].iloc[i], sum_odplot['Lat_y'].iloc[i]], color=color_i,
             linewidth=linewidth_i)

# no axis
plt.axis('off')


# set xlim ylim
plt.show()



###到机场时耗
data['到机场时耗']=data['9、您从起点到达本机场用了多长时间？（分钟）'].apply(lambda x: waitingfun(x))
sum_df=data.groupby('到机场时耗')['序号'].count().reset_index().rename(columns={'序号':'人数'})
sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
df_sort = pd.DataFrame({'到机场时耗': ['30min以内','30-60min','60-90min','90-120min','120min以上']})
sort_mapping = df_sort.reset_index().set_index('到机场时耗')
sum_df['num'] = sum_df['到机场时耗'].map(sort_mapping['index'])
sum_df = sum_df.sort_values('num').drop(columns=['num'])
sum_df=sum_df.append([{'到机场时耗':'平均（min）','人数':round(data['9、您从起点到达本机场用了多长时间？（分钟）'].mean(),1)}])
passengerdf.append(sum_df)


sum_df_d=data.groupby(['起点地区','到机场时耗'])['序号'].count().reset_index().rename(columns={'序号':'人数'})
sum_df_d=sum_df_d.pivot(index='到机场时耗',columns='起点地区',values='人数').reset_index().fillna(0)
rown=len(sum_df_d)
sum_df_d.loc[rown,'到机场时耗']='平均'
for col in sum_df_d.columns[1:]:
    sum_df_d[col]=round(100*sum_df_d[col]/sum_df_d[col].sum(),2)
    sum_df_d.loc[rown,col]=round(data.loc[data['起点地区']==col,'9、您从起点到达本机场用了多长时间？（分钟）'].mean(),2)
df_sort = pd.DataFrame({'到机场时耗': ['30min以内','30-60min','60-90min','90-120min','120min以上','平均']})
sort_mapping = df_sort.reset_index().set_index('到机场时耗')
sum_df_d['num'] = sum_df_d['到机场时耗'].map(sort_mapping['index'])
sum_df_d = sum_df_d.sort_values('num').drop(columns=['num'])
passengerdf.append(sum_df_d)

##意向航空公司
Airlines=[ '17、(乌鲁木齐航空)', '17、(国际航空)', '17、(南方航空)', '17、(东方航空)', '17、(海南航空)', '17、(深圳航空)',
           '17、(山东航空)', '17、(四川航空)', '17、(厦门航空)', '17、(其他)', '17、(无意向航空)']
preference=pd.DataFrame({'航空公司':Airlines, '人数':0})
for i in preference.index:
    name=preference.loc[i,'航空公司'][4:-1]
    count=data[preference.loc[i,'航空公司']].sum()
    preference.loc[i,'航空公司']=name
    preference.loc[i,'人数']=count

preference['pct']=round(100*preference['人数']/len(data),2)
passengerdf.append(preference)

satisfy=[]
satisfyname=[]
scorelist=['19、从您下车地点到机场步行交通环境是否便捷？（包括方便性、步行距离长度等）',
       '19、从您下车地点到乘机航站楼指引标识是否满意？', '19、您对航站楼内指示引导标识是否满意？',
       '19、您对航站楼内电子信息板、广播等设施是否满意？', '19、您对航站楼的卫生状况是否满意？（包括卫生间的条件等）',
       '19、您对航站楼内候机厅座位的数量是否满意？', '19、您对航站楼内安检、空调和照明等设施是否满意？',
       '19、对航站楼内安全保障是否满意？（包括保安巡逻、防盗防爆、 消防等）',
       '19、对航站楼内行李储存设施是否满意？（存取行李方便性、服务时间是否够长）', '19、您对航站楼内的拥挤程度是否满意？',
       '19、您对航站楼候机厅工作人员服务是否满意？', '20、您对机场是否还有其他的建议？']
data['score']=data[scorelist].mean(axis=1)
scoredf=data[scorelist].mean(axis=0).reset_index().rename(columns={'index':'内容',0:'平均分'})
for colname in ['2、性别', '3、您的职业', '4、您是哪里人？', '15、您多久乘坐一次飞机？']:
    for val in set(data[colname]):
        df = data.loc[data[colname] == val, scorelist].mean(axis=0).reset_index().rename(columns={0: val})
        scoredf=pd.merge(scoredf,df,how='left',left_on='内容',right_on='index').drop(columns='index')

scoredf.loc[len(scoredf),:]=scoredf.mean(axis=0)
scoredf.loc[len(scoredf)-1,'内容']='平均'


writer=pd.ExcelWriter(r'D:\Hyder安诚\调查结果数据\枢纽调查\机场满意度summary0713.xlsx')
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
    for i in range(len(passengerdfname)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, passengerdfname[i])

###3.满意度

scoredf.to_excel(writer, sheet_name='satisfaction', startrow=0, startcol=0, index=False)
writer.save()
