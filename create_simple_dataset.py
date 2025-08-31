import json
import re
import os

def extract_transcript_from_user_prompt(prompt: str) -> str:
    match = re.search(r"<TRANSCRIPT>\n(.*?)\n</TRANSCRIPT>", prompt, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def create_simple_dataset(input_path: str, output_path: str):
    """
    Creates a simplified dataset with only input and cleaned output transcripts.

    Args:
        input_path: Path to the combined_train.jsonl file.
        output_path: Path to write the new simple dataset.
    """
    print(f"Reading from {input_path}")
    print(f"Writing to {output_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                try:
                    data = json.loads(line)
                    
                    user_prompt = data.get("user", "")
                    assistant_output = data.get("assistant", {})
                    
                    original_transcript = extract_transcript_from_user_prompt(user_prompt)
                    cleaned_transcript = assistant_output.get("cleaned_transcript", "")
                    
                    if original_transcript and cleaned_transcript:
                        simple_record = {
                            "input": original_transcript,
                            "output": cleaned_transcript
                        }
                        outfile.write(json.dumps(simple_record, ensure_ascii=False) + '\n')
                        
                except json.JSONDecodeError:
                    print(f"Skipping line due to JSON decode error: {line.strip()}")
                except Exception as e:
                    print(f"An error occurred processing line: {e}")

        print("Dataset creation complete.")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Assuming the script is run from the root of the project
    project_root = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(project_root, "dataset", "newsimpleout", "combined_train.jsonl")
    output_file = os.path.join(project_root, "dataset", "cleaned_dataset.jsonl")
    
    create_simple_dataset(input_file, output_file)
