import pandas as pd
import numpy as np
import re


pd.options.mode.chained_assignment = None  # default='warn'
######################公交满意度调查结果分析#########################################################
data=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\乌鲁木齐市公交满意度调查数据06.15.xlsx',sheet_name='Sheet1')
dictionary=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\乌鲁木齐市公交满意度调查数据06.15.xlsx',sheet_name='代号')
dictionary=dictionary.iloc[:,0:49]
colnamelist=dictionary.columns[1:]

for colname in colnamelist:
    data=pd.merge(data,dictionary[['代号',colname]],how='left',left_on=colname,right_on='代号').drop(columns=['代号',colname+'_x'])
    data=data.rename(columns={colname+'_y':colname})

"""
乘客个人特征:	性别，年龄，收入，职业，月乘坐地铁次数，支付方式
乘客出行特征: 目的结构、总体及分站点的接驳方式和耗时
公交满意度:	整体满意度，子项目满意度，分性别、年龄、职业、换乘次数的满意度
"""

#各站点受调查人数
sum_stop=data.groupby('调查站点')['序号'].count().reset_index().rename(columns={'序号':'人数'})

#乘客个人特征
passengerdf=[]
passengerdfname=['性别','驾照','是否为本市户籍','家庭月收入','付费方式','乘车频率','月公交支出','年龄','各站点受调查人数']
colnamelistp=[ '1.性别：','3.是否有驾照', '4.是否为本市户籍人员', '您家庭的月经济收入:',
                 'II.您使用哪种付费方式：','4.3乘车频率']
for i in range(len(colnamelistp)) :
    colname=colnamelistp[i]
    colname2=passengerdfname[i]
    sum_df=data.groupby(colname)['序号'].count().reset_index().rename(columns={'序号':'人数',colname:colname2})
    sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
    df_sort = pd.DataFrame({colname2: list(dictionary[colname].dropna())})
    sort_mapping = df_sort.reset_index().set_index(colname2)
    sum_df['num'] = sum_df[colname2].map(sort_mapping['index'])
    sum_df = sum_df.sort_values('num').drop(columns=['num'])
    print(sum_df)
    passengerdf.append(sum_df)

def fare_group(x):
    if x>0 and x<=50:
        return 'under 50RMB'
    elif x>50 and x<=100:
        return '50-100RMB'
    elif x>100 and x<=150:
        return '100-150RMB'
    elif x>150 and x<=200:
        return '150-200RMB'
    elif x>200:
        return 'above 200RMB'
    else:
        return 'Free'

data['月公交支出'] =data['(1)您一个月花在公交上的支出是___元人民币。'].apply(lambda x:fare_group(x))
sum_df=data.groupby('月公交支出')['序号'].count().reset_index().rename(columns={'序号':'人数'})
sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
age_sort=pd.DataFrame({'月公交支出':['Free','under 50RMB','50-100RMB','100-150RMB','150-200RMB','above 200RMB']})
sort_mapping = age_sort.reset_index().set_index('月公交支出')
sum_df['num'] = sum_df['月公交支出'].map(sort_mapping['index'])
sum_df=sum_df.sort_values('num').drop(columns=['num'])
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

data['年龄'] =data['2.年龄：___岁'].apply(lambda x:age_group(x))
sum_df=data.groupby('年龄')['序号'].count().reset_index().rename(columns={'序号':'人数'})
sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
age_sort=pd.DataFrame({'年龄':['6-18', '19-33', '34-48','49-63','above 64']})
sort_mapping = age_sort.reset_index().set_index('年龄')
sum_df['age_num'] = sum_df['年龄'].map(sort_mapping['index'])
sum_df=sum_df.sort_values('age_num').drop(columns=['age_num'])
print(sum_df)
passengerdf.append(sum_df)
passengerdf.append(sum_stop)

#乘客出行特征

tripdf=[]
tripdfname=['本次换乘次数','可替代的交通方式','出行目的','公共自行车','选择公交的原因','最近公交站步行距离','出发地—目的地']
colnamelistt=['此次出行您需要换乘___次。(换乘包括：公交车和公交车的换乘；公交车和其他交通工具之间的换乘，如小汽车、自行车等)',
               '5.本次出行，若不使用公交，您当时可以采用哪种交通方式？(可选择多项)','8.出行目的:', '如果换乘公交可以使用公共自行车，且使用费用低廉，您是否愿意使用？','您为什么选择公交车？(可选择多项)']
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
    if colname=='本次换乘次数':
        sum_df=sum_df.append([{colname:'换乘系数','人数':round(data[colname2].mean()+1,2)}])
    print(sum_df)
    tripdf.append(sum_df)

def walk_group(x):
    if  x<5:
        return '<5min'
    elif x>=5 and x<=10:
        return '5 〜10min'
    elif x>10 and x<=20:
        return '10 〜20min'
    elif x>20 and x<=30:
        return '20 〜30min'
    elif x>30:
        return '>30min'

data['最近公交站步行距离'] =data['1.您从家到最近公交站一般需要步行_分钟'].apply(lambda x:walk_group(x))
sum_df=data.groupby('最近公交站步行距离')['序号'].count().reset_index().rename(columns={'序号':'人数'})
sum_df['pct']=round(100*sum_df['人数']/sum_df['人数'].sum(),2)
df_sort = pd.DataFrame({'最近公交站步行距离': ['<5min','5 〜10min','10 〜20min','20 〜30min','>30min']})
sort_mapping = df_sort.reset_index().set_index('最近公交站步行距离')
sum_df['num'] = sum_df['最近公交站步行距离'].map(sort_mapping['index'])
sum_df = sum_df.sort_values('num').drop(columns=['num'])
sum_df=sum_df.append([{'最近公交站步行距离':'平均（min）','人数':round(data['1.您从家到最近公交站一般需要步行_分钟'].mean(),1)}])
print(sum_df)
tripdf.append(sum_df)

def districtfunc(address):
    if '乌鲁木齐市' in str(address) and '区' in str(address):
        district=re.split('[区县]',str(address[5:]))[0]+'区'
    else:
        district='其他'
    return district

data['出发行政区']=data['出发详细地址'].apply(lambda x:districtfunc(x))
data['到达行政区']=data['到达详细地址'].apply(lambda x:districtfunc(x))

bus_sum_od=data.groupby(['出发行政区','到达行政区'])['序号'].count().reset_index().rename(columns={'序号':'人数'}).pivot(index='出发行政区',columns='到达行政区',values='人数').reset_index().fillna(0)
bus_sum_od=bus_sum_od[['出发行政区', '天山区', '头屯河区', '新市区', '水磨沟区','沙依巴克区', '米东区', '其他']]
df_sort=pd.DataFrame({'出发行政区':['天山区','头屯河区','新市区','水磨沟区','沙依巴克区','米东区','其他']})
sort_mapping = df_sort.reset_index().set_index('出发行政区')
bus_sum_od['num'] = bus_sum_od['出发行政区'].map(sort_mapping['index'])
bus_sum_od=bus_sum_od.sort_values('num').drop(columns=['num'])
print(bus_sum_od)
tripdf.append(bus_sum_od)

#满意度
weight=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\乌鲁木齐市公交满意度调查数据06.15.xlsx',sheet_name='满意度权重')
#score=pd.DataFrame({'choice':[1,2,3,4,5],'score':[10,8,6,4,2]})
data_score=pd.read_excel(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\乌鲁木齐市公交满意度调查数据06.15.xlsx',sheet_name='Sheet1')
for colname in weight['三级分项']:
    data_score[colname]=data_score[colname].apply(lambda x: 12-2*x)
person_score=pd.DataFrame({'序号':data['序号'],'行政区':data['行政区'],'性别':data['1.性别：'],'年龄':data['年龄'],'有无驾照':data['3.是否有驾照'],
                           '是否本市户籍':data['4.是否为本市户籍人员'],'职业':data['6.您的职业'],'家庭月收入':data['您家庭的月经济收入:'],
'候车时间长度':0,'换乘便捷度':0,'服务态度':0,'出行信息服务':0,'乘车舒适度':0,'候车环境':0,'车内卫生环境':0,'对公交系统的评价':0,'总体':0
})
for i in person_score.index:
    overall=0
    for row in ['候车时间长度','换乘便捷度','服务态度','出行信息服务','乘车舒适度','候车环境','车内卫生环境','对公交系统的评价']:
        collist=list(weight.loc[weight['二级分项']==row,'三级分项'])
        wght=list(weight.loc[weight['二级分项']==row,'二级权重'])[0]
        person_score.loc[i,row]=data_score.loc[i, collist].mean()
        overall=overall+data_score.loc[i, collist].mean()*wght
    person_score.loc[i,'总体']=overall

sum_score=pd.DataFrame({'三级分项':weight['三级分项'],'三级均分':0,'二级分项':weight['二级分项'],'二级均分':0})
for j in sum_score.index:
    colname1=sum_score.loc[j,'三级分项']
    sum_score.loc[j,'三级均分']=data_score[colname1].mean()
    colname2=sum_score.loc[j,'二级分项']
    sum_score.loc[j,'二级均分']=person_score[colname2].mean()
sum_score['三级均分']=round(sum_score['三级均分'],2)
sum_score['二级均分']=round(sum_score['二级均分'],2)


collist1=['行政区','1.性别：','3.是否有驾照','4.是否为本市户籍人员','6.您的职业','您家庭的月经济收入:']
collist2=['行政区','性别','有无驾照','是否本市户籍','职业','家庭月收入']
satisfydf=[]
for k in range(len(collist1)):
    colname1=collist1[k]
    colname2=collist2[k]
    sum_df=person_score.groupby(colname2)['总体'].mean().reset_index().rename(columns={'总体':'总体得分'})
    if colname2 in dictionary.columns:
        df_sort = pd.DataFrame({colname2: list(dictionary[colname1].dropna())})
        sort_mapping = df_sort.reset_index().set_index(colname2)
        sum_df['num'] = sum_df[colname2].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])
    if colname1=='行政区':
        df_sort = pd.DataFrame({'行政区': ['天山区', '头屯河区', '新市区', '水磨沟区', '沙依巴克区', '米东区', '其他']})
        sort_mapping = df_sort.reset_index().set_index('行政区')
        sum_df['num'] = sum_df['行政区'].map(sort_mapping['index'])
        sum_df = sum_df.sort_values('num').drop(columns=['num'])

    sum_df=sum_df.append([{colname2:'平均','总体得分':person_score['总体'].mean()}])
    sum_df['总体得分'] = round(sum_df['总体得分'], 2)
    print(sum_df)
    satisfydf.append(sum_df)

sum_df=person_score.groupby('年龄')['总体'].mean().reset_index().rename(columns={'总体':'总体得分'})
df_sort = pd.DataFrame({'年龄':['6-18', '19-33', '34-48','49-63','above 64']})
sort_mapping = df_sort.reset_index().set_index('年龄')
sum_df['num'] = sum_df['年龄'].map(sort_mapping['index'])
sum_df = sum_df.sort_values('num').drop(columns=['num'])
sum_df=sum_df.append([{'年龄':'平均','总体得分':person_score['总体'].mean()}])
sum_df['总体得分']=round(sum_df['总体得分'],2)
print(sum_df)
satisfydf.append(sum_df)
satisfydf.append(sum_score)
collist2.append('年龄')
collist2.append('分项满意度得分')

satisfydf.append(data.groupby(['3.2可容忍候车时间'])['序号'].count().reset_index())
satisfydf.append(data.groupby(['4.3乘车频率'])['序号'].count().reset_index())
collist2.append('可容忍候车时间')
collist2.append('乘车频率')

import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = [u'SimHei']
plt.rcParams['axes.unicode_minus'] = False
colorlist=['red','blue','green','purple','orange','gold', 'yellowgreen', 'lightcoral', 'lightskyblue']
for df in satisfydf[0:-1]:
    fz=10
    ave_score=df.iloc[-1,1]
    y=np.array(df.iloc[0:-1,1])
    x=np.arange(len(y))
    plt.ylim((70,95))
    plt.bar(x,y,alpha=0.6, width=0.5,color='blue',tick_label=np.array(df.iloc[0:-1,0]))
    if max(x)>8:
        plt.xticks(x,np.array(df.iloc[0:-1,0]),rotation=90)
        fz=8
    plt.axhline(y=ave_score,color='black',ls="--")
    plt.text(max(x)+0.5,ave_score,'平均:'+str(ave_score), fontsize=fz)
    for a, b in zip(x, y):
        plt.text(a, b + 0.05, b, ha='center', va='bottom', fontsize=fz)
    plt.title('分'+df.columns[0]+'满意度', fontsize=15)
    figname = r'D:/Hyder安诚/调查结果数据/公交满意度调查结果分析/' + df.columns[0] + '满意度.png'
    plt.savefig(figname, bbox_inches='tight')
    plt.close()

for ind in set(sum_score['二级分项']):
    sum_scorei=sum_score.loc[sum_score['二级分项']==ind,:]
    ave_score=sum_scorei.iloc[0,3]
    y=np.array(sum_score.loc[sum_score['二级分项']==ind,'三级均分'])
    x=np.arange(len(y))
    plt.bar(x, y, alpha=0.6, width=0.5, color='blue', tick_label=np.array(sum_scorei['三级分项']))
    if max(x)>=4:
        plt.xticks(x,np.array(sum_scorei['三级分项']),rotation=90)
    plt.axhline(y=ave_score, color='black', ls="--")
    plt.text(max(x) + 0.5, ave_score, '单项得分:' + str(ave_score), fontsize=10)
    for a, b in zip(x, y):
        plt.text(a-0.25, b + 0.05, b,  fontsize=10)
    plt.title(ind+'满意度', fontsize=15)
    figname = r'D:/Hyder安诚/调查结果数据/公交满意度调查结果分析/' + ind + '子项满意度.png'
    plt.savefig(figname, bbox_inches='tight')
    plt.close()

sum_scorej=sum_score[['二级分项','二级均分']].drop_duplicates()
y=np.array(sum_scorej['二级均分'])
x=np.arange(len(y))
plt.bar(x, y, alpha=0.6, width=0.5, color='blue')
plt.xticks(x,np.array(sum_scorej['二级分项']),rotation=90)
for a, b in zip(x, y):
    plt.text(a-0.25, b+0.05, b, fontsize=10)
plt.title('二级分项满意度', fontsize=15)
figname = r'D:/Hyder安诚/调查结果数据/公交满意度调查结果分析/二级分项满意度.png'
plt.savefig(figname, bbox_inches='tight')
plt.close()

#分区二级指标满意度
district_score=person_score.groupby('行政区').agg(
si1=pd.NamedAgg(column='候车时间长度',aggfunc='mean'),
si2=pd.NamedAgg(column='换乘便捷度',aggfunc='mean'),
si3=pd.NamedAgg(column='服务态度',aggfunc='mean'),
si4=pd.NamedAgg(column='出行信息服务',aggfunc='mean'),
si5=pd.NamedAgg(column='乘车舒适度',aggfunc='mean'),
si6=pd.NamedAgg(column='候车环境',aggfunc='mean'),
si7=pd.NamedAgg(column='车内卫生环境',aggfunc='mean'),
si8=pd.NamedAgg(column='对公交系统的评价',aggfunc='mean'),
).reset_index().rename(columns={'si1':'候车时间长度','si2':'换乘便捷度','si3':'服务态度', 'si4':'出行信息服务', 'si5':'乘车舒适度',
                                'si6':'候车环境', 'si7':'车内卫生环境', 'si8':'对公交系统的评价'})
for col in district_score.columns[1:]:
    district_score[col]=round(district_score[col],2)
    y=np.array(district_score[col])
    x=np.arange(len(y))
    plt.bar(x,y, alpha=0.6, width=0.5, color='blue',tick_label=np.array(district_score['行政区']))
    for a, b in zip(x, y):
        plt.text(a - 0.25, b + 0.05, b, fontsize=10)
    plt.title(col+'分区满意度',fontsize=15)
    figname = r'D:/Hyder安诚/调查结果数据/公交满意度调查结果分析/分区'+col+'满意度.png'
    plt.savefig(figname, bbox_inches='tight')
    plt.close()

for df in passengerdf[0:-1]:
    labels = np.array(df.iloc[:,0])
    sizes = np.array(df['人数'])
    colors = colorlist[0:len(labels)]
    # Plot
    plt.pie(sizes,  labels=labels, autopct='%1.1f%%', shadow=False, startangle=140)
    plt.axis('equal')
    plt.title(df.columns[0]+'比例',fontsize=15)
    plt.show()
    figname = r'D:/Hyder安诚/调查结果数据/公交满意度调查结果分析/乘客' + df.columns[0]+'比例.png'
    plt.savefig(figname, bbox_inches='tight')
    plt.close()









###save to excel###
writer=pd.ExcelWriter(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\公交满意度summary0729.xlsx')
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
if len(satisfydf)>0:
    startr = 1
    rowlist = [0]
    for i in range(len(satisfydf)):
        satisfydf[i].to_excel(writer, sheet_name='satisfaction', startrow=startr, startcol=0, index=False)
        r, c = satisfydf[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['satisfaction']
    for i in range(len(satisfydf)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, collist2[i])

writer.save()

###summarize how many people selected satisfied or not satisfied
collist1=['行政区','1.性别：','3.是否有驾照','4.是否为本市户籍人员','6.您的职业','您家庭的月经济收入:']
collist2=['行政区','性别','有无驾照','是否本市户籍','职业','家庭月收入','总体']
satisfydf=[]
for k in range(len(collist1)):
    colname1=collist1[k]
    colname2=collist2[k]
    sum_df=data.groupby(['10.3对公交服务总体的满意度',colname1])['序号'].count().reset_index().rename(columns={'10.3对公交服务总体的满意度':'总体满意度'})
    sum_df=sum_df.pivot(index='总体满意度',columns=colname1,values='序号').reset_index()
    df_sort = pd.DataFrame({'总体满意度': ['很满意', '满意', '可以接受', '不满意', '很不满意']})
    sort_mapping = df_sort.reset_index().set_index('总体满意度')
    sum_df['num'] = sum_df['总体满意度'].map(sort_mapping['index'])
    sum_df = sum_df.sort_values('num').drop(columns=['num'])
    sum_df.loc[len(sum_df),:]=sum_df[(sum_df['总体满意度']=='很满意')|(sum_df['总体满意度']=='满意')].sum(axis=0)
    sum_df.loc[len(sum_df)-1,'总体满意度']='很满意&满意'
    print(sum_df)
    satisfydf.append(sum_df)

sum_df=data.groupby(['10.3对公交服务总体的满意度'])['序号'].count().reset_index().rename(columns={'10.3对公交服务总体的满意度':'总体满意度'})
df_sort = pd.DataFrame({'总体满意度': ['很满意', '满意', '可以接受', '不满意', '很不满意']})
sort_mapping = df_sort.reset_index().set_index('总体满意度')
sum_df['num'] = sum_df['总体满意度'].map(sort_mapping['index'])
sum_df = sum_df.sort_values('num').drop(columns=['num'])
sum_df.loc[len(sum_df),:]=sum_df[(sum_df['总体满意度']=='很满意')|(sum_df['总体满意度']=='满意')].sum(axis=0)
sum_df.loc[len(sum_df)-1,'总体满意度']='很满意&满意'
print(sum_df)
satisfydf.append(sum_df)

writer=pd.ExcelWriter(r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\公交满意度summary0728.xlsx')
if len(satisfydf)>0:
    startr = 1
    rowlist = [0]
    for i in range(len(satisfydf)):
        satisfydf[i].to_excel(writer, sheet_name='satisfaction', startrow=startr, startcol=0, index=False)
        r, c = satisfydf[i].shape
        rowlist.append(startr + r + 2)
        startr = startr + r + 3
    sheet1 = writer.sheets['satisfaction']
    for i in range(len(satisfydf)):
        startr2 = rowlist[i]
        sheet1.write(startr2, 0, collist2[i])

writer.save()