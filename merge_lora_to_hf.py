#!/usr/bin/env python3
"""
Merge a LoRA adapter into a base HF model and export a standard HF model dir.

Usage:
  python full/merge_lora_to_hf.py \
    --base meta-llama/Llama-3.2-3B \
    --adapter full/full_lora_final/full_llama3.2-3b-transcript-lora \
    --out /path/to/out/merged-llama3.2-3b

Notes:
  - Requires: transformers, peft, torch. Use a Python env with these installed.
  - If your base is gated on Hugging Face, ensure HF_TOKEN is set or you are logged in.
  - Loads the base in (b)float16 on CPU, merges, and saves safetensors.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Literal

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def parse_args():
    p = argparse.ArgumentParser(description="Merge a LoRA adapter into a base model and export HF format.")
    p.add_argument("--base", required=True, help="Base HF model id or local path (e.g., meta-llama/Llama-3.2-3B)")
    p.add_argument("--adapter", required=True, help="Path to LoRA adapter directory")
    p.add_argument("--out", required=True, help="Output directory for merged model")
    p.add_argument(
        "--dtype",
        default="bfloat16",
        choices=["float16", "bfloat16"],
        help="Compute dtype to load base for merging (use bfloat16 if supported)",
    )
    return p.parse_args()


def main():
    args = parse_args()

    if os.path.exists(args.out) and os.listdir(args.out):
        print(f"[!] Output directory exists and is not empty: {args.out}", file=sys.stderr)
        sys.exit(1)

    dtype_map: dict[str, torch.dtype] = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
    }
    torch_dtype = dtype_map[args.dtype]

    print(f"-> Loading base model: {args.base}")
    base = AutoModelForCausalLM.from_pretrained(
        args.base,
        torch_dtype=torch_dtype,
        device_map="cpu",
        trust_remote_code=False,
    )
    tok = AutoTokenizer.from_pretrained(args.base, use_fast=True, trust_remote_code=False)

    # Ensure special tokens are set if missing (some Llama-3 variants omit pad token)
    if tok.pad_token is None and tok.eos_token is not None:
        tok.pad_token = tok.eos_token

    print(f"-> Loading LoRA adapter: {args.adapter}")
    lora_model = PeftModel.from_pretrained(base, args.adapter)

    print("-> Merging LoRA into base (this can take a few minutes)...")
    merged = lora_model.merge_and_unload()

    print(f"-> Saving merged model to: {args.out}")
    os.makedirs(args.out, exist_ok=True)
    merged.save_pretrained(args.out, safe_serialization=True)
    tok.save_pretrained(args.out)

    # Basic sanity output
    cfg = getattr(merged, "config", None)
    if cfg is not None:
        ctx = getattr(cfg, "max_position_embeddings", None)
        print(f"   Model size: {cfg.num_hidden_layers} layers, {cfg.hidden_size} hidden; context: {ctx}")
    print("✅ Merge complete.")


if __name__ == "__main__":
    main()
