import os
import streamlit as st
from google.cloud import storage
import json
from tempfile import NamedTemporaryFile
from urllib.parse import quote

# Page config
st.set_page_config(page_title="Client Photo Dashboard", layout="wide")
st.title("📸 Client Photo Dashboard")

# Load service account JSON from Streamlit secrets
gcs_credentials = dict(st.secrets["gcp"])
with NamedTemporaryFile(mode="w+", delete=False) as tmpfile:
    json.dump(gcs_credentials, tmpfile)
    tmpfile.flush()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmpfile.name

# Constants
BUCKET_NAME = "client-photos"

# Initialize and cache GCS client and bucket
@st.cache_resource
def get_bucket():
    client = storage.Client()
    return client.bucket(BUCKET_NAME)

bucket = get_bucket()

# Extract 3-level hierarchy: batch / agent / client
def list_all_blobs():
    return list(bucket.list_blobs())

def extract_hierarchy(blobs):
    hierarchy = {}
    for blob in blobs:
        parts = blob.name.split("/")
        if len(parts) >= 3 and blob.name.lower().endswith((".jpg", ".jpeg", ".png")):
            batch, agent, client = parts[:3]
            hierarchy.setdefault(batch, {}).setdefault(agent, {}).setdefault(client, []).append(blob)
    return hierarchy

# Display utility
def display_images(blobs):
    if not blobs:
        st.warning("⚠️ No images found for this selection.")
        return

    cols = st.columns(3)
    for i, blob in enumerate(blobs):
        with cols[i % 3]:
            try:
                url = bucket.blob(blob.name).generate_signed_url(version="v4", expiration=3600)
                label = "/".join(blob.name.split("/")[:3])
                st.image(url, caption=label, use_container_width=True)
            except Exception as e:
                st.error(f"❌ Failed to load image {blob.name}: {e}")

# Sidebar filters
with st.sidebar:
    st.header("🔍 Filters")
    with st.spinner("Fetching image data..."):
        try:
            all_blobs = list_all_blobs()
            hierarchy = extract_hierarchy(all_blobs)
        except Exception as e:
            st.error(f"❌ Failed to load GCS data: {e}")
            st.stop()

    batch = st.selectbox("Select Batch", sorted(hierarchy.keys())) if hierarchy else None
    agent = st.selectbox("Select Agent", sorted(hierarchy[batch].keys())) if batch else None
    client = st.selectbox("Select Client", sorted(hierarchy[batch][agent].keys())) if batch and agent else None

# Main display
if client:
    st.subheader(f"📁 Viewing: {batch} / {agent} / {client}")
    display_images(hierarchy[batch][agent][client])
elif agent:
    st.subheader(f"📁 Viewing all images for agent: {agent} in batch: {batch}")
    blobs = [b for c in hierarchy[batch][agent].values() for b in c]
    display_images(blobs)
elif batch:
    st.subheader(f"📁 Viewing all images for batch: {batch}")
    blobs = [b for a in hierarchy[batch].values() for c in a.values() for b in c]
    display_images(blobs)
else:
    st.info("👈 Please select a batch from the sidebar to begin.")
