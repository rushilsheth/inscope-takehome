from src.llm_functions import summarize_text
import pandas as pd

def create_summary_df(mapping_df, recreate_summaries = False):
    ''' You will write a data pipeline to process the provided HTML 
        into an intermediate representation that can be used for clustering. 
        One of the features in your intermediate representation should be a 
        1-paragraph summary of the report. You can use any pre-trained language 
        model you like to generate the summary.'''
    cik_summary_df = mapping_df.copy()
    try:
        # avoid duplicate callings of openai -- save dat money
        cik_summary_df = pd.read_csv('cik_summary_df.csv')
        if not recreate_summaries:
            return cik_summary_df
    except:
        print('creating summary df via openAI calls')

    if recreate_summaries:
        print("recreating summaries per user's request")
    
    # create cols and have hints on dtype of cols
    cik_summary_df['summary_list'] = []
    cik_summary_df['final_json'] = ''   
    for rows, idx in cik_summary_df:
        summary_list, final_json = summarize_text(rows.FileName)


    return cik_summary_df