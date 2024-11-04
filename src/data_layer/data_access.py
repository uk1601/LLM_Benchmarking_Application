from typing import Type
import os
import sys
# Add the 'src' directory to the Python path dynamically
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from sqlalchemy.orm import Session, sessionmaker
from src.data_layer.models import Task, LLM, LLMResponse
from sqlalchemy import func, create_engine, delete
import streamlit as st
class DataAccess:
    def __init__(self):
        DATABASE_URL = st.secrets["database"]["database_url"]

        engine = create_engine(DATABASE_URL)
        SessionMaker = sessionmaker(bind=engine)
        session = SessionMaker()
        print("Connected to database")
        self.session = session

    def get_all_tasks(self):
        return self.session.query(Task).all()
    def get_random_task_that_is_not_tested(self) -> Type[Task]| None:
        # Perform a left join between Task and LLMResponse, then filter where LLMResponse is NULL
        return (
            self.session.query(Task)
            .outerjoin(LLMResponse, Task.taskid == LLMResponse.taskid)
            .filter(LLMResponse.taskid == None)
            .order_by(func.random())  # Random order
            .first()  # Get one random task
        )

    def get_random_task(self):
        return (
            self.session.query(Task)
            .order_by(func.random())
            .first()
        )

    def get_task_by_id(self, task_id: str):
        return self.session.query(Task).filter(Task.taskid == task_id).first()

    def get_tasks_by_level(self, level: int):
        return self.session.query(Task).filter(Task.level == level).all()

    def get_all_llms(self):
        return self.session.query(LLM).all()

    def get_llm_by_id(self, llm_id: int):
        return self.session.query(LLM).filter(LLM.llmid == llm_id).first()

    def get_responses_for_task(self, task_id: str):
        return self.session.query(LLMResponse).filter(LLMResponse.taskid == task_id).all()

    def get_responses_for_llm(self, llm_id: int):
        return self.session.query(LLMResponse).filter(LLMResponse.llmid == llm_id).all()

    def query_by_file_type(self, file_extension: str):
        return (self.session.query(Task).filter(
            func.right(Task.filename, len(file_extension) + 1).like(f'.{file_extension}')
        ).order_by(func.random())
                .first())

    def get_all_llms(self) -> list[LLM]:
        """
        Fetches all LLMs from the database.
        """
        return self.session.query(LLM).all()

    def delete_llm(self, llmid: int) -> None:
        """
        Deletes an LLM by ID from the database.
        """
        self.session.execute(delete(LLM).where(LLM.llmid == llmid))
        self.session.commit()
    def create_llm_response_for_task(self, taskid: str, responsetext: str,
                                     resultcategory: str,
                                     llmid: int = 2,
                                     isannotated: bool = False):
        if resultcategory not in ["With Annotation" , "AS IS" , "Helpless!"]:
            raise ValueError(f"Invalid result category: {resultcategory}. "
                             f"Expected one of 'correct', 'incorrect', 'incomplete'.")
        new_response = LLMResponse(
            taskid=taskid,
            llmid=llmid,
            responsetext=responsetext,
            resultcategory=resultcategory,
            isannotated=isannotated
        )
        self.session.add(new_response)
        self.session.commit()
        print(new_response)# Commit the transaction to save the new row in the database
        return new_response

    def create_llm_entry(self, llmid: int, llmname: str, version: str, parameters: str):
        new_llm = LLM(
            llmid=llmid,
            llmname=llmname,
            version=version,
            parameters=parameters
        )
        self.session.add(new_llm)
        self.session.commit()  # Commit the transaction to save the new LLM in the database
        return new_llm


data_access_instance = DataAccess()

if __name__ == "__main__":
    data_access_instance = DataAccess()

