import os
import streamlit as st
from google.cloud import storage
import json
from tempfile import NamedTemporaryFile

st.title("Client Photo Dashboard")

# Load service account JSON from Streamlit secrets
gcs_credentials = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_JSON"])
with NamedTemporaryFile(mode="w+", delete=False) as tmpfile:
    json.dump(gcs_credentials, tmpfile)
    tmpfile.flush()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmpfile.name

# Set GCS config
BUCKET_NAME = "your-bucket-name"  # TODO: replace with your actual GCS bucket name

# Get batches (folders)
def list_subfolders(bucket_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    return sorted(set(blob.name.split("/")[0] for blob in bucket.list_blobs() if "/" in blob.name))

# Get images in a folder
def list_images(bucket_name, folder):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    return [blob for blob in bucket.list_blobs(prefix=folder + "/") if blob.name.lower().endswith((".jpg", ".jpeg", ".png"))]

# Main UI
batches = list_subfolders(BUCKET_NAME)
batch = st.selectbox("Select Batch", batches)

if batch:
    blobs = list_images(BUCKET_NAME, batch)
    if blobs:
        for blob in blobs:
            url = blob.generate_signed_url(version="v4", expiration=3600)
            st.image(url, caption=blob.name.split("/")[-1], use_column_width=True)
    else:
        st.warning("No images found in this batch.")
