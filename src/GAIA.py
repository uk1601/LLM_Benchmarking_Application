import streamlit as st
from PIL import Image

# Set page config as the first Streamlit function
st.set_page_config(page_title="LLM Benchmarking Application", layout="centered")

# Load and display a banner or logo (if available)
# image = Image.open('./src/Logo.png')  # Add a relevant logo or banner
# st.image(image, use_column_width=True)

# Title and Subtitle
st.title("Welcome to the LLM Benchmarking Application")
st.write("""
The **LLM Benchmarking Application** is designed to analyze and assess the performance of Large Language Models (LLMs) based on their responses to a variety of tasks.
By leveraging cloud-based infrastructure, this platform provides real-time insights and metrics for LLM evaluations.
""")

# Overview of the Features
st.subheader("Main Features")
st.write("""
- **LLM Prompting**: Send prompts to LLMs with or without annotations and gather their responses.
- **Performance Dashboards**: Visualize LLM performance through various metrics such as overall accuracy, improvement rate, and failure rate.
- **Customizable**: Choose your LLM Model, Reprompt with annotations for better evaluation, enabling a more robust LLM comparison.
""")

# Instructions for Use
st.subheader("How to Use This Application:")
st.write("""
1. **LLM Prompting**: Go to the LLM Prompting page, Select the LLM Model in LLM Management section, and then select a task, prompt a large language model, and assess its performance. You can either accept the response as is or reprompt with annotations.
2. **Performance Dashboards**: Use the dashboards to visualize various metrics about the LLM's performance.
3. **Interact with the LLM**: Use the application to send real-time requests to LLMs and evaluate their responses based on real-world tasks.
""")

# Navigation buttons to other pages
st.subheader("Explore the Application")
st.write("Navigate to the available pages using the buttons below:")

col1, col2 = st.columns(2)

# Redirect buttons using the correct st.experimental_set_query_params method
with col1:
    if st.button('LLM Prompting'):
        #st.experimental_set_query_params(page="1_LLM_Prompting")
        st.write("To test different LLM models, Navigate to LLM Prompting Page using the left side bar. ")

with col2:
    if st.button('Dashboard'):
        #st.experimental_set_query_params(page="2_Dashboard")
        st.write("To View the dashboard of Metrics related to the application, Navigate to Dashboard Page using the left side bar. ")

# Footer
footer = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #f255f255f255;
    color: white;
    text-align: center;
    padding: 10px;
    font-size: 12px;
}
</style>
<div class="footer">
    LLM Performance Evaluation System.
</div>
"""
st.markdown(footer, unsafe_allow_html=True)
