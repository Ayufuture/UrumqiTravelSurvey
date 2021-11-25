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
        return round(distance, 1)
    except:
        return 0
##### use amap api to obtain busstop coordinates
key=r''
busstops=pd.DataFrame()
linelist=[17,29,56,72,98,311,535,5035,5201,9,1002,22,2007,23,45,70,76,518,613,910,3401,5031,5033,5036,5037,6005,6007,6008,6009,
          6011,52,303,44,68,6502,'S601','S602']
for line in linelist:
    url = 'https://restapi.amap.com/v3/bus/linename?s=rsv3&extensions=all&key={}&output=json&city=%E4%B9%8C%E9%B2%81%E6%9C%A8%E9%BD%90&offset=2&keywords={}&platform=JS'.format(key,
        line)
    r = requests.get(url, verify=False).text
    rt = json.loads(r)
    print(line,len(rt['buslines']))
    if len(rt['buslines']) >0:
        for d in range(len(rt['buslines'])):
            dt = {}
            dt['line_name'] = rt['buslines'][d]['name']  # 公交线路名字
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
#busstops.to_excel( r'C:\Users\yi.gu\Documents\bus_stops_fromWeb.xlsx',index=False)
busstops=pd.read_excel( r'D:\乌鲁木齐公交运行\bus_stops_fromWeb.xlsx')

buslines=pd.read_excel( r'D:\乌鲁木齐公交运行\buslinematchstop.xls')
buslines['Stop']=buslines['noalight']+buslines['noboard']
buslines['Stop']=buslines['Stop'].apply(lambda x: 'Y' if x<2 else 'N')
buslines['bus_line']=buslines['bus_line'].apply(lambda x:str(x))
busstops['bus_line']=busstops['bus_line'].apply(lambda x:str(x))
buslines=buslines[[ 'FID_',
       'Busline', 'Direction', 'i', 'j', 'noalight', 'noboard','Stop', 'alight',
       'board', 'BLD', 'Index', 'bus_line', 'directio_1', 'sequence',
       'bus_stop_n', 'long', 'lat', 'Longitude', 'Latitude','Distance']]
print(len(set(buslines.Busline)))
print(len(set(buslines.BLD)))
for bld in set(buslines.BLD):
    print(bld)
    orig_idx=buslines[(buslines['BLD']==bld) & (buslines['Index']==1)].index[0]
    orig_lat=buslines.loc[orig_idx,'Latitude']
    orig_long = buslines.loc[orig_idx, 'Longitude']
    line=buslines.loc[orig_idx, 'Busline']
    busstop_orig = busstops[(busstops['bus_line'] == line)&(busstops['sequence'] == 1)]
    busstop_orig['long2'] = orig_long
    busstop_orig['lat2'] = orig_lat
    busstop_orig['distance'] = busstop_orig.apply(
        lambda x: distancefun(x['lat'], x['long'], x['lat2'], x['long2']), axis=1)
    min_d = min(busstop_orig['distance'])
    idx = busstop_orig[busstop_orig['distance'] == min_d].index[0]
    direction=busstop_orig.loc[idx,'direction']
    buslines.loc[buslines['BLD'] == bld, 'directio_1']=direction
    buslines.loc[buslines['BLD'] == bld, 'bus_line'] = line
    colist1 = ['sequence', 'bus_stop_n', 'long', 'lat', 'Distance']
    colist2 = ['sequence', 'bus_stop name', 'long', 'lat', 'distance']
    for j in range(len(colist1)):
        print(busstop_orig.loc[idx, colist2[j]])
        buslines.loc[(buslines['BLD']==bld) & (buslines['Index']==1), colist1[j]] = busstop_orig.loc[idx, colist2[j]]



busstops['closestpoint']=0
for i2 in busstops.index:
    buslinei=buslines[(buslines['bus_line']==busstops.loc[i2,'bus_line']) & (buslines['directio_1']==busstops.loc[i2,'direction']) & (buslines['Stop']=='Y') ]
    if len(buslinei) >0:
        buslinei['long2'] = busstops.loc[i2, 'long']
        buslinei['lat2'] = busstops.loc[i2, 'lat']
        buslinei['dist'] = buslinei.apply(lambda x: distancefun(x['Latitude'], x['Longitude'], x['lat2'], x['long2']),
                                          axis=1)
        min_d = min(buslinei['dist'])
        idx = buslinei[buslinei['dist'] == min_d].index[0]
        busstops.loc[i2, 'closestpoint'] = buslinei.loc[idx, 'i']
        print(i2, busstops.loc[i2, 'closestpoint'])

colist1 = ['bus_line', 'directio_1', 'sequence', 'bus_stop_n', 'long', 'lat', 'Distance']
colist2 = ['bus_line', 'direction', 'sequence', 'bus_stop name', 'long', 'lat', 'distance']

for i in buslines.index:
    if buslines.loc[i,'Index']>1:
        print(i,buslines.loc[i,'Busline'],buslines.loc[i,'bus_line'],buslines.loc[i,'directio_1'])
        point=buslines.loc[i,'i']
        busstopi1=busstops[(busstops['bus_line']==buslines.loc[i,'Busline']) & (busstops['direction']==buslines.loc[i,'directio_1'])  &
                           busstops['closestpoint']==point]
        if len(busstopi1)>0:
            idx=busstopi1.index[0]
            for j in range(len(colist1)):
                buslines.loc[i, colist1[j]] = busstopi.loc[idx, colist2[j]]
            print(busstopi.loc[idx, :])
        else:
            busstopi = busstops[(busstops['bus_line'] == buslines.loc[i, 'Busline']) & (
                        busstops['direction'] == buslines.loc[i, 'directio_1'])]
            busstopi['long2'] = buslines.loc[i, 'Longitude']
            busstopi['lat2'] = buslines.loc[i, 'Latitude']
            busstopi['distance'] = busstopi.apply(
                lambda x: distancefun(x['lat'], x['long'], x['lat2'], x['long2']), axis=1)
            min_d = min(busstopi['distance'])
            idx = busstopi[busstopi['distance'] == min_d].index[0]

            for j in range(len(colist1)):
                buslines.loc[i, colist1[j]] = busstopi.loc[idx, colist2[j]]
            print(busstopi.loc[idx, :])





buslines.to_excel( r'D:\bus_stops_sj0425.xlsx',index=False)

boardcount=buslines.groupby(['Busline','Direction'])['board'].sum().reset_index()
boardcount.to_excel( r'D:\bus_boardcount.xlsx',index=False)



buslines=pd.read_excel(r'F:\乌鲁木齐公交运行\BUSLINES.xlsx',sheet_name='Sheet1')
writer=pd.ExcelWriter(r'F:\乌鲁木齐公交运行\BUSLINES_reshape.xlsx')
for bl in linelist:
    buslinei=buslines[buslines['Busline']==bl]
    startr = 0
    startc = 1
    for bld in set(buslinei['BLD']):
        buslineid=buslinei.loc[buslinei['BLD']==bld,['BLD','alight','board','i','j', 'bus_stop_n']]
        buslineid.to_excel(writer,sheet_name=str(bl),startrow=startr,startcol=startc,index=False)
        r, c = buslineid.shape
        startc=startc+c+2

writer.save()

buslines=pd.read_excel(r'C:\Users\yi.gu\Documents\bus_stops_sj0421.xlsx')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = [u'SimHei']
plt.rcParams['axes.unicode_minus'] = False
for bld in set(buslines.BLD):
    print(bld)
    x=np.array(buslines.loc[buslines['BLD']==bld,'Latitude'])
    y=np.array(buslines.loc[buslines['BLD']==bld,'Longitude'])
    pointn=np.array(buslines.loc[buslines['BLD']==bld,'i'])
    stop=np.array(buslines.loc[buslines['BLD']==bld,'Stop'])
    line=np.array(buslines.loc[buslines['BLD']==bld,'Busline'])[0]
    dir=np.array(buslines.loc[buslines['BLD']==bld,'directio_1'])[0]

    x_ref=np.array(busstops.loc[busstops['direction']==dir,'lat'])
    y_ref=np.array(busstops.loc[busstops['direction']==dir,'long'])
    point_ref=np.array(busstops.loc[busstops['direction']==dir,'bus_stop name'])

    plt.figure(figsize=(10, 10), dpi=100)
    plt.plot(x_ref,y_ref,marker='D', c='r')
    for i in range(len(x_ref)):
        plt.annotate(point_ref[i], xy=(x_ref[i], y_ref[i]), xytext=(x_ref[i] + 0.0001, y_ref[i] + 0.0001),fontsize=8)  # 这里xy是需要标记的坐标，xytext是对应的标签坐标
    plt.plot(x, y, marker='o', c='g',markersize=3)
    for i in range(len(x)):
        if stop[i]=="Y":
            plt.annotate(pointn[i], xy=(x[i], y[i]), xytext=(x[i] - 0.0001, y[i] - 0.0001),fontsize=8)

    plt.title(dir)
    figname=r'C:\Users\yi.gu\Documents\busfigs\{}.png'.format(dir)
    plt.savefig(figname, bbox_inches='tight')
    plt.close()
    #plt.show()

# urumqi stations
"https://restapi.amap.com/v3/place/text?keywords=%E7%AB%99&city=%E4%B9%8C%E9%B2%81%E6%9C%A8%E9%BD%90&offset=20&page=1&key={}&extensions=base".format(key)

