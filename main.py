# main.py
import sys
import asyncio
import os
import requests
import streamlit as st
import time
import json
import sqlite3
from helper import playwright_install
from aiohttp import ClientSession
from bs4 import BeautifulSoup

# Set up the event loop
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
else:
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass

# Set up Streamlit configuration
st.set_page_config(page_title="Scrapegraph-ai demo", page_icon="🕷")

# Install playwright browsers
playwright_install()

# Check and create logs directory if it doesn't exist
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Define the database file path
db_path = os.path.join(logs_dir, "user_logs.db")

# Function to initialize the database
def init_db():
    conn = sqlite3.connect(db_path)  # Connect to the database
    c = conn.cursor()
    
    # Create logs table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    user TEXT,
                    provider TEXT,
                    url TEXT,
                    prompt TEXT,
                    duration REAL
                )''')
    conn.commit()
    conn.close()  # Close the connection

# Initialize the database
try:
    init_db()
    print("Database initialized successfully.")
except sqlite3.OperationalError as e:
    print("Operational error while initializing the database:", e)

# Function to insert a log entry
def insert_log(timestamp, user, provider, url, prompt, duration):
    try:
        conn = sqlite3.connect("logs/user_logs.db")
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO logs (timestamp, user, provider, url, prompt, duration)
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (timestamp, user, provider, url, prompt, duration))
        conn.commit()
    except Exception as e:
        st.error(f"Error inserting log: {e}")
    finally:
        conn.close()  # Close the connection


# Sidebar content
with st.sidebar:
    st.write("Official demo for [Scrapegraph-ai](https://github.com/VinciGit00/Scrapegraph-ai) library")
    st.markdown("""---""")
    st.write("# Usage Examples")
    st.write("## Prompt 1")
    st.write("- Give me all the news with their abstracts")
    st.write("## Prompt 2")
    st.write("- Create a voice summary of the webpage")
    st.write("## Prompt 3")
    st.write("- List me all the images with their visual description")
    st.write("## Prompt 4")
    st.write("- Read me the summary of the news")
    st.markdown("""---""")
    st.write("You want to suggest tips or improvements? Contact me through email to mvincig11@gmail.com")
    st.markdown("""---""")
    st.write("Follow our [Github page](https://github.com/ScrapeGraphAI)")

# Main app content
st.title("Scrapegraph-ai")
left_co, cent_co, last_co = st.columns(3)
with cent_co:
    st.image("assets/scrapegraphai_logo.png")

st.title('Scrapegraph-api')
st.write("### Refill at this page [Github page](https://scrapegraphai.com)")

# AI provider selection
ai_providers = {
    "DeepAI": "https://api.deepai.org/api/summarization",
    "MeaningCloud": "https://api.meaningcloud.com/summarization-1.0",
    "Diffbot": "https://api.diffbot.com/v3/article",
    "TextRazor": "https://api.textrazor.com",
    "Aylien": "https://api.aylien.com/api/v1/summarize"
}
selected_provider = st.selectbox('Select AI Provider', list(ai_providers.keys()))

# Session user auth
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""

if not st.session_state.authenticated:
    with st.form("auth_form"):
        st.warning("You must be authenticated to use the scraper.")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_btn = st.form_submit_button("Login")
        if submit_btn:
            if username == "admin" and password == "admin123":
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

# API key input based on selected provider
api_key = None
api_id = None

if selected_provider in ["DeepAI", "MeaningCloud", "Diffbot", "TextRazor"]:
    api_key = st.text_input(f'Enter your {selected_provider} API key:', type="password")
else:
    api_id = st.text_input('Enter your Aylien Application ID:')
    api_key = st.text_input('Enter your Aylien API key:', type="password")

# Get the URL, prompt, and optional schema from the user
url = st.text_input('Enter the URL to scrape:')
prompt = st.text_input('Enter your prompt:')
schema = st.text_input('Enter your optional schema (e.g. div,h1,img):')

# Validate required fields
def validate_input(selected_provider, url, prompt, api_key, api_id=None):
    if not url:
        return False, "Error: URL is required."
    if not prompt:
        return False, "Error: Prompt is required."
    if selected_provider == "Aylien":
        if not api_id or not api_key:
            return False, "Error: For Aylien, both the Application ID and the API key are required."
    else:
        if not api_key:
            return False, f"Error: For {selected_provider}, the API key is required."
    return True, ""

# Async scraper using aiohttp + BeautifulSoup
async def run_scraper_async(url, prompt, headers, schema=None):
    async with ClientSession() as session:
        try:
            async with session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                preview_text = soup.get_text()[:1000]

                # Basic local scraping
                result = {
                    "provider": selected_provider,
                    "prompt": prompt,
                    "title": soup.title.string if soup.title else "No title",
                    "schema_data": {},
                    "length": len(html),
                    "preview": preview_text
                }

                if schema:
                    result["schema_data"] = {
                        key.strip(): [el.get_text(strip=True) for el in soup.find_all(key.strip())]
                        for key in schema.split(',') if key.strip()
                    }

                # Send preview to selected provider API
                provider_url = ai_providers[selected_provider]

                # Request payloads differ by provider
                if selected_provider == "DeepAI":
                    api_response = requests.post(provider_url, data={"text": preview_text}, headers=headers)
                    result["api_result"] = api_response.json()
                elif selected_provider == "MeaningCloud":
                    api_response = requests.post(provider_url, data={"key": api_key, "txt": preview_text, "sentences": 5})
                    result["api_result"] = api_response.json()
                elif selected_provider == "Diffbot":
                    params = {"token": api_key, "url": url, "discussion": "false"}
                    api_response = requests.get(provider_url, params=params)
                    result["api_result"] = api_response.json()
                elif selected_provider == "TextRazor":
                    headers.update({"x-textrazor-key": api_key})
                    api_response = requests.post(provider_url, data={"text": preview_text, "extractors": "entities,topics"}, headers=headers)
                    result["api_result"] = api_response.json()
                elif selected_provider == "Aylien":
                    headers.update({"X-AYLIEN-TextAPI-Application-ID": api_id, "X-AYLIEN-TextAPI-Application-Key": api_key})
                    api_response = requests.post(provider_url, data={"text": preview_text}, headers=headers)
                    result["api_result"] = api_response.json()

                return result

        except Exception as e:
            return {"error": str(e)}

# Start scraping on button press
if st.button('Start Scraping'):
    is_valid, error_message = validate_input(selected_provider, url, prompt, api_key, api_id)
    if not is_valid:
        st.error(error_message)
    else:
        start_time = time.time()
        headers = {"Authorization": f"Bearer {api_key}"} if selected_provider not in ["TextRazor", "Aylien"] else {}

        with st.spinner("Scraping in progress. Please wait..."):
            try:
                result = asyncio.run(run_scraper_async(url, prompt, headers, schema))
                duration = time.time() - start_time

                st.success("Scraping completed successfully!")
                st.toast(f"Done in {duration:.2f} seconds", icon='✅')

                st.write("Result:")
                st.write(result)

                json_filename = "scrape_result.json"
                with open(json_filename, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                with open(json_filename, "rb") as f:
                    st.download_button("Download JSON Result", data=f, file_name=json_filename, mime="application/json")

                insert_log(
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    st.session_state.username,
                    selected_provider,
                    url,
                    prompt,
                    round(duration, 2)
                )

            except Exception as e:
                st.error(f"Unexpected error occurred: {str(e)}")

left_co2, *_, cent_co2, last_co2, last_c3 = st.columns([1] * 18)
