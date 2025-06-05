# main.py
import sys
import asyncio
import os
import requests
import streamlit as st
from helper import playwright_install

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
    "DeepAI": "DeepAI",
    "MeaningCloud": "MeaningCloud",
    "Diffbot": "Diffbot",
    "TextRazor": "TextRazor",
    "Aylien": "Aylien"
}
selected_provider = st.selectbox('Select AI Provider', list(ai_providers.keys()))

# API key input based on selected provider
api_key = None
api_id = None

if selected_provider in ["DeepAI", "MeaningCloud", "Diffbot", "TextRazor"]:
    api_key = st.text_input(f'Enter your {selected_provider} API key:', type="password")
else:  # Aylien
    api_id = st.text_input('Enter your Aylien Application ID:')
    api_key = st.text_input('Enter your Aylien API key:', type="password")

# Get the URL, prompt, and optional schema from the user
url = st.text_input('Enter the URL to scrape:')
prompt = st.text_input('Enter your prompt:')
schema = st.text_input('Enter your optional schema (leave blank if not needed):')

# Validate required fields
def validate_input(selected_provider, url, prompt, api_key, api_id=None):
    if selected_provider == "Aylien":
        return bool(api_id) and bool(api_key), "For Aylien, both the Application ID and the API key are required."
    else:
        return bool(api_key), f"For {selected_provider}, the API key is required."

# Scraping functions for each AI provider
def scrape_with_deepai(url, prompt, schema, api_key):
    api_url = "https://api.deepai.org/api/summarization"
    headers = {'api-key': api_key, 'Content-Type': 'application/json'}
    data = {"text": f"URL: {url}, Prompt: {prompt}, Schema: {schema}"}
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get('output', "No output received.")
    except requests.exceptions.HTTPError as http_err:

        return f"HTTP error occurred: {http_err.response.status_code} - {http_err.response.text}"
    except requests.exceptions.RequestException as req_err:
        return f"Request failed: {req_err}"

def scrape_with_meaningcloud(url, prompt, schema, api_key):
    api_url = "https://api.meaningcloud.com/summarization-2.0"
    headers = {'Content-Type': 'application/json'}
    data = {
        "key": api_key,
        "url": url,
        "txt": prompt,
        "lang": "en"  # Assuming English language for the summary
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get('summary', "No summary received.")
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err.response.status_code} - {http_err.response.text}"
    except requests.exceptions.RequestException as req_err:
        return f"Request failed: {req_err}"

def scrape_with_diffbot(url, prompt, schema, api_key):
    api_url = "https://api.diffbot.com/v3/article"
    params = {
        'token': api_key,
        'url': url,
        'mode': 'product'
    }
    
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        return response.json().get('objects', [{}])[0].get('text', "No text received.")
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err.response.status_code} - {http_err.response.text}"
    except requests.exceptions.RequestException as req_err:
        return f"Request failed: {req_err}"

def scrape_with_textrazor(url, prompt, schema, api_key):
    api_url = "https://api.textrazor.com"
    headers = {'x-api-key': api_key}
    data = {
        "extractors": ["entities", "topics"],
        "text": f"URL: {url}, Prompt: {prompt}, Schema: {schema}"
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get('response', {}).get('entities', [])
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err.response.status_code} - {http_err.response.text}"
    except requests.exceptions.RequestException as req_err:
        return f"Request failed: {req_err}"

def scrape_with_aylien(url, prompt, schema, api_id, api_key):
    api_url = "https://api.aylien.com/api/v1/summarize"
    headers = {
        'X-AYLIEN-TextAPI-Application-ID': api_id,
        'X-AYLIEN-TextAPI-Application-Key': api_key
    }
    params = {
        'url': url,
        'title': prompt,
        'schema': schema
    }
    
    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('summary', "No summary received.")
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err.response.status_code} - {http_err.response.text}"
    except requests.exceptions.RequestException as req_err:
        return f"Request failed: {req_err}"

# Start scraping on button press
if st.button('Start Scraping'):
    is_valid, error_message = validate_input(selected_provider, url, prompt, api_key, api_id)
    if not is_valid:
        st.error(error_message)
    else:
        result = ""
        if selected_provider == "DeepAI":
            result = scrape_with_deepai(url, prompt, schema, api_key)
        elif selected_provider == "MeaningCloud":
            result = scrape_with_meaningcloud(url, prompt, schema, api_key)
        elif selected_provider == "Diffbot":

            result = scrape_with_diffbot(url, prompt, schema, api_key)
        elif selected_provider == "TextRazor":
            result = scrape_with_textrazor(url, prompt, schema, api_key)
        elif selected_provider == "Aylien":
            result = scrape_with_aylien(url, prompt, schema, api_id, api_key)
        
        # Displaying the result
            st.write("Result:")
            st.write(result)
        else:
            headers = {
                'accept': 'application/json',
                'APIKEY': api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'website_url': url,
                'user_prompt': prompt,
                'type': 'object'
            }

            if schema:
                payload['schema'] = schema

            try:
                response = requests.post(
                    'https://api.......',
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    st.write("Result:", data)
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"Error: {str(e)}")            
            
left_co2, *_, cent_co2, last_co2, last_c3 = st.columns([1] * 18)

