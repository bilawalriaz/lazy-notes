# Enhanced Processor Configuration
# Copy this to config.py and customize as needed

# --- Transcription Model Configuration ---
# Set this to "whisper" or "parakeet"
TRANSCRIPTION_MODEL = "whisper"  # Change to "parakeet" to use Parakeet MLX

# Whisper Configuration (only used when TRANSCRIPTION_MODEL = "whisper")
WHISPER_MODEL = "turbo"  # Options: tiny, base, small, medium, large, turbo
WHISPER_CPU_THREADS = 8  # Adjust based on your CPU cores
WHISPER_DEVICE = "cpu"   # Options: cpu, cuda (for GPU)
WHISPER_COMPUTE_TYPE = "int8"  # Options: int8, float16, float32

# Parakeet MLX Configuration (only used when TRANSCRIPTION_MODEL = "parakeet")
PARAKEET_MODEL = "mlx-community/parakeet-tdt-0.6b-v3"
PARAKEET_ATTENTION_MODEL = "rel_pos_local_attn"
PARAKEET_ATTENTION_PARAMS = (256, 256)

# --- LM Studio Configuration for Fine-tuned Model ---
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"
LM_STUDIO_TEMPERATURE = 0.2
LM_STUDIO_MAX_TOKENS = 16384

# --- Directory Configuration ---
INPUT_DIR = "notes/input"
PROCESSED_DIR = "notes/processed"
DB_FILE = "notes.db"

# --- Model Comparison ---
# Whisper:
# + More accurate for complex speech
# + Better language detection
# + Wider language support
# - Requires ffmpeg preprocessing
# - Slower transcription
# - Larger memory footprint

# Parakeet MLX:
# + Much faster transcription (Apple Silicon optimized)
# + Direct audio file support (no ffmpeg needed)
# + Lower memory usage
# + Better for quick notes and dictation
# - Less accurate for complex speech
# - Primarily English focused
# - Requires Apple Silicon Mac
