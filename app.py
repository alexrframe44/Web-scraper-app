import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

st.set_page_config(page_title="Web Scraper → Google Sheets", page_icon="📊", layout="wide")
st.title("🌐 Web Scraper to Google Sheets")
st.markdown("**Scrape any website and export directly to Google Sheets**")

st.sidebar.header("🔑 Google Service Account")
cred_file = st.sidebar.file_uploader("Upload your credentials.json", type=["json"])

if cred_file is None:
    st.sidebar.warning("Upload your Google credentials.json to enable export")
else:
    st.sidebar.success("✅ Credentials loaded!")

st.subheader("Enter Website URL")
url = st.text_input("Website URL", placeholder="https://example.com")

if st.button("🚀 Scrape Website", type="primary"):
    if not url.startswith("http"):
        st.error("Enter a valid URL with http/https")
    else:
        with st.spinner("Scraping..."):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                data = {}
                data["Page Title"] = soup.title.string.strip() if soup.title else "No title"

                tables = pd.read_html(response.text)
                st.success(f"✅ Found {len(tables)} table(s)!")

                st.subheader("📊 Preview of Tables")
                for i, table in enumerate(tables):
                    st.dataframe(table.head(10), use_container_width=True)

                st.session_state['scrape_data'] = {
                    "title": data["Page Title"],
                    "tables": tables,
                    "url": url
                }
            except Exception as e:
                st.error(f"Error: {str(e)}")

if "scrape_data" in st.session_state and cred_file:
    st.subheader("📤 Export to Google Sheets")
    sheet_name = st.text_input("Google Sheet Name", value="My Scraped Data")
    if st.button("💾 Export to Google Sheets", type="primary"):
        with st.spinner("Exporting..."):
            try:
                creds = Credentials.from_service_account_info(
                    json.loads(cred_file.getvalue()),
                    scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                )
                client = gspread.authorize(creds)
                sheet = client.create(sheet_name) if sheet_name not in [s.title for s in client.list_spreadsheets()] else client.open(sheet_name)
                worksheet = sheet.sheet1
                data = st.session_state['scrape_data']
                for i, table in enumerate(data["tables"]):
                    table_list = [table.columns.astype(str).tolist()] + table.fillna("").values.tolist()
                    worksheet.update(f"A{1 + i*30}", table_list)
                st.success("🎉 Exported! Open your new Google Sheet.")
            except Exception as e:
                st.error(f"Export error: {str(e)}")
