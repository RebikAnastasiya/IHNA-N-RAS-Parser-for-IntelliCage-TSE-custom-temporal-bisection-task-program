# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 13:38:30 2024

@author: Ольга
"""
import os
import pandas as pd
data_path = r'C:\Users\akhmi\OneDrive\Рабочий стол\ИВНД\журнал\ratus\behav2024\analysis\learning\11.03-12.03'
#input_txt_path = os.path.join(data_path, 'Input.txt')
list_fls = pd.read_csv(r'C:\Users\akhmi\OneDrive\Рабочий стол\ИВНД\журнал\ratus\behav2024\analysis\learning\11.03-12.03\list.txt',header= None)
# create common lists for all rats
for nm_fl in list_fls[0]:
 if  'common' in locals() :
                stat_one = pd.read_excel(os.path.join(data_path,nm_fl+'.xlsx'))
                common = pd.concat([common,stat_one],sort=False,axis=0) 
 else :
                common = pd.read_excel(os.path.join(data_path,nm_fl+'.xlsx'))
                #common_mean =  pd.DataFrame( common.columns).T
                #common_sd = common_mean             
un_tags = common.animal_tag.unique()            
for one_rat in un_tags:
     df_one_rat = common[common.animal_tag == one_rat]
     del df_one_rat['animal_tag']
     df_init =  pd.DataFrame({'animal_tag' : [one_rat]})
     df_mean = pd.concat([df_init, pd.DataFrame(df_one_rat.mean()).T],sort=False,axis=1)
     df_sd =  pd.concat([df_init,pd.DataFrame(df_one_rat.std()).T],sort=False,axis=1)
     if  'common_mean' in locals() :
         common_mean = pd.concat([common_mean, df_mean],sort=False,axis=0) 
         common_sd = pd.concat([common_sd, df_sd],sort=False,axis=0)
     else:
         common_mean = df_mean
         common_sd = df_sd    
common_mean.to_excel('Mean.xlsx', sheet_name='mean', index=False)       
common_sd.to_excel('Std.xlsx', sheet_name='sd', index=False)
del common_mean
del common_sd
del common
