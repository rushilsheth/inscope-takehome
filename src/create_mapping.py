import os
import pandas as pd

def get_sp500(file_name):
    with open(file_name, 'r') as file:
        sp500_list = [line.strip() for line in file]
    print(f'list contains {len(sp500_list)} elements')
    return sp500_list

def create_mapping_df(form_10k_directory):
    ''' You will create a script that given a directory with report files 
        can produce a CIK -> Company Name mapping in the shape of a CSV file 
        with two columns: CIK and Company Name. Each row in this file will represent 
        each file in the provided data.'''
    
    sp_list = get_sp500('SP500.txt')
    mappings = []

    # Walk through the directory
    for root, dirs, file_names in os.walk(form_10k_directory):
        for file_name in file_names:
            cik_number = file_name.partition('.')[0]
            if cik_number in sp_list:
                # Construct full file path and add the CIK, file path pair to the list
                mappings.append((cik_number, os.path.join(root, file_name)))

    df = pd.DataFrame(mappings, columns=['CIK', 'FileName'])

    df.to_csv('other_data/cik_file_mapping.csv', index=False)
    
    return df
    