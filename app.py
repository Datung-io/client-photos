import os
import streamlit as st
from google.cloud import storage
import json
from tempfile import NamedTemporaryFile

st.title("Client Photo Dashboard")

# Load service account JSON from Streamlit secrets
gcs_credentials = dict(st.secrets["gcp"])
with NamedTemporaryFile(mode="w+", delete=False) as tmpfile:
    json.dump(gcs_credentials, tmpfile)
    tmpfile.flush()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmpfile.name

# Set GCS config
BUCKET_NAME = "client-photos"

# Initialize storage client and bucket once
client = storage.Client()
bucket = client.bucket(BUCKET_NAME)

# List top-level folders (e.g., batch names)
def list_subfolders():
    return sorted(set(blob.name.split("/")[0] for blob in bucket.list_blobs() if "/" in blob.name))

# List image blobs inside a selected folder
def list_images(folder):
    return [blob for blob in bucket.list_blobs(prefix=folder + "/") if blob.name.lower().endswith((".jpg", ".jpeg", ".png"))]

# UI: Batch selection
batches = list_subfolders()
batch = st.selectbox("Select Batch", batches)

if batch:
    with st.spinner("Loading images..."):
        blobs = list_images(batch)

    if blobs:
        for blob in blobs:
            # Correct way to generate signed URL
            url = bucket.blob(blob.name).generate_signed_url(version="v4", expiration=3600)
            filename = blob.name.split("/")[-1]
            folder = blob.name.split("/")[0]
            st.image(url, caption=f"{folder}: {filename}", use_column_width=True)
    else:
        st.warning("No images found in this batch.")
