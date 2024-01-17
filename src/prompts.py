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

SUMMARIZE_SUMMARIES = f'''
We have asked an LLM to summarize a 10-K and had to do it in chunks. 

Combine the following summaries and create a new summary. Here is the summary used for each chunk:

{USUAL_PROMPT}

Ensure the new summary follows this same format and prompt.
'''