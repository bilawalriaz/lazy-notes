# Enhanced Processor Configuration
# Auto-generated configuration file

# --- Transcription Model Configuration ---
TRANSCRIPTION_MODEL = "parakeet"

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
