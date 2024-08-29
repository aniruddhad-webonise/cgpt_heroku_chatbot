import pandas as pd
import json
from cgptda_helper import CGPTDA
import datetime
from dotenv import load_dotenv
import os
import streamlit as st
import boto3
from io import StringIO


def pull_data(bucket_name, file_key):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=file_key)
    data = response['Body'].read().decode('utf-8')
    df = pd.read_csv(StringIO(data))

    df['Date'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2) + '-' + '01'
    df = df[df['year'] >= 2022]
    grouped_df = df.groupby(['metric_name', 'Date'], as_index=False)['actual_mtd'].sum()
    grouped_df.rename(columns={'metric_name':'Metrics', 'actual_mtd':'Value'}, inplace=True)
    grouped_df.sort_values(by=['Date', 'Metrics'], inplace=True)

    return grouped_df

load_dotenv()

# Streamlit UI
st.set_page_config(page_title="ChatGPT Financial Data Analyzer", page_icon=":chart_with_upwards_trend:", layout="wide")

# Sidebar for initialization
with st.sidebar:
    st.title("ChatGPT Financial Data Analayzer")

    if 'cgptda' not in st.session_state:
        # Loading Data
        bucket_name = 'presentation-demo-cgptbot'
        file_key = 'pt_pnl.csv'
        d = pull_data(bucket_name, file_key)
        st.session_state.cgptda = CGPTDA(d)

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    # Toggle for dark mode
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False

    st.session_state.dark_mode = st.checkbox("Dark Mode", value=st.session_state.dark_mode)

    st.session_state.report_type = st.text_input("Enter the financial report type:", "")

    if st.button("Initialize Conversation"):
        if st.session_state.report_type.strip():
            st.session_state.cgptda.input_generator()
            st.session_state.conversation_history.append({"role": "user", "content": f"Entered financial report is a {st.session_state.report_type} report"})
            # st.session_state.conversation_history.append({"role": "assistant", "content": st.session_state.cgptda.data_summarizer()})
        else:
            st.error("Please enter a valid report type.")

# Main Chat Interface
st.markdown("<h2 style='text-align: center;'>Chat Interface</h2>", unsafe_allow_html=True)

# Display conversation history
def display_conversation():
    st.write("Conversation History:")
    user_bg = "#333333" if st.session_state.dark_mode else "#daf5da"
    user_color = "#FFFFFF" if st.session_state.dark_mode else "#000000"
    bot_bg = "#555555" if st.session_state.dark_mode else "#f0f0f5"
    bot_color = "#FFFFFF" if st.session_state.dark_mode else "#000000"
    
    for msg in st.session_state.conversation_history:
        if msg['role'] == 'user':
            st.markdown(f'<div style="text-align: right; background-color: {user_bg}; color: {user_color}; padding: 10px; border-radius: 10px; margin-bottom: 10px; margin-left: 15%;"><strong>USER:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align: left; background-color: {bot_bg}; color: {bot_color}; padding: 10px; border-radius: 10px; margin-bottom: 10px; margin-right: 15%;"><strong>BOT:</strong> {msg["content"]}</div>', unsafe_allow_html=True)

user_query = st.text_area("Enter your specific query (if any). Type 'exit chat' to discontinue.", "")
if st.button("Submit Query"):
    if user_query.strip().lower() != "exit chat":
        chat_response = st.session_state.cgptda.ai_analyzer(user_query)
        if len(user_query) != 0:
            st.session_state.conversation_history.append({"role": "user", "content": user_query})
        st.session_state.conversation_history.append({"role": "assistant", "content": chat_response})
        st.rerun()
    else:
        st.stop()

display_conversation()