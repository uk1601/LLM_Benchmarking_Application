import base64
import json
import os

from openai import OpenAI
import streamlit as st

from src.data_layer.data_access import data_access_instance
from src.data_layer.models import Task
from src.data_layer.object_store import download_file_from_gcs
from src.utils.tools import tools

from dotenv import load_dotenv
import os

load_dotenv()
# print("-----------------------")
# print(os.getcwd())
# burl = st.secrets["openAI"]["base_url"]
# print(burl)
# print(st.secrets["openAI"]["api_key"])
# print("-----------------------")
client = OpenAI(
    api_key=st.secrets["openAI"]["api_key"]
)


def get_image_data_url(image_file: str, image_format: str) -> str:
    """
    Helper function to converts an image file to a data URL string.

    Args:
        image_file (str): The path to the image file.
        image_format (str): The format of the image file.

    Returns:
        str: The data URL of the image.
    """
    try:
        with open(image_file, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"Could not read '{image_file}'.")
        exit()
    return f"data:image/{image_format};base64,{image_data}"


def handle_file_reading(task: Task, file_path: str = None):
    print(f"File path: {file_path}")
    if task.filename:
        # Attempt to download the file from GCS

        # Check if the file was downloaded successfully and exists on disk
        if file_path and os.path.exists(file_path):
            # Determine the file type and use the appropriate tool
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            tool = None  # Default to None
            print(f"File extension: {ext}")
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

            if tool and tool != "ReadImage" and tool in tools:
                context = tools[tool](file_path)
                # If the tool is ReadAudio, extract transcription
                if tool == "ReadAudio":
                    try:
                        audio_data = json.loads(context)
                        transcription = audio_data.get('transcription', '')
                        context += f"\nTranscription: {transcription}"
                    except json.JSONDecodeError:
                        st.warning("Failed to decode audio metadata.")
                print("-------------Context----------------")
                print(context)
                return (context, tool)
            elif tool == "ReadImage":
                context = get_image_data_url(file_path, ext)
                return (context, tool)
            else:
                # If the tool is unsupported, treat as plain text or return empty string
                with open(file_path, 'r', encoding='utf-8') as f:
                    return (f.read(), tool)
        else:
            # If the file download failed or file does not exist
            st.warning(f"File {task.filename} could not be downloaded or was not found.")
            return ("", None)
    return ("", None)


def evaluate(task: Task, file_path, llm, annotation=False):
    print(f"llm: {llm.llmname}")
    context, tool = handle_file_reading(task, file_path)
    question = task.question
    if annotation:
        print("---Annotation---")
        print(task.annotations)
        question = task.question + task.annotations
    agent_full_answer = get_agent_answer(question, context, llm, tool=tool)
    return agent_full_answer


def get_agent_answer(question, context="", llm=None, additional_prompt="", tool=None):
    if llm is None:
        llm = {"llmname": "gpt-4o-mini"}
    prompt = f"""You are a general AI assistant. I will ask you a question. Report your thoughts, and finish your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER]. YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings. If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise. If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise. If you are asked for a comma-separated list, apply the above rules depending on whether the element is a number or a string. Answer the following question as best you can, speaking as a general AI assistant.
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

Question: {question}

{additional_prompt}
"""
    message = {"role": "user",
                   "content": [
                       {
                           "type": "text",
                           "text": prompt
                       }
                   ]}
    if tool == "ReadImage":
        message["content"].append({
            "type": "image_url",
            "image_url": {
                "url": context,
                "detail": "low"
            }
        })
    else:
        message["content"].append({
            "type": "text",
            "text": f"Context: {context}"
        })
    print(f"Message: {message}")
    response = client.chat.completions.create(
        model=llm.llmname or "gpt-4o-mini",
        messages=[message],
        temperature=0)

    # Ensure response.choices is a list and access the first element
    if response.choices:
        return response.choices[0].message.content
    else:
        return "No response received from the model."


def get_random_task():
    task: Task | None = data_access_instance.get_random_task()
    return task


if __name__ == "__main__":
    llm = data_access_instance.get_all_llms()[0]
    task = data_access_instance.query_by_file_type("png")
    path = None
    if task.filename:
        path = download_file_from_gcs(task.filename)
    print(f"{task.taskid}\n"
          f"{task.question}\n"
          f"{task.expectedanswer}\n"
          f"{task.filename}"
          f"\nFile Path = {task.filepath}")
    print(path)
    response = evaluate(task, path, llm)
    print(response)
