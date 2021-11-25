import numpy as np
import pandas as pd
from geopy.distance import geodesic
import datetime
import time
import os
import matplotlib.pyplot as plt
pd.options.mode.chained_assignment = None  # default='warn'


bounds = [87.346553, 43.6237533, 87.748105, 44.018018]
path=r'C:\Documents\taxi&bus gps\Bus GPS\GPS_20210514'
files = os.listdir(path)
data=pd.DataFrame()
for file in files:
    data0 = pd.read_csv(path + "/" + file,sep='\n',header=None)
    data0['busid']=data0[0].apply(lambda x: x.split(',')[4])
    data0['routeid']=data0[0].apply(lambda x: x.split(',')[2])
    data0['subrouteid'] = data0[0].apply(lambda x: x.split(',')[3])
    data0['actdatetime']= data0[0].apply(lambda x: x.split(',')[8])
    data0['longitude']=data0[0].apply(lambda x: x.split(',')[13])
    data0['latitude']=data0[0].apply(lambda x: x.split(',')[14])
    data0['longitude']=data0['longitude'].replace('','0')
    data0['latitude'] =data0['latitude'].replace('','0')
    data0['longitude']=data0['longitude'].apply(lambda x: float(x))
    data0['latitude'] = data0['latitude'].apply(lambda x: float(x))
    data0=data0[(data0['longitude']>bounds[0])&(data0['longitude']<bounds[2])&(data0['latitude']>bounds[1])&(data0['latitude']<bounds[3])]
    data0['gpsspeed'] = data0[0].apply(lambda x: x.split(',')[16])
    data0['angle']=data0[0].apply(lambda x: x.split(',')[18])
    data0=data0.drop(columns=[0])
    #data0 = data0[(data0['longitude'] != '') & (data0['latitude'] != '')]
    #data0 = data0[(data0['longitude'] != '0') & (data0['latitude'] != '0')]

    #print(data0.head(5))
    data=pd.concat([data,data0],ignore_index=True)
    print(file, data.shape)


data=data.sort_values(by=['routeid','subrouteid','busid','actdatetime'])
data['Date']=data['actdatetime'].apply(lambda x: x[0:8])
data = data[data['Date']=='20210514']
print(data.shape)
data=data.reset_index().drop(columns=['index'])
data['long_prev']=data.groupby(['routeid','subrouteid','busid'])['longitude'].shift(1)
data['lat_prev']=data.groupby(['routeid','subrouteid','busid'])['latitude'].shift(1)
#去掉一直停止的行和GPS跳太多的行
data['stop']=0
data.loc[(data['long_prev']==data['longitude'])&(data['lat_prev']==data['latitude']),'stop']=1
data['stop_prev']=data.groupby(['routeid','subrouteid','busid'])['stop'].shift(1)
data=data[~(data['stop']+data['stop_prev']==2)]
data=data[(abs(data['longitude']-data['long_prev'])<0.015) &(abs(data['latitude']-data['lat_prev'])<0.015)]
print(data.shape)
data['Time']=data['actdatetime'].apply(lambda x: x[8:14])
data['Date_prev']=data.groupby(['routeid','subrouteid','busid'])['Date'].shift(1)
data['Time_prev']=data.groupby(['routeid','subrouteid','busid'])['Time'].shift(1)

data['Hour']=data['actdatetime'].apply(lambda x: int(x[8:10]))
data['Hour_prev']=data.groupby(['routeid','subrouteid','busid'])['Hour'].shift(1)
data['hourcheck']=abs(data['Hour']-data['Hour_prev'])
data.loc[data['hourcheck']>1,'Hour_prev']=data.loc[data['hourcheck']>1,'Hour']
data.loc[data['hourcheck']>1,'Time_prev']=data.loc[data['hourcheck']>1,'Hour'].apply(lambda x: str(x).zfill(2)+'0000')


def str_dur(prev_t,curr_t,prev_d,curr_d):
    try:
        if prev_d == curr_d:
            duration = 3600 * (int(curr_t[0:2]) - int(prev_t[0:2])) + 60 * (int(curr_t[2:4]) - int(prev_t[2:4])) + (
                        int(curr_t[4:6]) - int(prev_t[4:6]))
        else:
            duration = 3600 * (int(prev_t[0:2]) - int(curr_t[0:2])) + 60 * (int(prev_t[2:4]) - int(curr_t[2:4])) + (
                        int(prev_t[4:6]) - int(curr_t[4:6]))
            duration = 3600 * 24 - duration
        return duration
    except:
        return 0


data['duration']=data.apply(lambda x: str_dur(x['Time_prev'],x['Time'],x['Date_prev'],x['Date']),axis=1)
print(data.loc[data['duration']!=0,'duration'].describe())

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

data['distance']=data.apply(lambda x: distancefun(x['latitude'],x['longitude'],x['lat_prev'],x['long_prev']),axis=1)
data.loc[data['duration']!=0,'speed']=round(3.6*data.loc[data['duration']!=0,'distance']/data.loc[data['duration']!=0,'duration'],1)

print(data.loc[data['duration']!=0,'distance'].describe())
print(data.loc[data['duration']!=0,'speed'].describe())

data['mark']='N'
data.loc[(data['duration']>600),'mark']='Y' #gap too long
data.loc[data['distance']>2000,'mark']='Y' #gps excursion
data.loc[data['speed']>100,'mark']='Y' # infeasible speed
data=data[data['mark']=='N']
print('去除间隔大、距离大、速度过大的行')
print(data.shape)
##summarizing
bus_gps_sum=data.groupby(['routeid','subrouteid','busid','Hour']).agg(
    speed=pd.NamedAgg(column='speed',aggfunc='mean'),
    distance=pd.NamedAgg(column='distance',aggfunc='sum'),
    duration=pd.NamedAgg(column='duration',aggfunc='sum'),
).reset_index()
bus_gps_sum['speed']=round(bus_gps_sum['speed'],1).fillna(0)
bus_gps_sum['distance']=round(bus_gps_sum['distance']/1000,1)
bus_gps_sum['duration']=round(bus_gps_sum['duration']/60,1)
bus_gps_sum=bus_gps_sum.rename(columns={'speed':'avg_speed','distance':'hour_dist','duration':'hour_dur'})

data=data.merge(bus_gps_sum,how='left',on=['routeid','subrouteid','busid','Hour'])
data.loc[data['avg_speed']==0,'mark']='R'
data.loc[data['hour_dist']==0,'mark']='R'
data.loc[data['hour_dur']==0,'mark']='R'
data=data[data['mark']=='N']
print('去除整个小时没有移动的行')
print(data.shape)

bus_gps_sum.to_csv(r'C:\Documents\taxi&bus gps\Bus GPS\bus_gps_hour_summary.csv',index=False)
data.drop(columns=['Date_prev','Hour_prev','hourcheck','avg_speed','hour_dist','hour_dur']).to_csv(r'C:\Documents\taxi&bus gps\Bus GPS\bus_gps_cleaned_data.csv',index=False)

bus_hour_avgspeed=bus_gps_sum[bus_gps_sum['avg_speed']>0].groupby('Hour').agg(
avgspeed=pd.NamedAgg(column='avg_speed',aggfunc='mean'),
    buscount=pd.NamedAgg(column='busid',aggfunc='count')
).reset_index()
bus_hour_avgspeed['avgspeed']=round(bus_hour_avgspeed['avgspeed'],2)

import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'simhei'
import plot_map
import matplotlib

bounds = [87.346553, 43.6237533, 87.748105, 44.018018]
for i in range(23):
    data_aggi = data[data['Hour'] == i]
    fig = plt.figure(1, (8, 8), dpi=300)
    ax = plt.subplot(111)
    plt.sca(ax)
    plot_map.plot_map(plt, bounds, zoom=12, style=4)
    # 设置colormap的数据
    vmax = data['speed'].quantile(0.99)  # colorbar的最大值取99%分位数
    norm = matplotlib.colors.Normalize(vmin=0, vmax=vmax)  # norm是标准化工具
    cmapname = 'autumn'
    #cmap = matplotlib.cm.get_cmap(cmapname)
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list('cmap', ['#FF0000','#E9420E','#F7941D','#FFFE03','#9DCC42'], 256)
    plt.scatter(data_aggi['longitude'],
                data_aggi['latitude'],
                s=0.1,  # s是点的大小
                alpha=0.5,  # alpha是点的透明度
                c=data_aggi['speed'],  # c是以哪一列的依据去画
                cmap=cmap,
                norm=norm)
    plt.title(str(i) + ':00')  # 图标题
    plt.axis('off')

    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])

    # 加比例尺和指北针   textsize 字体大小,compasssize = 指北针大小,accuracy = 指北针长度
    plot_map.plotscale(ax, bounds=bounds, textsize=6, compasssize=1, accuracy=1300, rect=[0.12, 0.03])  # rect指北针的位置

    plt.imshow([[0, vmax]], cmap=cmap)
    cax = plt.axes([0.13, 0.32, 0.02, 0.3])  # 调位置
    cbar = plt.colorbar(cax=cax)

    plt.savefig(r'C:\公交系统运营指标\{}点公交速度.png'.format(i)) #保存图片的文件夹
    plt.close()

busspeed=pd.read_csv(r'C:\Users\yi.gu\Documents\taxi&bus gps\Bus GPS\bus_gps_hour_summary.csv')
busspeed[(busspeed['Hour']==9)|(busspeed['Hour']==19)].groupby('Hour')['avg_speed'].mean()
