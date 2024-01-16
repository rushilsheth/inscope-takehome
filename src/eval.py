from src.llm_functions import summarize_text
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import ChatMessagePromptTemplate
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI

# OPENAI INFO
OPENAI_MODEL='gpt-3.5-turbo-16k'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') 

def eval_revenue(revenue_validation, mapping_df):
    '''for now we will just do new LLM calls
    revenue_validation: pandas df'''
    revenue_validation['llm_revenue'] = 0
    for index, row in revenue_validation.iterrows():
        file_path = mapping_df.loc[mapping_df.CIK == row.CIK].FileName.values[0]
        summary_list, summary_json = summarize_text(file_path)
        revenue_validation['llm_revenue'] = summary_json['revenue']
    return revenue_validation

load_dotenv() 

def eval_summary(CIK, pdf_path, mapping_df):
    '''compare a ceo exec summary to the llm summary'''
    file_path = mapping_df.loc[mapping_df.CIK == CIK].FileName.values[0]
    summary_list, json_response = summarize_text(file_path)
    llm_full_article_summary = json_response['summary']
    with open(pdf_path, 'r') as file:
        file_contents = file.read()
    comparing_summary_prompt = '''"I have two executive summaries related to STERIS. The first is an executive summary written by the CEO in a letter to shareholders, and the second is a summary I generated from STERIS's 10-K report. I would like to compare these summaries to understand how they align or differ in terms of content, tone, and focus areas.

            CEO's Letter Summary:
            {ceo_letter}

            10-K Report Summary:
            {tenk_summary}

            Please analyze these summaries and provide insights into their similarities and differences. Focus on the key messages conveyed, the tone of each summary, and the main areas of emphasis. Highlight any notable contrasts or parallels in how STERIS is presented in these two documents.

            Also output a score out of 10 for the accuracy of the 10-K report vs CEO's letter summary
            '''


    chat_message_prompt = ChatMessagePromptTemplate.from_template(
        role="user", template=comparing_summary_prompt
    ).format(ceo_letter=file_contents, tenk_summary=llm_full_article_summary)
    messages = [chat_message_prompt]
    model = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature = 0.1, max_tokens=500, model = OPENAI_MODEL)
    return model.invoke(messages).content