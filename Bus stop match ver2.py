import requests
import pandas as pd
import numpy as np
import json
import re
import time
from bs4 import BeautifulSoup
import math
from geopy.distance import geodesic
pd.options.mode.chained_assignment = None  # default='warn'

def distancefun(lat1, long1, lat2, long2):
    try:
        lat1 = float(lat1)
        long1 = float(long1)
        lat2 = float(lat2)
        long2 = float(long2)
        distance = geodesic((lat1, long1), (lat2, long2)).m  # 计算两个坐标直线距离
        return round(distance/1000, 2)
    except:
        return 0

#########use amap api to obtain bus stop coordinates
busstops=pd.DataFrame()
linelist=['3路',157,203,301,527,537,701,914]
for line in linelist:
    url = 'https://restapi.amap.com/v3/bus/linename?s=rsv3&extensions=all&key=559bdffe35eec8c8f4dae959451d705c&output=json&city=%E4%B9%8C%E9%B2%81%E6%9C%A8%E9%BD%90&offset=2&keywords={}&platform=JS'.format(
        line)
    r = requests.get(url, verify=False).text
    rt = json.loads(r)
    print(line,len(rt['buslines']))
    if len(rt['buslines']) >0:
        for d in range(len(rt['buslines'])):
            dt = {}
            dt['line_name'] = rt['buslines'][d]['name']  # 公交线路名字
            # create a dataframe containing the bus polyline information
            polylinelist=rt['buslines'][d]['polyline'].split(';')
            polylinedf=pd.DataFrame({
                'long':[float(polylinelist[i].split(',')[0]) for i in range(len(polylinelist))],
                'lat': [float(polylinelist[i].split(',')[1]) for i in range(len(polylinelist))],
                'name':rt['buslines'][d]['name']
            })
            polylinedf.to_excel(r'D:\Hyder安诚\乌鲁木齐公交运行\Bus Route From Web\bus_{}.xlsx'.format(rt['buslines'][d]['name'] ), index=False)
            # a dataframe containing the stop coordinates
            dt['bus_stops'] = rt['buslines'][d]['busstops']
            busstopdf = pd.DataFrame(index=range(len(dt['bus_stops'])),
                                     columns=['bus_line', 'direction', 'sequence', 'bus_stop name', 'long', 'lat'])
            i = 0
            for items in dt['bus_stops']:
                busstopdf.loc[i, 'bus_line'] = line
                busstopdf.loc[i, 'direction'] = dt['line_name']
                busstopdf.loc[i, 'sequence'] = int(items['sequence'])
                busstopdf.loc[i, 'bus_stop name'] = items['name']
                long, lat = items['location'].split(',')
                busstopdf.loc[i, 'long'] = float(long)
                busstopdf.loc[i, 'lat'] = float(lat)
                i = i + 1
            busstops = pd.concat([busstops, busstopdf], axis=0)

busstops=busstops.reset_index().drop(columns=['index'])
busstops.to_excel( r'D:\Hyder安诚\乌鲁木齐公交运行\Bus Route From Web\bus_stops_fromWeb.xlsx',index=False)



###match busline nodes from EMME with bus stops from Urumqi Transportation Center's Database
###需要人工检查好用于匹配的站点
data=pd.read_excel(r'D:\Hyder安诚\乌鲁木齐公交运行\buslinematchstop9.xls')
busdb=pd.read_excel(r'D:\Hyder安诚\乌鲁木齐公交运行\9条线路fromdatabase.xlsx')
busdb=busdb.sort_values(by=['BUS_LINE_NAME', 'DIRECTION', 'STATION_SEQ'])
busdb['BUS_LINE_NAME']=busdb['BUS_LINE_NAME'].replace('528A','528路')
busdb['BLD']=''
busdb['i'] = 0
data=data.drop_duplicates(subset=[ 'Bus Name', 'i', 'j'])
print(len(data))
data_sum_p=data.groupby(['Bus Name']).agg(
    board=pd.NamedAgg(column='board',aggfunc='sum'),
    alight=pd.NamedAgg(column='alight',aggfunc='sum'),
).reset_index()
data['direction']=''
data['stop_name']=''
data['seq']=0
data['distance']=0
data['stop_id']=0
buslist=[]
### find the direction, first/last stop of busline and find the closest stop for each point
for b in set(data['Bus Name']):
    blname= re.split('[AB]', str(b))[0] + '路'
    print(b)
    if blname not in buslist:
        buslist.append(blname)
    stop1df=busdb[(busdb['BUS_LINE_NAME']==blname)&(busdb['STATION_SEQ']==1)] #匹配起点站寻找方向
    min_ind=min(data[data['Bus Name']==b].index)
    max_ind=max(data[data['Bus Name']==b].index)
    long1=data.loc[min_ind,'Longitude']
    lat1=data.loc[min_ind,'Latitude']
    stop1df['d']=stop1df.apply(lambda x:distancefun(x['LAT'],x['LON'],lat1,long1),axis=1)
    stop1_ind=list(stop1df[stop1df['d']==stop1df['d'].min()].index)[0]
    stop1=list(stop1df.loc[stop1df['d']==stop1df['d'].min(),'BUS_STATION_NAME'])[0] #find the first stop
    dircode= list(stop1df.loc[stop1df['d']==stop1df['d'].min(),'DIRECTION'])[0]
    last_seq=busdb.loc[(busdb['BUS_LINE_NAME']==blname)&(busdb['DIRECTION']==dircode),'STATION_SEQ'].max()
    stoplast=busdb.loc[(busdb['BUS_LINE_NAME']==blname)&(busdb['DIRECTION']==dircode)&(busdb['STATION_SEQ']==last_seq),'BUS_STATION_NAME']
    stoplast=list(stoplast)[0]
    stoplast_ind=list(busdb[(busdb['BUS_LINE_NAME']==blname)&(busdb['DIRECTION']==dircode)&(busdb['STATION_SEQ']==last_seq)].index)[0]
   #fill the first and last stop name to dataframe
    data.loc[data['Bus Name']==b,'direction']=blname+'('+stop1+'--'+stoplast+')'
    data.loc[min_ind,'stop_name']=stop1
    data.loc[max_ind,'stop_name']=stoplast
    data.loc[min_ind, 'seq'] = 1
    data.loc[max_ind, 'seq'] = last_seq
    data.loc[min_ind, 'stop_id'] =busdb.loc[stop1_ind,'BUS_STATION_ID']
    data.loc[max_ind, 'stop_id'] =busdb.loc[stoplast_ind,'BUS_STATION_ID']

    busdb.loc[stop1_ind, 'i'] = data.loc[min_ind, 'i']
    busdb.loc[stoplast_ind, 'i'] = data.loc[max_ind, 'i']
    busdb.loc[(busdb['BUS_LINE_NAME'] == blname) & (busdb['DIRECTION'] == dircode),'BLD']=b
    stopdf = busdb[(busdb['BUS_LINE_NAME'] == blname) & (busdb['DIRECTION'] == dircode)]

    #calculate the distance to first stop in column 'dsum'
    stopdf['lon_lag'] = stopdf['LON'].shift(1)
    stopdf['lat_lag'] = stopdf['LAT'].shift(1)
    stopdf['d'] = stopdf.apply(lambda x: distancefun(x['LAT'], x['LON'], x['lat_lag'], x['lon_lag']), axis=1)
    stopdf['d'] = stopdf['d'].fillna(0)
    stopdf['dsum'] = 0


    data_slice = data[data['Bus Name'] == b]
    # data_slice['d']=0
    data_slice['lon_lag'] = data_slice['Longitude'].shift(1)
    data_slice['lat_lag'] = data_slice['Latitude'].shift(1)
    data_slice['d'] = data_slice.apply(lambda x: distancefun(x['Latitude'], x['Longitude'], x['lat_lag'], x['lon_lag']),
                                       axis=1)
    data_slice['d'] = data_slice['d'].fillna(0)
    data_slice['dsum'] = 0
    for ind in data[data['Bus Name'] == b].index:
        if ind != min_ind :
            data_slice.loc[ind, 'dsum'] = data_slice.loc[min_ind:ind, 'd'].sum()

    for i in stopdf.index[1:]:
        stopdf.loc[i, 'dsum'] = stopdf.loc[stopdf.index[0]:i, 'd'].sum()
        if i != stoplast_ind:
            rel_d = stopdf.loc[i, 'dsum']

            data_slice['delta'] = data_slice['dsum'].apply(lambda x: abs(x - rel_d))
            data_slice['distance'] = data_slice.apply(lambda x: distancefun(x['Latitude'], x['Longitude'],
                                                                            stopdf.loc[i, 'LAT'], stopdf.loc[i, 'LON']),
                                                      axis=1)
            data_slice['score'] = data_slice['delta'] + data_slice['distance']+stopdf.loc[i,'STATION_SEQ']
            listi=list(stopdf['i'].dropna())
            data_slice['mark']=data_slice['i'].apply(lambda x: 'Y' if x not in listi else 'N')
            data_slice1 = data_slice[data_slice['mark']=='Y']
            #print(len(data_slice),len(data_slice1))
            close_ind = data_slice1[data_slice1['score'] == data_slice1['score'].min()].index[0]
            stopdf.loc[i, 'i'] = data_slice1.loc[close_ind, 'i']
            busdb.loc[i, 'i'] = data_slice1.loc[close_ind, 'i']

data=pd.merge(data,busdb[['BLD','i','BUS_STATION_NAME','STATION_SEQ']],how='left',left_on=['Bus Name','i'],right_on=['BLD','i'])
data=data.drop(columns=['stop_name', 'seq', 'distance', 'stop_id', 'BLD']).rename(columns={'BUS_STATION_NAME':'stop_name',                                                                                          'STATION_SEQ':'seq'})
data=data.fillna('')
data['Is A Stop']=data['stop_name'].apply(lambda x: 'N' if x=='' else 'Y')
print(len(data))
data_sum=data[data['Is A Stop']=='Y'].groupby(['Bus Name']).agg(
    total_stop=pd.NamedAgg(column='seq',aggfunc='max'),
    stop_count=pd.NamedAgg(column='seq',aggfunc='count'),
).reset_index()

data_sum=pd.merge(data_sum,data_sum_p,how='left',on='Bus Name')

print(data.groupby(['Bus Name']).agg(
    board=pd.NamedAgg(column='board',aggfunc='sum'),
    alight=pd.NamedAgg(column='alight',aggfunc='sum'),
).reset_index())
########adjust alight and board volumns
data.to_excel(r'D:\Hyder安诚\乌鲁木齐公交运行\buslinematchstop9_0626mid2.xlsx',index=False)

data=pd.read_excel(r'D:\Hyder安诚\乌鲁木齐公交运行\buslinematchstop9_0626mid2.xlsx')
data['change'] = 'N'
data.loc[(data['Is A Stop'] == 'Y') & (data['no_alight'] == 1), 'change'] = 'Y'
data.loc[(data['Is A Stop'] == 'N') & (data['no_alight'] == 0), 'change'] = 'Y'
changelist = np.array(data[data['change'] == 'Y'].index)
print(len(changelist))
stoplist = np.array(data[data['Is A Stop'] == 'Y'].index)
for i in changelist:
    if i not in stoplist:
        ind = np.searchsorted(stoplist, i, side='left')
        preced = stoplist[ind - 1]
        next = stoplist[ind]
        print(preced, '{} is not a stop'.format(i), next)
    else:
        ind = np.searchsorted(stoplist, i, side='left')
        preced = stoplist[ind - 1]
        next = stoplist[ind + 1]
        print(preced, '{} is a stop'.format(i), next)

    print(data.loc[[preced, i, next], ['alight', 'board', 'Is A Stop', 'change']])

    if data.loc[i, 'Is A Stop'] == 'N' and data.loc[i, 'no_alight'] == 0:  # stop change from 'Y' to 'N'
        alight = data.loc[i, 'alight']
        board = data.loc[i, 'board']
        if alight > 0:
            if data.loc[i, 'Bus Name'] == data.loc[preced, 'Bus Name'] and data.loc[i, 'Bus Name'] == data.loc[next, 'Bus Name']:
                data.loc[preced, 'alight'] = data.loc[preced, 'alight'] + math.ceil(alight / 2)
                data.loc[next, 'alight'] = data.loc[next, 'alight'] + math.floor(alight / 2)
                data.loc[i, 'alight'] = 0
                data.loc[i, 'change'] = 'changed'
        else:
            data.loc[i, 'change'] = 'not need change'
        if board > 0:
            if data.loc[i, 'Bus Name'] == data.loc[preced, 'Bus Name'] and data.loc[i, 'Bus Name'] == data.loc[
                next, 'Bus Name']:
                data.loc[preced, 'board'] = data.loc[preced, 'board'] + math.ceil(board / 2)
                data.loc[next, 'board'] = data.loc[next, 'board'] + math.floor(board / 2)
                data.loc[i, 'board'] = 0
                data.loc[i, 'change'] = 'not need change'
        else:
            data.loc[i, 'change'] = 'changed'
        print(data.loc[[preced, i, next],['alight','board', 'Is A Stop','change']])
    elif data.loc[i, 'Is A Stop'] == 'Y' and data.loc[i, 'no_alight'] == 1:  # stop change from 'N' to 'Y'
        if data.loc[i, 'Bus Name'] == data.loc[preced, 'Bus Name'] and data.loc[i, 'Bus Name'] == data.loc[
            next, 'Bus Name']:
            data.loc[i, 'alight'] = data.loc[i, 'alight']+math.ceil(data.loc[preced, 'alight'] / 2) + math.floor(data.loc[next, 'alight'] / 2)
            data.loc[preced, 'alight'] = data.loc[preced, 'alight'] - math.ceil(data.loc[preced, 'alight'] / 2)
            data.loc[next, 'alight'] = data.loc[next, 'alight'] - math.floor(data.loc[next, 'alight'] / 2)
            data.loc[i, 'board'] = data.loc[i, 'board']+math.ceil(data.loc[preced, 'board'] / 2) + math.floor(data.loc[next, 'board'] / 2)
            data.loc[preced, 'board'] = data.loc[preced, 'board'] - math.ceil(data.loc[preced, 'board'] / 2)
            data.loc[next, 'board'] = data.loc[next, 'board'] - math.floor(data.loc[next, 'board'] / 2)
            data.loc[i, 'change'] = 'changed'
        print(data.loc[[preced, i, next], ['alight', 'board', 'Is A Stop','change']])



data_unchange = data[data['change'] == 'Y']
print(data_unchange)


data.loc[data['change']=='changed','no_alight']=1-data.loc[data['change']=='changed','no_alight']
data.loc[data['change']=='changed','no_board']=1-data.loc[data['change']=='changed','no_board']

data_sum2=data[data['Is A Stop']=='Y'].groupby(['Bus Name']).agg(
    #total_stop=pd.NamedAgg(column='seq',aggfunc='max'),
    #stop_count=pd.NamedAgg(column='seq',aggfunc='count'),
    board=pd.NamedAgg(column='board', aggfunc='sum'),
    alight=pd.NamedAgg(column='alight', aggfunc='sum'),
).reset_index()

data_sum=pd.merge(data_sum,data_sum2,how='left',on='Bus Name')
data_sum['diff_b']=data_sum['board_x']-data_sum['board_y']
data_sum['diff_a']=data_sum['alight_x']-data_sum['alight_y']

data_sum_stop=data[data['Is A Stop']=='Y'].groupby(['Bus Name', 'stop_name', 'seq']).agg(
    board=pd.NamedAgg(column='board',aggfunc='sum'),
    alight=pd.NamedAgg(column='alight',aggfunc='sum'),
).reset_index().sort_values(by=['Bus Name','seq'])



writer = pd.ExcelWriter(r'D:\Hyder安诚\乌鲁木齐公交运行\buslinematchstop9_0626ver2.xlsx')
data.to_excel(writer,sheet_name='data', startrow=0, startcol=0, index=False)
data_sum.to_excel(writer,sheet_name='line_sum', startrow=0, startcol=0, index=False)
writer.save()


####画图
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = [u'SimHei']
plt.rcParams['axes.unicode_minus'] = False
data['stop']=data['no_alight']+data['no_board']
data['stop']=data['stop'].apply(lambda x: 'Y' if x>0 else 'N')
data['i']=data['i'].apply(lambda x: int(x))

for bld in set(data['Bus Name']):
    print(bld)

    x=np.array(data.loc[data['Bus Name']==bld,'Latitude'])
    y=np.array(data.loc[data['Bus Name']==bld,'Longitude'])
    pointn=np.array(data.loc[data['Bus Name']==bld,'i'])
    stop=np.array(data.loc[data['Bus Name']==bld,'stop'])

    x_ref=np.array(busdb.loc[busdb['BLD']==bld,'LAT'])
    y_ref=np.array(busdb.loc[busdb['BLD']==bld,'LON'])
    point_ref=np.array(busdb.loc[busdb['BLD']==bld,'BUS_STATION_NAME'])

    plt.figure(figsize=(20, 20), dpi=300)
    plt.scatter(x_ref,y_ref,marker='D', c='r')
    for i in range(len(x_ref)):
        plt.annotate(point_ref[i], xy=(x_ref[i], y_ref[i]), xytext=(x_ref[i] + 0.0001, y_ref[i] + 0.0001),fontsize=8)  # 这里xy是需要标记的坐标，xytext是对应的标签坐标
    plt.scatter(x, y, marker='o', c='g',markersize=3)
    for i in range(len(x)):
        if stop[i]=="Y":
            plt.annotate(pointn[i], xy=(x[i], y[i]), xytext=(x[i] - 0.0002, y[i] - 0.0002),fontsize=8)

    plt.title(bld)
    figname=r'D:\Hyder安诚\乌鲁木齐公交运行\busfigs\{}.png'.format(bld)
    plt.savefig(figname, bbox_inches='tight')
    plt.close()
    #plt.show()



