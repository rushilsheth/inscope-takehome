#### prompts ####
USUAL_PROMPT = '''Your task is to read through the provided 10-K report and return a summary and the total revenue for the company.

**Summary Instructions:**

Please provide a one-paragraph summary of the provided 10-K report with a focus on the revenue. Include the following details:

1. **Revenue Growth:** Highlight the percentage growth or decline in revenue compared to the previous year.
2. **Key Drivers and Blockers:** Identify the main factors that contributed to or hindered the revenue growth.
3. **Numerical Insights:** Mention any significant numerical figures related to revenue (e.g., total revenue, revenue by segment, or geographic region).
4. **Annual Performance Evaluation:** Assess whether this was a financially successful year for the company in terms of revenue.
5. **Future Outlook:** Provide insights into the company's revenue expectations or projections for the next year, including any strategies or market conditions that might impact these figures.

End the summary with a concise statement on the overall financial health of the company with respect to its revenue performance.

**Revenue Instructions**
- Only give a revenue value if it is:
    - full revenue for the year
    - is stated in the the document
    - return 'N/A' if it is not present
**Not following these instructions will deem the output fully incorrect**

**Output Instructions**
Output as a RFC 8259 compliant JSON with two fields where revenue should not contain any words and should be rounded to the nearest integer if and only if the above conditions are met. If the text says 200 million, you will return 200,000,000:

{"summary": "This is a summary of the 10-K report", "revenue": "200,000,000"}

OR

{"summary": "This is a summary of the 10-K report", "revenue": "N/A"}
''' 

REVENUE_RETRY_PROMPT = ''''''

SUMMARIZE_SUMMARIES = f'''
We have asked an LLM to summarize a 10-K and had to do it in chunks. 

Combine the following summaries and create a new summary. Here is the summary used for each chunk:

{USUAL_PROMPT}

Ensure the new summary follows this same format and prompt.
'''



############## LLM INTERACTIONS ##############
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

load_dotenv() 

# OPENAI INFO
OPENAI_MODEL='gpt-3.5-turbo-16k'
MAX_TOKENS = 16_385
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  
ANTHRO_API_KEY = os.getenv('ANTHRO_API_KEY')  

summary_mappings = {'usual': USUAL_PROMPT,
                    'map_reduce': SUMMARIZE_SUMMARIES,
                    'rev_retry': REVENUE_RETRY_PROMPT}

# LLM instance with low temp since we just want facts
model = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature = 0.1, max_tokens=500, model = OPENAI_MODEL)

#### diff chains! ####
def full_summary_call(doc_text):
    '''NEED'''
    # add json response format, so that i can easily get Revenue
    
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
# def revenue_retry_summary_call(doc, ):
#     '''NEED'''
#     prompt = summary_mappings['rev_retry']
#     return


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
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=.8*MAX_TOKENS, chunk_overlap=0, model_name = OPENAI_MODEL)
    texts = text_splitter.split_documents(docs_transformed)
    summary_list = []
    print(file_path)
    for chunk in tqdm(texts):
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
        # handle and rev amount
        rev_amounts = [int(resp['revenue'].replace(',', '')) for resp in summary_list if resp['revenue'] != 'N/A']
        rev_amount = max(rev_amounts)
        summary_json = {'summary': combined_summary, 'revenue': rev_amount}            
    
    return summary_list, summary_json

## eval stuff!
def eval_revenue():
    return

def eval_summary():
    return
    
