## Process
### Preparation
##### Manual Download Website code

* Navigate to [MICS survey site](http://mics.unicef.org/surveys)
* Sign in
* Save the website (This has to be after signning in)
    * Manually click different available page numbers at the bottom of the website
    * Save the html of all pages into ***htmls folder***
    Click three dots at the right corner of Chrome=>more tools=>Save website
    
##### Save Original data
* Save catalogue list
    * Click Green button Export on the site
    * Move the downloaded ***source_data/surveys_catalogue.csv*** to the working directory
* Download UIS HHS data 
    * save as ***source_data/SEP_2020_HHS_27-10-08.csv***
* Save EDUN_data country reference from UIS as 
***source_data//EDUN_COUNTRY.csv***

### Scrap MICS and join with HHS 

* Run scrap_join notebook or ***scrap_join.py***
* Output a csv with not joined surveys ***mismatch.csv***

### Manually fix mis-aligned surveys
* manually join the misaligned surveys due to entry issues which is supposed to match 
* filter surveys we manually joined out
* filter the subnational surveys out
* the surveys left are those national surveys in MICS but not in HHS
* Save filtered result as ***survey_to_download.csv***

###  Download and extract datasets

* run download_extract notebook or ***download_extract.py***
* data will be downloaded in the data_downloaded folder

   