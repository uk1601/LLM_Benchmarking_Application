import streamlit as st
import os
import random
from google.cloud import storage
from google.oauth2 import service_account

# Load credentials from Streamlit secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

# Define the bucket name
BUCKET_NAME = 'gaia_data_damg_7245'

# Define the cache or download folder
CACHE_FOLDER = '.streamlit/cache/'

# Function to download a random file from the bucket and save it in the cache folder
def download_random_file_from_bucket():
    # Initialize a GCP storage client with the loaded credentials
    client = storage.Client(credentials=credentials)

    # Get the bucket
    bucket = client.bucket(BUCKET_NAME)

    # Define the folder in GCP bucket
    folder_prefix = '2023_gaia_dataset/validation/'

    # List all files in the specified folder
    blobs = list(bucket.list_blobs(prefix=folder_prefix))

    # Filter out any folder paths
    files = [blob for blob in blobs if not blob.name.endswith('/')]

    if not files:
        raise Exception(f"No files found in the folder {folder_prefix}")

    # Randomly choose a file from the folder
    random_blob = random.choice(files)

    # Create the cache folder if it doesn't exist
    if not os.path.exists(CACHE_FOLDER):
        os.makedirs(CACHE_FOLDER)

    # Define the path where the file will be saved locally
    file_name = random_blob.name.split('/')[-1]
    download_path = os.path.join(CACHE_FOLDER, file_name)

    # Download the file
    random_blob.download_to_filename(download_path)

    return download_path

# Streamlit App
def main():
    st.title("GCP Random File Downloader with Cache Check")

    st.write("Click the button to download a random file from the GCP bucket into a cache folder and check if it can be accessed.")

    # Button to trigger the download
    if st.button('Download Random File and Check Access'):
        # Call the function to download a random file
        try:
            file_path = download_random_file_from_bucket()
            st.success(f'File downloaded successfully! Saved at: {file_path}')

            # Check if the file exists in the cache folder
            if os.path.exists(file_path):
                st.write(f"Access check: The file '{file_path}' is accessible.")
                # Optionally display the file's contents if it's a text-based file
                if file_path.endswith(".txt") or file_path.endswith(".csv"):
                    with open(file_path, 'r') as file:
                        content = file.read()
                    st.text_area("File content:", content)
            else:
                st.error(f"Access check failed: The file '{file_path}' is not accessible.")
        except Exception as e:
            st.error(f'Error: {e}')

if __name__ == '__main__':
    main()
