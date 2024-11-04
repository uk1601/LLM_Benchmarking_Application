import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.tools import tools  # Assuming this module has tool functions defined

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load environment variables
load_dotenv()

# Load the GAIA dataset locally 
with open('/path/to/dataset/metadata.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

# Set up OpenAI API key

# Function to get answer from OpenAI API based on question, context, and optional additional prompt
def get_agent_answer(question, context="", additional_prompt=""):
    prompt = f"""You are a general AI assistant. I will ask you a question. Report your thoughts, and finish your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER]. YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings. If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise. If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise. If you are asked for a comma-separated list, apply the above rules depending on whether the element is a number or a string. Answer the following question as best you can, speaking as a general AI assistant. You have access to the following tools:

Search: useful for when you need to answer questions about current events or the current state of the world
ReadImage: useful for reading image files. Input should be the file path to the image.
ReadExcel: useful for reading Excel files. Input should be the file path to the Excel file.
ReadCSV: useful for reading CSV files. Input should be the file path to the CSV file.
ReadZIP: useful for reading ZIP files. Input should be the file path to the ZIP file.
ReadPDF: useful for reading PDF files. Input should be the file path to the PDF file.
ReadJSON: useful for reading JSON files. Input should be the file path to the JSON file.
ReadPython: useful for reading Python files. Input should be the file path to the Python file.
ReadDOCX: useful for reading DOCX files. Input should be the file path to the DOCX file.
ReadPPTX: useful for reading PPTX files. Input should be the file path to the PPTX file.
ReadAudio: useful for reading audio files (MP3, WAV). Input should be the file path to the audio file.
ReadPDB: useful for reading PDB files. Input should be the file path to the PDB file.
ReadJSONLD: useful for reading JSON-LD files. Input should be the file path to the JSON-LD file.
ReadTXT: useful for reading TXT files. Input should be the file path to the TXT file.

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of the tool names
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin Remember to speak as a general AI assistant when giving your final answer.

Context: {context}

Question: {question}

{additional_prompt}
"""
    response = client.chat.completions.create(model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0)

    # Ensure response.choices is a list and access the first element
    if response.choices:
        return response.choices[0].message.content
    else:
        return "No response received from the model."

# Function to select a test case
def select_test_case():
    st.header("Select a Test Case")
    test_cases = [f"{case['task_id']}: {case['Question']}" for case in data]
    selected_case = st.selectbox("Choose a test case:", test_cases)
    return next(case for case in data if f"{case['task_id']}: {case['Question']}" == selected_case)

# Function to compare the LLM's answer with the correct answer
def compare_answers(test_case, agent_full_answer):
    st.subheader("Compare Answers")

    # Display the full LLM answer
    st.write("**LLM Full Answer:**")
    st.write(agent_full_answer)

    # Extract the final answer
    final_answer = agent_full_answer.split("Final Answer:")[-1].strip() if "Final Answer:" in agent_full_answer else agent_full_answer

    st.write("**LLM Final Answer:**", final_answer)
    st.write("**Correct Answer:**", test_case['Final answer'])

    # Determine correctness
    is_correct = final_answer.lower().strip() == test_case['Final answer'].lower().strip()
    st.write("**Is the answer correct?**", "Yes" if is_correct else "No")

    # If incorrect, prompt for additional guidance
    if not is_correct:
        st.session_state.show_guide_llm = True
        st.session_state.current_test_case = test_case
        st.session_state.current_context = test_case.get('file_name', '')

    return agent_full_answer, final_answer, is_correct

"""
####### Changed lines for download. (reference)
"""
def download_file(file_path):
    """Provide a download button for a file."""    # Ensure file exists
    if os.path.exists(file_path):
        with open(file_path, "rb") as file:
            file_bytes = file.read()
            file_name = os.path.basename(file_path)
            
            # Display download button
            st.download_button(
                label=f"Download {file_name}",
                data=file_bytes,
                file_name=file_name,
                mime="application/octet-stream"
            )
    else:
        st.warning(f"File {file_path} not found.")
"""
####### Changed lines for download. (reference) 

"""

# Function to generate a report after the evaluations
def generate_report():
    st.header("Evaluation Report")
    if 'feedback' not in st.session_state or not st.session_state.feedback:
        st.write("No evaluations have been performed yet.")
        return

    df = pd.DataFrame(st.session_state.feedback)

    accuracy = df['is_correct'].mean()
    st.write(f"**Overall Accuracy:** {accuracy:.2%}")

    fig, ax = plt.subplots()
    value_counts = df['is_correct'].value_counts()
    value_counts.plot(kind='bar', ax=ax, color=['red', 'green'])
    ax.set_xlabel("Correctness")
    ax.set_ylabel("Count")
    ax.set_title("Correct vs Incorrect Answers")

    labels = []
    if False in value_counts.index:
        labels.append('Incorrect')
    if True in value_counts.index:
        labels.append('Correct')
    ax.set_xticklabels(labels)

    plt.setp(ax.get_xticklabels(), rotation=0, ha='center')

    st.pyplot(fig)

    st.write("**Detailed Feedback:**")
    st.dataframe(df[['task_id', 'question', 'llm_full_answer', 'llm_final_answer', 'correct_answer', 'is_correct']])

# Function to handle reading any dependent files for a test case
def handle_file_reading(test_case):
    if test_case.get('file_name'):
        file_path = os.path.join('2023', 'validation', test_case['file_name'])
        if os.path.exists(file_path):
            # Determine the file type and use the appropriate tool
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            tool = None  # Default to None

            # Identify the appropriate tool based on file extension
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                tool = "ReadImage"
            elif ext in ['.xlsx', '.xls']:
                tool = "ReadExcel"
            elif ext == '.csv':
                tool = "ReadCSV"
            elif ext == '.zip':
                tool = "ReadZIP"
            elif ext == '.pdf':
                tool = "ReadPDF"
            elif ext == '.json':
                tool = "ReadJSON"
            elif ext == '.py':
                tool = "ReadPython"
            elif ext == '.docx':
                tool = "ReadDOCX"
            elif ext == '.pptx':
                tool = "ReadPPTX"
            elif ext in ['.mp3', '.wav']:
                tool = "ReadAudio"
            elif ext == '.pdb':
                tool = "ReadPDB"
            elif ext == '.jsonld':
                tool = "ReadJSONLD"
            elif ext == '.txt':
                tool = "ReadTXT"

            if tool and tool in tools:
                context = tools[tool](file_path)
                # If the tool is ReadAudio, extract transcription
                if tool == "ReadAudio":
                    try:
                        audio_data = json.loads(context)
                        transcription = audio_data.get('transcription', '')
                        context += f"\nTranscription: {transcription}"
                    except json.JSONDecodeError:
                        st.warning("Failed to decode audio metadata.")
                
                # Call the download function here
                download_file(file_path)
                
                return context
            else:
                # For unsupported tools or ReadTXT
                with open(file_path, 'r', encoding='utf-8') as f:
                    download_file(file_path)  # Call download function for text files too
                    return f.read()
        else:
            st.warning(f"Dependent file {test_case['file_name']} not found.")
            return ""
    return ""

# Function to evaluate the LLM's answer for a selected test case
def evaluate(test_case):
    st.spinner("Evaluating...")
    context = handle_file_reading(test_case)
    agent_full_answer = get_agent_answer(test_case['Question'], context)
    llm_full_answer, llm_final_answer, is_correct = compare_answers(test_case, agent_full_answer)

    # Save feedback
    st.session_state.feedback.append({
        'task_id': test_case['task_id'],
        'question': test_case['Question'],
        'llm_full_answer': llm_full_answer,
        'llm_final_answer': llm_final_answer,
        'correct_answer': test_case['Final answer'],
        'is_correct': is_correct
    })

# Function to re-evaluate a test case with additional user guidance
def re_evaluate(test_case, additional_prompt):
    st.spinner("Re-evaluating...")
    context = handle_file_reading(test_case)
    new_agent_full_answer = get_agent_answer(test_case['Question'], context, additional_prompt)
    new_llm_full_answer, new_llm_final_answer, new_is_correct = compare_answers(test_case, new_agent_full_answer)

    # Update the last feedback entry
    st.session_state.feedback[-1].update({
        'llm_full_answer': new_llm_full_answer,
        'llm_final_answer': new_llm_final_answer,
        'is_correct': new_is_correct
    })

# Main function to manage the Streamlit app flow
def main():
    st.title("LLM Evaluation Tool")

    # Initialize session state
    if 'feedback' not in st.session_state:
        st.session_state.feedback = []
    if 'show_guide_llm' not in st.session_state:
        st.session_state.show_guide_llm = False

    # Test case selection
    test_case = select_test_case()

    if st.button("Evaluate"):
        evaluate(test_case)

    if st.session_state.show_guide_llm:
        st.subheader("Provide Additional Guidance to the LLM")
        additional_prompt = st.text_area("Enter your prompt to guide the LLM:")
        if st.button("Re-evaluate"):
            re_evaluate(test_case, additional_prompt)
            st.session_state.show_guide_llm = False

    if st.button("Generate Report"):
        generate_report()

if __name__ == "__main__":
    main()
