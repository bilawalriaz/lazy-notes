
import os
import time
import subprocess
import sqlite3
import json
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Configuration ---
INPUT_DIR = "notes/input"
PROCESSED_DIR = "notes/processed"
DB_FILE = "notes.db"
WHISPER_MODEL = "medium.en"
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_audio_path TEXT,
            raw_transcript_path TEXT,
            processed_transcript_path TEXT,
            tags TEXT,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# --- Transcription ---
def transcribe_audio(file_path):
    print(f"Transcribing {file_path}...")
    output_filename = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join(PROCESSED_DIR, output_filename)
    os.makedirs(output_path, exist_ok=True)
    
    transcript_json_path = os.path.join(output_path, "transcript.json")
    
    command = [
        "whisper-mps",
        "--file-name",
        file_path,
        "--model-name",
        WHISPER_MODEL,
        
    ]
    
    try:
        subprocess.run(command, check=True)
        
        # Move and rename the output file
        default_output_path = "output.json"
        os.rename(default_output_path, transcript_json_path)
        
        print(f"Transcription successful. Output saved to {transcript_json_path}")
        return transcript_json_path
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error during transcription: {e}")
        return None

# --- LLM Interaction ---
import requests

def process_with_llm(transcript_path):
    print(f"Processing transcript with LLM: {transcript_path}")
    
    with open(transcript_path, 'r') as f:
        transcript_data = json.load(f)
    
    raw_text = transcript_data.get("text", "")

    # Prepare the prompt for the LLM
    prompt = f"""
    Here is a raw transcript from an audio note:

    ---
    {raw_text}
    ---

    Please perform the following tasks:
    1.  Clean up the transcript: Correct any obvious transcription errors, fix punctuation, and format it for readability. Fix any excessive verbal fillers (e.g., "um", "uh", "so").
    2.  Categorise the note: Choose a single, relevant category for this note (e.g., "Work", "Personal", "Ideas", "Meeting").
    3.  Tag the note: Provide a few relevant tags, separated by commas (e.g., "project-management, team-meeting, Q3-planning").

    Return your response in the following format:

    **Cleaned Transcript:**
    [Your cleaned transcript here]

    **Category:**
    [Your chosen category here]

    **Tags:**
    [Your chosen tags here]
    """

    # --- LM Studio API Call ---
    try:
        response = requests.post(
            LM_STUDIO_API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
            }
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        # Parse the response from the LLM
        cleaned_transcript = content.split("**Cleaned Transcript:**")[1].split("**Category:**")[0].strip()
        category = content.split("**Category:**")[1].split("**Tags:**")[0].strip()
        tags = content.split("**Tags:**")[1].strip()

        return cleaned_transcript, category, tags

    except requests.exceptions.RequestException as e:
        print(f"Error calling LM Studio API: {e}")
        return "Error processing transcript.", "Error", ""



# --- File Handling ---
class AudioFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"New file detected: {event.src_path}")
            
            # 1. Transcribe the audio file
            transcript_path = transcribe_audio(event.src_path)
            
            if transcript_path:
                # 2. Process the transcript with the LLM
                cleaned_transcript, category, tags = process_with_llm(transcript_path)
                
                # 3. Save the processed output
                output_filename = os.path.splitext(os.path.basename(event.src_path))[0]
                output_dir = os.path.join(PROCESSED_DIR, output_filename)
                processed_md_path = os.path.join(output_dir, "processed.md")
                
                with open(processed_md_path, 'w') as f:
                    f.write(f"# {output_filename}\n\n")
                    f.write(f"**Category:** {category}\n")
                    f.write(f"**Tags:** {tags}\n\n")
                    f.write("---\n\n")
                    f.write(f"## Cleaned Transcript\n\n")
                    f.write(cleaned_transcript)
                
                print(f"Processed note saved to {processed_md_path}")

                # 4. Save to database
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO notes (original_audio_path, raw_transcript_path, processed_transcript_path, tags, category)
                    VALUES (?, ?, ?, ?, ?)
                ''', (event.src_path, transcript_path, processed_md_path, tags, category))
                conn.commit()
                conn.close()
                print("Note saved to database.")


if __name__ == "__main__":
    init_db()
    
    print(f"Watching for new audio files in: {INPUT_DIR}")
    
    event_handler = AudioFileHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()
