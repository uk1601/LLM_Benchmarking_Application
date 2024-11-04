from google.cloud import storage
import os

def upload_folder_to_bucket(bucket_name, source_folder_path, destination_blob_name):

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    for root, dirs, files in os.walk(source_folder_path):
        for file in files:
            local_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_file_path, source_folder_path)
            blob_path = os.path.join(destination_blob_name, relative_path)

            blob = bucket.blob(blob_path)
            blob.upload_from_filename(local_file_path)
            print(f"File {local_file_path} uploaded to {blob_path}.")

bucket_name = "gaia_data_damg_7245"
source_folder_path = "2023"
destination_blob_name = "2023_gaia_dataset"

upload_folder_to_bucket(bucket_name, source_folder_path, destination_blob_name)