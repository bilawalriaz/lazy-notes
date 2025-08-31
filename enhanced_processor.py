#!/usr/bin/env python3
"""
Enhanced processor that integrates with fine-tuned LLM via LM Studio
and creates aesthetic HTML cards for processed transcripts.
Supports both Whisper and Parakeet MLX transcription models.
"""

import os
import time
import sqlite3
import json
import requests
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
from new_html_card import create_html_card

load_dotenv()

# --- Configuration ---
# Try to load from config.py if it exists, otherwise use defaults
try:
    from config import *
    print("📁 Using configuration from config.py")
except ImportError:
    print("📁 Using default configuration (create config.py to customize)")
    # Default configuration
    INPUT_DIR = "notes/input"
    PROCESSED_DIR = "notes/processed"
    DB_FILE = "notes.db"
    
    # --- Transcription Model Configuration ---
    TRANSCRIPTION_MODEL = "whisper"  # Change to "parakeet" to use Parakeet MLX
    
    # Whisper Configuration
    WHISPER_MODEL = "turbo"
    WHISPER_CPU_THREADS = int(os.environ.get("WHISPER_CPU_THREADS", 8))
    WHISPER_DEVICE = "cpu"
    WHISPER_COMPUTE_TYPE = "int8"
    
    # Parakeet MLX Configuration
    PARAKEET_MODEL = "mlx-community/parakeet-tdt-0.6b-v3"
    PARAKEET_ATTENTION_MODEL = "rel_pos_local_attn"
    PARAKEET_ATTENTION_PARAMS = (256, 256)
    
    # --- LM Studio Configuration for Fine-tuned Model ---
    LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"
    LM_STUDIO_TEMPERATURE = 0.2
    LM_STUDIO_MAX_TOKENS = 16384

# --- Model Initialization ---
print(f"Initializing {TRANSCRIPTION_MODEL.upper()} model...")

if TRANSCRIPTION_MODEL == "whisper":
    from faster_whisper import WhisperModel
    # Use configuration variables for Whisper
    transcription_model = WhisperModel(
        WHISPER_MODEL, 
        device=WHISPER_DEVICE, 
        compute_type=WHISPER_COMPUTE_TYPE, 
        cpu_threads=WHISPER_CPU_THREADS
    )
    print(f"Whisper model initialized: {WHISPER_MODEL} on {WHISPER_DEVICE}")
elif TRANSCRIPTION_MODEL == "parakeet":
    from parakeet_mlx import from_pretrained
    transcription_model = from_pretrained(PARAKEET_MODEL)
    transcription_model.encoder.set_attention_model(
        PARAKEET_ATTENTION_MODEL,
        PARAKEET_ATTENTION_PARAMS,
    )
    print(f"Parakeet MLX model initialized: {PARAKEET_MODEL}")
else:
    raise ValueError(f"Invalid TRANSCRIPTION_MODEL: {TRANSCRIPTION_MODEL}. Choose 'whisper' or 'parakeet'")

# --- Database Setup ---
def migrate_database():
    """Add new columns to existing database if they don't exist"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Get existing columns
    c.execute("PRAGMA table_info(notes)")
    existing_columns = [column[1] for column in c.fetchall()]
    
    # Add new columns if they don't exist
    new_columns = [
        ("html_card_path", "TEXT"),
        ("summary_short", "TEXT"),
        ("structured_data", "TEXT")
    ]
    
    for column_name, column_type in new_columns:
        if column_name not in existing_columns:
            try:
                c.execute(f"ALTER TABLE notes ADD COLUMN {column_name} {column_type}")
                print(f"✅ Added database column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"⚠️  Could not add column {column_name}: {e}")
    
    conn.commit()
    conn.close()

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
            html_card_path TEXT,
            tags TEXT,
            category TEXT,
            summary_short TEXT,
            location TEXT,
            recorded_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transcription_time REAL,
            llm_processing_time REAL,
            structured_data TEXT
        )
    ''')
    conn.commit()
    conn.close()
    
    # Run migration to add any missing columns to existing database
    migrate_database()

def count_tokens_estimate(text):
    """Rough estimation: ~4 characters per token for English text"""
    return len(text) / 4

# --- Transcription ---
def transcribe_audio(file_path):
    print(f"Transcribing {file_path} using {TRANSCRIPTION_MODEL.upper()}...")
    start_time = time.time()
    output_filename = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join(PROCESSED_DIR, output_filename)
    os.makedirs(output_path, exist_ok=True)
    
    transcript_json_path = os.path.join(output_path, "transcript.json")
    
    try:
        if TRANSCRIPTION_MODEL == "whisper":
            # Whisper requires ffmpeg preprocessing
            temp_wav_path = os.path.join(tempfile.gettempdir(), f"{os.path.basename(file_path)}.wav")
            
            # Convert audio to a standardized WAV format that Whisper prefers
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
                print(f"Error during ffmpeg conversion for {file_path}.")
                print(f"ffmpeg stderr: {result.stderr}")
                return None, 0

            # Transcribe the converted WAV file with Whisper
            segments, info = transcription_model.transcribe(temp_wav_path, beam_size=5)
            
            print(f"Detected language '{info.language}' with probability {info.language_probability}")
            
            # The transcription is a generator, consume it to get the text
            full_text = "".join(segment.text for segment in segments)
            
            # Clean up the temporary WAV file
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
                
        elif TRANSCRIPTION_MODEL == "parakeet":
            # Parakeet MLX can handle the file directly
            result = transcription_model.transcribe(file_path)
            full_text = result.text
            print(f"Parakeet MLX transcription completed")
        
        transcript_data = {"text": full_text}
        
        with open(transcript_json_path, 'w') as f:
            json.dump(transcript_data, f, indent=4)
            
        print(f"Transcription successful. Output saved to {transcript_json_path}")
        end_time = time.time()
        transcription_time = end_time - start_time
        return transcript_json_path, transcription_time
        
    except FileNotFoundError as e:
        if "ffmpeg" in str(e) and TRANSCRIPTION_MODEL == "whisper":
            print("Error: `ffmpeg` command not found.")
            print("Please install ffmpeg on your system to proceed. On macOS: brew install ffmpeg")
        else:
            print(f"File not found error: {e}")
        return None, 0
    except Exception as e:
        print(f"An unexpected error occurred during transcription: {e}")
        return None, 0

# --- LLM Processing with Fine-tuned Model ---
def process_with_fine_tuned_llm(transcript_path):
    """Process transcript with fine-tuned model via LM Studio"""
    print(f"Processing transcript with fine-tuned LLM: {transcript_path}")
    start_time = time.time()
    
    with open(transcript_path, 'r') as f:
        transcript_data = json.load(f)
    
    raw_text = transcript_data.get("text", "")
    
    # Format for your fine-tuned model
    user_content = f"<RAW>{raw_text}</RAW>"
    
    try:
        # Make API call to LM Studio
        response = requests.post(
            LM_STUDIO_API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "model": "local-model",  # LM Studio placeholder
                "messages": [
                    {"role": "user", "content": user_content}
                ],
                "temperature": LM_STUDIO_TEMPERATURE,
                "max_tokens": LM_STUDIO_MAX_TOKENS,
                "stream": False  # Get complete response for JSON parsing
            }
        )
        
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        # Parse the JSON response from your fine-tuned model
        try:
            # The model should return JSON directly
            structured_data = json.loads(content)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            return {
                "success": True,
                "structured_data": structured_data,
                "processing_time": processing_time,
                "input_chars": len(raw_text),
                "output_chars": len(content),
                "input_tokens_est": count_tokens_estimate(raw_text),
                "output_tokens_est": count_tokens_estimate(content)
            }
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from LLM response: {e}")
            print(f"Raw response: {content}")
            return {"success": False, "error": f"JSON parsing error: {e}"}
            
    except requests.exceptions.RequestException as e:
        print(f"Error calling LM Studio API: {e}")
        return {"success": False, "error": f"API error: {e}"}
    except Exception as e:
        print(f"Unexpected error in LLM processing: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}



def sanitize_filename(filename):
    """Sanitizes a string to be used as a filename."""
    filename = filename.replace(' ', '_')
    filename = re.sub(r'[^\w\\-_]', '', filename)
    return filename[:50]

# --- Enhanced File Handling ---
class EnhancedAudioFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"New file detected: {event.src_path}")
            time.sleep(2)  # Allow file to be fully written

            # 1. Extract info from file
            location = os.path.splitext(os.path.basename(event.src_path))[0]
            recorded_at_unix = os.path.getmtime(event.src_path)
            recorded_at_dt = datetime.fromtimestamp(recorded_at_unix)
            recorded_at_iso = recorded_at_dt.isoformat()
            date_str = recorded_at_dt.strftime('%Y-%m-%d')
            
            # 2. Transcribe the audio file
            transcript_path, transcription_time = transcribe_audio(event.src_path)
            
            if transcript_path:
                # 3. Process the transcript with fine-tuned LLM
                result = process_with_fine_tuned_llm(transcript_path)
                
                if result.get("success"):
                    structured_data = result["structured_data"]
                    processing_time = result["processing_time"]
                    
                    print(f"Transcription time: {transcription_time:.2f} seconds")
                    print(f"LLM processing time: {processing_time:.2f} seconds")
                    
                    # 4. Extract data for folder naming and database
                    title = structured_data.get("title", "Untitled Note")
                    cleaned_transcript = structured_data.get("cleaned_transcript", "")
                    category = structured_data.get("category", "Uncategorized")
                    tags = structured_data.get("tags", [])
                    summary = structured_data.get("summary_short", "")
                    
                    # 5. Create proper folder structure
                    sanitized_title = sanitize_filename(title)
                    folder_name = f"{date_str}_{sanitized_title}"
                    
                    old_output_dir = os.path.dirname(transcript_path)
                    new_output_dir = os.path.join(PROCESSED_DIR, folder_name)
                    
                    if old_output_dir != new_output_dir:
                        if os.path.exists(new_output_dir):
                            i = 1
                            while os.path.exists(f"{new_output_dir}_{i}"):
                                i += 1
                            new_output_dir = f"{new_output_dir}_{i}"
                        
                        os.rename(old_output_dir, new_output_dir)
                    
                    # 6. Update paths
                    new_transcript_path = os.path.join(new_output_dir, "transcript.json")
                    processed_md_path = os.path.join(new_output_dir, "processed.md")
                    
                    # 7. Read original transcript for HTML card
                    with open(new_transcript_path, 'r') as f:
                        original_transcript_data = json.load(f)
                    original_transcript = original_transcript_data.get("text", "")
                    
                    # 8. Create HTML card
                    html_card_path = create_html_card(structured_data, original_transcript, new_output_dir)
                    
                    # 9. Save structured data as JSON
                    structured_json_path = os.path.join(new_output_dir, "structured_data.json")
                    with open(structured_json_path, 'w', encoding='utf-8') as f:
                        json.dump(structured_data, f, indent=2, ensure_ascii=False)
                    
                    # 10. Create markdown file
                    with open(processed_md_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {title}\n\n")
                        f.write(f"**Category:** {category}\n")
                        f.write(f"**Tags:** {', '.join(tags)}\n")
                        if summary:
                            f.write(f"**Summary:** {summary}\n")
                        f.write("\n---\n\n")
                        f.write("## Cleaned Transcript\n\n")
                        f.write(cleaned_transcript)
                        
                        # Add structured sections
                        key_points = structured_data.get("key_points", [])
                        if key_points:
                            f.write("\n\n## Key Points\n\n")
                            for point in key_points:
                                f.write(f"- {point}\n")
                        
                        action_items = structured_data.get("action_items", [])
                        if action_items:
                            f.write("\n\n## Action Items\n\n")
                            for item in action_items:
                                priority = item.get("priority", "")
                                due = item.get("due", "")
                                desc = item.get("description", "")
                                f.write(f"- [ ] {desc}")
                                if priority:
                                    f.write(f" (Priority: {priority})")
                                if due:
                                    f.write(f" (Due: {due})")
                                f.write("\n")
                    
                    print(f"Processed note saved to {processed_md_path}")
                    print(f"HTML card created at {html_card_path}")
                    
                    # 11. Save to database
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO notes (
                            original_audio_path, raw_transcript_path, processed_transcript_path, 
                            html_card_path, title, tags, category, summary_short, location, 
                            recorded_at, transcription_time, llm_processing_time, structured_data
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        event.src_path, new_transcript_path, processed_md_path, html_card_path,
                        title, ', '.join(tags), category, summary, location, recorded_at_iso,
                        transcription_time, processing_time, json.dumps(structured_data)
                    ))
                    conn.commit()
                    conn.close()
                    print("Note saved to database with HTML card reference.")
                    
                else:
                    print(f"❌ LLM processing failed: {result.get('error', 'Unknown error')}")
            else:
                print("❌ Transcription failed")

if __name__ == "__main__":
    init_db()
    
    print(f"Enhanced processor watching for new audio files in: {INPUT_DIR}")
    print("Features:")
    print(f"- Transcription: {TRANSCRIPTION_MODEL.upper()} model")
    print("- Fine-tuned LLM processing via LM Studio")
    print("- Aesthetic HTML cards with structured data")
    print("- Enhanced markdown with action items and key points")
    print("- Complete structured data preservation")
    print(f"- Current config: {TRANSCRIPTION_MODEL} + LM Studio fine-tuned model")
    
    event_handler = EnhancedAudioFileHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()
