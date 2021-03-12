#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import pyreadstat
import os
from pathlib import Path
import re
import functools
import pickle


# In[2]:


MICS6_varstr= 'LN WB2 WB5 WB6 WB7 WB8 WB9 WB10 WB11 WB12 WB13 WB14 wmweight WM17 MWB2   MWB5   MWB6  MWB7   MWB8   MWB9  MWB10   MWB11   MWB12  MWB13    MWB14  mnweight  MWM17 HH3  HH46  HH47  ED4  ED4A ED4B ED5 ED6 ED8 ED9 ED10 ED15 ED16 ED6A ED6B ED8A ED8B HHWEIGHT WB6A WB6B WB12A WB12B'
MICS5_varstr='LN WB3 WB4 WB5 WB6 WB7 wmweight  WM7  MWB3  MWB4  MWB5 MWB6 MWB7 mnweight  MWM7 HH3  HH9   HH10 ED3 ED4A ED4B ED5 ED6 ED7 ED8 ED6A ED6B ED8A ED8B HHWEIGHT WB6A WB6B WB12A WB12B'
MICS4_varstr ='LN WB6 WB7 wmweight WB3 WB4 WB5 WM7 MWM7 MWB3 MWB5 MWB7 HH3  HH9  HH10  ED3 ED4A ED4B ED5 ED6 ED7 ED8 ED6A ED6B ED8A ED8B HHWEIGHT WB6A WB6B WB12A WB12B'
MICS3_varstr='LN WM10 WM11 WM12 WM13  WM14  wmweight  WM7 HH3 HH9 HH10 ED2 ED3 ED4 ED5 ED6 ED7 ED8 ED6A ED6B ED8A ED8B HHWEIGHT WB6A WB6B WB12A WB12B  ED4A ED4B '


# In[3]:


var_6=re.split('\s+',MICS6_varstr)
var_5=re.split('\s+',MICS5_varstr)
var_4=re.split('\s+',MICS4_varstr)
var_3=re.split('\s+',MICS3_varstr)


# In[4]:


# using survey batch to decide variable name for the literacy question
def get_lit_variables (survey,ex_variables):
#   make a copy of the variables
    if 'MICS3' in survey:
        variables=var_3[:]
    elif 'MICS4' in survey:
        variables=var_4[:]
    elif 'MICS5' in survey:
        variables=var_5[:]
    elif 'MICS6' in survey:
        variables=var_6[:]
    
    variables.extend(ex_variables)
    variables_lower= [i.lower() for i in variables]
    variables.extend(variables_lower)
    return variables


# In[5]:


test_hh_variables=['HH1','HH2','HL4','HL6','HL1','HH_WEIGHT','HH3']


# In[6]:


test_hh_variables


# In[7]:


# read in the SPSS data of selected variables
def get_data(filename,survey_name,variables):
    variables=get_lit_variables(survey_name,variables)
    df,meta= pyreadstat.read_sav(filename,apply_value_formats=True, usecols=variables)
    df['survey']=survey_name        
    df.columns = df.columns.str.upper()
    return [df,meta]


# In[14]:


# walk through the downloaded files folder, put joined data into a dataframe for each survey
def walk_4_data(datapath,hh_variables):
#   all_obj used to store all the dataframes for all surveys
    all_obj={}
    df_meta=pd.DataFrame(columns=['var','label','survey','module'])
    for root, dirs, files in os.walk(datapath):
        for dire in dirs:
#           go inside the microdata folder where sav files are stored
#           MICS2 doesn't have literacy question in woman modules, skip MICS2 folders

            if (dire =='microdata') &('MICS2' not in os.path.join(root, dire)):
        
#           empty dfs for this survey
                dfs=[]
                current_dir=os.path.join(root, dire)
        
#               walk through the SAV files in microdata folder
                for name in os.listdir(current_dir): 
                    if name.lower().endswith('mn.sav')|name.lower().endswith('wm.sav')|name.lower().endswith('hl.sav'):
#                       SPSS file path
                        path=os.path.join(current_dir, name)
#                       grandparent folder of the file path, survey_path contains the survey name
                        survey_path=Path(path).parents[1]
#                       Basename is the survey name
                        survey=os.path.basename(survey_path)
    
#                       Get data from SPSS file and add to dfs
                        variables=get_lit_variables(survey,hh_variables)
                        result_survey=get_data(path,survey,variables)
                        df_single=result_survey[0]
                        if ('HL1') in df_single.columns:
                            df_single.rename(columns={'HL1':'LN'},inplace=True)
                        dfs.append(df_single)
#                       merge different module lieracy information into one dataframe

                        my_dict=result_survey[1].column_names_to_labels
                        df_single_meta = pd.DataFrame(list(my_dict.items()),columns = ['var','label']) 
                        df_single_meta['survey']=survey
                        if name.lower().endswith('mn.sav'):
                            df_single_meta['module']='Man'
                        if name.lower().endswith('wm.sav'):
                            df_single_meta['module']='Woman'
                        if name.lower().endswith('hl.sav'):
                            df_single_meta['module']='Household'
                        df_meta=df_meta.append(df_single_meta)


                if  len(dfs)>1:

                    df_final = functools.reduce(lambda left,right: pd.merge(left,right,on=['SURVEY','HH1','HH2','LN'],how='outer'), dfs)
                    if 'HH3_y' in df_final.columns:
                        df_final.drop(columns='HH3_y',inplace=True)
                        df_final.rename(columns={'HH3_x':'HH3'},inplace=True)
                    if 'HH9_y' in df_final.columns:
                        df_final.drop(columns='HH9_y',inplace=True)
                        df_final.rename(columns={'HH9_x':'HH9'},inplace=True)
                    if 'HH10_y' in df_final.columns:
                        df_final.drop(columns='HH10_y',inplace=True)
                        df_final.rename(columns={'HH10_x':'HH10'},inplace=True)
                    df_final.to_csv('result_csv//'+survey+'.csv',encoding='utf-8-sig')
                    all_obj[survey]= df_final
                    print(survey)


    return [all_obj,df_meta]


# In[15]:


all_result=walk_4_data('C://Users//annda//1//Documents//UIS//Nov//default//data_downloaded',test_hh_variables)


# In[18]:


df_metadata_total=all_result[1]
df_metadata_total.reset_index(inplace=True,drop=True)
df_metadata_total.to_csv('result_csv//metadata.csv',encoding='utf-8-sig')


# In[11]:


f = open("result//all.pkl","wb")
pickle.dump(all_result[0],f)
f.close()

