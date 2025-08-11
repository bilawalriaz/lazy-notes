
import os
import time
import sqlite3
import json
import requests
import re
import subprocess
import tempfile
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from faster_whisper import WhisperModel
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
INPUT_DIR = "notes/input"
PROCESSED_DIR = "notes/processed"
DB_FILE = "notes.db"
WHISPER_MODEL = "large-v3-turbo"

# --- LLM Configuration ---
# Set this to "lm_studio", "ollama", or "openrouter"
LLM_PROVIDER = "openrouter"

# LM Studio Configuration
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_TEMPERATURE = 0.2

# Ollama Configuration
OLLAMA_API_URL = "http://localhost:11434/api/chat" # default ollama API URL
OLLAMA_MODEL = "qwen3:4b"
OLLAMA_CONTEXT_WINDOW = 8000
OLLAMA_TEMPERATURE = 0.6

# OpenRouter Configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "z-ai/glm-4-32b"
OPENROUTER_TEMPERATURE = 0.2

# --- Model Initialization ---
# This is done once when the script starts.
# For CPU usage. For GPU, you can use device="cuda" and compute_type="float16"
print("Initializing Whisper model...")
model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
print("Whisper model initialized.")


# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            original_audio_path TEXT,
            raw_transcript_path TEXT,
            processed_transcript_path TEXT,
            tags TEXT,
            category TEXT,
            location TEXT,
            recorded_at TIMESTAMP,
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
    
    # Create a temporary file path for the WAV file
    temp_wav_path = os.path.join(tempfile.gettempdir(), f"{os.path.basename(file_path)}.wav")

    try:
        # Convert audio to a standardized WAV format that Whisper prefers
        # This helps avoid issues with various audio formats and codecs.
        # It requires ffmpeg to be installed on the system.
        command = [
            "ffmpeg",
            "-i", file_path,
            "-ar", "16000",      # Resample to 16kHz
            "-ac", "1",          # Convert to mono
            "-c:a", "pcm_s16le", # Use 16-bit PCM codec
            "-y",                # Overwrite output file if it exists
            temp_wav_path
        ]
        
        print("Converting audio to a compatible WAV format using ffmpeg...")
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            # If ffmpeg is not found, FileNotFoundError will be raised by subprocess.run
            # This handles other ffmpeg errors.
            print(f"Error during ffmpeg conversion for {file_path}.")
            print(f"ffmpeg stderr: {result.stderr}")
            return None

        # Transcribe the converted WAV file
        segments, info = model.transcribe(temp_wav_path, beam_size=5)
        
        print(f"Detected language '{info.language}' with probability {info.language_probability}")
        
        # The transcription is a generator, consume it to get the text
        full_text = "".join(segment.text for segment in segments)
        
        transcript_data = {"text": full_text}
        
        with open(transcript_json_path, 'w') as f:
            json.dump(transcript_data, f, indent=4)
            
        print(f"Transcription successful. Output saved to {transcript_json_path}")
        return transcript_json_path
    except FileNotFoundError:
        print("Error: `ffmpeg` command not found.")
        print("Please install ffmpeg on your system to proceed. On Debian/Ubuntu: sudo apt update && sudo apt install ffmpeg")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during transcription: {e}")
        return None
    finally:
        # Clean up the temporary WAV file
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

# --- LLM Interaction ---
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
    1.  Clean up the transcript: Correct any obvious transcription errors, fix punctuation, and format it for readability. Fix any excessive verbal fillers (e.g., "um", "uh", "so"). Otherwise, do not make any changes, don't summarise, just clean the transcript.
    2.  Suggest a concise and descriptive title for the note.
    3.  Categorise the note: Choose a single, relevant category for this note (e.g., "Work", "Personal", "Ideas", "Meeting").
    4.  Tag the note: Provide a few relevant tags, separated by commas (e.g., "project-management, team-meeting, Q3-planning").

    Return your response in the following format:

    **Title:**
    [Your suggested title here]

    **Cleaned Transcript:**
    [Your cleaned transcript here]

    **Category:**
    [Your chosen category here]

    **Tags:**
    [Your chosen tags here]
    """

    content = ""
    try:
        if LLM_PROVIDER == "lm_studio":
            print("Using LM Studio for processing...")
            response = requests.post(
                LM_STUDIO_API_URL,
                headers={"Content-Type": "application/json"},
                json={
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."}, 
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": LM_STUDIO_TEMPERATURE,
                }
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            content = data['choices'][0]['message']['content']

        elif LLM_PROVIDER == "ollama":
            print("Using Ollama for processing...")
            response = requests.post(
                OLLAMA_API_URL,
                headers={"Content-Type": "application/json"},
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": OLLAMA_TEMPERATURE,
                        "num_ctx": OLLAMA_CONTEXT_WINDOW
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            content = data['message']['content']

        elif LLM_PROVIDER == "openrouter":
            print("Using OpenRouter for processing...")
            if not OPENROUTER_API_KEY:
                raise ValueError("OPENROUTER_API_KEY environment variable not set.")
            
            response = requests.post(
                OPENROUTER_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": OPENROUTER_TEMPERATURE,
                }
            )
            response.raise_for_status()
            data = response.json()
            content = data['choices'][0]['message']['content']
        
        else:
            raise ValueError(f"Invalid LLM_PROVIDER: {LLM_PROVIDER}. Please choose 'lm_studio', 'ollama', or 'openrouter'.")

        # Parse the response from the LLM
        title = content.split("**Title:**")[1].split("**Cleaned Transcript:**")[0].strip()
        cleaned_transcript = content.split("**Cleaned Transcript:**")[1].split("**Category:**")[0].strip()
        category = content.split("**Category:**")[1].split("**Tags:**")[0].strip()
        tags = content.split("**Tags:**")[1].strip()

        return title, cleaned_transcript, category, tags

    except requests.exceptions.RequestException as e:
        print(f"Error calling {LLM_PROVIDER} API: {e}")
        return "Error generating title.", "Error processing transcript.", "Error", ""
    except (KeyError, IndexError) as e:
        print(f"Error parsing LLM response: {e}")
        print(f"LLM Raw Response: {content}")
        return "Error parsing title.", "Error parsing transcript.", "Error", ""
    except ValueError as e:
        print(e)
        return "Error generating title.", "Error processing transcript.", "Error", ""


def sanitize_filename(filename):
    """
    Sanitizes a string to be used as a filename.
    - Replaces spaces with underscores.
    - Removes characters that are not alphanumeric, underscore, or hyphen.
    - Truncates to a reasonable length.
    """
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove invalid characters
    filename = re.sub(r'[^\w\\-_]', '', filename)
    # Truncate to 50 characters
    return filename[:50]


# --- File Handling ---
class AudioFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"New file detected: {event.src_path}")

            # 1. Extract info from file
            location = os.path.splitext(os.path.basename(event.src_path))[0]
            recorded_at_unix = os.path.getmtime(event.src_path)
            recorded_at_dt = datetime.fromtimestamp(recorded_at_unix)
            recorded_at_iso = recorded_at_dt.isoformat()
            date_str = recorded_at_dt.strftime('%Y-%m-%d')
            
            # 2. Transcribe the audio file
            transcript_path = transcribe_audio(event.src_path)
            
            if transcript_path:
                # 3. Process the transcript with the LLM
                title, cleaned_transcript, category, tags = process_with_llm(transcript_path)
                
                # 4. Sanitize title and create new folder name
                sanitized_title = sanitize_filename(title)
                folder_name = f"{date_str}_{sanitized_title}"

                old_output_dir = os.path.dirname(transcript_path)
                new_output_dir = os.path.join(PROCESSED_DIR, folder_name)

                if old_output_dir != new_output_dir:
                    # Handle cases where the new directory name already exists
                    if os.path.exists(new_output_dir):
                        i = 1
                        while os.path.exists(f"{new_output_dir}_{i}"):
                            i += 1
                        new_output_dir = f"{new_output_dir}_{i}"
                    
                    os.rename(old_output_dir, new_output_dir)

                # 5. Update paths
                new_transcript_path = os.path.join(new_output_dir, "transcript.json")
                processed_md_path = os.path.join(new_output_dir, "processed.md")
                
                # 6. Save the processed output
                with open(processed_md_path, 'w') as f:
                    f.write(f"# {title}\n\n")
                    f.write(f"**Category:** {category}\n")
                    f.write(f"**Tags:** {tags}\n\n")
                    f.write("---\n\n")
                    f.write(f"## Cleaned Transcript\n\n")
                    f.write(cleaned_transcript)
                
                print(f"Processed note saved to {processed_md_path}")

                # 7. Save to database
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('''
                    INSERT INTO notes (original_audio_path, raw_transcript_path, processed_transcript_path, title, tags, category, location, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (event.src_path, new_transcript_path, processed_md_path, title, tags, category, location, recorded_at_iso))
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
