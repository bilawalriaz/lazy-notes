import json
import argparse
import pandas as pd
import numpy as np

# Attempt to import tokenizers, but don't fail if they are not installed
# We will handle the missing dependency gracefully later.
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

try:
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

def get_tokenizer(tokenizer_name):
    """Gets a tokenizer by name, either from tiktoken or huggingface."""
    if tokenizer_name == "cl100k_base":
        if not TIKTOKEN_AVAILABLE:
            raise ImportError("tiktoken is not installed. Please run `pip install tiktoken`")
        return tiktoken.get_encoding(tokenizer_name)
    else:
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers is not installed. Please run `pip install transformers`")
        return AutoTokenizer.from_pretrained(tokenizer_name)

def analyze_line(line, tokenizer, tokenizer_name):
    """Analyzes a single line of the JSONL file."""
    try:
        data = json.loads(line)
        input_text = data.get("input", "")
        # The output is a JSON string within the "output" key
        output_field = data.get("output", "{}")
        if isinstance(output_field, str):
            try:
                output_data = json.loads(output_field)
            except json.JSONDecodeError:
                output_data = {}
        else:
            output_data = output_field

        cleaned_transcript = output_data.get("cleaned_transcript", "")

        if tokenizer_name == "cl100k_base":
            input_tokens = len(tokenizer.encode(input_text))
            output_tokens = len(tokenizer.encode(cleaned_transcript))
        else: # Hugging Face tokenizer
            input_tokens = len(tokenizer.encode(input_text, add_special_tokens=False))
            output_tokens = len(tokenizer.encode(cleaned_transcript, add_special_tokens=False))

        analysis = {
            "line_num": None, # Will be set in the main loop
            "input_chars": len(input_text),
            "input_words": len(input_text.split()),
            "input_tokens": input_tokens,
            "output_chars": len(cleaned_transcript),
            "output_words": len(cleaned_transcript.split()),
            "output_tokens": output_tokens,
        }
        analysis["total_tokens"] = analysis["input_tokens"] + analysis["output_tokens"]
        return analysis
    except (json.JSONDecodeError, AttributeError):
        return None

def print_histogram(series, title, bins=10):
    """Prints a text-based histogram for a pandas Series."""
    hist, bin_edges = np.histogram(series, bins=bins)
    max_hist = np.max(hist)
    if max_hist == 0:
        print(" (no data to display)")
        return
        
    print(f"\n--- {title} Distribution ---")
    for i in range(len(hist)):
        bin_start = int(bin_edges[i])
        bin_end = int(bin_edges[i+1])
        count = hist[i]
        bar_length = int(60 * count / max_hist) if max_hist > 0 else 0
        bar = '█' * bar_length
        print(f"{bin_start:5d} - {bin_end:5d} | {count:5d} | {bar}")


def main():
    """Main function to analyze the JSONL file."""
    parser = argparse.ArgumentParser(
        description="Analyze a JSONL file, providing statistics on tokens, words, and characters.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("file_path", help="The path to the JSONL file to analyze.")
    parser.add_argument(
        "--tokenizer",
        default="cl100k_base",
        help="The tokenizer to use for token counting.\n"
             "Can be 'cl100k_base' (for tiktoken) or a model name from Hugging Face (e.g., 'google/gemma-2b').\n"
             "Default: cl100k_base"
    )
    args = parser.parse_args()

    try:
        tokenizer = get_tokenizer(args.tokenizer)
    except ImportError as e:
        print(f"Error: {e}")
        return
    except Exception as e:
        print(f"Could not load tokenizer '{args.tokenizer}': {e}")
        return

    line_analyses = []
    total_lines = 0

    with open(args.file_path, 'r') as f:
        for i, line in enumerate(f):
            total_lines += 1
            analysis = analyze_line(line, tokenizer, args.tokenizer)
            if analysis:
                analysis["line_num"] = i + 1
                line_analyses.append(analysis)
            else:
                print(f"Warning: Could not parse line {i+1}")

    if not line_analyses:
        print("No valid JSONL lines found to analyze.")
        return

    df = pd.DataFrame(line_analyses)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_columns', 10)

    print("\n" + "="*50)
    print("      Summary Statistics")
    print("="*50)
    print(f"Total lines processed: {total_lines}")
    print(f"Valid JSONL lines:   {len(df)}")
    print(f"Tokenizer used:      {args.tokenizer}")

    print("\n" + "="*50)
    print("      Overall Statistics (per line)")
    print("="*50)
    print(df[['input_tokens', 'output_tokens', 'total_tokens', 'input_words', 'output_words', 'input_chars', 'output_chars']].describe())
    
    print_histogram(df['total_tokens'], "Total Tokens")
    print_histogram(df['input_tokens'], "Input Tokens")
    print_histogram(df['output_tokens'], "Output Tokens")

    print("\nTop 5 lines with most tokens:")
    print(df.nlargest(5, 'total_tokens').to_string(index=False))


if __name__ == "__main__":
    main()
