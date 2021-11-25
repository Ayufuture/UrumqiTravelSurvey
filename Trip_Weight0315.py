import numpy as np
import pandas as pd
from ipfn import ipfn
import datetime
pd.options.mode.chained_assignment = None  # default='warn'

## peak hour definition: 8:00-9:59 AM Peak, 19:00-19:59 PM Peak, 10:00-18:59: daytime, 20:00-7:59: nighttime
## travel pattern grouping:
## create following summary table (Y: trip in a certain period; N: no trip in that period; 17 rows):
## am	pm	day	night	headcount
## Y	Y	N	N	    5234
## N	N	Y	N	    5109
## N	Y	N	Y	    3147
## Y	N	Y	N	    3133
## N	N	Y	Y	    2851
## sort the table by headcount, ignore the group with no trip (N N N N)
## starting naming group with largest headcount,
## and adjust the weights of the largest groups

# starting with pattern with most people
rawdatafile=r'C:\调查结果数据\居民出行调查\乌鲁木齐市居民出行调查数据-0918.xlsx'
restrictionfile=r'C:\调查结果数据\居民出行调查\Restrictions0922.xlsx'
hhweightfile=r'C:\调查结果数据\居民出行调查\Results\Results0922\df_Kid_adj.xlsx'
dfppfile=r'C:\调查结果数据\居民出行调查\Results\Results0922\dfpp4.xlsx'
dfppcarfile=r'C:\调查结果数据\居民出行调查\Results\Results0922\dfpp_car.xlsx'
tazreference=r'C:\调查结果数据\居民出行调查\TAZReference.xlsx'
dfpp = pd.read_excel(dfppfile, sheet_name='dfpp') #info per person
dftrip = pd.read_excel(rawdatafile, sheet_name='出行信息')
dftrip=dftrip.rename(columns={'出发时间（24小时制）':'出发时间','到达时间（24小时制）':'到达时间'})
TAZrefer=pd.read_excel(tazreference,sheet_name='小区大区对照表')
dftrip=dftrip.merge(TAZrefer[['小区','大区']],how='left',left_on='TAZ_O',right_on='小区').rename(columns={'大区':'LZ_O'})
dftrip=dftrip.drop('小区',axis=1)
dftrip=dftrip.merge(TAZrefer[['小区','大区']],how='left',left_on='TAZ_D',right_on='小区').rename(columns={'大区':'LZ_D'})
dftrip=dftrip.drop('小区',axis=1)


if 'hour' not in dftrip.columns:
    dftrip['hour'] = dftrip['出发时间'].apply(lambda x: int(str(x).split(':')[0]))


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
if 'period' not in dftrip.columns:
    dftrip['period'] = dftrip['hour'].apply(lambda x: periodfun(x))


appendtrip=pd.read_excel(rawdatafile,sheet_name='appendtrips')
dftrip=pd.concat([dftrip,appendtrip],ignore_index=True)


columnlist=['第一种交通方式', '第二种交通方式', '第三种交通方式', '第四种交通方式', '第五种交通方式']
dftrip = dftrip.replace('私人小汽车(自驾)','私家车(驾驶)')
dftrip = dftrip.replace('私人小汽车(搭乘)','私家车(搭乘)')


dftrip=pd.merge(dftrip,dfpp[['成员编号','total']], how='inner',left_on='成员编号',right_on='成员编号')
print(dftrip.shape)
dfpp=dfpp.rename(columns={'total':'PPweight'})

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

dftrip['bus']=dftrip[columnlist].apply(lambda x: bustrip(x), axis=1)
dftrip['taxi']=dftrip[columnlist].apply(lambda x: taxitrip(x), axis=1)
dftrip['pc']=dftrip[columnlist].apply(lambda x: pctrip(x), axis=1)
dftrip['auto']=dftrip['bus']+dftrip['taxi']+dftrip['pc']


## count the bus/taxi/private car trips in each period per person
dfbussum=dftrip.loc[dftrip['bus']==1,['成员编号','bus','period']].groupby(['成员编号','period'])['bus'].count().reset_index()
dfbussum=dfbussum.pivot(index='成员编号',columns='period',values='bus').reset_index()
dfbussum=dfbussum.where(dfbussum.notnull(),0)
dfbussum=dfbussum.rename(columns={'AM_Peak':'bus_am','Day_time':'bus_day','Night_time':'bus_night', 'PM_Peak':'bus_pm'})

dftxsum=dftrip.loc[dftrip['taxi']==1,['成员编号','taxi','period']].groupby(['成员编号','period'])['taxi'].count().reset_index()
dftxsum=dftxsum.pivot(index='成员编号',columns='period',values='taxi').reset_index()
dftxsum=dftxsum.where(dftxsum.notnull(),0)
dftxsum=dftxsum.rename(columns={'AM_Peak':'taxi_am','Day_time':'taxi_day','Night_time':'taxi_night', 'PM_Peak':'taxi_pm'})

dfpcsum=dftrip.loc[dftrip['pc']==1,['成员编号','pc','period']].groupby(['成员编号','period'])['pc'].count().reset_index()
dfpcsum=dfpcsum.pivot(index='成员编号',columns='period',values='pc').reset_index()
dfpcsum=dfpcsum.where(dfpcsum.notnull(),0)
dfpcsum=dfpcsum.rename(columns={'AM_Peak':'pc_am','Day_time':'pc_day','Night_time':'pc_night', 'PM_Peak':'pc_pm'})

dfpp=pd.merge(dfpp,dfbussum,how='left',left_on='成员编号',right_on='成员编号')
dfpp=pd.merge(dfpp,dftxsum,how='left',left_on='成员编号',right_on='成员编号')
dfpp=pd.merge(dfpp,dfpcsum,how='left',left_on='成员编号',right_on='成员编号')
dfpp=dfpp.where(dfpp.notnull(),0)





def typefun(am_count , pm_count , day_count , night_count):
    if am_count + pm_count == 0 and day_count > 0:
        return 'Only_Day'
    elif am_count + pm_count == 0 and night_count > 0:
        return 'Only_Night'
    elif am_count * pm_count > 0 and day_count + night_count == 0:
        return 'Both_Peak'
    elif am_count + pm_count == 0 and day_count * night_count > 0:
        return 'day&night'
    elif am_count >0 and (day_count + night_count)>= 0 and pm_count == 0:
        return 'AM_Peak'
    elif pm_count >0 and (day_count + night_count)>= 0 and am_count == 0:
        return 'PM_Peak'
    elif am_count + pm_count > 0 and day_count + night_count > 0:
        return 'Mix'
    elif am_count + pm_count == 0 and day_count + night_count == 0:
        return 'no trip'

################## calculate ratio of (mode by period predicted)/(mode by period from ground truth)###########
def periodrate(dfpp,namelist,gtlist,weight,adj):
    #namelist: am_mode,pm_mode,day_mode,night_mode
    #gtlist: ground truth list: am_volume,pm_volume,day_volume,night_volume
    predictlist=[]
    ratelist=[]
    for i in range(len(namelist)):
        col=namelist[i]
        predict=(dfpp[col]*dfpp[weight]*dfpp[adj]).sum()
        rate=predict/gtlist[i]
        predictlist.append(predict)
        ratelist.append(rate)

    return predictlist,ratelist

#############calculate the weight adjust factor#################################
def weightadj(dfpp,type_name,adj,predlist,ratelist,gtlist):

    dfpp.loc[dfpp[type_name] == 'Both_Peak', adj] = dfpp.loc[dfpp[type_name] == 'Both_Peak', adj] * (gtlist[0]+gtlist[1]) / (
                                                                         predlist[0]+predlist[1])
    dfpp.loc[dfpp[type_name] == 'day&night', adj] = dfpp.loc[dfpp[type_name] == 'day&night', adj] * (gtlist[2]+gtlist[3]) / (
                                                                         predlist[2]+predlist[3])
    dfpp.loc[dfpp[type_name] == 'AM_Peak', adj] = dfpp.loc[dfpp[type_name] == 'AM_Peak', adj] / ratelist[0]
    dfpp.loc[dfpp[type_name] == 'PM_Peak', adj] = dfpp.loc[dfpp[type_name] == 'PM_Peak', adj] / ratelist[1]
    dfpp.loc[dfpp[type_name] == 'Only_Day', adj] = dfpp.loc[dfpp[type_name] == 'Only_Day', adj] / ratelist[2]
    dfpp.loc[dfpp[type_name] == 'Only_Night', adj] = dfpp.loc[dfpp[type_name] == 'Only_Night', adj] / ratelist[3]
    return dfpp


#### bus travel pattern (total number and proportions)####

## import bus count data
print("日公交出行量")
#bustotal=input()
#bustotal=int(bustotal)
bustotal=1702618
starttime = datetime.datetime.now()
## read bus proportion table
## column names:period, percentage  row names:'AM_Peak', 'PM_Peak', 'Day_time', 'Night_time'
## example     :| period     |percentage|,
##              |   AM_Peak  |   0.1256 |
##              |   PM_Peak  |  0.5372  |
buspdf=pd.read_excel(restrictionfile, sheet_name='Bus')
buspdf['volume']=buspdf['percentage'] * bustotal
#buspdf=pd.DataFrame({'period':['AM_Peak', 'PM_Peak', 'Day_time', 'Night_time'],'volume':[265644,239630,1136178,473548]})


## create sex proportion table and age proportion table using sum PPweight group by sex or age_group
sexp=dfpp.groupby('性别')['PPweight'].sum()
sexp=sexp.rename('total')
agep=dfpp.groupby('年龄1')['PPweight'].sum()
agep=agep.rename('total')
empp=dfpp.groupby('就业就学状态')['PPweight'].sum()
empp=empp.rename('total')
carpp=dfpp.groupby(['行政区','有无私家车'])['PPweight'].sum()
carpp=carpp.rename('total')
streetpp=dfpp.groupby('扩样街道编号')['PPweight'].sum()
streetpp=streetpp.rename('total')
aggregates = [streetpp, agep, sexp, empp, carpp]
dimensions = [['扩样街道编号'], ['年龄1'], ['性别'], ['就业就学状态'], ['行政区', '有无私家车']]
aggregates1=[streetpp]
dimensions1=[['扩样街道编号']]


dfpp3=dfpp[['成员编号', '扩样街道编号','性别','年龄1','行政区', '有无私家车', '就业就学状态', 'PPweight', 'bus_am','bus_pm','bus_day','bus_night']]
dfpp3['bus_type']='no bus'
### compute the bus travel type for each person
dfpp3['bus_type'] = dfpp3.apply(lambda x: typefun(x.bus_am, x.bus_pm,x.bus_day,x.bus_night), axis = 1)
dfpp3['bus_adj']=1


bus_am_IC=buspdf.loc[buspdf['period'] == 'AM_Peak', 'volume'].mean()
bus_pm_IC=buspdf.loc[buspdf['period'] == 'PM_Peak', 'volume'].mean()

bus_day_IC=buspdf.loc[buspdf['period'] == 'Day_time', 'volume'].mean()
bus_night_IC=buspdf.loc[buspdf['period'] == 'Night_time', 'volume'].mean()

bus_gtlist=[bus_am_IC,bus_pm_IC,bus_day_IC,bus_night_IC]


bus_predict,bus_rate=periodrate(dfpp3,['bus_am','bus_pm','bus_day','bus_night'],bus_gtlist,'PPweight','bus_adj')
if min(bus_rate)<0.999 or max(bus_rate)>1.001 or abs(sum(bus_predict)-bustotal)>10 :
    conditionb=1
else:
    conditionb=0

loopb=0

while conditionb==1:
    dfpp3=weightadj(dfpp3,'bus_type','bus_adj',bus_predict,bus_rate,bus_gtlist)
    dfpp3['total'] = dfpp3['PPweight'] * dfpp3['bus_adj']
    IPF = ipfn.ipfn(dfpp3, aggregates, dimensions,max_iteration=400)
    dfpp3 = IPF.iteration()
    dfpp3['bus_adj'] = dfpp3['total'] / dfpp3['PPweight']
    loopb = loopb + 1
    bus_predict, bus_rate = periodrate(dfpp3, ['bus_am', 'bus_pm', 'bus_day', 'bus_night'], bus_gtlist, 'PPweight',
                                       'bus_adj')
    #print('busloop {}'.format(loopb))
    #print(round(bus_rate[0], 4), round(bus_rate[1], 4), round(bus_rate[2], 4), round(bus_rate[3], 4))
    if min(bus_rate) >= 0.999 and max(bus_rate) <= 1.001 and abs(sum(bus_predict)-bustotal)<10:
        conditionb = 0

print('四时段公交次数，总公交次数，总人口')
print(bus_predict,round(sum(bus_predict),0),round(dfpp3['total'].sum(),0))


dfpp=pd.merge(dfpp,dfpp3[['成员编号','bus_adj','bus_type','total']],how='left',on='成员编号')
dfpp=dfpp.rename(columns={'total':'busweight'})
endtime = datetime.datetime.now()
print('bus weight adjustment:')
print((endtime - starttime).seconds)



#### taxi travel pattern (total number and proportions)####
dfpp4=dfpp[[ '成员编号', '扩样街道编号','性别', '年龄1', '行政区', '有无私家车', '就业就学状态','busweight', 'bus_am', 'bus_pm', 'bus_day', 'bus_night','bus_type', 'taxi_am',
       'taxi_pm', 'taxi_day', 'taxi_night']]
## import taxi count data
print("请输入日出租车出行量: 1.324098, 2.273004 ")
option = input()
if option == '1':
    taxitotal = 324098
else:
    taxitotal = 273004

starttime = datetime.datetime.now()
## read taxi proportion table
## column names:period, percentage  row names:'AM_Peak', 'PM_Peak', 'Day_time', 'Night_time'
## example     :| period     |percentage|,
##              |   AM_Peak  |   0.0443 |
##              |   PM_Peak  |  0.0515  |
taxidf=pd.read_excel(restrictionfile, sheet_name='Taxi')
taxidf['volume']=taxidf['percentage'] * taxitotal
#taxidf=pd.DataFrame({'period':['AM_Peak', 'PM_Peak', 'Day_time', 'Night_time'],'volume':[21466,24955,231527,206620]})


dfpp4['taxi_type'] = dfpp4.apply(lambda x: typefun(x.taxi_am, x.taxi_pm,x.taxi_day,x.taxi_night), axis = 1)
dfpp4['taxi_adj']=1

taxi_am_IC=taxidf.loc[taxidf['period'] == 'AM_Peak', 'volume'].mean()
taxi_pm_IC=taxidf.loc[taxidf['period'] == 'PM_Peak', 'volume'].mean()
taxi_day_IC=taxidf.loc[taxidf['period'] == 'Day_time', 'volume'].mean()
taxi_night_IC=taxidf.loc[taxidf['period'] == 'Night_time', 'volume'].mean()
taxi_gtlist=[taxi_am_IC,taxi_pm_IC,taxi_day_IC,taxi_night_IC]


taxi_predict,taxi_rate=periodrate(dfpp4,['taxi_am','taxi_pm','taxi_day','taxi_night'],taxi_gtlist,'busweight','taxi_adj')
if min(taxi_rate)<0.999 or max(taxi_rate)>1.001 or abs(sum(taxi_predict)-taxitotal)>10:
    conditiont=1
else:
    conditiont=0

loopt=0
while loopt<20 and conditiont==1:
    dfpp4=weightadj(dfpp4,'taxi_type','taxi_adj',taxi_predict,taxi_rate,taxi_gtlist)
    dfpp4['total']=dfpp4['busweight']*dfpp4['taxi_adj']
    IPF = ipfn.ipfn(dfpp4, aggregates, dimensions, max_iteration=400)
    dfpp4 = IPF.iteration()
    dfpp4['taxi_adj'] = dfpp4['total'] / dfpp4['busweight']
    bus_predict, bus_rate = periodrate(dfpp4, ['bus_am', 'bus_pm', 'bus_day', 'bus_night'], bus_gtlist, 'busweight',
                                       'taxi_adj')
    if min(bus_rate)<0.999 or max(bus_rate)>1.001 or abs(sum(bus_predict)-bustotal)>10:
        conditionb = 1
    else:
        conditionb = 0
    loopb = 0
    while loopb<50 and conditionb==1:
        dfpp4 = weightadj(dfpp4, 'bus_type', 'taxi_adj', bus_predict, bus_rate, bus_gtlist)
        dfpp4['total'] = dfpp4['busweight'] * dfpp4['taxi_adj']

        IPF = ipfn.ipfn(dfpp4, aggregates, dimensions,max_iteration=400)
        dfpp4 = IPF.iteration()
        dfpp4['taxi_adj'] = dfpp4['total'] / dfpp4['busweight']

        loopb = loopb + 1

        bus_predict, bus_rate = periodrate(dfpp4, ['bus_am', 'bus_pm', 'bus_day', 'bus_night'], bus_gtlist, 'busweight',
                                           'taxi_adj')
        #print('busloop {}'.format(loopb))
        #print(round(bus_rate[0], 4), round(bus_rate[1], 4), round(bus_rate[2], 4), round(bus_rate[3], 4))
        if min(bus_rate) >= 0.999 and max(bus_rate) <= 1.001 and abs(sum(bus_predict)-bustotal)<10:
            conditionb = 0

    taxi_predict, taxi_rate = periodrate(dfpp4, ['taxi_am', 'taxi_pm', 'taxi_day', 'taxi_night'], taxi_gtlist,
                                         'busweight', 'taxi_adj')
    if min(taxi_rate) >= 0.999 and max(taxi_rate) <= 1.001 and abs(sum(taxi_predict)-taxitotal)<10:
        conditiont = 0
    #print('taxiloop {}'.format(loopt))
    #print(round(taxi_rate[0], 4), round(taxi_rate[1], 4), round(taxi_rate[2], 4), round(taxi_rate[3], 4))
    loopt=loopt+1

print('四时段公交次数，总公交次数，总人口')
print(bus_predict,round(sum(bus_predict),0),round(dfpp4['total'].sum(),0))
print('四时段出租次数，总出租次数，总人口')
print(taxi_predict,round(sum(taxi_predict),0))


dfpp=pd.merge(dfpp,dfpp4[['成员编号','taxi_type','taxi_adj','total']],how='left',on='成员编号')
dfpp=dfpp.rename(columns={'total':'txweight'})
endtime = datetime.datetime.now()
print('taxi weight adjustment:')
print((endtime - starttime).seconds)
#dfpp.to_excel(r'D:\Urumqi\results\dfpp_taxi.xlsx', index=False)

print(dftrip.loc[dftrip['pc']==1,'pc'].count())
#### private car travel pattern (just proportions)####

dfpp5=dfpp[['成员编号','扩样街道编号','性别','年龄1','行政区', '有无私家车', '就业就学状态',
            'bus_am', 'bus_pm', 'bus_day', 'bus_night', 'bus_type',
            'taxi_am', 'taxi_pm', 'taxi_day', 'taxi_night', 'taxi_type','txweight',
            'pc_am', 'pc_pm', 'pc_day','pc_night']]

## import private car proportion data
## read private car proportion table
## column names:period, percentage  row names:'AM_Peak', 'PM_Peak', 'Day_time', 'Night_time'
## example     :| period     |percentage|,
##              |   AM_Peak  |   0.0443 |
##              |   PM_Peak  |  0.0515  |
carpdf=pd.read_excel(restrictionfile, sheet_name='PC')
#carpdf=pd.DataFrame({'period':['AM_Peak', 'PM_Peak', 'Day_time', 'Night_time'],'percentage':[0.0801,0.0702,0.6056,0.2441]})
#cartotal=931039*2.12*1.36*5.35/7
#carpdf['volume']=carpdf['percentage'] * cartotal
starttime = datetime.datetime.now()
# the following four lines are used to explore the travel pattern category
dfppcar=dfpp[['成员编号','pc_am', 'pc_pm', 'pc_day','pc_night' ]]
dfppcar=dfppcar.replace([1,2,3,4,5,6,7],'Y')
dfppcar=dfppcar.replace(0,'N')
dfppcar2=dfppcar.groupby(['pc_am', 'pc_pm', 'pc_day','pc_night'])['成员编号'].count().reset_index()

# define the car travel pattern category
dfpp5['car_type'] = dfpp5.apply(lambda x: typefun(x.pc_am, x.pc_pm,x.pc_day,x.pc_night), axis = 1)
#dfpp5.to_excel(r'D:\Urumqi\results\dfpp5.xlsx',index=False)
# calculate the proportion of each period
am_car_IC=carpdf.loc[carpdf['period']=='AM_Peak','percentage'].sum()
pm_car_IC=carpdf.loc[carpdf['period']=='PM_Peak','percentage'].sum()
day_car_IC=carpdf.loc[carpdf['period']=='Day_time','percentage'].sum()
night_car_IC=carpdf.loc[carpdf['period']=='Night_time','percentage'].sum()
car_gtlist=[am_car_IC,pm_car_IC,day_car_IC,night_car_IC]

dfpp5['car_adj']=1
#dfpp5['total']=dfpp5['car_adj']*dfpp5['txweight']

pc_predict,pc_rate=periodrate(dfpp5,['pc_am','pc_pm','pc_day','pc_night'],car_gtlist,'txweight','car_adj')
pc_total=sum(pc_predict)
for i in range(len(pc_predict)):
    pc_predict[i]=pc_predict[i]/pc_total
    pc_rate[i]=pc_rate[i]/pc_total
if min(pc_rate)<0.999 or max(pc_rate)>1.001:
    conditionc=1
else:
    conditionc=0


loopc=0
while loopc<100 and conditionc==1:
    dfpp5=weightadj(dfpp5,'car_type','car_adj',pc_predict,pc_rate,car_gtlist)
    dfpp5['total'] = dfpp5['txweight'] * dfpp5['car_adj']
    IPF = ipfn.ipfn(dfpp5, aggregates, dimensions, max_iteration=400)
    dfpp5 = IPF.iteration()
    dfpp5['car_adj'] = dfpp5['total'] / dfpp5['txweight']

    taxi_predict, taxi_rate = periodrate(dfpp5, ['taxi_am', 'taxi_pm', 'taxi_day', 'taxi_night'], taxi_gtlist,
                                         'txweight', 'car_adj')
    if min(taxi_rate) < 0.999 or max(taxi_rate) > 1.001 or abs(sum(taxi_predict)-taxitotal)>10:
        conditiont = 1
    else:
        conditiont = 0

    loopt = 0
    while loopt < 20 and conditiont == 1:
        dfpp5 = weightadj(dfpp5, 'taxi_type', 'car_adj', taxi_predict, taxi_rate, taxi_gtlist)
        dfpp5['total'] = dfpp5['txweight'] * dfpp5['car_adj']
        IPF = ipfn.ipfn(dfpp5, aggregates, dimensions, max_iteration=400)
        dfpp5 = IPF.iteration()
        dfpp5['car_adj'] = dfpp5['total'] / dfpp5['txweight']
        bus_predict, bus_rate = periodrate(dfpp5, ['bus_am', 'bus_pm', 'bus_day', 'bus_night'], bus_gtlist, 'txweight',
                                           'car_adj')
        if min(bus_rate) < 0.999 or max(bus_rate) > 1.001 or abs(sum(bus_predict)-bustotal)>10:
            conditionb = 1
        else:
            conditionb = 0
        loopb = 0
        while loopb < 50 and conditionb == 1:
            dfpp5 = weightadj(dfpp5, 'bus_type', 'car_adj', bus_predict, bus_rate, bus_gtlist)
            dfpp5['total'] = dfpp5['txweight'] * dfpp5['car_adj']

            IPF = ipfn.ipfn(dfpp5, aggregates, dimensions,max_iteration=400)
            dfpp5 = IPF.iteration()
            dfpp5['car_adj'] = dfpp5['total'] / dfpp5['txweight']

            loopb = loopb + 1

            bus_predict, bus_rate = periodrate(dfpp5, ['bus_am', 'bus_pm', 'bus_day', 'bus_night'], bus_gtlist,
                                               'txweight','car_adj')
            #print('busloop {}'.format(loopb))
            #print(round(bus_rate[0], 4), round(bus_rate[1], 4), round(bus_rate[2], 4), round(bus_rate[3], 4))
            if min(bus_rate) >= 0.999 and max(bus_rate) <= 1.001 and abs(sum(bus_predict)-bustotal)<10:
                conditionb = 0

        taxi_predict, taxi_rate = periodrate(dfpp5, ['taxi_am', 'taxi_pm', 'taxi_day', 'taxi_night'], taxi_gtlist,
                                             'txweight', 'car_adj')
        if min(taxi_rate) >= 0.999 and max(taxi_rate) <= 1.001 and abs(sum(taxi_predict)-taxitotal)<10:
            conditiont = 0
        #print('taxiloop {}'.format(loopt))
        #print(round(taxi_rate[0], 4), round(taxi_rate[1], 4), round(taxi_rate[2], 4), round(taxi_rate[3], 4))
        loopt = loopt + 1

    pc_predict, pc_rate = periodrate(dfpp5, ['pc_am', 'pc_pm', 'pc_day', 'pc_night'], car_gtlist, 'txweight', 'car_adj')
    pc_total = sum(pc_predict)
    for i in range(len(pc_predict)):
        pc_predict[i] = pc_predict[i] / pc_total
        pc_rate[i] = pc_rate[i] / pc_total

    print('pc loop')
    print(loopc, round(pc_rate[0],4), round(pc_rate[1],4), round(pc_rate[2],4), round(pc_rate[3],4))
    loopc = loopc + 1
    if min(pc_rate) >= 0.999 and max(pc_rate) <= 1.001:
        conditionc = 0

print('四时段公交次数，总公交次数，总人口')
print(bus_predict,round(sum(bus_predict),0),round(dfpp5['total'].sum(),0))
print('四时段出租次数，总出租次数')
print(taxi_predict,round(sum(taxi_predict),0))


print((dfpp5['pc_am']*dfpp5['total']).sum())
print((dfpp5['pc_pm']*dfpp5['total']).sum())
print((dfpp5['pc_day']*dfpp5['total']).sum())
print((dfpp5['pc_night']*dfpp5['total']).sum())


print((dfpp5['pc_am']*dfpp5['txweight']).sum())
print((dfpp5['pc_pm']*dfpp5['txweight']).sum())
print((dfpp5['pc_day']*dfpp5['txweight']).sum())
print((dfpp5['pc_night']*dfpp5['txweight']).sum())



dfpp=pd.merge(dfpp,dfpp5[['成员编号','car_type','car_adj','total']],how='left',on='成员编号')
dfpp=dfpp.rename(columns={'total':'carweight'})

endtime = datetime.datetime.now()
print('pc weight adjustment time:')
print((endtime - starttime).seconds)
bustrip_pred=((dfpp['bus_am']+dfpp['bus_pm']+dfpp['bus_day']+dfpp['bus_night'])*dfpp['carweight']).sum()
taxitrip_pred=((dfpp['taxi_am']+dfpp['taxi_pm']+dfpp['taxi_day']+dfpp['taxi_night'])*dfpp['carweight']).sum()
pp=dfpp['carweight'].sum()
agepp=dfpp.groupby('年龄1')['carweight'].sum()/pp
sexpp=dfpp.groupby('性别')['carweight'].sum()/pp
emply=dfpp.groupby('就业就学状态')['carweight'].sum()/pp
print('bus trip: {} taxi trip: {} total population: {}'.format(bustrip_pred,taxitrip_pred,pp))
print(agepp)
print(sexpp)
print(emply)
dfpp.to_excel(dfppcarfile, index=False)


