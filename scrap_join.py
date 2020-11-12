#!/usr/bin/env python
# coding: utf-8

# In[46]:


import requests
import pandas as pd
import numpy as np
from pyquery import PyQuery as pq
import re
import urllib.parse
import os


# In[2]:


# get the available survey information from a single html
def get_url_per(file):
    df=pd.DataFrame(columns=['link','year','country','round'])
#   read in the html
    data = pq(open(file,'r').read())
    links= data('span:contains(Available)').prev_all()
    for span in links:
#       get the download url
        url=pq(span).attr('href')
#       decode url to normal text, extract year,country and round from decoded_url
        decoded_url=urllib.parse.unquote(url)
        year=re.findall('/\d+\W*\d+/',decoded_url)[0][1:-1]
        country=re.findall('/[^/]*/\d',decoded_url)[0][1:-2]
        round_s=re.findall('MICS\d',decoded_url)[-1]
#       add extracted data into the df
        df.loc[-1] = [url, year, country, round_s]  # adding a row
        df.index = df.index + 1  # shifting index
        df = df.sort_index()  # sorting by index
    return df


# In[3]:


# get the available survey info from all html pages
def getall ():
    df=pd.DataFrame(columns=['link','year','country','round'])
    for root, dirs, files in os.walk('htmls', topdown=False):
                for name in files:
                    file_name=os.path.join(root, name)
                    current_df=get_url_per(file_name)
                    df=pd.concat([df,current_df])
    return df


# In[4]:


# df_links is info of avaiable surveys derived from download url for each survey dataset
df_links=getall ()


# In[5]:


# the survey catalogue list downloaded from MICs site
df_survey=pd.read_csv('source_data//surveys_catalogue.csv')


# In[6]:


country_code=pd.read_csv('source_data//EDUN_COUNTRY.csv')


# In[39]:


# Join the scarped survey info with download link to the survey catelogue 
# Select only the survey with datasets available
# df_available is the df from MICS site
df_available=(pd.merge(df_survey,df_links,how='outer',on=['year','country','round'])
                .query('datasets=="Available"')
                .assign(year = lambda x:x['year'].astype('str'))
    )


# In[40]:


# Join df_available with UIS country_code
# check where the same country has different names in UIS database and MICS database
df_temp=pd.merge(country_code,df_available,how='right',left_on='COUNTRY_NAME_EN',right_on='country')
df_temp.loc[df_temp['COUNTRY_ID'].isna(),'country'].unique()


# In[41]:


# Manually adjust MICs country name to the UIS country name
df_available.loc[df_available['country']=='State of Palestine','country']='Palestine'
df_available.loc[df_available['country']=='Myanmar, Republic of the Union of','country']='Myanmar'
df_available.loc[df_available['country']=='Congo, Democratic Republic of the','country']='Democratic Republic of the Congo'
df_available.loc[df_available['country']=='South Sudan, Republic of','country']='South Sudan'
df_available.loc[df_available['country']=='Moldova, Republic of','country']='Republic of Moldova'
df_available.loc[df_available['country']=='North Macedonia, Republic of','country']='North Macedonia'
df_available.loc[df_available['country']=='Bolivia, Plurinational State of','country']='Bolivia (Plurinational State of)'
df_available.loc[df_available['country']=='Venezuela, Bolivarian Republic of','country']='Venezuela (Bolivarian Republic of)'
df_available.loc[df_available['country']=='Sudan (including current South Sudan, Republic of)','country']='Sudan'
# df_available = (df_available.assign(iso3 = lambda x: x['country'].apply(lambda i: find_iso(i))))


# In[42]:


# Join df_available with UIS country_code
# check if the unmatched country names are all sub-national areas
df_available=pd.merge(country_code,df_available,how='right',left_on='COUNTRY_NAME_EN',right_on='country')
df_available.loc[df_available['COUNTRY_ID'].isna(),'country'].unique()


# In[43]:


df_available.drop(columns='COUNTRY_NAME_EN',inplace=True)
df_available.rename(columns={'COUNTRY_ID':'ISO'},inplace=True)
df_available


# In[14]:


# function to get MICs info from the HHS data Note column
def match_MICS(x):
    result=re.findall('^\w+\s+MICS\s\d+\W*\d+\W',x)
    if len(result)>0:
        return result[0][:-1].split(' ')
    else:
        return np.nan


# In[15]:


df_hhs=(pd.read_csv('source_data//SEP_2020_HHS_27-10-08.csv')
          .assign(Mics=lambda x : x['NOTE'].apply(lambda i: match_MICS(i)))
          .query('Mics==Mics')
          .assign(year = lambda x : x['Mics'].apply(lambda i: i[2]))
          .assign(year = lambda x:x['year'].astype('str'))
          .assign(country =lambda x : x['Mics'].apply(lambda i: i[0]))
       )


# In[16]:


# Check if any country name in HHS database and the country_code in UIS
df_temp2=pd.merge(country_code,df_hhs,how='right',left_on='COUNTRY_NAME_EN',right_on='country')
df_temp2.loc[df_temp2['COUNTRY_ID'].isna(),'country'].unique()


# In[17]:


# Manually adjust this different country name
df_hhs.loc[df_hhs['country']=='Swaziland','country']='Eswatini'


# In[18]:


# add country_code to df_hhs, check again if there is any unmatched country name 
df_hhs=pd.merge(country_code,df_hhs,how='right',left_on='COUNTRY_NAME_EN',right_on='country')
df_hhs.rename(columns={'COUNTRY_ID':'ISO'},inplace=True)
df_hhs[df_hhs['ISO'].isna()].country.unique()


# In[19]:


# We only need the unique combinations of country and year available in HHS dataset, write this to hhs_use
hhs_use=df_hhs.loc[:,['year','country','ISO']].copy()
hhs_use.drop_duplicates(inplace=True)
hhs_use.reset_index(inplace=True,drop=True)


# In[20]:


# formatting the hhs year column, e.g. change '2016-17' to '2016-2017'
# so it matches with the MICS dataset df_available
filter_hhs=(hhs_use['year'].str.contains('-'))&(~hhs_use['year'].str.contains('-20'))
hhs_use.loc[filter_hhs,'year'] = hhs_use.loc[filter_hhs,'year'].apply(lambda x: re.sub(r'-','-20',x))
hhs_use


# In[45]:


# try to join HHS dataset hhs_use with MICS dataset df_available
# filter out the mismatched year and country
# write to mismatch.csv
df_mismatch=(pd.merge(df_available,hhs_use,how='outer',on=['year','ISO'])
            .query('(country_x!=country_x)|(country_y!=country_y)')
)
df_mismatch.reset_index(inplace=True,drop=True)
df_mismatch.to_csv('mismatch.csv')

