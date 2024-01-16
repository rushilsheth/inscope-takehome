from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredHTMLLoader
from langchain_community.document_transformers import Html2TextTransformer

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from dotenv import load_dotenv
import os
import json
from langchain_openai import ChatOpenAI
from tqdm import tqdm

from src.prompts import USUAL_PROMPT, SUMMARIZE_SUMMARIES

load_dotenv() 

# OPENAI INFO
OPENAI_MODEL='gpt-3.5-turbo-16k' 
MAX_TOKENS = 16_385
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  
ANTHRO_API_KEY = os.getenv('ANTHRO_API_KEY')  

summary_mappings = {'usual': USUAL_PROMPT,
                    'map_reduce': SUMMARIZE_SUMMARIES}

# LLM instance with low temp since we just want facts
model = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature = 0.1, max_tokens=500, model = OPENAI_MODEL)

#### diff chains! ####
def full_summary_call(doc_text):
    '''NEED'''
    
    # Define your desired data structure.
    # class Summary_Revenue(BaseModel):
    #     summary: str = Field(description="summary based on prompt instructions")
    #     revenue: str = Field(description="total revenue for the fiscal year")
    # parser = JsonOutputParser(pydantic_object=Summary_Revenue)

    system_prompt = summary_mappings['usual']
    prompt = ChatPromptTemplate.from_messages([SystemMessage(content=system_prompt),
                                               HumanMessage(content=doc_text.page_content+'\n\nJSON RESPONSE:')])
    chain = prompt | model #| parser

    return chain.invoke(input={}).content
def combine_summaries(llm_response_list):
    '''map reduce these summaries from chunks'''
    system_prompt = summary_mappings['map_reduce']
    summary_list_txt = ''
    for i, llm_response in enumerate(llm_response_list):
        summary_txt = llm_response.get('summary', '')
        summary_list_txt += f'{i}. {summary_txt}\n'
    
    prompt = ChatPromptTemplate.from_messages([SystemMessage(content=system_prompt),
                                               HumanMessage(content='Summary List:\n\n'+summary_list_txt)])

    model = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature = 0.1, max_tokens=500, model = OPENAI_MODEL)
    chain = prompt | model
    return chain.invoke(input={})

import re

import re

def extract_item_7(doc):
    text = doc[0].page_content

    # Define the pattern to find the end of the Table of Contents
    toc_end_pattern = r"Table\s+of\s+Contents"

    # Define the pattern to find the start of Item 7 with flexible punctuation and spacing
    start_pattern = r"Item\s*7[:.]\s*Managemen"

    # Define the pattern to find the start of the next Item with flexible punctuation and spacing
    end_pattern = r"Item\s*8[:.]\s*Financial Statem"

    # Find the end of the Table of Contents
    toc_end_match = re.search(toc_end_pattern, text, re.IGNORECASE | re.DOTALL)

    # Set the starting point for searching Item 7 after the Table of Contents
    start_index = toc_end_match.end()+20_000 if toc_end_match else 0

    # Find the start of Item 7 after the Table of Contents
    start_match = re.search(start_pattern, text[start_index:], re.IGNORECASE | re.DOTALL)

    if start_match:
        # Adjust the index for the start of Item 7 relative to the entire document
        adjusted_start_index = start_index + start_match.start()

        # Find the start of the next Item after Item 7
        end_match = re.search(end_pattern, text[adjusted_start_index:], re.IGNORECASE | re.DOTALL)

        if end_match:
            # Adjust the index for the end of the extraction relative to the entire document
            adjusted_end_index = adjusted_start_index + end_match.start()

            # Extract the text from the start of Item 7 to the start of the next Item
            item_7_text = text[adjusted_start_index:adjusted_end_index]
            return item_7_text
        else:
            # If the end pattern is not found, return text from Item 7 to the end of the document
            return text[adjusted_start_index:]
    else:
        # If Item 7 is not found, return an empty string or an appropriate message
        return ""


def summarize_text(file_path):
    '''use openAI to summarize the 10-K. need to split 
    based on tokens due to large size of the file (over 100 pages)
    # ideally have a mapping for model to tokens
    # chunk it and summarize each chunk
    # reduce summaries if needed
    '''
    loader = UnstructuredHTMLLoader(file_path)
    doc = loader.load()
    html2text = Html2TextTransformer()
    docs_transformed = html2text.transform_documents(doc)
    reduced_doc = extract_item_7(docs_transformed)
    docs_transformed[0].page_content = reduced_doc
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=.8*MAX_TOKENS, chunk_overlap=0, model_name = OPENAI_MODEL)
    texts = text_splitter.split_documents(docs_transformed)
    summary_list = []
    print(file_path)
    for chunk in tqdm(texts[:2]):
        # get summary from openai
        chunk_summary = full_summary_call(chunk)
        summary_list.append(json.loads(chunk_summary))
    if len(summary_list) == 0:
        print(f'no summary given for {file_path}!')
        # better return!
        return {'summary': '', 'revenue': ''}
    elif len(summary_list) == 1:
        summary_json = summary_list[0]
    else:
        # combine summaries
        combined_summary = combine_summaries(summary_list)
        combined_summary_dict = json.loads(combined_summary.content)
        # handle and rev amount
        rev_amounts = [int(resp['revenue'].replace(',', '')) for resp in summary_list if resp['revenue'] != 'N/A']
        if rev_amounts:
            rev_amount = max(rev_amounts)
        else:
            llm_revenues = [resp['revenue'] for resp in summary_list if resp['revenue']]
            print(f'no max for revenue; {llm_revenues}')
            if combined_summary_dict['revenue']!='N/A':
                rev_amount = combined_summary['revenue']
            else:
                rev_amount = None  
        summary_json = {'summary': combined_summary_dict['summary'], 'revenue': rev_amount}            
    
    return summary_list, summary_json