import os
import sys

# Add the 'src' directory to the Python path dynamically
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.data_layer.data_access import data_access_instance
from src.data_layer.models import Task
from src.utils.gpt import evaluate

import time
import streamlit as st

session_defaults = {
    "Task": None,
    "Response": None,
    "Reprompt": False,
    "Re_Response": None,
    "File_Path": None,
    'selected_llm': None,
    'display_reponse': False,
    'display_re_reponse': False,
    'display_annotation': False,
    'display_question_answer': False,
    'display_container': True
}


def initialize_session_state():
    for key, default in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def clear_session_storage():
    print("Clearing storage")
    for key, default in session_defaults.items():
        if key != "selected_llm":
            st.session_state[key] = default

def need_an_update():
    st.rerun()

def llm_management_ui():
    st.sidebar.title("LLM Management")
    print("LLM:-------------------", st.session_state['selected_llm'])
    # Fetch all LLMs
    llms = data_access_instance.get_all_llms()

    # Extract the names of LLMs for the dropdown
    llm_options = {f"{llm.llmname}": llm for llm in llms}
    if st.session_state["selected_llm"] is None:
        st.session_state["selected_llm"] = llms[0]
    # Initialize session state for selected_llm if not already set
    if 'selected_llm' not in st.session_state:
        st.session_state['selected_llm'] = next(iter(llm_options.values())) if llm_options else None

    # Sidebar dropdown to select the current LLM
    st.sidebar.subheader("Select LLM")
    selected_llm_str = st.sidebar.selectbox(
        "Select from available LLMs",
        list(llm_options.keys()),
        index=list(llm_options.keys()).index(st.session_state['selected_llm'].llmname) if st.session_state['selected_llm'] else 0,
        key="selected_llm_str"
    )

    # Update session state with the newly selected LLM object
    if selected_llm_str != st.session_state['selected_llm'].llmname:
        st.session_state['selected_llm'] = llm_options[selected_llm_str]
        st.rerun()

    # Display the currently selected LLM
    st.sidebar.write(f"**Currently Selected LLM:** {selected_llm_str}")

    # Debugging or logging purposes
    print(f"Selected LLM: {st.session_state['selected_llm']}")  # This prints the actual LLM object for verification


def get_random_task():
    clear_session_storage()
    task: Task | None = data_access_instance.get_random_task()
    st.session_state["Task"] = task
    print("🧹🧹🧹🧹Got random question nd cleared storage 🧹🧹🧹🧹")
    return task


def parse_response(response):
    # Split the response into explanation and final answer
    parts = response.split("Final Answer:", 1)

    if len(parts) == 2:
        explanation = parts[0].strip()
        final_answer = parts[1].strip()
        return explanation, final_answer
    else:
        return None, None


# def display_response(response):
#     st.session_state["Response"] = response
#     explanation, final_answer = parse_response(response)
#
#     if explanation is not None and final_answer is not None:
#         # Display the explanation in an expander
#         with st.expander("Thought Process", expanded=False):
#             st.write(explanation)
#
#         # Display the final answer
#         st.success(f"Final Answer: {final_answer}")
#         # st.rerun()
#     else:
#         # Backup: Display the whole response if parsing fails
#         st.warning("Couldn't parse the response into separate parts. Displaying the full response:")
#         st.success(response)
#         # st.rerun()
def display_random_button():
    if st.button("Pick a random question 🎲"):
        task: Task | None = get_random_task()
        st.session_state["Task"] = task

def set_title():
    title = "Prompting 🤖"
    if st.session_state["selected_llm"]:

        title += f" with {st.session_state['selected_llm'].llmname}"
    st.title(title)


def display_question_answer():
    task: Task = st.session_state["Task"]
    st.text_area(label="Question", value=task.question)
    st.text_input(label="Expected Answer", value=task.expectedanswer)
    if task.filename and st.session_state["File_Path"] is None:
        with st.spinner("Getting required files"):
            from src.data_layer.object_store import download_file_from_gcs
            file_path = download_file_from_gcs(task.filename)
            st.session_state["File_Path"] = file_path


def display_download_button():
    if st.session_state["File_Path"]:
        file_path = st.session_state["File_Path"]
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


def hide_re_annotation_button():
    st.session_state["Reprompt"] = True


def display_re_annotation_button():
    if st.session_state["Reprompt"] is False and st.button("Re-prompt with annotations", type="secondary",
                                                           on_click=hide_re_annotation_button):
        print("-----------Re-prompting with annotations-----------------")
        st.session_state["Reprompt"] = True


def display_mark_as_is_button():
    if st.button("Mark as correct", type="primary"):
        # Show success message if db ubdate is successful
        if data_access_instance.create_llm_response_for_task(task.taskid, st.session_state["Response"], "AS IS", st.session_state["selected_llm"].llmid):
            st.toast("Response marked as correct.", icon='✅')
            clear_session_storage()
            time.sleep(2)
            st.rerun()
        else:
            st.toast("Failed to update response in the database.", icon='⚠️')
            time.sleep(2)
            clear_session_storage()
            st.rerun()


def display__mark_correct_after_annotation_button():
    if st.button("Mark as correct", type="primary"):
        if data_access_instance.create_llm_response_for_task(task.taskid, st.session_state["Re_Response"],
                                                             "With Annotation", st.session_state["selected_llm"].llmid, isannotated=True):
            st.toast("Response marked as correct.", icon='✅')
            clear_session_storage()
            time.sleep(2)
            st.rerun()
        else:
            st.toast("Failed to update response in the database.", icon='⚠️')
            clear_session_storage()
            st.renrun()

def hide_container():
    st.session_state["display_container"] = False

def display_prompt_button():
    if st.button("Prompt LLM", type="primary"):
        task: Task = st.session_state["Task"]
        with st.spinner("Generating Response..."):
            st.session_state["Response"] = evaluate(task, st.session_state["File_Path"], llm = st.session_state["selected_llm"])
            st.session_state["display_container"] = True
            st.rerun()
            # display_response(st.session_state["Response"])


def display_failed_even_after_annotation_button():
    if st.button("Mark as failed to answer", type="secondary"):
        with st.spinner("Updating response..."):
            if data_access_instance.create_llm_response_for_task(task.taskid, st.session_state["Re_Response"],
                                                                 "Helpless!", st.session_state["selected_llm"].llmid, isannotated=True):
                st.toast("Response marked as failed to answer.", icon='✅')
                clear_session_storage()
                time.sleep(2)
                st.rerun()
            else:
                st.toast("Failed to update response in the database.", icon='⚠️')
                clear_session_storage()
                time.sleep(2)
                st.rerun()


def display_re_response():
    pass


def display_response(res):
    response = None
    if res == "Response":
        response = st.session_state["Response"]
    elif res == "Re_Response":
        response = st.session_state["Re_Response"]
    if response is not None:
        explanation, final_answer = parse_response(response)
        if explanation is not None and final_answer is not None:
            with st.expander("Thought Process", expanded=False):
                st.write(explanation)
            st.success(f"Final Answer: {final_answer}")
        else:
            st.warning("Couldn't parse the response into separate parts. Displaying the full response:")
            st.success(response)


def display_reprompt_button():
    if st.button("Re-Prompt", type="primary"):
        task: Task = st.session_state["Task"]
        with st.spinner("Generating Response..."):
            st.session_state["Re_Response"] = evaluate(task, st.session_state["File_Path"], llm = st.session_state["selected_llm"], annotation=True)
            st.rerun()


def display_footer_buttons():
    if st.session_state["display_container"]:
        if st.session_state["Task"]:
            st.markdown("---")
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                display_download_button()
            with col2:
                if (st.session_state["Reprompt"] is False) and (st.session_state["Response"] is not None) and (
                        st.session_state["Re_Response"] is None):
                    display_re_annotation_button()
                if st.session_state["Re_Response"] is not None and st.session_state["Response"] is not None and \
                        st.session_state["Reprompt"]:
                    display_failed_even_after_annotation_button()
            with col3:
                if st.session_state["Response"] is None and st.session_state["Task"] is not None and not st.session_state[
                    "Reprompt"]:
                    display_prompt_button()
                if st.session_state["Response"] is not None and st.session_state["Re_Response"] is None and not \
                st.session_state["Reprompt"]:
                    display_mark_as_is_button()
                if st.session_state["Re_Response"] is None and st.session_state["Response"] is not None and \
                        st.session_state["Reprompt"]:
                    display_reprompt_button()
                if st.session_state["Re_Response"] is not None and st.session_state["Response"] is not None and \
                        st.session_state["Reprompt"]:
                    display__mark_correct_after_annotation_button()


def display_annotation():
    task: Task = st.session_state["Task"]
    print("Task", task)
    st.session_state["Task"].annotations = st.text_area("Annotator Metadata", task.annotations)


if __name__ == "__main__":
    initialize_session_state()
    llm_management_ui()
    task = st.session_state["Task"]
    set_title()
    selected_llm = st.session_state['selected_llm']
    display_random_button()
    if st.session_state["Task"]:
        display_question_answer()
    if st.session_state["Response"] is not None and st.session_state["Reprompt"] is True:
        display_annotation()
    if st.session_state["Response"] and not st.session_state["Re_Response"] and not st.session_state["Reprompt"]:
        display_response("Response")
    elif st.session_state["Re_Response"]:
        display_response("Re_Response")
    display_footer_buttons()
