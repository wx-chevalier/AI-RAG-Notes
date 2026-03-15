import os
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from openai import OpenAI

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METADATA_PATH = os.path.join(PROJECT_ROOT, 'Cleaned_Knowledge_Base', 'metadata.json')

MAX_WORKERS = 3
SAVE_INTERVAL = 10

# Load env
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))
API_KEY = os.getenv('api_key')
BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = os.getenv('model_name')

if not API_KEY:
    print("Error: API Key not found.")
    exit(1)

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
full_metadata = []
lock = threading.Lock()

def load_metadata():
    if not os.path.exists(METADATA_PATH):
        print("Metadata file not found!")
        return []
    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_metadata():
    with lock:
        with open(METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(full_metadata, f, ensure_ascii=False, indent=2)
        print(f"--- Progress Saved ---")

def process_item(item):
    # Skip if already enriched
    if "summary" in item and item["summary"]:
        return None 

    md_path = item["markdown_path"]
    if not os.path.exists(md_path):
        return None

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {md_path}: {e}")
        return None

    # Truncate content to avoid exceeding context window (e.g., first 5000 chars)
    # Most summary/keywords can be derived from the first part of the document.
    truncated_content = content[:5000]

    prompt = f"""
    You are a professional technical document analyst. 
    Analyze the following technical documentation content and output a JSON object with the following fields:
    
    1. "summary": A concise summary of the document (max 2 sentences) in Chinese.
    2. "keywords": A list of 5-8 key technical terms or product names found in the doc.
    3. "questions": A list of 3-5 hypothetical user questions that this document answers (in Chinese).
    
    Document Content:
    {truncated_content}
    
    Output strictly valid JSON. Do not include markdown formatting like ```json.
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            timeout=60 # Timeout to prevent hanging
        )
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        # Update item
        item["summary"] = result_json.get("summary", "")
        item["keywords"] = result_json.get("keywords", [])
        item["questions"] = result_json.get("questions", [])
        
        print(f"Enriched: {item['filename']}")
        return True

    except Exception as e:
        print(f"Failed to enrich {item['filename']}: {e}")
        return False

def main():
    global full_metadata
    full_metadata = load_metadata()
    
    print(f"Loaded {len(full_metadata)} items. identifying pending items...")
    
    # Filter items that need processing for the queue, but keep reference to full list objects
    pending_items = [item for item in full_metadata if "summary" not in item or not item["summary"]]
    
    print(f"Found {len(pending_items)} items to enrich.")
    
    processed_count = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_item = {executor.submit(process_item, item): item for item in pending_items}
        
        for future in as_completed(future_to_item):
            success = future.result()
            if success:
                processed_count += 1
                
            if processed_count > 0 and processed_count % SAVE_INTERVAL == 0:
                save_metadata()

    # Final save
    save_metadata()
    print("Enrichment complete.")

if __name__ == "__main__":
    main()
