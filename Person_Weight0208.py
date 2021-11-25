
import pandas as pd
from ipfn import ipfn
import datetime
pd.options.mode.chained_assignment = None  # default='warn'


rawdatafile=r'C:\调查结果数据\居民出行调查\乌鲁木齐市居民出行调查数据-0918.xlsx'
restrictionfile=r'C:\调查结果数据\居民出行调查\Restrictions0922.xlsx'
hhweightfile=r'C:\调查结果数据\居民出行调查\Results\Results0922\df_Kid_adj.xlsx'
dfppfile=r'C:\调查结果数据\居民出行调查\Results\Results0922\dfpp4.xlsx'


dfpp = pd.read_excel(rawdatafile,sheet_name='成员信息') #info per person
dfpp['就业就学状态']=dfpp['就业就学状态'].replace(['无业','离退休再就业'],['待业','离退休'])
dfpp['居住状态']='常住'
dfpp.loc[(dfpp['非乌鲁木齐户籍（20年初起算）']=='居住乌鲁木齐半年以下'),'居住状态']='暂住'
dfpp.loc[(dfpp['就业就学状态']=='就学') & (dfpp['详细地址']=='新疆财经大学'),'居住状态']='暂住'
dfpp=dfpp.rename(columns={'区域名称':'行政区'})
dfhhweight=pd.read_excel(hhweightfile, sheet_name='df_Kid')
starttime = datetime.datetime.now()
## only calculate the weight of each residents, remove visitors
dfpp1=dfpp.loc[dfpp['居住状态']=='常住',:]
dfpp1=dfpp1.loc[dfpp1['年龄']>=6,:]

print(dfpp1.shape)
dfhhweight['resident_notkid']=dfhhweight['常住人口数']-dfhhweight['不满6周岁人口数']
dfhhweight['有无私家车']=0
dfhhweight.loc[dfhhweight['私家车']>0,'有无私家车']=1
dfpp2=dfpp1[['成员编号','行政区', '街道名称','家庭编号','就业就学状态','性别', '年龄']]
dfpp2=pd.merge(dfpp2,dfhhweight[['家庭编号','扩样街道编号','常住人口数', '不满6周岁人口数', '有无私家车','CensusPop','HHweight4']],how='inner',on='家庭编号')
# calculate rate of population with or without private cars
dfhhweight['weighttotal']=dfhhweight['resident_notkid'] * dfhhweight['HHweight4']
dfpp2['有无常用车辆']=dfpp2['有无私家车'].apply(lambda x:'有' if x>0 else '无')



### calculate total population above 6 per street
dfhhweight['residweighttotal']=dfhhweight['常住人口数']*dfhhweight['HHweight4']
streetpp=dfhhweight.groupby('扩样街道编号')['CensusPop'].mean()
dfhhweight['kidweighttotal']=dfhhweight['不满6周岁人口数']*dfhhweight['HHweight4']
streetkidpp=dfhhweight.groupby('扩样街道编号')['kidweighttotal'].sum()
streetnokidpp=streetpp-streetkidpp
streetnokidpp=streetnokidpp.rename('total')




dfpp3=dfpp2
dfpp3['total']=dfpp3['HHweight4']

# update proportions of age group , sex group , employment group
## read an age proportion table with n rows 3 columns, set max upperbound to 200
## example     :|lowerbound|upperbound|proportion|,
##              |      6   |     18   |    0.12  |
##              |     19   |     33   |   0.263  |
agedf=pd.read_excel(restrictionfile, sheet_name='age')
agedf['range']=''
for row in agedf.index:
    if row < len(agedf)-1:
        agedf.loc[row, 'range'] = str(agedf.loc[row, 'lowerbound']) + '-' + str(agedf.loc[row, 'upperbound'])
    else:
        agedf.loc[row, 'range'] = 'above ' + str(agedf.loc[row, 'lowerbound'])


def age(x):
    agegrp= agedf[(agedf['lowerbound']<=int(x)) & (agedf['upperbound']>=int(x))]
    if len(agegrp) ==1:
            return agegrp.iloc[0,3]
    else:
        return 'unknown'

dfpp3['年龄1']=dfpp3.apply(lambda x: age(x['年龄']), axis=1)
dfpp3=dfpp3[dfpp3['年龄1']!='unknown']
agep=dfpp3.groupby('年龄1')['total'].sum()
for ran in set(dfpp3['年龄1']) :
    agep.loc[ran] = list(agedf.loc[agedf['range']==ran,'proportion'])[0] * streetnokidpp.sum()
print(agep)

## read a sex proportion table with 2 rows 2 columns,column names:sex,proportion, row names:男，女
## example     :| sex |proportion|,
##              |  男 |   0.5175  |
##              |  女 |   0.4825  |
sexdf=pd.read_excel(restrictionfile, sheet_name='sex')
malepop=list(sexdf.loc[sexdf['sex']=='男','proportion'])[0] * streetnokidpp.sum()
femalepop=list(sexdf.loc[sexdf['sex']=='女','proportion'])[0] * streetnokidpp.sum()

sexp=dfpp3.groupby('性别')['total'].sum()
sexp.loc['男'] = malepop
sexp.loc['女'] = femalepop

print(sexp)


## read an employment proportion table with 2 rows 2 columns,
## column names:employment,proportion, row names:'就学', '工作', '离退休再就业', '离退休', '待业'
## example     :| employment |proportion|,
##              |     就学    |   0.136  |
##              |      工作   |   0.548  |
empdf=pd.read_excel(restrictionfile, sheet_name='employ')
empp=dfpp3.groupby('就业就学状态')['total'].sum()
for em in set(dfpp3['就业就学状态']):
    empp.loc[em]=list(empdf.loc[empdf['employment']==em,'proportion'])[0] * streetnokidpp.sum()
print(empp)

###年龄性别比例表格？
## read a sex-age table with  rows 4 columns,
## column names:lowerbound|upperbound| male |female,
## example：       7      |     18   | 0.53 | 0.47
##                 19     |     33   | 0.52 | 0.48
# agesexdf=pd.read_excel(r'D:\Urumqi\成员.xlsx', sheet_name='age-sex')
#   agesexp= dfpp3.groupby(['年龄1','性别'])['total'].sum()
#   agesexdf['range']= ' '
#   for row in agedf.index:
#     if row < len(agedf)-1:
#         agedf.loc[row, 'range'] = str(agedf.loc[row, 'lowerbound']) + '-' + str(agedf.loc[row, 'upperbound'])
#     else:
#         agedf.loc[row, 'range'] = 'above ' + str(agedf.loc[row, 'lowerbound'])
#   for ag in set(dfpp3['年龄1']):
#        agesexp.loc[ag,'男']= list(agesexdf.loc[agesexdf['range']==ag,'男'])[0] * streetnokidpp.sum()
#        agesexp.loc[ag,'女']= list(agesexdf.loc[agesexdf['range']==ag,'女'])[0] * streetnokidpp.sum()
#   aggregates.append(agesexp)
#   dimensions.append(['年龄1',,'性别'])



dfpp4=dfpp3

print("请选择车辆信息表的形式：1：全市；2：分区；3：分街道，请输入数字")
VehTableN=input()
if VehTableN=='1': #only total vehicle of whole city is available
    carpp=dfhhweight.groupby('有无私家车')['weighttotal'].sum()
    carpp=carpp.rename('total')
    aggregates = [streetnokidpp,agep, sexp,empp,carpp]
    dimensions = [['扩样街道编号'],['年龄1'], ['性别'],['就业就学状态'],['有无私家车']]
elif VehTableN=='2': #vehicle per district is available
    carpp=dfhhweight.groupby(['行政区','有无私家车'])['weighttotal'].sum()
    carpp = carpp.rename('total')
    aggregates = [streetnokidpp,agep, sexp, empp, carpp]
    dimensions = [['扩样街道编号'],['年龄1'], ['性别'], ['就业就学状态'], ['行政区','有无私家车']]
elif VehTableN=='3':
    carpp = dfhhweight.groupby(['扩样街道编号', '有无私家车'])['weighttotal'].sum()
    carpp = carpp.rename('total')
    aggregates = [streetnokidpp,agep, sexp, empp, carpp]
    dimensions = [['扩样街道编号'],['年龄1'], ['性别'], ['就业就学状态'], ['扩样街道编号', '有无私家车']]



IPF = ipfn.ipfn(dfpp3, aggregates, dimensions,max_iteration=400)
dfpp4 = IPF.iteration()
aggregates1=[streetnokidpp]
dimensions1=[['扩样街道编号']]
IPF2=ipfn.ipfn(dfpp4, aggregates1, dimensions1,max_iteration=1000)
dfpp4 = IPF2.iteration()


dfpp4['pp_adj']=dfpp4['total']/dfpp4['HHweight4']
print(dfpp4.head())


dfpp4.to_excel(dfppfile, sheet_name='dfpp',index=False)
endtime = datetime.datetime.now()
print("person weight adjustment operation time")
print((endtime - starttime).seconds)
pp=dfpp4['total'].sum()
agepp=dfpp4.groupby('年龄1')['total'].sum()/pp
sexpp=dfpp4.groupby('性别')['total'].sum()/pp
emply=dfpp4.groupby('就业就学状态')['total'].sum()/pp
print(pp,streetnokidpp.sum(),streetpp.sum(),streetkidpp.sum())
print(agepp)
print(sexpp)
print(emply)
##test the operating time and at least how many iterations are needed to reach the accuracy requirements
"""
import datetime

for i in range(1,6):
    print(i)
    starttime = datetime.datetime.now()
    IPFi=ipfn.ipfn(dfpp3, aggregates, dimensions,max_iteration= i*100)
    dfppi=IPFi.iteration()
    pp = dfppi['total'].sum()
    agepp = dfppi.groupby('年龄1')['total'].sum() / pp
    sexpp = dfppi.groupby('性别')['total'].sum() / pp
    emply = dfppi.groupby('就业就学状态')['total'].sum() / pp
    endtime = datetime.datetime.now()
    print((endtime - starttime).seconds)
    print(pp)
    print(agepp)
    print(sexpp)
    print(emply)
"""
