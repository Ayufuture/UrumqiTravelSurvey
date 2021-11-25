
import pandas as pd

pd.options.mode.chained_assignment = None  # default='warn'
rawdatafile=r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\乌鲁木齐市居民出行调查数据-0914.xlsx'
restrictionfile=r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Restrictions0922.xlsx'
df5_kidfilename=r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Results\Results0922\df_Kid_adj.xlsx'
dfstr_kidfilename=r'C:\Users\yi.gu\Documents\Hyder Related\调查结果数据\居民出行调查\Results\Results0922\dfStr_Kid_adj.xlsx'

df0=pd.read_excel(rawdatafile,sheet_name='家庭信息') #info per household) #info per household
df0=df0.rename(columns={'区域名称':'行政区','家庭总人数':'常住人口数','其中不满6周岁人数':'不满6周岁人口数','私人小客车':'私家车'})
"""
dfhh_district=df0.groupby('街道名称').agg(
    resident=pd.NamedAgg(column='常住人口数',aggfunc='sum'),
kid=pd.NamedAgg(column='不满6周岁人口数',aggfunc='sum'),
).reset_index()
print(dfhh_district['kid'].sum(),dfhh_district['resident'].sum(),dfhh_district['kid'].sum()/dfhh_district['resident'].sum())
dfpp0['手机']=dfpp0['移动']+dfpp0['联通']+dfpp0['电信']
dfpp_phone=dfpp0.groupby(['手机'])['成员编号'].count()
print('有手机的人占比',1-dfpp_phone.loc[0]/dfpp_phone.sum())
print('移动市场占有率',dfpp0['移动'].sum()/dfpp0['手机'].sum())
print(dfpp0.loc[dfpp0['移动']>0,'移动'].count()/dfpp0.loc[dfpp0['手机']>0,'手机'].count())

"""
StreetN=pd.read_excel(restrictionfile, sheet_name='StreetNo') #total HH numbers and population per district (常住人口only)
df2=df0.loc[df0['常住人口数']>0,['家庭编号','街道名称','行政区','常住人口数', '不满6周岁人口数','私家车']]
## remove household where resident count doesn't match member table

dfpp0 = pd.read_excel(rawdatafile,sheet_name='成员信息')
dfpp0['居住状态']='常住'
dfpp0.loc[(dfpp0['户口登记情况']=='非乌鲁木齐户籍') & (dfpp0['非乌鲁木齐户籍（20年初起算）']=='居住乌鲁木齐半年以下'),'居住状态']='暂住'
dfpp0.loc[(dfpp0['就业就学状态']=='就学') & (dfpp0['详细地址']=='新疆财经大学'),'居住状态']='暂住'
dfpp1=dfpp0.loc[dfpp0['居住状态']=='常住',:]
dfpp1=dfpp1.loc[dfpp1['年龄']>=6,:]
pp_hhcount=dfpp1.groupby(['家庭编号'])['成员编号'].count().reset_index()
pp_hhcount=pd.merge(pp_hhcount,df2[['家庭编号','常住人口数', '不满6周岁人口数']],how='left',on='家庭编号')
pp_hhcount['non_kid']=pp_hhcount['常住人口数']-pp_hhcount['不满6周岁人口数']
pp_hhcount['mark']=pp_hhcount['成员编号']-pp_hhcount['non_kid']
pp_hhcount=pp_hhcount[pp_hhcount['mark']!=0]
pp_hhcount1 = pp_hhcount[~pp_hhcount['mark'].isnull()]
pp_notmatch=list(set(pp_hhcount1['家庭编号']))
df2['flag']=df2['家庭编号'].apply(lambda x: 1 if x in pp_notmatch else 0)
df2 = df2[df2['flag']==0]
df2 = df2.drop(columns=['flag'])


df3=pd.merge(df2,StreetN,how='inner',left_on='街道名称',right_on='街道名称')
df3=df3.dropna()
df3=df3.drop_duplicates() #1 street number might match multiple streets
dfStr=df3.groupby(by=['扩样街道编号','行政区','CensusPop','CensusHH']).agg(
    HH=pd.NamedAgg(column='扩样街道编号',aggfunc='count'), #HH: household
    Pop=pd.NamedAgg(column='常住人口数',aggfunc='sum'), #Pop: population
    Kid=pd.NamedAgg(column='不满6周岁人口数',aggfunc='sum'), #Kid: kid under 6
    Car=pd.NamedAgg(column='私家车',aggfunc='sum'), #car:private car
).reset_index()
dfStr['HHweight']=dfStr['CensusHH']/dfStr['HH'] #household weight per district
dfStr['HHsize_Census']=dfStr['CensusPop']/dfStr['CensusHH'] #household size
df4_HHsize=pd.merge(df3,dfStr[['扩样街道编号','HHweight','HHsize_Census']],how='inner',on='扩样街道编号')
##check if hh * hhweight match the total hh per street
df_HHcheck=df4_HHsize.groupby(['扩样街道编号','CensusHH'])['HHweight'].sum().reset_index()
df_HHcheck=df_HHcheck.rename(columns={'HHweight':'HH_predict'})
df_HHcheck['HH_diff']=df_HHcheck['CensusHH']-df_HHcheck['HH_predict']

while (len(df_HHcheck[abs(df_HHcheck['HH_diff'])>0.0001]) >0):
    Strlist=list(df_HHcheck[abs(df_HHcheck['HH_diff'])>0.0001]['扩样街道编号'])
    if len(Strlist)>0:
        df_HHadj = df_HHcheck[abs(df_HHcheck['HH_diff']) > 0.0001]
        df_HHadj['weightadj'] = df_HHadj['CensusHH'] / df_HHadj['HH_predict']
        for streeti in Strlist:
            df4_HHsize.loc[df4_HHsize['扩样街道编号']==streeti,'HHweight'] = \
                df4_HHsize.loc[df4_HHsize['扩样街道编号']==streeti,'HHweight'] * df_HHadj.loc[df_HHadj['扩样街道编号']==streeti,'weightadj']
        df_HHcheck = df4_HHsize.groupby(['扩样街道编号', 'CensusHH'])['HHweight'].sum().reset_index()
        df_HHcheck = df_HHcheck.rename(columns={'HHweight': 'HH_predict'})
        df_HHcheck['HH_diff'] = df_HHcheck['CensusHH'] - df_HHcheck['HH_predict']
    else:
        print("HH total per street is checked!")

### check hh size

dfStr_HHsize = df4_HHsize.groupby(['扩样街道编号', '常住人口数', 'HHsize_Census']).agg(
    HHCount=pd.NamedAgg(column='HHweight', aggfunc='count'),  # HH: household
).reset_index()
dfStr['HHsize_sample'] = dfStr['Pop'] / dfStr['HH']
dfStr_HHsize = pd.merge(dfStr_HHsize, dfStr[['扩样街道编号','CensusPop', 'HH', 'HHweight','HHsize_sample']], how='inner', on='扩样街道编号')
dfStr_HHsize['size_adj'] = 1
dfStr_HHsize['size_err'] = abs(
    (dfStr_HHsize['HHsize_sample'] - dfStr_HHsize['HHsize_Census']) / dfStr_HHsize['HHsize_Census'])
for streeti in list(set(dfStr_HHsize['扩样街道编号'])):
    dfStr_HHsizei = dfStr_HHsize[dfStr_HHsize['扩样街道编号'] == streeti]
    pop_sample=(dfStr_HHsizei['常住人口数']*dfStr_HHsizei['HHCount']*dfStr_HHsizei['HHweight']*dfStr_HHsizei['size_adj']).sum()
    pop_census=dfStr_HHsizei['CensusPop'].mean()
    pop_err=abs(pop_sample-pop_census)
    i = 0
    while (pop_err>=0.1):
        i = i + 1
        hhsizes = dfStr_HHsizei['HHsize_sample'].mean()
        hhsizec = dfStr_HHsizei['HHsize_Census'].mean()
        dfStr_HHsizei.loc[dfStr_HHsizei['常住人口数'] > hhsizec, 'size_adj'] = (hhsizec / hhsizes) * \
                                                                              dfStr_HHsizei.loc[dfStr_HHsizei[
                                                                                                    '常住人口数'] > hhsizec, 'size_adj']
        hhpred = (dfStr_HHsizei['HHCount'] * dfStr_HHsizei['size_adj']).sum()
        hhsamp = dfStr_HHsizei['HH'].mean()
        dfStr_HHsizei['size_adj'] = (hhsamp / hhpred) * dfStr_HHsizei['size_adj']
        hhave = (dfStr_HHsizei['常住人口数'] * dfStr_HHsizei['HHCount'] * dfStr_HHsizei['size_adj']).sum() / \
                (dfStr_HHsizei['HHCount'] * dfStr_HHsizei['size_adj']).sum()
        dfStr_HHsizei['HHsize_sample'] = hhave
        dfStr_HHsizei['size_err'] = abs(
            (dfStr_HHsizei['HHsize_sample'] - dfStr_HHsizei['HHsize_Census']) / dfStr_HHsizei['HHsize_Census'])
        pop_sample = (dfStr_HHsizei['常住人口数'] * dfStr_HHsizei['HHCount'] * dfStr_HHsizei['HHweight'] * dfStr_HHsizei[
            'size_adj']).sum()
        pop_err = abs(pop_sample - pop_census)
        print("hh size census: {} sample {}".format(hhsizec, hhsizes))
    print("街道 {} loop {} pop_sample{} pop_census{}".format(streeti, i,pop_sample,pop_census))

    dfStr_HHsize.loc[dfStr_HHsize['扩样街道编号'] == streeti, ['size_adj', 'HHsize_sample', 'size_err']] = dfStr_HHsizei.loc[
                                                                                                     :, ['size_adj',
                                                                                                         'HHsize_sample',
                                                                                                         'size_err']]
df5_HHsize=pd.merge(df4_HHsize,dfStr_HHsize[['扩样街道编号', '常住人口数','size_adj']],how='left',on=['扩样街道编号','常住人口数'])
df5_HHsize['total']=df5_HHsize['HHweight']*df5_HHsize['size_adj']*df5_HHsize['常住人口数']
dfStr1=df5_HHsize.groupby(['扩样街道编号', 'CensusPop','CensusHH'])['total'].sum().reset_index()
dfStr1['diff']=dfStr1['CensusPop']-dfStr1['total']
print(dfStr1)
#df5_HHsize.to_excel(r'D:\Hyder安诚\调查结果数据\居民出行调查\Results\df_HHsize_adj.xlsx', sheet_name='df_HHsize',index=False)
#dfStr_HHsize.to_excel(r'D:\Hyder安诚\调查结果数据\居民出行调查\Results\dfStr_HHsize_adj.xlsx', sheet_name='dfStr_HHsize',index=False)


print("请选择车辆信息表的形式：1：全市；2：分区；3：分街道，请输入数字")
VehTableN=input()
VehDF=pd.read_excel(restrictionfile, sheet_name='Vehicle') # private vehicle information

df5_Veh=df5_HHsize
df5_Veh['HHweight2']=df5_Veh['HHweight']*df5_Veh['size_adj']
dfStr_Veh = df5_Veh.groupby(['扩样街道编号', '行政区', '常住人口数', '私家车', 'HHsize_Census', 'CensusPop','CensusHH', 'HHweight2']).agg(
    HHCount=pd.NamedAgg(column='HHweight', aggfunc='count'),  # HH: household
).reset_index()
dfStr_Veh['veh_adj'] = 1
if VehTableN=='1': # only total vehicle number of whole city is available, dataframe should be 1 row 2 columns
    print("请选择车总数：1：961039；2：937565；请输入数字")
    option = input()
    if option=='1':
        veh = VehDF.iloc[0, 1]
    else:
        veh=VehDF.iloc[1,1]

    #adjust the weight of hh with vehicles
    vehpred = (dfStr_Veh['私家车'] * dfStr_Veh['HHweight2'] * dfStr_Veh['veh_adj'] * dfStr_Veh['HHCount']).sum()
    veh_err= abs(vehpred-veh)
    loopv=0
    total_pop_sample = (dfStr_Veh['常住人口数'] * dfStr_Veh['HHweight2'] * dfStr_Veh['veh_adj'] * dfStr_Veh['HHCount']).sum()
    total_pop_err=abs(total_pop_sample-StreetN['CensusPop'].sum())
    while ((veh_err >=1 or total_pop_err>10) and loopv <100):
        loopv=loopv+1
        dfStr_Veh.loc[dfStr_Veh['私家车'] > 0, 'veh_adj'] = (veh / vehpred) * dfStr_Veh.loc[
            dfStr_Veh['私家车'] > 0, 'veh_adj']
        # make sure the total hh number per district matches census data
        for streeti in list(set(dfStr_Veh['扩样街道编号'])):
            dfStr_Vehi = dfStr_Veh[dfStr_Veh['扩样街道编号'] == streeti]
            if len(dfStr_Vehi) > 0:
                hhtotal_pred = (dfStr_Vehi['HHCount'] * dfStr_Vehi['HHweight2'] * dfStr_Vehi['veh_adj']).sum()
                hhtotal_census = dfStr_Vehi['CensusHH'].mean()
                dfStr_Vehi['veh_adj'] = dfStr_Vehi['veh_adj'] * (hhtotal_census / hhtotal_pred)
                pop_sample = (dfStr_Vehi['常住人口数'] * dfStr_Vehi['HHCount'] * dfStr_Vehi['HHweight2'] *
                              dfStr_Vehi['veh_adj']).sum()
                pop_census = dfStr_Vehi['CensusPop'].mean()
                pop_err = abs(pop_sample - pop_census)
                hhsize_pred = pop_sample / (dfStr_Vehi['HHCount'] * dfStr_Vehi['HHweight2'] * dfStr_Vehi['veh_adj']).sum()
                hhsize_census = dfStr_Vehi['HHsize_Census'].mean()
                HHsize_err = abs((hhsize_pred - hhsize_census) / hhsize_census)
                loopi = 0
                while (loopi <= 100 and pop_err>= 0.01):
                    loopi = loopi + 1
                    dfStr_Vehi.loc[dfStr_Vehi['常住人口数'] > hhsize_census, 'veh_adj'] = dfStr_Vehi.loc[dfStr_Vehi[
                                                                                                            '常住人口数'] > hhsize_census, 'veh_adj'] * (
                                                                                                 hhsize_census / hhsize_pred)
                    hhtotal_pred = (dfStr_Vehi['HHCount'] * dfStr_Vehi['HHweight2'] * dfStr_Vehi['veh_adj']).sum()
                    dfStr_Vehi['veh_adj'] = dfStr_Vehi['veh_adj'] * (hhtotal_census / hhtotal_pred)
                    pop_sample = (dfStr_Vehi['常住人口数'] * dfStr_Vehi['HHCount'] * dfStr_Vehi['HHweight2'] *
                                  dfStr_Vehi['veh_adj']).sum()
                    hhsize_pred = pop_sample / (dfStr_Vehi['HHCount'] * dfStr_Vehi['HHweight2'] * dfStr_Vehi['veh_adj']).sum()
                    HHsize_err = abs((hhsize_pred - hhsize_census) / hhsize_census)

                    pop_err = abs(pop_sample - pop_census)
            else:
                print("{} vehicle weight is unable to update".format(streeti))
            dfStr_Veh.loc[dfStr_Veh['扩样街道编号'] == streeti, 'veh_adj'] = dfStr_Vehi.loc[:, 'veh_adj']
        vehpred = (dfStr_Veh['私家车'] * dfStr_Veh['HHweight2'] * dfStr_Veh['veh_adj'] * dfStr_Veh['HHCount']).sum()
        veh_err = abs(vehpred - veh)
        total_pop_sample = (dfStr_Veh['常住人口数'] * dfStr_Veh['HHweight2'] * dfStr_Veh['veh_adj'] * dfStr_Veh['HHCount']).sum()
        total_pop_err = abs(total_pop_sample - StreetN['CensusPop'].sum())
        print('vehicle adjustment loop {} vehicle err {} pop_err {}'.format(loopv,int(veh_err),int(total_pop_err)))
    df5_Veh=pd.merge(df5_Veh,dfStr_Veh[['扩样街道编号', '行政区', '常住人口数', '私家车','veh_adj']],how='left',on=['扩样街道编号', '行政区', '常住人口数', '私家车'])
    #df5_Veh.to_excel(r'D:\Hyder安诚\调查结果数据\居民出行调查\Results\df_Veh_adj.xlsx', sheet_name='df_Veh',index=False)
    #dfStr_Veh.to_excel(r'D:\Hyder安诚\调查结果数据\居民出行调查\Results\dfStr_Veh_adj.xlsx', sheet_name='dfStr_Veh',index=False)



#### update kid proportion
print("请选择不满6周岁人口比例表的形式：1：全市；2：分区；3：分街道，请输入数字")
KidTableN=input()
KidDF=pd.read_excel(restrictionfile, sheet_name='Kid') # private vehicle information
df5_Kid=df5_Veh
df5_Kid['HHweight3']=df5_Kid['HHweight2']*df5_Kid['veh_adj']
dfStr_Kid = df5_Kid.groupby(['扩样街道编号', '行政区', '常住人口数', '私家车','不满6周岁人口数', 'HHsize_Census','CensusPop', 'CensusHH', 'HHweight3']).agg(
    HHCount=pd.NamedAgg(column='HHweight', aggfunc='count'),  # HH: household
).reset_index()
dfStr_Kid['kid_adj'] = 1
if KidTableN=='1': # only total kid under 6 number of whole city is available, dataframe should be 1 row 2 columns
    kid=KidDF.iloc[0,1]
    #kid=147141
    kidtotal=(dfStr_Kid['kid_adj'] * dfStr_Kid['不满6周岁人口数'] * dfStr_Kid['HHCount'] * dfStr_Kid['HHweight3']).sum()
    kid_err=abs(kidtotal-kid)
    vehtotal = (dfStr_Kid['kid_adj'] * dfStr_Kid['私家车'] * dfStr_Kid['HHCount'] * dfStr_Kid['HHweight3']).sum()
    veh_err = abs(vehtotal - 961039)
    pptotal = (dfStr_Kid['kid_adj'] * dfStr_Kid['常住人口数'] * dfStr_Kid['HHCount'] * dfStr_Kid['HHweight3']).sum()
    pp_err = abs(pptotal - StreetN['CensusPop'].sum())
    loopk = 0
    while loopk < 100 and (kid_err>= 1 or veh_err>=5 or pp_err>=50) :
        loopk=loopk+1
        dfStr_Kid.loc[dfStr_Kid['不满6周岁人口数'] > 0, 'kid_adj'] = dfStr_Kid.loc[dfStr_Kid['不满6周岁人口数'] > 0, 'kid_adj'] * (
                    kid / kidtotal)
        for streeti in list(set(dfStr_Kid['扩样街道编号'])):
            dfStr_kidi = dfStr_Kid[dfStr_Kid['扩样街道编号'] == streeti]
            hhtotal_census = dfStr_kidi['CensusHH'].mean()
            hhsize_census = dfStr_kidi['HHsize_Census'].mean()
            pop_census = dfStr_kidi['CensusPop'].mean()
            hhtotal_pred = (dfStr_kidi['kid_adj'] * dfStr_kidi['HHCount'] * dfStr_kidi['HHweight3']).sum()
            dfStr_kidi['kid_adj'] = dfStr_kidi['kid_adj'] * hhtotal_census / hhtotal_pred
            veh = (dfStr_kidi['私家车'] * dfStr_kidi['HHCount'] * dfStr_kidi['HHweight3']).sum()
            veh_pred = (dfStr_kidi['kid_adj'] * dfStr_kidi['私家车'] * dfStr_kidi['HHCount'] * dfStr_kidi[
                'HHweight3']).sum()
            veh_err = abs(veh_pred - veh)
            #print("街道 {} initial veh_err {}".format(streeti,veh_err))
            loopv = 0
            while loopv < 100 and veh_err >= 0.1:
                loopv = loopv + 1
                dfStr_kidi.loc[dfStr_kidi['私家车'] > 0, 'kid_adj'] = dfStr_kidi.loc[dfStr_kidi[
                                                                                      '私家车'] > 0, 'kid_adj'] * veh / veh_pred
                hhtotal_pred = (dfStr_kidi['kid_adj'] * dfStr_kidi['HHCount'] * dfStr_kidi['HHweight3']).sum()
                dfStr_kidi['kid_adj'] = dfStr_kidi['kid_adj'] * hhtotal_census / hhtotal_pred
                hhsize_pred = (dfStr_kidi['kid_adj'] * dfStr_kidi['常住人口数'] * dfStr_kidi['HHCount'] * dfStr_kidi[
                    'HHweight3']).sum() / (
                                          dfStr_kidi['kid_adj'] * dfStr_kidi['HHCount'] * dfStr_kidi['HHweight3']).sum()
                hhsize_err = abs(hhsize_pred - hhsize_census) / hhsize_census
                pop_sample = (dfStr_kidi['常住人口数'] * dfStr_kidi['HHCount'] * dfStr_kidi['HHweight3'] *
                              dfStr_kidi['kid_adj']).sum()

                pop_err = abs(pop_sample - pop_census)
                loopi = 0
                while loopi < 100 and pop_err >= 0.01:
                    loopi = loopi + 1
                    dfStr_kidi.loc[dfStr_kidi['常住人口数'] > hhsize_census, 'kid_adj'] = dfStr_kidi.loc[dfStr_kidi[
                                                                                                            '常住人口数'] > hhsize_census, 'kid_adj'] * (
                                                                                                 hhsize_census / hhsize_pred)
                    hhtotal_pred = (dfStr_kidi['kid_adj'] * dfStr_kidi['HHCount'] * dfStr_kidi['HHweight3']).sum()
                    dfStr_kidi['kid_adj'] = dfStr_kidi['kid_adj'] * hhtotal_census / hhtotal_pred
                    hhsize_pred = (dfStr_kidi['kid_adj'] * dfStr_kidi['常住人口数'] * dfStr_kidi['HHCount'] * dfStr_kidi[
                        'HHweight3']).sum() / (
                                          dfStr_kidi['kid_adj'] * dfStr_kidi['HHCount'] * dfStr_kidi['HHweight3']).sum()
                    hhsize_err = abs(hhsize_pred - hhsize_census) / hhsize_census
                    pop_sample = (dfStr_kidi['常住人口数'] * dfStr_kidi['HHCount'] * dfStr_kidi['HHweight3'] *
                                  dfStr_kidi['kid_adj']).sum()
                    pop_err = abs(pop_sample - pop_census)
                    #print("街道{} : 车辆 loop {} error {}, Population loop {} error {} ".format(streeti, loopv, veh_err,loopi,pop_err))
                veh_pred = (dfStr_kidi['kid_adj'] * dfStr_kidi['私家车'] * dfStr_kidi['HHCount'] * dfStr_kidi[
                    'HHweight3']).sum()
                veh_err = abs(veh_pred - veh)
            dfStr_Kid.loc[dfStr_Kid['扩样街道编号'] == streeti,'kid_adj']=dfStr_kidi.loc[dfStr_kidi['扩样街道编号'] == streeti,'kid_adj']
        kidtotal = (dfStr_Kid['kid_adj'] * dfStr_Kid['不满6周岁人口数'] * dfStr_Kid['HHCount'] * dfStr_Kid['HHweight3']).sum()
        kid_err = abs(kidtotal - kid)
        vehtotal = (dfStr_Kid['kid_adj'] * dfStr_Kid['私家车'] * dfStr_Kid['HHCount'] * dfStr_Kid['HHweight3']).sum()
        veh_err = abs(vehtotal - 961039)
        pptotal = (dfStr_Kid['kid_adj'] * dfStr_Kid['常住人口数'] * dfStr_Kid['HHCount'] * dfStr_Kid['HHweight3']).sum()
        pp_err = abs(pptotal - StreetN['CensusPop'].sum())
    print("车辆 loop {} error {}, Population error {} ".format(loopv, int(veh_err),int(pp_err)))
    print(loopk,int(kid_err) )

    df5_Kid=pd.merge(df5_Kid,dfStr_Kid[['扩样街道编号', '行政区', '常住人口数', '私家车','不满6周岁人口数','kid_adj']], how='left',
                     on=['扩样街道编号', '行政区', '常住人口数', '私家车','不满6周岁人口数'])
    df5_Kid['HHweight4'] = df5_Kid['HHweight3'] * df5_Kid['kid_adj']
    df5_Kid.to_excel(df5_kidfilename, sheet_name='df_Kid',index=False)
    dfStr_Kid.to_excel(dfstr_kidfilename, sheet_name='dfStr_Kid',index=False)

print('population 3388129:',sum(dfStr_Kid['常住人口数']*dfStr_Kid['HHweight3']*dfStr_Kid['kid_adj']*dfStr_Kid['HHCount']))
print('vehicle 961039:',sum(dfStr_Kid['私家车']*dfStr_Kid['HHweight3']*dfStr_Kid['kid_adj']*dfStr_Kid['HHCount']))
print('kid 23359:',sum(dfStr_Kid['不满6周岁人口数']*dfStr_Kid['HHweight3']*dfStr_Kid['kid_adj']*dfStr_Kid['HHCount']))



