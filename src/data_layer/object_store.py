from google.cloud import storage
from google.oauth2 import service_account
import tempfile
from google.api_core.exceptions import Forbidden
import streamlit as st
import os

def download_file_from_gcs(file_name):
    try:
        gcp_service_account = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(gcp_service_account)
        client = storage.Client(credentials=credentials)

        # Define the bucket name and full object path
        bucket_name = "gaia_data_damg_7245"
        object_name = f"2023_gaia_dataset/validation/{file_name}"

        # Get the bucket and blob
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)

        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        # Define the local file path
        local_file_path = os.path.join(temp_dir, file_name)

        # Download the file
        blob.download_to_filename(local_file_path)
        print(f"🗳️🗳️🗳️🗳️Successful downloading the required file:{local_file_path} 🗳️🗳️🗳️🗳️")
        return local_file_path

    except Forbidden as e:
        print(f"Permission denied: {e}")
        print("Please check the service account permissions and ensure it has access to the bucket and object.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
if __name__ == "__main__":
    print(download_file_from_gcs("076c8171-9b3b-49b9-a477-244d2a532826.xlsx"))
