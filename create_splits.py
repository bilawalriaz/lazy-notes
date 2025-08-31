
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

def create_splits(input_file: Path, output_dir: Path, val_split: float = 0.1, seed: int = 42):
    """
    Splits a JSONL file into training and validation sets, maintaining the
    distribution of categories based on the 'mode' field.

    Args:
        input_file (Path): Path to the input JSONL file.
        output_dir (Path): Directory to save the train.jsonl and val.jsonl files.
        val_split (float): The proportion of the dataset to allocate to the validation set.
        seed (int): Random seed for reproducibility.
    """
    random.seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group lines by mode
    records_by_mode = defaultdict(list)
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                mode = record.get("mode")
                if mode:
                    records_by_mode[mode].append(line.strip())
            except (json.JSONDecodeError, AttributeError):
                print(f"Skipping invalid line: {line.strip()}", file=sys.stderr)
                continue

    train_file = output_dir / "train.jsonl"
    val_file = output_dir / "val.jsonl"

    with open(train_file, 'w', encoding='utf-8') as f_train, \
         open(val_file, 'w', encoding='utf-8') as f_val:

        for mode, records in records_by_mode.items():
            random.shuffle(records)
            split_idx = int(len(records) * val_split)
            
            val_records = records[:split_idx]
            train_records = records[split_idx:]

            for record in val_records:
                f_val.write(record + '\n')
            
            for record in train_records:
                f_train.write(record + '\n')

    print(f"Splitting complete.")
    print(f"Training set saved to: {train_file}")
    print(f"Validation set saved to: {val_file}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_splits.py <input_jsonl_file> <output_directory> <validation_split_ratio>")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    split_ratio = float(sys.argv[3])

    create_splits(input_path, output_path, val_split=split_ratio)
