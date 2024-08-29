import os
import openai
import pandas as pd
import numpy as np
import streamlit as st

class CGPTDA:
    def __init__(self, data):
        """
        Initialize the CGPT Data Analyzer class.

        Args:
            data: input data table to be analyzed by cgpt
        """
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        self.client = openai.OpenAI()
        self.data = data
        self.model = "gpt-3.5-turbo-16k"
        self.tools = None
        self.messages = []
        self.tool_choice = None

    def data_summarizer(self):
        self.data = self.data.pivot_table(index='Date', columns='Metrics', values='Value', aggfunc='first')
        self.data.reset_index(inplace=True)

        """
        print('\n')
        print('DATA TO BE ANALYSED 1:')
        print(self.data.head())
        print('\n')
        """

        f_date = self.data['Date'][0]
        l_date = self.data['Date'][len(self.data)-1]

        col_desc = ''
        col_desc = f'The financial data was recorded over a time period from {f_date} to {l_date} at one month intervals '
        for col in self.data.columns:
            if col == 'Date':
                continue
            else:
                cd = self.data[col].describe()
                cd = cd.to_dict()
                p = f".Statistical analysis of finanical numeric data of metric '{col}' says the "
                for key in cd.keys():
                    v = cd[key]
                    p += f"{key} is {v} "

            col_desc += p

        """
        print('DATA PREPROCESSING:')
        print(col_desc)
        print('\n')
        return col_desc
        """

        return col_desc
    
    def input_generator(self):
        s_dict = {'role': 'system', 'content': 'The output will take this financial analysis and provide the partnership a summary of the report and give the partners 5 actionable insights to improve the financial and business performance of the portfolio company with a focus on increasing profitability. After the 5 takeaways, please include both a brief optimistic and pessimistic summary of the information and future outlook of the business based on the information analyzed.'}
        u_dict = {'role': 'user', 'content': f"Entered financial report is a {st.session_state.report_type} report"}
        nd_desc_dict = {'role': 'assistant', 'content': 'The numerical data analysis is being obtained using the pandas describe() function which is stored as a python dictionary. The metric name is also added to this dictionary. Then the dictionary is converted to a string which is added to an array. This array contains the numerical analysis for all the metrics'}

        prompt = self.data_summarizer()
        ana_dict = {'role': 'assistant', 'content': prompt}

        self.messages = [s_dict, u_dict, nd_desc_dict, ana_dict]

    def ai_analyzer(self, user_query=None):
        if len(self.messages) == 0:
            self.input_generator()

        if user_query:
            user_message = {'role': 'user', 'content': user_query}
            self.messages.append(user_message)

        response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages
                )

        R = response.choices[0].message.content

        self.messages.append({'role': 'assistant', 'content': R})

        return R
