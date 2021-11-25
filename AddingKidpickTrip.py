#补充出行

import numpy as np
import pandas as pd
path=r''
rawdatafile=path+ r'/调查结果数据/居民出行调查/乌鲁木齐市居民出行调查数据-0917.xlsx'
#补充了部分接送小孩的出行
typefile=path+ r'/调查结果数据/居民出行调查/kidpicktip_detection2.xlsx'

typedf=pd.read_excel(typefile,sheet_name='NoAdult').dropna()
print(len(typedf))
typedf['AddTrips']=typedf['AddTrips'].replace('yes','Yes')
dfhh0 = pd.read_excel(rawdatafile, sheet_name='家庭信息')
dfpp0 = pd.read_excel(rawdatafile, sheet_name='成员信息')
dftrip0=pd.read_excel(rawdatafile,sheet_name='出行信息')
dftrip0=dftrip0.replace('普通自行车','个人自行车')
deletefml=typedf[typedf['AddTrips']=='Delete']
dftrip0=dftrip0.merge(typedf,how='left',on='家庭编号')
dftrip0=dftrip0[dftrip0['AddTrips']!='Delete']
dfpp0=dfpp0.merge(typedf,how='left',on='家庭编号')
dfpp0=dfpp0[dfpp0['AddTrips']!='Delete']
dfhh0=dfhh0.merge(typedf,how='left',on='家庭编号')
dfhh0=dfhh0[dfhh0['AddTrips']!='Delete']

dftripiddup=dftrip0.groupby('出行编号')['出行序号'].count().reset_index()
dftripiddup=dftripiddup[dftripiddup['出行序号']>1]



def primarymode(dftripn):
    nameind=dftripn.groupby(['使用的主要交通方式'])['出行序号'].count().argmax()
    return dftripn.groupby(['使用的主要交通方式'])['出行序号'].count().index[nameind]
###给需要加trips的成员打mark
dfpp0['pickkid']=0 ##是否接送孩子的优先级 0最低最不可能,2:退休待业人员,需要加4次trip,1：工作人员，需要加2次trip
dfpp0['primarymode']=''
for j in dfpp0[dfpp0['指定调查日是否有出行']=='有出行'].index:
    ppid=dfpp0.loc[j,'成员编号']
    dftripi = dftrip0[dftrip0['成员编号'] == ppid]
    if len(dftripi)>0:
        dfpp0.loc[j, 'primarymode'] = primarymode(dftripi)
    else:
        print(ppid,'有出行但无记录！')


for i in typedf[typedf['AddTrips']=='Yes'].index:
    familyid=typedf.loc[i,'家庭编号']
    for m in dfpp0[(dfpp0['家庭编号']==familyid)].index:
        if dfpp0.loc[m, '就业就学状态'] in ['离退休', '待业']:
            dfpp0.loc[m, 'pickkid'] = 2
        elif (dfpp0.loc[m, '就业就学状态'] == '工作') and (dfpp0.loc[m, '性别'] == '女'):
            dfpp0.loc[m, 'pickkid'] = 1
        elif (dfpp0.loc[m, '就业就学状态'] == '工作') and (dfpp0.loc[m, '性别'] == '男') and (dfpp0.loc[m,'primarymode'] in ['全程步行','个人自行车','电动自行车','私家车(驾驶)']):
            dfpp0.loc[m, 'pickkid'] = 1
    if dfpp0.loc[(dfpp0['家庭编号']==familyid) &(dfpp0['pickkid']>0),'pickkid'].count()>1:
        maxval=dfpp0.loc[(dfpp0['家庭编号']==familyid) &(dfpp0['pickkid']>0),'pickkid'].max()
        keepid=list(dfpp0.loc[(dfpp0['家庭编号']==familyid) &(dfpp0['pickkid']==maxval),'成员编号'])[0]
        dfpp0.loc[(dfpp0['家庭编号'] == familyid) & (dfpp0['成员编号']!=keepid), 'pickkid']=0
    elif dfpp0.loc[(dfpp0['家庭编号']==familyid) &(dfpp0['pickkid']>0),'pickkid'].count()==0:
        keepid=list(dfpp0.loc[(dfpp0['家庭编号']==familyid)&(dfpp0['年龄']>16) ,'成员编号'])[0]
        dfpp0.loc[(dfpp0['家庭编号'] == familyid) & (dfpp0['成员编号'] == keepid), 'pickkid'] = 1
        dfpp0.loc[(dfpp0['家庭编号'] == familyid) & (dfpp0['成员编号']!=keepid), 'pickkid']=0

pickkiddf=dfpp0[dfpp0['AddTrips']=='Yes'].groupby(['家庭编号','pickkid'])['成员编号'].count().reset_index().pivot(index='家庭编号',columns='pickkid',values='成员编号').reset_index()
pickkiddf=pickkiddf.fillna(0)
pickkiddf['能接送孩子的人数']=pickkiddf[1]+pickkiddf[2]
print(pickkiddf.groupby(['能接送孩子的人数'])['家庭编号'].count())


dftrip0=dftrip0.drop(columns={'就业就学状态','pickkid'})

if ('就业就学状态' not in dftrip0.columns) and ('pickkid'not in dftrip0.columns):
    dftrip0=dftrip0.merge(dfpp0[['成员编号','就业就学状态','pickkid']],how='inner',on='成员编号')

appendtrip=pd.DataFrame(columns=['成员编号','出行序号','出行目的','第一种交通方式','使用的主要出行方式','period'])
for ppid in dfpp0.loc[dfpp0['pickkid']>0,'成员编号']:
    dftripi = dftrip0[dftrip0['成员编号'] == ppid]
    lastseq=dftripi['出行序号'].max()
    worktrip=len(dftripi[dftripi['出行目的']=='上班'])

    if list(dfpp0.loc[dfpp0['成员编号']==ppid,'pickkid'])[0]==2 or worktrip==0: #不需要上班的人员
        mode = primarymode(dftripi)
        print(ppid,mode,'离退休 or 待业')
        if mode in ['全程步行','个人自行车','电动自行车','私家车(驾驶)']:
            appendtripi = pd.DataFrame({
                '成员编号': [ppid, ppid, ppid, ppid],
                '出行序号': [lastseq + 1, lastseq + 2, lastseq + 3, lastseq + 4],
                '出行目的': ['接送人', '回家', '接送人', '回家'],
                '使用的主要出行方式': [mode, mode, mode, mode],
                '第一种交通方式': [mode, mode, mode, mode],
                'period': ['AM_Peak', 'AM_Peak', 'Day_time', 'Day_time']
            })
        else:
            appendtripi = pd.DataFrame({
                '成员编号': [ppid, ppid, ppid, ppid],
                '出行序号': [lastseq + 1, lastseq + 2, lastseq + 3, lastseq + 4],
                '出行目的': ['接送人', '回家', '接送人', '回家'],
                '使用的主要出行方式': ['全程步行', '全程步行', '全程步行', '全程步行'],
                '第一种交通方式': ['全程步行', '全程步行', '全程步行', '全程步行'],
                'period': ['AM_Peak', 'AM_Peak', 'Day_time', 'Day_time']
            })
        appendtrip=pd.concat([appendtrip,appendtripi],ignore_index=True)
    elif list(dfpp0.loc[dfpp0['成员编号']==ppid,'pickkid'])[0]==1 or worktrip>0: #需要上班的人员
        mode = primarymode(dftripi)
        print(ppid, mode, '工作')
        if mode in ['全程步行','个人自行车','电动自行车','私家车(驾驶)']:
            appendtripi = pd.DataFrame({
                '成员编号': [ppid, ppid],
                '出行序号': [lastseq + 1, lastseq + 2],
                '出行目的': ['接送人',  '接送人'],
                '使用的主要出行方式': [mode, mode],
                '第一种交通方式': [mode, mode],
                'period': ['AM_Peak',  'Day_time']
            })
        else:
            appendtripi = pd.DataFrame({
                '成员编号': [ppid, ppid],
                '出行序号': [lastseq + 1, lastseq + 2],
                '出行目的': ['接送人',  '接送人'],
                '使用的主要出行方式': ['全程步行', '全程步行'],
                '第一种交通方式': ['全程步行', '全程步行'],
                'period': ['AM_Peak',  'Day_time']
            })
        appendtrip=pd.concat([appendtrip,appendtripi],ignore_index=True)

print(len(appendtrip))

####
appendtrip=appendtrip.merge(dfpp0[['成员编号','家庭编号','区域名称', '街道名称', '社区名称']],how='left',on='成员编号')
appendtrip['其他出行目的']='接送幼儿'

appendtrip=appendtrip[['家庭编号','成员编号', '出行序号','区域名称', '街道名称', '社区名称','出行目的', '第一种交通方式', '使用的主要出行方式', 'period']]
writer=pd.ExcelWriter(path+r'/调查结果数据/居民出行调查/乌鲁木齐市居民出行调查数据-0918.xlsx')
dfhh0.to_excel(writer,sheet_name='家庭信息', startrow=0, startcol=0,index=False)
dfpp0.to_excel(writer,sheet_name='成员信息', startrow=0, startcol=0,index=False)
dftrip0.to_excel(writer,sheet_name='出行信息', startrow=0, startcol=0,index=False)
appendtrip.to_excel(writer, sheet_name='appendtrips', startrow=0, startcol=0,index=False)
writer.save()
#把appendtrip加到raw data 的excel里


