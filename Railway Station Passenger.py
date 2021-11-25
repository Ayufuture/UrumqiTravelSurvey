import pandas as pd
import re
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from shapely.geometry import Point,Polygon,shape
pd.options.mode.chained_assignment = None  # default='warn'
######################火车站满意度调查结果分析#########################################################
"""
客运站旅客个人信息	根据客流规模扩样，性别/年龄/来自哪里
客运站旅客出行信息	根据客流规模扩样，起终点/到达客运站的交通方式/时耗/出行目的/候车时间/同行人数
客运站旅客出行意愿信息	根据客流规模扩样，乘车频率/选择乘车的理由
客运站满意度	根据客流规模扩样，总体/分项目
"""
data=pd.read_excel(r'C:\调查结果数据\枢纽调查\火车站枢纽问卷调查数据0615.xlsx',sheet_name='Sheet1')
dictionary=pd.read_excel(r'C:\调查结果数据\枢纽调查\火车站枢纽问卷调查数据0615.xlsx',sheet_name='代号')
#data['mark']='N'
#data.loc[(data['您此次出行的起点：']==2) &(data['您从火车站去哪儿？']==2) & (data['出行的交通方式：']==12),'mark']='Y'
#data=data[data['mark']=='N'].drop(columns=['mark'])
passengerdf=[]
passengerdfname=['性别','职业','籍贯','出行方式','出行目的','乘车频率','选择火车的原因','同行人数','进入候车厅人数','候车时间','起终点','到车站时耗','分地区到车站时耗']
for i in range(1,8):
    colname=dictionary.columns[i]
    colname2=passengerdfname[i-1]
    data=pd.merge(data,dictionary[['代号',colname]],how='left',left_on=colname,right_on='代号').drop(columns=['代号',colname+'_x'])
    data=data.rename(columns={colname+'_y':colname})
    sum_df=data.groupby(colname)['序号'].count().reset_index().rename(columns={'序号':'人数'})
    sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
    df_sort = pd.DataFrame({colname2: list(dictionary[colname].dropna())})
    sort_mapping = df_sort.reset_index().set_index(colname2)
    sum_df['num'] = sum_df[colname].map(sort_mapping['index'])
    sum_df = sum_df.sort_values('num').drop(columns=['num'])
    print(sum_df)
    passengerdf.append(sum_df)
for colname in ['(1)您从起点到火车站，同行有___人，包括本人', '(2)您的同伴中总共有\t___人进入候车厅？']:
    data[colname]=data[colname].apply(lambda x: '>=5人' if x>=5 else str(x)+'人')
    sum_df=data.groupby(colname)['序号'].count().reset_index().rename(columns={'序号':'人数'})
    sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
    passengerdf.append(sum_df)

##候车时间
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
data['候车时间']=data['您从进安检开始总共要等候多久，才可以乘车？（分钟）'].apply(lambda x: waitingfun(x))
sum_df=data.groupby('候车时间')['序号'].count().reset_index().rename(columns={'序号':'人数'})
sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
df_sort = pd.DataFrame({'候车时间': ['30min以内','30-60min','60-90min','90-120min','120min以上']})
sort_mapping = df_sort.reset_index().set_index('候车时间')
sum_df['num'] = sum_df['候车时间'].map(sort_mapping['index'])
sum_df = sum_df.sort_values('num').drop(columns=['num'])
sum_df=sum_df.append([{'候车时间':'平均（min）','人数':round(data['您从进安检开始总共要等候多久，才可以乘车？（分钟）'].mean(),1)}])
passengerdf.append(sum_df)

##起终点
#load shapefile and do spatial join
Province=gpd.read_file(r'C:/全国区划/省.shp')
Province=Province.to_crs(4326)
Region=gpd.read_file(r'C:/Test GIS/District/District.shp',encoding='gbk')
Region=Region.to_crs(4326)

City=gpd.read_file(r'C:/全国区划/市.shp')
City=City.to_crs(4326)
City=City[City['省代码']==650000]

origin = gpd.GeoDataFrame(data[data['您此次出行的起点：']==2], geometry = gpd.points_from_xy(data.loc[data['您此次出行的起点：']==2,'来自城区外X'], data.loc[data['您此次出行的起点：']==2,'来自城区外Y'], crs="EPSG:4326"))
desti = gpd.GeoDataFrame(data[data['您从火车站去哪儿？']==2], geometry = gpd.points_from_xy(data.loc[data['您从火车站去哪儿？']==2,'去往城区外X'], data.loc[data['您从火车站去哪儿？']==2,'去往城区外Y'], crs="EPSG:4326"))


Origin_Province = gpd.sjoin(origin,Province,how="left",op='within').rename(columns={'名称':'省'})
Origin_City=gpd.sjoin(origin,City,how='left',op='within').rename(columns={'名称':'市'})
Origin_Province_City=pd.merge(Origin_Province,Origin_City[['序号','市']],how='left',on='序号')
Origin_Province_City=Origin_Province_City[['序号','来自城区外X', '来自城区外Y', 'geometry','省','市']]
Origin_Province_City=Origin_Province_City.rename(columns={'省':'Province_O','市':'District_O'})

Desti_Province = gpd.sjoin(desti,Province,how="left",op='within')
Desti_City=gpd.sjoin(desti,City,how='left',op='within')
Desti_Province_City=pd.merge(Desti_Province,Desti_City[['序号','市']],how='left',on='序号')
Desti_Province_City=Desti_Province_City[['序号', '去往城区外X', '去往城区外Y', 'geometry','省','市']]
Desti_Province_City=Desti_Province_City.rename(columns={'省':'Province_D','市':'District_D'})

data=pd.merge(data,Origin_Province_City[['序号','Province_O','District_O']],how='left',on='序号')
data=pd.merge(data,Desti_Province_City[['序号','Province_D','District_D']],how='left',on='序号')
data['Province_O']=data['Province_O'].fillna('NA')
data['Province_D']=data['Province_D'].fillna('NA')
data['District_O']=data['District_O'].fillna('NA')
data['District_D']=data['District_D'].fillna('NA')

data['起点行政区']=''
data['终点行政区']=''
for i in data.index:
    if data.loc[i,'您此次出行的起点：']==1:
        address=data.loc[i,'来自城区内详细地址']
        if '乌鲁木齐市' in str(address) and '区' in str(address):
            data.loc[i,'起点行政区'] = re.split('[区县]', str(address[5:]))[0] + '区'
        elif '乌鲁木齐市' in str(address) and '县' in str(address):
            data.loc[i,'起点行政区'] = re.split('[区县]', str(address[5:]))[0] + '县'
        else:
            data.loc[i, '起点行政区'] = '其他地区'
    elif data.loc[i,'您此次出行的起点：']==2:
        if '新疆' in data.loc[i,'Province_O']:
            data.loc[i,'起点行政区']=data.loc[i,'District_O']
        else:
            data.loc[i, '起点行政区'] = data.loc[i,'Province_O']


    if data.loc[i,'您从火车站去哪儿？']==1:
        address=data.loc[i,'去往城区内详细地址']
        if '乌鲁木齐市' in str(address) and '区' in str(address):
            data.loc[i,'终点行政区'] = re.split('[区县]', str(address[5:]))[0] + '区'
        elif '乌鲁木齐市' in str(address) and '县' in str(address):
            data.loc[i,'起点行政区'] = re.split('[区县]', str(address[5:]))[0] + '县'
        else:
            data.loc[i, '终点行政区'] = '其他地区'
    elif data.loc[i,'您从火车站去哪儿？']==2:
        if '新疆' in data.loc[i, 'Province_D']:
            data.loc[i, '终点行政区'] = data.loc[i, 'District_D']
        else:
            data.loc[i, '终点行政区'] = data.loc[i, 'Province_D']

print(set(data['起点行政区']),set(data['终点行政区']))
data['起点地区']=data['起点行政区'].apply(lambda x: '乌鲁木齐市'if x in ['天山区', '头屯河区', '新市区', '水磨沟区','沙依巴克区', '米东区','达坂城区','乌鲁木齐县'] else x)
data['终点地区']=data['终点行政区'].apply(lambda x: '乌鲁木齐市'if x in ['天山区', '头屯河区', '新市区', '水磨沟区','沙依巴克区', '米东区','达坂城区','乌鲁木齐县'] else x)
sum_od=data.groupby(['起点地区','终点地区'])['序号'].count().reset_index().rename(columns={'序号':'人数'}).pivot(index='起点地区',columns='终点地区',values='人数').reset_index().fillna(0)
sum_od=sum_od[['起点地区', '乌鲁木齐市', '新疆其他地区', '新疆外']]
df_sort=pd.DataFrame({'起点地区':['乌鲁木齐市','新疆其他地区', '新疆外']})
sort_mapping = df_sort.reset_index().set_index('起点地区')
sum_od['num'] = sum_od['起点地区'].map(sort_mapping['index'])
sum_od=sum_od.sort_values('num').drop(columns=['num'])
print(sum_od)
passengerdf.append(sum_od)

###到车站时耗
data['到车站时耗']=data['您从起点到达火车站用了多长时间？（分钟）'].apply(lambda x: waitingfun(x))
sum_df=data.groupby('到车站时耗')['序号'].count().reset_index().rename(columns={'序号':'人数'})
sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
df_sort = pd.DataFrame({'到车站时耗': ['30min以内','30-60min','60-90min','90-120min','120min以上']})
sort_mapping = df_sort.reset_index().set_index('到车站时耗')
sum_df['num'] = sum_df['到车站时耗'].map(sort_mapping['index'])
sum_df = sum_df.sort_values('num').drop(columns=['num'])
sum_df=sum_df.append([{'到车站时耗':'平均（min）','人数':round(data['您从起点到达火车站用了多长时间？（分钟）'].mean(),1)}])
passengerdf.append(sum_df)


sum_df_d=data.groupby(['起点行政区','到车站时耗'])['序号'].count().reset_index().rename(columns={'序号':'人数'})
sum_df_d=sum_df_d.pivot(index='到车站时耗',columns='起点行政区',values='人数').reset_index().fillna(0)
sum_df_d=sum_df_d[['到车站时耗','天山区', '头屯河区', '新市区', '水磨沟区','沙依巴克区', '米东区', '新疆其他地区', '新疆外']]
rown=len(sum_df_d)
sum_df_d.loc[rown,'到车站时耗']='平均'
for col in sum_df_d.columns[1:]:
    sum_df_d[col]=round(100*sum_df_d[col]/sum_df_d[col].sum(),2)
    sum_df_d.loc[rown,col]=round(data.loc[data['起点行政区']==col,'您从起点到达火车站用了多长时间？（分钟）'].mean(),2)
df_sort = pd.DataFrame({'到车站时耗': ['30min以内','30-60min','60-90min','90-120min','120min以上','平均']})
sort_mapping = df_sort.reset_index().set_index('到车站时耗')
sum_df_d['num'] = sum_df_d['到车站时耗'].map(sort_mapping['index'])
sum_df_d = sum_df_d.sort_values('num').drop(columns=['num'])
passengerdf.append(sum_df_d)


satisfy=[]
satisfyname=[]
scorelist=['从您下车地点到火车站步行交通环境是否便捷？', '从您下车地点到火车站指引标识是否满意？', '您对车站内指示引导标识是否满意？',
       '您对车站内电子信息板、广播等设施是否满意？', '您对车站内的卫生状况是否满意？', '您对候车室座位的数量是否满意？',
       '您对车站内安检、空调和照明等设施是否满意？', '您对车站内安全保障是否满意？', '您对车站内行李储存设施是否满意？',
       '车站对节假日客流的安排您是否满意？', '您对候车室的拥挤程度是否满意？', '您对车站候车室工作人员服务是否满意？']
data['score']=data[scorelist].mean(axis=1)
scoredf=data[scorelist].mean(axis=0).reset_index().rename(columns={'index':'内容',0:'平均分'})
for colname in ['您的性别：', '您的职业：', '您是哪里人：', '您多久乘坐一次火车？']:
    for val in set(data[colname]):
        df = data.loc[data[colname] == val, scorelist].mean(axis=0).reset_index().rename(columns={0: val})
        scoredf=pd.merge(scoredf,df,how='left',left_on='内容',right_on='index').drop(columns='index')

scoredf.loc[len(scoredf),:]=scoredf.mean(axis=0)
scoredf.loc[len(scoredf)-1,'内容']='平均'


writer=pd.ExcelWriter(r'D:\调查结果数据\火车站满意度summary0622.xlsx')
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


#### OD Plot




centroid=pd.read_excel(r'C:/全国区划/Centroid.xlsx')
centroid=centroid[centroid['级别']!='乌鲁木齐行政区']


for i in data.index:
    if data.loc[i,'起点地区']=='新疆外':
        data.loc[i,'起点地区']=data.loc[i,'Province_O']
    elif data.loc[i,'起点地区']=='新疆其他地区':
        data.loc[i,'起点地区']=data.loc[i,'District_O']
    if data.loc[i,'终点地区']=='新疆外':
        data.loc[i,'终点地区']=data.loc[i,'Province_D']
    elif data.loc[i,'终点地区']=='新疆其他地区':
        data.loc[i,'终点地区']=data.loc[i,'District_D']


sum_odplot=data.groupby(['起点地区','终点地区'])['序号'].count().reset_index().rename(columns={'序号':'人数'})
sum_odplot=pd.merge(sum_odplot,centroid,how='left',left_on='起点地区',right_on='名称').rename(columns={'Long':'Long_x','Lat':'Lat_x'})
sum_odplot=pd.merge(sum_odplot,centroid,how='left',left_on='终点地区',right_on='名称').rename(columns={'Long':'Long_y','Lat':'Lat_y'})
fig = plt.figure()
ax = plt.subplot(111)
plt.sca(ax)
# plot administration shp
Province.plot(ax=ax, edgecolor=(0, 0, 0, 1), facecolor=(0, 0, 0, 0), linewidths=0.5)
City.plot(ax=ax,edgecolor=(0,0,0,1),facecolor=(0,0,0,0),linewidths=0.35)
Region.plot(ax=ax,edgecolor=(0,0,0,1),facecolor=(0,0,0,0),linewidths=0.15)
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
