from sqlalchemy import create_engine, MetaData, Table, select, func, case
from sqlalchemy.orm import sessionmaker
import random
from datetime import datetime
import os
import streamlit as st


# Construct the database URL for SQLAlchemy
DATABASE_URL = st.secrets["database"]["database_url"]
# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Function to list all tables in the database
def list_tables():
    metadata.reflect(bind=engine)
    tables = metadata.tables.keys()
    print("Tables in the database:")
    for table in tables:
        print(table)

# Function to list columns and optionally fetch data from a table
def list_columns_and_data(table_name, fetch_data=False):
    metadata.reflect(bind=engine)
    if table_name not in metadata.tables:
        print(f"Table {table_name} does not exist.")
        return
    
    table = metadata.tables[table_name]
    columns = [column.name for column in table.columns]
    print(f"Columns in table {table_name}: {columns}")
    
    if fetch_data:
        with engine.connect() as connection:
            select_query = select(table)
            result = connection.execute(select_query)
            for row in result.fetchall():
                print(row)


# Insert random data into 'llms' and 'llmresponses' tables
def insert_random_data(start,end):

    # Begin a transaction
    with engine.begin() as connection:
        # Reflect the metadata of the database tables
        metadata.reflect(bind=engine)

        # Insert into llms table
        llms_table = metadata.tables['llms']
        llms_data = [
            {'llmid': 1, 'llmname': 'GPT-3', 'version': 'v1', 'parameters': 175000000000},
            {'llmid': 2, 'llmname': 'GPT-4', 'version': 'v2', 'parameters': 175000000000},
            {'llmid': 3, 'llmname': 'ChatGPT', 'version': 'v1', 'parameters': 6800000000}
        ]
        connection.execute(llms_table.insert().values(llms_data))
        print("Inserted data into llms table.")

        # Fetch task data from 'tasks' table
        tasks_table = metadata.tables['tasks']
        tasks = connection.execute(select(tasks_table.c.taskid, tasks_table.c.expectedanswer)).fetchall()

        # Insert into llmresponses table
        llmresponses_table = metadata.tables['llmresponses']
        is_annotated_options = [True, False]
        result_category_options = ['AS IS', 'With Annotation', 'Helpless!']

        for i in range(start,end):
            task = random.choice(tasks)
            taskid = task.taskid
            responsetext = task.expectedanswer
            llmid = random.choice([1, 2, 3])  # Random LLM ID
            isannotated = random.choice(is_annotated_options)
            resultcategory = random.choice(result_category_options)
            timestamp = datetime.now()

            connection.execute(llmresponses_table.insert().values(
                responseid=i,
                taskid=taskid,
                llmid=llmid,
                responsetext=responsetext,
                isannotated=isannotated,
                resultcategory=resultcategory,
                timestamp=timestamp
            ))

        print("Inserted data into llmresponses table.")

# Function to delete all data from the llms and llmresponses tables
def delete_data():
    # Start a session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Reflect the tables
    metadata.reflect(bind=engine)
    llms_table = metadata.tables['llms']
    llmresponses_table = metadata.tables['llmresponses']

    try:
        # Delete data from the 'llmresponses' table
        session.execute(llmresponses_table.delete())
        print("Deleted all data from llmresponses table.")

        # Delete data from the 'llms' table
        session.execute(llms_table.delete())
        print("Deleted all data from llms table.")

        # Commit the transaction
        session.commit()

    except Exception as e:
        # Rollback in case of any errors
        session.rollback()
        print(f"An error occurred: {e}")
    
    finally:
        # Close the session
        session.close()


# # Function to calculate overall accuracy per LLM
# def overall_accuracy_per_llm():
#     Session = sessionmaker(bind=engine)
#     session = Session()
#     metadata.reflect(bind=engine)

#     llmresponses_table = metadata.tables['llmresponses']
#     llms_table = metadata.tables['llms']

#     # Corrected query to calculate the "AS IS" responses where is_annotated == False for each specific LLM
#     query = session.query(
#         llms_table.c.llmname,
#         (func.sum(case(
#             (llmresponses_table.c.isannotated == False, 1)
#         )) / func.count(llmresponses_table.c.responseid) * 100).label("accuracy_percentage")
#     ).filter(
#         llmresponses_table.c.resultcategory == 'AS IS'
#     ).join(llms_table, llmresponses_table.c.llmid == llms_table.c.llmid).group_by(
#         llms_table.c.llmname
#     )

#     results = [(row[0], row[1]) for row in query.all()]
#     session.close()
#     return results
    # print("Overall Accuracy per LLM (As Is):")
    # for row in query.all():
    #     print(f"LLM ID: {row[0]}, Accuracy: {row[1]:.2f}%")

    # session.close()


# Function to calculate accuracy with annotation per LLM
def accuracy_with_annotation():
    Session = sessionmaker(bind=engine)
    session = Session()
    metadata.reflect(bind=engine)

    llmresponses_table = metadata.tables['llmresponses']
    llms_table = metadata.tables['llms']

    query = session.query(
        llms_table.c.llmname,
        (func.count(case(
            (llmresponses_table.c.isannotated == True, llmresponses_table.c.responseid)
        )) / func.count(func.distinct(llmresponses_table.c.taskid)) * 100).label("accuracy_with_annotation")
    ).filter(
        llmresponses_table.c.resultcategory == 'With Annotation'
    ).join(llms_table, llmresponses_table.c.llmid == llms_table.c.llmid).group_by(
        llms_table.c.llmname
    )

    results = [(row[0], row[1]) for row in query.all()]
    session.close()
    return results

    # print("\nAccuracy with Annotation:")
    # for row in query.all():
    #     print(f"LLM ID: {row[0]}, Accuracy with Annotation: {row[1]:.2f}%")

    # session.close()


# Function to calculate improvement rate per LLM
def improvement_rate():
    Session = sessionmaker(bind=engine)
    session = Session()
    metadata.reflect(bind=engine)

    llmresponses_table = metadata.tables['llmresponses']
    llms_table = metadata.tables['llms']

    query = session.query(
        llms_table.c.llmname,
        (func.count(case(
            (llmresponses_table.c.resultcategory == 'With Annotation', llmresponses_table.c.responseid)
        )) / func.count(case(
            (llmresponses_table.c.resultcategory != 'AS IS', llmresponses_table.c.responseid)
        )) * 100).label("improvement_rate")
    ).join(llms_table, llmresponses_table.c.llmid == llms_table.c.llmid).group_by(
        llms_table.c.llmname
    )

    results = [(row[0], row[1]) for row in query.all()]
    session.close()
    return results
    # print("\nImprovement Rate:")
    # for row in query.all():
    #     print(f"LLM ID: {row[0]}, Improvement Rate: {row[1]:.2f}%")

    # session.close()


# Function to calculate failure rate after annotation per LLM
def failure_rate_after_annotation():
    Session = sessionmaker(bind=engine)
    session = Session()
    metadata.reflect(bind=engine)

    llmresponses_table = metadata.tables['llmresponses']
    llms_table = metadata.tables['llms']

    query = session.query(
        llms_table.c.llmname,
        (func.count(case(
            (llmresponses_table.c.resultcategory == 'Helpless!', llmresponses_table.c.responseid)
        )) / func.count(func.distinct(llmresponses_table.c.taskid)) * 100).label("failure_rate")
    ).join(llms_table, llmresponses_table.c.llmid == llms_table.c.llmid).group_by(
        llms_table.c.llmname
    )

    results = [(row[0], row[1]) for row in query.all()]
    session.close()
    return results


    # print("\nFailure Rate after Annotation:")
    # for row in query.all():
    #     print(f"LLM ID: {row[0]}, Failure Rate after Annotation: {row[1]:.2f}%")

    # session.close()


# Function to calculate performance by task level
def performance_by_task_level():
    Session = sessionmaker(bind=engine)
    session = Session()
    metadata.reflect(bind=engine)

    tasks_table = metadata.tables['tasks']
    llmresponses_table = metadata.tables['llmresponses']
    llms_table = metadata.tables['llms']

    query = session.query(
        llms_table.c.llmname,
        tasks_table.c.level,
        (func.count(case(
            (llmresponses_table.c.resultcategory == 'AS IS', llmresponses_table.c.responseid)
        )) / func.count(func.distinct(llmresponses_table.c.taskid)) * 100).label("performance_by_level")
    ).join(llms_table, llmresponses_table.c.llmid == llms_table.c.llmid).join(
        tasks_table, tasks_table.c.taskid == llmresponses_table.c.taskid
    ).group_by(
        llms_table.c.llmname, tasks_table.c.level
    )

    results = [(row[0], row[1], row[2]) for row in query.all()]
    session.close()
    return results

    # print("\nPerformance by Task Level:")
    # for row in query.all():
    #     print(f"LLM ID: {row[0]}, Task Level: {row[1]}, Performance: {row[2]:.2f}%")

    # session.close()





# # Execute the functions
# list_tables()
# print("------------------------------\n")
# list_columns_and_data('tasks', fetch_data=False)
# print("------------------------------\n")
# list_columns_and_data('llms',True)
# print("------------------------------\n")
# list_columns_and_data('llmresponses',True)
# print("------------------------------\n")
# # Execute the delete function
# #delete_data()

# print("Insering Data...................\n")
# # Execute the insert function
# #insert_random_data(1,1001)


#list_columns_and_data('llms',True)
#list_columns_and_data('llmresponses',True)


# acc1=overall_accuracy_per_llm()
# print(f"Metrics 1.........\n{acc1}")
# acc2=accuracy_with_annotation()
# print(f"Metrics 2.........\n{acc2}")
# acc3=improvement_rate()
# print(f"Metrics 3.........\n{acc3}")
# acc4=failure_rate_after_annotation()
# print(f"Metrics 4.........\n{acc4}")
# acc5=performance_by_task_level()
# print(f"Metrics 5.........\n{acc5}")

def response_count_by_category():
    Session = sessionmaker(bind=engine)
    session = Session()
    # Reflect the tables
    metadata.reflect(bind=engine)

    llmresponses_table = metadata.tables['llmresponses']

    query = session.query(
        llmresponses_table.c.resultcategory,
        func.count(llmresponses_table.c.responseid).label('count')
    ).group_by(llmresponses_table.c.resultcategory)

    return query.all()

def response_breakdown_by_task_level():
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Reflect the tables
    metadata.reflect(bind=engine)

    llmresponses_table = metadata.tables['llmresponses']
    tasks_table = metadata.tables['tasks']

    # Query to count responses by resultcategory and task level
    query = session.query(
        tasks_table.c.level,
        llmresponses_table.c.resultcategory,
        func.count(llmresponses_table.c.responseid).label('count')
    ).join(tasks_table, llmresponses_table.c.taskid == tasks_table.c.taskid).group_by(tasks_table.c.level, llmresponses_table.c.resultcategory)

    return query.all()
