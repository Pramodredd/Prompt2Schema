import streamlit as st
import requests
import json

FASTAPI_BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{FASTAPI_BASE_URL}/upload"

Collections = ["sales", "marketing", "finance", "hr"]

def upload_schema(json_string: str, collection_name: str):
    """Validates a JSON string and sends it to the configured endpoint."""
    with st.spinner("Uploading... Please wait."):
        try:
            payload = {
                "collection_name": collection_name,
                "schema_data": json.loads(json_string)
            }

            headers = {"Content-Type": "application/json"}
            response = requests.post(UPLOAD_ENDPOINT, json=payload, headers=headers)

            if response.status_code in (200, 201):
                st.success("🚀 Schema uploaded successfully!")
                st.json(response.json())
            else:
                st.error(f"❌ Upload failed. Status Code: {response.status_code}")
                st.text_area("Server Error Response", response.text, height=150)

        except requests.exceptions.ConnectionError:
            st.error("🔌 Connection Error: Could not connect to the endpoint.")
            st.error(f"Ensure your server is running at `{FASTAPI_BASE_URL}`.")
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON format.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# --- Streamlit UI ---
st.set_page_config(page_title="JSON Schema Uploader", layout="centered")
st.title("📤 JSON Schema Uploader")

collection_name = st.selectbox("Select collection type", Collections)

pasted_text = st.text_area(
    "Paste your JSON schema content here",
    height=300,
    placeholder='{\n  "field": "value"\n} or [\n  {..}, {..}\n]'
)

if pasted_text:
    if st.button("Validate"):
        try:
            parsed = json.loads(pasted_text)
            if isinstance(parsed, dict):
                st.success("✅ Valid single JSON object.")
            elif isinstance(parsed, list) and all(isinstance(i, dict) for i in parsed):
                st.success("✅ Valid list of JSON objects.")
            else:
                st.error("❌ Must be a JSON object or a list of JSON objects.")
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON: {e}")

    if st.button("Upload from Text", key="upload_text_button"):
        upload_schema(pasted_text, collection_name)
