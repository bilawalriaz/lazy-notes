#!/usr/bin/env python3
"""
Quick configuration helper for switching between transcription models.
"""

import os
import sys

def get_current_config():
    """Check current configuration"""
    try:
        from config import TRANSCRIPTION_MODEL
        return TRANSCRIPTION_MODEL
    except ImportError:
        return "whisper (default)"

def create_config(model_type):
    """Create config.py with specified model"""
    if model_type not in ["whisper", "parakeet"]:
        print("❌ Invalid model type. Choose 'whisper' or 'parakeet'")
        return False
    
    config_content = f'''# Enhanced Processor Configuration
# Auto-generated configuration file

# --- Transcription Model Configuration ---
TRANSCRIPTION_MODEL = "{model_type}"

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
'''
    
    with open("config.py", "w") as f:
        f.write(config_content)
    
    return True

def main():
    print("🎛️  Enhanced Processor Configuration Helper")
    print("=" * 50)
    
    current = get_current_config()
    print(f"Current model: {current}")
    print()
    
    if len(sys.argv) > 1:
        # Command line argument provided
        model_type = sys.argv[1].lower()
        if create_config(model_type):
            print(f"✅ Configuration updated to use {model_type.upper()} model")
            print(f"📝 Created/updated config.py")
            print()
            print("🔄 Restart enhanced_processor.py to use the new configuration")
        return
    
    # Interactive mode
    print("Choose transcription model:")
    print("1. Whisper (more accurate, slower)")
    print("2. Parakeet MLX (faster, Apple Silicon only)")
    print("3. Show current config")
    print("4. Exit")
    print()
    
    while True:
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            if create_config("whisper"):
                print("\n✅ Switched to WHISPER model")
                print("📝 Configuration saved to config.py")
                print("🔄 Restart enhanced_processor.py to apply changes")
            break
        elif choice == "2":
            if create_config("parakeet"):
                print("\n✅ Switched to PARAKEET MLX model")
                print("📝 Configuration saved to config.py")
                print("🔄 Restart enhanced_processor.py to apply changes")
            break
        elif choice == "3":
            print(f"\nCurrent configuration: {current}")
            if os.path.exists("config.py"):
                print("📁 Using config.py")
            else:
                print("📁 Using default configuration (no config.py found)")
            print()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main()
