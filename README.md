# Local Notes Transcribe

A powerful local audio note transcription and processing system with dual model support (Whisper and Parakeet MLX) and fine-tuned LLM integration.

## Features ✨

- **Dual Transcription Models**: Switch between Whisper (accuracy) and Parakeet MLX (speed)
- **Fine-tuned LLM Integration**: Uses your custom model via LM Studio for rich structured output
- **Aesthetic HTML Cards**: Beautiful, interactive cards displaying all extracted data
- **Enhanced Database**: Stores comprehensive structured data including action items, key points, entities
- **Notes Browser**: Web interface to browse and view all your processed notes
- **Batch Processing**: Process existing transcripts with the enhanced pipeline
- **Flexible Configuration**: Easy model switching via config file

## Installation

```bash
# Clone the repository
git clone https://github.com/bilawalriaz/local-notes-transcribe.git
cd local-notes-transcribe

# Create and activate virtual environment
python -m venv packages
source packages/bin/activate  # On Windows: packages\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

1. **Configure Your Environment**
```bash
# Copy the configuration template
cp config_template.py config.py

# Edit config.py to choose your transcription model:
# TRANSCRIPTION_MODEL = "whisper"  # More accurate, slower
# TRANSCRIPTION_MODEL = "parakeet"  # Faster, Apple Silicon only
```

2. **Start LM Studio** (if using fine-tuned model)
- Load your fine-tuned model in LM Studio
- Ensure it's running on `http://localhost:1234`

3. **Process Audio Notes**
```bash
python enhanced_processor.py
```
Drop audio files into `notes/input/` to process them automatically.

4. **Browse Your Notes**
```bash
python notes_browser.py
```
Access your notes at `http://localhost:8000`

## Model Selection

### Whisper
✅ More accurate for complex speech  
✅ Better language detection  
✅ Wider language support  
❌ Slower transcription  
❌ Larger memory footprint  

### Parakeet MLX
✅ Much faster transcription  
✅ Direct audio file support  
✅ Lower memory usage  
✅ Better for quick notes  
❌ Less accurate for complex speech  
❌ Primarily English focused  
❌ Requires Apple Silicon Mac  

## Configuration

See `config_template.py` for detailed configuration options including:
- Transcription model selection
- Model-specific settings
- LM Studio integration
- Directory paths


## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
