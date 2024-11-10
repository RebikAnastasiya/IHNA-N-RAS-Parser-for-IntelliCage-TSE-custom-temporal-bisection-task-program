'''

*Заметки по запуску*

Для запуска нужнны библиотеки

  python -m pip install pandas openpyxl

Чтобы указать папку для анализа, изменяется переменная *data_path*. В
папке должны быть файлы Input.txt, Visits.txt, Nosepokes.txt

'''
import os

import pandas as pd
from datetime import datetime, timedelta


# data_path = '/home/administrator/Public/invd__intelicage_parser/sample_data/IntelliCage/'
# experiment_date = input('Enter folder path: ')
data_path = r'C:\Users\akhmi\OneDrive\Рабочий стол\ИВНД\журнал\ratus\behav2024\archive\2024-05-17 14.46.29\IntelliCage'   #2023-11-13 15.02.21  2024-03-08 14.03.23
time_begin = ' 16:00:00.000'
time_end = ' 23:59:59.000'
experiment_date = input('Experiment date on (format 2023-04-01): ')
output_file = 'results_' + experiment_date + '_' + time_begin.replace(':','-')[:6] + '_' + time_end.replace(':','-')[:6]+'.xlsx'
stat_output_file = 'stat2_' + experiment_date + '_' + time_begin.replace(':','-')[:6] + '_' + time_end.replace(':','-')[:6]+'.xlsx'

#output_file = 'result_learn_2.xlsx'

####################################################################################################
# constants
####################################################################################################
# 'known_intervals_delta' - timedelta to lookup standard intervals
known_intervals_delta = timedelta(seconds=.2)
# 'known_intervals' - list of intervals in which interval lookup is done with delta 'known_intervals_delta'
known_intervals = [
    timedelta(seconds=4),
    timedelta(seconds=1),
    timedelta(seconds=1.7),
    timedelta(seconds=2.5),
    timedelta(seconds=3.3)
]
all_intervals = [1,1.7,2.5,3.3,4]   #- OK
####################################################################################################
# read files to stat objects
####################################################################################################

def get_intellicage_txt_pathes(data_path):
    input_txt_path = os.path.join(data_path, 'Input.txt')
    visit_txt_path = os.path.join(data_path, 'Visits.txt')
    nosepoke_txt_path = os.path.join(data_path, 'Nosepokes.txt')
    
    return (input_txt_path, visit_txt_path, nosepoke_txt_path)

def add_anim_tag(nose_spoke,visits_df):   #  - OK
    df_nose_spoke =pd.DataFrame(nose_spoke).T
    df_nose_spoke['animal_tag'] = df_nose_spoke['visit_id']
    for idx, row in visits_df.iterrows():
        df_nose_spoke.loc[df_nose_spoke.visit_id == row['visit_id'],'animal_tag'] = row['animal_tag']
    return df_nose_spoke  
 
    
    
def add_times_from_light(df_nose_spoke,led_events_df):   #  - OK
    df_nose_spoke['start_interval_time'] = df_nose_spoke['start_date']
    df_nose_spoke['time_from_light'] = df_nose_spoke['start_date']
    df_nose_spoke['interval'] = df_nose_spoke['start_date']
    
    #wrk = df_nose_spoke['visit_id'] #['animal_tag']
    for idx, row in df_nose_spoke.iterrows():
        light_on_side = int(row['side'])
        if  light_on_side % 2 == 0 :
            light_on_side = light_on_side - 1 #  ! time of light on in even side!
        light_on = led_events_df[(led_events_df.event_date < row['start_date']) & (led_events_df.state == 'on')  & (led_events_df.side ==  light_on_side)]
        if not light_on.empty :
            #light_on_side = light_on[-1:].iloc[0]['side']
            light_on = light_on[-1:].iloc[0]['event_date']
            
            light_off = led_events_df[(led_events_df.event_date > light_on) & (led_events_df.state == 'off') & (led_events_df.side ==  light_on_side)]
            light_off =  light_off.iloc[0]['event_date']
        #row = row['animal_tag']
            df_nose_spoke.loc[idx,'time_from_light'] =  ( row['start_date'] - light_on).total_seconds()   
            interval = get_interval_from_variable_timedelta(light_off - light_on) 
            df_nose_spoke.loc[idx,'interval'] =  interval 
            df_nose_spoke.loc[idx,'start_interval_time'] =  light_on
        else :
            df_nose_spoke.loc[idx,'time_from_light'] = 0
            df_nose_spoke.loc[idx,'interval'] = 0
            df_nose_spoke.loc[idx,'start_interval_time'] = 0
    # old variant:
           # row['time_from_light'] =  ( row['start_date'] - light_on).total_seconds()   
           # interval = get_interval_from_variable_timedelta(light_off - light_on) 
           # row['interval'] =  interval 
           # row['start_interval_time'] =  light_on
        #else :
           # row['time_from_light'] = 0
           # row['interval'] = 0
           # row['start_interval_time'] = 0
            
    return df_nose_spoke 
def analyze(tab):
    ids = tab.visit_id.unique()
    for vid in (ids) :
        one = tab[tab.visit_id == vid]
        one.start_interval_time.unique()
        dif = one.start_interval_time.unique()
        sides = one.side.unique().astype(int)
        if (len(dif) > 1) & (max(sides) - min(sides) > 1):
        #if (len(dif) > 1) :
            one.to_excel('dif_'+ str(vid) + '.xlsx')
    
def find_gaps_visits_lights(visits_df,all_nose_spoke_animals) :   #  - OK
     gap_visit = [] 
     for idx, row in visits_df.iterrows():
       visits = all_nose_spoke_animals[(abs(all_nose_spoke_animals.start_interval_time - row['start_date']) <= known_intervals_delta)]
       visits = visits[visits.visit_id == row['visit_id']]  # != 
       if not visits.empty :
           gap_visit.append( visits.visit_id.unique())  #row['visit_id']
     df = pd.DataFrame({'GAP_visits' : gap_visit})      
     return  df
 
def  calc_need_spoke_after_interval_end(df_interval,intrvl,trials_start) : #  - OK
    res_1 = 0  #  count of trials without nosepokes after light off
    res_2 = 0
    for time in (trials_start) :
        df_need = df_interval[df_interval.start_interval_time == time] # part of row: nosepokes times from begin of trial
        res = df_need[df_need.time_from_light > intrvl] # count of nosepokes after light off
        if len(res) == 0 :
            res_1 = res_1 + 1
        elif int(res.iloc[0].side) % 2 == 1 :  
            res_2 = res_2 + 1
    return res_1, res_2
 
def output_results_all_nose_spoke(all_nose_spoke_animals,nm_output):   #  - OK
      un_tags = all_nose_spoke_animals.animal_tag.unique()
      for one_tag in (un_tags) :
            tab_one_animal = all_nose_spoke_animals[all_nose_spoke_animals.animal_tag == one_tag] #un_tag[1]
            k = 0
            analyze(tab_one_animal)
            interval_count = [0] * len(all_intervals) * 3
            for intrvl in all_intervals:
                df_interval = tab_one_animal[tab_one_animal.interval == intrvl]
                df_interval.reset_index(drop= True , inplace= True )
                df_interval_times = pd.DataFrame({ 'start_interval_time' :  df_interval.start_interval_time, str(intrvl) :  df_interval.time_from_light, 'Side' :  df_interval.side}).T
                trials_start = df_interval.start_interval_time.unique()
                interval_count[k] = len(trials_start)
                interval_count[k+1],interval_count[k+2] = calc_need_spoke_after_interval_end(df_interval,intrvl,trials_start)
                #df_interval_sides = pd.DataFrame({ "Side' :  df_interval.side}).T
                if  'df_one_animal' in locals() :
                    df_one_animal = pd.concat([df_one_animal,df_interval_times],sort=False,axis=0) #,  sort=False, axis=0)
                else:
                    df_one_animal = df_interval_times
                k = k + 3    
           # nm_output = 'N_'+ one_tag + '_' + nm_output  
            df_one_animal.insert(0, 'count', interval_count, allow_duplicates = False)
            df_one_animal.to_excel('N_'+ one_tag + '_' + nm_output)
            del df_one_animal

def load_experiment_data_from_files(log, input_txt_path, visit_txt_path, nosepoke_txt_path):
    led_events_df = read_led_events_from_input_txt_to_dataframe(log, input_txt_path);
    visits_df = read_visit_txt_to_dataframe(log, visit_txt_path)
    visit_nosepoke_stat, all_nose_spoke = read_nosepoke_for_visit_significant_nosepoke_stat(log, nosepoke_txt_path)
    
    beginning_str = experiment_date + time_begin #' 16:00:00.000' # Replace with your desired start '2023-07-01 00:00:00.000'
    beginning = datetime.strptime(beginning_str, '%Y-%m-%d %H:%M:%S.%f')
    ending_str = experiment_date + time_end # Replace with your desired end '2022-12-06 13:07:11.000'
    ending = datetime.strptime(ending_str, '%Y-%m-%d %H:%M:%S.%f')
# OK:_________________ all_nose_spoke - all nosepoke inf. for output times of all rats to files, in all intervals
     # Add the filtering condition here: 
    #visits_df = visits_df[(visits_df['start_date'] >= beginning)  &  (visits_df['end_date'] <= ending)]
    all_nose_spoke_animals = add_anim_tag(all_nose_spoke,visits_df)
    all_nose_spoke_animals = all_nose_spoke_animals[(all_nose_spoke_animals['start_date'] >= beginning)  &  (all_nose_spoke_animals['end_date'] <= ending)] 
    #__________________________________
    all_nose_spoke_animals = add_times_from_light(all_nose_spoke_animals,led_events_df)
    output_results_all_nose_spoke(all_nose_spoke_animals,output_file.replace('results_',""))
#OK: find gaps of visits  and lights:_____
    visits_df_need = visits_df[(visits_df.start_date >= beginning)  &  (visits_df.end_date <= ending)]
    gap_visits = find_gaps_visits_lights(visits_df_need,all_nose_spoke_animals) 
    gap_visits.to_excel('GAP_'+ output_file.replace('results_',""))
# end of OK' code____________________________________________ 
    items = []
    for idx, row in visits_df.iterrows():
        light_interval = get_light_on_off_duration(log, led_events_df, row['start_date'], row['end_date'], get_sides_by_corner(row['corner']))
        parsed_light_interval = get_interval_from_variable_timedelta(light_interval)
    
        result_item = {} 
        result_item['visit_time'] = (row['end_date'] - row['start_date']).total_seconds()

        for k in visits_df.columns:
            result_item[k] = row[k]
        result_item['light_interval'] = parsed_light_interval
            #result_item['light_interval'] = light_interval #OS???
        result_item['light_interval_total_seconds'] = light_interval.total_seconds()
        
        if row['visit_id'] in visit_nosepoke_stat:
            visit_stat = visit_nosepoke_stat[row['visit_id']]

            for k in visit_stat:
                result_item[k] = visit_stat[k]

            if result_item['significant_nosepoke_start_date']:
                delta_since_start = result_item['significant_nosepoke_start_date'] - result_item['start_date']
                result_item['significant_nosepoke_seconds_from_visit'] = delta_since_start.total_seconds()
            else:
                result_item['significant_nosepoke_seconds_from_visit'] = 0

            result_item['significant_nosepoke_start_date'] = str(result_item['significant_nosepoke_start_date']).split('.')[0]
            result_item['significant_nosepoke_end_date'] = str(result_item['significant_nosepoke_end_date']).split('.')[0]
        else:
            result_item['nosepoke_count'] = 0
            result_item['is_significant_nosepoke'] = False

        # Add the filtering condition here
        if (result_item['start_date'] >= beginning) and (result_item['start_date'] <= ending):
            items.append(result_item)


    df = pd.DataFrame(items)

    correct_order_columns = [
        'visit_id', 'animal_tag', 'start_date', 'end_date', 'corner', 'visit_time', 'light_interval', 'is_significant_nosepoke', 'significant_nosepoke_side', 'significant_nosepoke_state', 'significant_nosepoke_seconds_from_visit', 'significant_nosepoke_start_date', 'significant_nosepoke_end_date', 'nosepoke_count', 'light_interval_total_seconds'
    ]
    df = df[correct_order_columns]

    return df


def read_led_events_from_input_txt_to_dataframe(log, input_txt_path):
    led_events = []
    with open(input_txt_path, 'r') as f:
        line = f.readline()
        
        while line:
            line = f.readline()
        
            if not 'LedState' in line:
                continue
        
            vals = line.split('\t')
            event_date = datetime.strptime(vals[0], '%Y-%m-%d %H:%M:%S.%f')
        
            state = 'on' if vals[11] == 'Blue' else 'off'
        
            data = {
                'event_date': event_date,
                'side': int(vals[10]),
                'state': state
            }
        
            led_events.append(data)

        log.log('read led events: ' + str(len(led_events)))
            
        led_events_df = pd.DataFrame(led_events)

    return led_events_df


def read_visit_txt_to_dataframe(log, visit_txt_path):
    visits = []

    with open(visit_txt_path, 'r') as f:
        line = f.readline()

        while line:
            line = f.readline().strip()
            if not line:
                break

            vals = line.split('\t')

            data = {
                'visit_id': int(vals[0]),
                'animal_tag': vals[1],
                'start_date': datetime.strptime(vals[2], '%Y-%m-%d %H:%M:%S.%f'),
                'end_date': datetime.strptime(vals[3], '%Y-%m-%d %H:%M:%S.%f'),
                'corner': vals[6],
            }

            visits.append(data)

    log.log('read visit events: ' + str(len(visits)))

    visits_df = pd.DataFrame(visits)

    return visits_df


def read_nosepoke_for_visit_significant_nosepoke_stat(log, nosepoke_txt_path):
    visit_nosepoke_stat = {}
    all_nose_spoke_times = {} #OK 
    all_visit_counter = 0     #OK
    current_visit_id = None
    is_first_singnificant_nosepoke_found = False
    nosepoke_count = 0

    with open(nosepoke_txt_path, 'r') as f:
        line = f.readline()

        while True:
            line = f.readline().strip()
            if not line:
                break

            vals = line.split('\t')

            visit_id = int(vals[0])
 # OK: get inf. about times of all nosepokes:
            all_nose_spoke_times[all_visit_counter] = {
                'visit_id': visit_id,
                'start_date': datetime.strptime(vals[1], '%Y-%m-%d %H:%M:%S.%f'),
                'end_date': datetime.strptime(vals[2], '%Y-%m-%d %H:%M:%S.%f'), 
                'side': vals[3],   
                'side_condition' : int(vals[4])                    
                }
            all_visit_counter = all_visit_counter + 1
 #________________________________________________

            if visit_id != current_visit_id:

                if current_visit_id is not None:
                    item = {
                        'visit_id': current_visit_id,
                        'nosepoke_count': nosepoke_count,
                        'is_significant_nosepoke': False,
                        'significant_nosepoke_start_date': '',
                        'significant_nosepoke_end_date': '',
                        'significant_nosepoke_side': '',
                        'significant_nosepoke_state': ''
                    }
                    if significant_nosepoke:
                        item['is_significant_nosepoke'] = True
                        item['significant_nosepoke_start_date'] = significant_nosepoke['start_date']
                        item['significant_nosepoke_end_date'] = significant_nosepoke['end_date']
                        item['significant_nosepoke_side'] = significant_nosepoke['side']
                        item['significant_nosepoke_state'] = significant_nosepoke['state']

                    visit_nosepoke_stat[current_visit_id] = item

                is_first_singnificant_nosepoke_found = False
                nosepoke_count = 0
                current_visit_id = visit_id
                significant_nosepoke = None

            nosepoke_count = nosepoke_count + 1

            side_condition = int(vals[4])

            if side_condition != 0 and not is_first_singnificant_nosepoke_found:          
                if side_condition == 0:
                    state = 'neutral'
                elif side_condition == 1:
                    state = 'correct'
                elif side_condition == -1:
                    state = 'wrong'
                else:
                    state = 'UNK'
                    log.log(f'ERROR: side condition unknown [{side_condition}]')

                significant_nosepoke = {
                    'start_date': datetime.strptime(vals[1], '%Y-%m-%d %H:%M:%S.%f'),
                    'end_date': datetime.strptime(vals[2], '%Y-%m-%d %H:%M:%S.%f'),
                    'side': vals[3],
                    'state': state
                }
                is_first_singnificant_nosepoke_found = True

    log.log('read nosepoke visits: ' + str(len(visit_nosepoke_stat)))

    return visit_nosepoke_stat,all_nose_spoke_times


####################################################################################################
# common functions
####################################################################################################

def get_light_on_off_duration(log, led_events_df, start_date, end_date, sides):
    led_events_in_visit = led_events_df[
        (led_events_df['event_date'] >= start_date)
        & (led_events_df['event_date'] <= end_date)
        & (led_events_df['side'].isin(sides))
    ]
    
    turned_on_time = None
    turned_off_time = None
    for idx, row in led_events_in_visit.iterrows():
        is_on_not_found = turned_on_time is None
        is_off_not_found = turned_off_time is None
        if is_on_not_found:
            if row['state'] == 'on':
                turned_on_time = row['event_date']
        elif is_off_not_found:
            if row['state'] == 'off':
                turned_off_time = row['event_date']
        else:
            if row['state'] == 'on':
                log.log(f'FAILED CHECK: light is turned on second time {start_date}, {end_date}, {sides}')
    
    if turned_on_time is None:
        log.log('FAILED CHECK: NO LIGHT IS ON')
        return timedelta(seconds=0)
    if turned_off_time is None:
        return turned_on_time - start_date
    
    return turned_off_time - turned_on_time

def get_sides_by_corner(corner_num):
    side_to_corner_map = {
        '1': [1, 2],
        '2': [3, 4],
        '3': [5, 6],
        '4': [7, 8]
    }
    return side_to_corner_map[corner_num]



def get_interval_from_variable_timedelta(dt):
    found_interval = None
    
    for i in known_intervals:
        if dt >= i - known_intervals_delta and dt <= i + known_intervals_delta:
            found_interval = i
            break

    if found_interval is None:
        return -1
    return found_interval.total_seconds()

####################################################################################################
# reporter
####################################################################################################

class SimpleLogger:
    def log(self, msg):
        m = self.format_message(msg)
        print(m)

    def format_message(self, msg):
        today = datetime.now().isoformat()
        m = f'[{today}] {msg}'
        return m
#####################################################################################################
#   OK: create df for one animal
#####################################################################################################
def get_stat_interval(data_df,interval):
#even
    #significant_nosepoke = data_df.[not(data_df.is_significant_nosepoke.isna())]
    #significant_nosepoke = data_df.loc[data_df.is_significant_nosepoke == True] 
    k = str(interval)
    df_interval = data_df[data_df.light_interval == interval]
    even_nosepoke = df_interval[df_interval.significant_nosepoke_side % 2 == 0]
    
    Number_even = len(even_nosepoke)
    if Number_even == 0 :
        Number_even_visit_time = 0
        Number_even_nosepoke_count = 0
        Number_even_significant_nosepoke_seconds_from_visit = 0
    else :      
        Number_even_visit_time = even_nosepoke.visit_time.median()
        Number_even_nosepoke_count = even_nosepoke.nosepoke_count.median()
        Number_even_significant_nosepoke_seconds_from_visit = even_nosepoke.significant_nosepoke_seconds_from_visit.median()
# odd:
    odd_nosepoke = df_interval[df_interval.significant_nosepoke_side % 2 == 1]
    Number_odd = len(odd_nosepoke) #odd_nosepoke.light_interval[odd_nosepoke.light_interval == 1].sum()
    if Number_odd == 0 :
        Number_odd_visit_time = 0
        Number_odd_nosepoke_count = 0
        Number_odd_significant_nosepoke_seconds_from_visit = 0
    else :
        Number_odd_visit_time = odd_nosepoke.visit_time.median()
        Number_odd_nosepoke_count = odd_nosepoke.nosepoke_count.median()
        Number_odd_significant_nosepoke_seconds_from_visit = odd_nosepoke.significant_nosepoke_seconds_from_visit.median()
 ## light_interval_total_seconds -  min-max:
    Number_li_total_sec_min = df_interval.light_interval_total_seconds.min() 
    Number_li_total_sec_max = df_interval.light_interval_total_seconds.max() 
#____________________________no_nosepoke 
    not_significant_nosepoke = df_interval[df_interval.is_significant_nosepoke == False]
    if not_significant_nosepoke.empty :  #not_significant_nosepoke[not_significant_nosepoke.light_interval == 1].empty :
        Number_no_nosepoke = 0
        Number_no_nosepoke_visit_time = 0
        Number_no_nosepoke_count  = 0
    else:
        not_significant_nosepoke = not_significant_nosepoke[not_significant_nosepoke.light_interval == interval]
        if not_significant_nosepoke.empty :  #not_significant_nosepoke[not_significant_nosepoke.light_interval == 1].empty :
             Number_no_nosepoke = 0
             Number_no_nosepoke_visit_time = 0
             Number_no_nosepoke_count  = 0
        else:
             Number_no_nosepoke = len(not_significant_nosepoke) 
             Number_no_nosepoke_visit_time = not_significant_nosepoke.visit_time.median()
             Number_no_nosepoke_count  = not_significant_nosepoke.nosepoke_count.median()
    newtab = {'Number'+ k +'_even ': [Number_even],'Number'+ k +'_odd': [Number_odd],
              'Number'+ k +'_even_visit_time' : [Number_even_visit_time], 'Number'+ k +'_odd_visit_time' : [Number_odd_visit_time], 
              'Number'+ k +'_even_nosepoke_count' : [Number_even_nosepoke_count], 'Number'+ k +'_even_significant_nosepoke_seconds_from_visit' : [Number_even_significant_nosepoke_seconds_from_visit],
              'Number'+ k +'_odd_nosepoke_count' : [Number_odd_nosepoke_count],'Number'+ k +'_odd_significant_nosepoke_seconds_from_visit' : [Number_odd_significant_nosepoke_seconds_from_visit],
              'Number'+ k +'_li_total_sec_min' : [Number_li_total_sec_min], 'Number'+ k +'_li_total_sec_max' : [Number_li_total_sec_max],
              'Number'+ k +'_no_nosepoke' : [Number_no_nosepoke], 'Number'+ k +'_no_nosepoke_visit_time' : [Number_no_nosepoke_visit_time],
              'Number'+ k +'_no_nosepoke_count' :[Number_no_nosepoke_count]
              }
    return(pd.DataFrame(newtab))  
    
def get_stat_animal_df(data_df):   # OK
    animal_tag = data_df.animal_tag.unique()
    corner_count_1 = len(data_df[data_df.corner == 1])
    corner_count_2 = len(data_df[data_df.corner == 2])
    corner_count_4 = len(data_df[data_df.corner == 4])
#even
    #significant_nosepoke = data_df.[not(data_df.is_significant_nosepoke.isna())]
    #significant_nosepoke = data_df.loc[data_df.is_significant_nosepoke == True] 
    anim_stat = pd.DataFrame( {'animal_tag': [animal_tag[0]],'corner_count_1': [corner_count_1],
                               'corner_count_2': [corner_count_2],'corner_count_4': [corner_count_4] })
    #all_intervals = [1,1.7,2.5,3.3,4]
#___ *5 intervals
    for i in all_intervals:
        stat_int = get_stat_interval(data_df,i)
        anim_stat = pd.concat([anim_stat,stat_int],sort=False,axis=1)
    premature_data_df = data_df[data_df.light_interval == -1]
    Number_1_premature = len(premature_data_df)
    Number_1_premature_1 = len(premature_data_df[premature_data_df.visit_time < 1])
    Number_1_premature_17 = len(premature_data_df[(premature_data_df.visit_time >=1) & (premature_data_df.visit_time < 1.7)])
    Number_1_premature_25 = len(premature_data_df[(premature_data_df.visit_time >= 1.7) & (premature_data_df.visit_time < 2.5)])
    Number_1_premature_33 = len(premature_data_df[(premature_data_df.visit_time >= 2.5) & (premature_data_df.visit_time < 3.3)])
    Number_1_premature_4 = len(premature_data_df[(premature_data_df.visit_time >= 3.3) & (premature_data_df.visit_time < 4)])
#___create dataframe:
    newtab = {'Number_1_premature' : [Number_1_premature],'Number_1_premature1' : [Number_1_premature_1],
              'Number_1_premature_17' : [Number_1_premature_17],'Number_1_premature_25' : [Number_1_premature_25],
              'Number_1_premature_33' : [Number_1_premature_33],'Number_1_premature_4' : [Number_1_premature_4]      
              }
   # dt = (pd.DataFrame(newtab))
    df = pd.concat([anim_stat,pd.DataFrame(newtab)],sort=False,axis=1)   
    return (df)
####################################################################################################
# cmd loop
####################################################################################################

def run__cmd():
    log = SimpleLogger()

    (input_txt_path, visit_txt_path, nosepoke_txt_path) = get_intellicage_txt_pathes(data_path)

    is_ok = True
    errors = []

    for f in (input_txt_path, visit_txt_path, nosepoke_txt_path):
        is_ok = os.path.isfile(f)

        if not is_ok:
            b_name = os.path.basename(f)
            log.log(f'ОШИБКА! Файл не найден [{b_name}]')

    if is_ok:
#OK: output for one animal and all-in-one tables
        result_df = load_experiment_data_from_files(log, input_txt_path, visit_txt_path, nosepoke_txt_path)
        sort_for_animal = result_df.sort_values(by='animal_tag') #xxx
        indexs_animal = sort_for_animal.animal_tag  #yyy
        un_tags = indexs_animal.unique()
        for one_tag in (un_tags) :
            one_animal = indexs_animal[indexs_animal == one_tag] #un_tag[1]
            tab_one_animal = result_df.iloc[one_animal.index,:]
            sort_tab_one_animal = tab_one_animal.sort_values(by='visit_id')
            nm_output = 'AT'+ one_tag + '_' + output_file.replace('results_',"")    
            sort_tab_one_animal.to_excel(nm_output, index=False)  
            sort_tab_one_animal = pd.read_excel(nm_output)  # to work around the error with empty values
            if  'animals_stat' in locals() :
                stat_one = get_stat_animal_df(sort_tab_one_animal)
                animals_stat = pd.concat([animals_stat,stat_one],sort=False,axis=0) #,  sort=False, axis=0)
            else:
                animals_stat = get_stat_animal_df(sort_tab_one_animal)
# all results:_________________________________:
        animals_stat.to_excel(stat_output_file, sheet_name='result', index=False)       
        result_df.to_excel(output_file, sheet_name='result', index=False)
        log.log(f'Файл сохранен: [{output_file}]')


####################################################################################################
# window loop
####################################################################################################

def run__tk_window():
    root = tk.Tk()

    log = TKLogger(report_txt)

    log.log('start')
    root.mainloop()


if __name__ == '__main__':
    run__cmd()
