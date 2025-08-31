# Enhanced Local Notes Processing

This enhanced version integrates your fine-tuned transcript processing LLM with aesthetic HTML card generation for a complete local audio-to-notes pipeline. **Now supports both Whisper and Parakeet MLX transcription models!**

## New Features ✨

- **Dual Transcription Models**: Switch between Whisper (accuracy) and Parakeet MLX (speed)
- **Fine-tuned LLM Integration**: Uses your custom model via LM Studio for rich structured output
- **Aesthetic HTML Cards**: Beautiful, interactive cards displaying all extracted data
- **Enhanced Database**: Stores comprehensive structured data including action items, key points, entities
- **Notes Browser**: Web interface to browse and view all your processed notes
- **Batch Processing**: Process existing transcripts with the enhanced pipeline
- **Flexible Configuration**: Easy model switching via config file

## Model Comparison 🤖

### Whisper
- ✅ More accurate for complex speech
- ✅ Better language detection  
- ✅ Wider language support
- ❌ Requires ffmpeg preprocessing
- ❌ Slower transcription
- ❌ Larger memory footprint

### Parakeet MLX  
- ✅ Much faster transcription (Apple Silicon optimized)
- ✅ Direct audio file support (no ffmpeg needed)
- ✅ Lower memory usage
- ✅ Better for quick notes and dictation
- ❌ Less accurate for complex speech
- ❌ Primarily English focused
- ❌ Requires Apple Silicon Mac

## File Structure

```
enhanced_processor.py      # Main enhanced processor (replaces main.py)
batch_process_existing.py  # Batch process existing notes
notes_browser.py          # Web browser for viewing notes
main.py                   # Original processor (still available)
```

## Quick Start

### 1. Install Dependencies
```bash
source packages/bin/activate
pip install -r requirements.txt
```

### 2. Choose Your Transcription Model
**Option A: Use default Whisper**
```bash
# No additional setup needed - uses Whisper by default
```

**Option B: Switch to Parakeet MLX (faster on Apple Silicon)**
```bash
# Copy the configuration template
cp config_template.py config.py

# Edit config.py and change:
# TRANSCRIPTION_MODEL = "parakeet"
```

### 3. Start LM Studio
- Load your fine-tuned model in LM Studio
- Ensure it's running on `http://localhost:1234`
- Your model should accept `<RAW>transcript</RAW>` format and output JSON

### 4. Process New Audio Files
```bash
python enhanced_processor.py
```
Drop audio files into `notes/input/` and get:
- Original transcript.json
- Enhanced processed.md with action items and key points
- Beautiful HTML card (note_card.html)
- Complete structured data (structured_data.json)

The processor will show which model it's using at startup:
```
📁 Using configuration from config.py
Initializing PARAKEET model...
Parakeet MLX model initialized: mlx-community/parakeet-tdt-0.6b-v3
```

### 4. Process Existing Notes
```bash
python batch_process_existing.py
```
This will enhance all your existing notes with:
- HTML cards
- Structured data extraction
- Enhanced markdown files
- Updated database records

### 5. Browse Your Notes
```bash
python notes_browser.py
```
Opens a web interface at `http://localhost:8000` to:
- Browse all your notes with filters
- Search by title, content, or tags
- View beautiful HTML cards
- Filter by category and tags

## Expected LLM Output Format

Your fine-tuned model should output JSON with this structure:

```json
{
  "title": "Note Title",
  "cleaned_transcript": "Cleaned text...",
  "category": "Work",
  "tags": ["tag1", "tag2"],
  "summary_short": "Brief summary...",
  "key_points": ["Point 1", "Point 2"],
  "action_items": [
    {
      "description": "Task description",
      "due": "2024-01-15",
      "priority": "H"
    }
  ],
  "decisions": ["Decision made"],
  "questions": ["Open question?"],
  "people": ["Person1", "Person2"],
  "entities": [
    {
      "text": "Company Name",
      "type": "ORG"
    }
  ],
  "time_extractions": [
    {
      "text": "next Tuesday",
      "normalized": "2024-01-16",
      "kind": "DATE"
    }
  ]
}
```

## HTML Card Features

The generated HTML cards include:
- 🎨 Beautiful gradient design with animations
- 📱 Responsive layout for mobile and desktop
- 🏷️ Visual tags and category indicators
- 📋 Collapsible sections for different data types
- 🎯 Color-coded action items by priority
- 👥 People and entities extraction display
- ⏰ Time references with normalization
- 📄 Original transcript toggle view

## Database Schema

Enhanced database includes:
- `html_card_path`: Path to the HTML card
- `summary_short`: Brief summary for quick preview
- `structured_data`: Complete JSON output from LLM

## Configuration

### Easy Model Switching
1. Copy the template: `cp config_template.py config.py`
2. Edit `config.py` to customize:
   - `TRANSCRIPTION_MODEL = "whisper"` or `"parakeet"`
   - Model-specific settings (size, device, etc.)
   - LM Studio endpoint and parameters

### Whisper Settings
```python
WHISPER_MODEL = "turbo"  # tiny, base, small, medium, large, turbo
WHISPER_DEVICE = "cpu"   # cpu, cuda
WHISPER_COMPUTE_TYPE = "int8"  # int8, float16, float32
WHISPER_CPU_THREADS = 8
```

### Parakeet MLX Settings
```python
PARAKEET_MODEL = "mlx-community/parakeet-tdt-0.6b-v3"
PARAKEET_ATTENTION_MODEL = "rel_pos_local_attn"
PARAKEET_ATTENTION_PARAMS = (256, 256)
```

### LM Studio Settings
```python
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_TEMPERATURE = 0.2
LM_STUDIO_MAX_TOKENS = 16384
```

## Batch Processing Options

```bash
# Process with custom LM Studio URL
python batch_process_existing.py --base_url http://localhost:1234/v1

# Process with different temperature
python batch_process_existing.py --temperature 0.1

# Process with more tokens
python batch_process_existing.py --max_tokens 32768
```

## Notes Browser Options

```bash
# Run on different port
python notes_browser.py --port 8080

# Use different directories
python notes_browser.py --processed-dir /path/to/notes --db-file /path/to/db

# Don't auto-open browser
python notes_browser.py --no-browser
```

## Choosing the Right Model 🎯

### Use Whisper When:
- You need maximum transcription accuracy
- Working with complex speech (accents, technical terms, multiple speakers)
- Processing recordings in languages other than English
- Quality is more important than speed
- You don't mind the ffmpeg dependency

### Use Parakeet MLX When:
- You have an Apple Silicon Mac (M1/M2/M3)
- Speed is critical (real-time or near real-time processing)
- Processing simple dictation or voice notes
- You want minimal dependencies (no ffmpeg required)
- Working primarily with clear English speech

### Recommended Workflow:
1. **Start with Parakeet** for quick daily notes and voice memos
2. **Switch to Whisper** for important meetings, interviews, or complex content
3. **Use the config.py** to quickly switch between models as needed

## Example Workflow

1. **Record** audio note on your phone
2. **Drop** the .m4a file into `notes/input/`
3. **Wait** for processing (transcript → LLM → HTML card)
   - Parakeet: ~5-10 seconds for a 1-minute note
   - Whisper: ~30-60 seconds for a 1-minute note
4. **Browse** your notes at `http://localhost:8000`
5. **View** the beautiful HTML card with all extracted data

## Troubleshooting

### LM Studio Connection Issues
- Ensure LM Studio is running and model is loaded
- Check the API endpoint in enhanced_processor.py
- Verify your model outputs valid JSON

### HTML Cards Not Displaying
- Run `batch_process_existing.py` to generate cards for old notes
- Check that `note_card.html` exists in note directories
- Verify database has `html_card_path` entries

### Missing Dependencies
```bash
pip install openai pathlib
```

## File Outputs

For each processed audio file, you get:
```
notes/processed/2024-01-15_Meeting_Notes/
├── transcript.json         # Original whisper output
├── processed.md           # Basic markdown (backward compatibility)
├── enhanced.md           # Enhanced markdown with action items
├── note_card.html        # Beautiful HTML card
└── structured_data.json  # Complete LLM output
```

## Quick Model Switching 🔄

Use the helper script to switch models easily:

```bash
# Interactive mode
python switch_model.py

# Command line mode
python switch_model.py whisper    # Switch to Whisper
python switch_model.py parakeet   # Switch to Parakeet MLX
```

## File Structure

```
enhanced_processor.py      # Main enhanced processor with dual model support
batch_process_existing.py  # Batch process existing notes
notes_browser.py          # Web browser for viewing notes
switch_model.py           # Quick model switching helper
config_template.py        # Configuration template
config.py                 # Your custom configuration (create this)
main.py                   # Original processor (still available)
parakeet-app.py          # Original Parakeet processor (still available)
```

---

**Enhanced processing with flexible transcription models and rich, searchable, visually appealing notes from your voice recordings!** 🎉
