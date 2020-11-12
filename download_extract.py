#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import pandas as pd
import numpy as np
import re
import os
from os import listdir
from os.path import isfile, join
import zipfile
import shutil


# In[2]:


# manually join the misaligned surveys due to entry issues which is supposed to match 
# filter them out
# filter the subnational datasets out
# surveys in mismatch_filtered are those to be downloaded
df_download=(pd.read_csv('survey_to_download.csv')
#           create a column for unique identifier in the form of iso3c_survey_year
            .assign(filename = lambda x: x['ISO']+'_'+x['round']+'_'+x['year'])
            )
df_download


# In[3]:


# download the zip using links and extract them into proper folder

def download_df(df,no):
#   no is number of surveys we are downloading and unziping
    for i in range(0,no):
        url = df.loc[i,'link']
#       dir_new is folder for the survey
        dir_new = 'data_downloaded//'+ df.loc[i,'filename']
#       file_name is the zip downloaded
        file_name = 'data_downloaded//'+ df.loc[i,'filename']+'.zip'
#       micro_data is spss data folder
        micro_data = dir_new +'//microdata'
#       doc_data is documentation folder
        doc_data = dir_new +'//documentation'
    
#       Create folders if they don't already exist
        if os.path.exists('data_downloaded')==False:
             os.makedirs('data_downloaded')
        if os.path.exists(dir_new)==False:
             os.makedirs(dir_new)
        if os.path.exists(micro_data)==False:
             os.makedirs(micro_data)
        if os.path.exists(doc_data)==False:
             os.makedirs(doc_data)
                
#  Check if zip file for the survey already downloaded, if not download and save
        downloaded_zips = [f for f in listdir('data_downloaded') if isfile(join('data_downloaded', f))]
        if file_name not in downloaded_zips:
            r = requests.get(url, allow_redirects=True)
            open(file_name, 'wb').write(r.content)
            
#       Extract file into the survey folder  
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            zip_ref.extractall(dir_new)
            
#       move documentation file into the documentation folder, other files in the microdata folder
        for root, dirs, files in os.walk(dir_new, topdown=False):
                for name in files:
                    if name.endswith('doc')|name.endswith('txt')|name.endswith('DOC'):
                        os.replace(os.path.join(root, name),os.path.join(doc_data, name))
                    else:
                        os.replace(os.path.join(root, name),os.path.join(micro_data, name))
                        
#           Delete the original extracted folder
                for dir in dirs:
                    if 'MICS' in dir:
                        shutil.rmtree(os.path.join(root, dir))

        os.replace(file_name,dir_new+'//'+ df.loc[i,'filename']+'.zip') 


# In[4]:


# Yeah, we want to download all rows in df_download
download_df(df_download,df_download.shape[0])

