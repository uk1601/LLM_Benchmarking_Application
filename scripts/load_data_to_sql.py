from datasets import load_dataset

ds = load_dataset("gaia-benchmark/GAIA", "2023_all")
validation = ds["validation"]
print(validation)
type(validation[1]["Annotator Metadata"])

#TODO: Update values
# Database connection parameters
db_params = {
    'dbname': '***',
    'user': '***',
    'password': '***',
    'host': '***',
    'port': '***'
}
from datasets import load_dataset
import psycopg2
from psycopg2.extras import Json


# Function to insert data into the Tasks table
def insert_task(cursor, task_id, question, level, expected_answer, file_name, file_path, annotations):
    sql = """
    INSERT INTO Tasks (TaskId, Question, ExpectedAnswer, Level, FileName, FilePath, Annotations)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (TaskId) DO UPDATE SET
    Question = EXCLUDED.Question,
    ExpectedAnswer = EXCLUDED.ExpectedAnswer,
    Level = EXCLUDED.Level,
    FileName = EXCLUDED.FileName,
    FilePath = EXCLUDED.FilePath,
    Annotations = EXCLUDED.Annotations
    """
    cursor.execute(sql, (task_id, question, expected_answer, level, file_name, file_path, Json(annotations)))

# Main function to process the dataset and insert data
def process_dataset():
    # Load the dataset
    ds = load_dataset("gaia-benchmark/GAIA", "2023_all")
    validation_set = ds["validation"]

    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    try:
        for row in validation_set:
            task_id = row['task_id']
            question = row['Question']
            level = row['Level']
            expected_answer = row['Final answer']
            file_name = row['file_name'] if row['file_name'] else None
            file_path = row['file_path'] if row['file_path'] else None
            annotations = row['Annotator Metadata']

            insert_task(cursor, task_id, question, level, expected_answer, file_name, file_path, annotations)

        conn.commit()
        print(f"Data inserted successfully! {validation_set.num_rows} rows processed.")

    except (Exception, psycopg2.Error) as error:
        print("Error while inserting data:", error)
        conn.rollback()

    finally:
        if conn:
            cursor.close()
            conn.close()

# Run the script
if __name__ == "__main__":
    process_dataset()