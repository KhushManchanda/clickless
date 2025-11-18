input_file = "meta_Electronics.jsonl"
output_file = "meta_Electronic_sample_1000.jsonl"
num_lines = 1000

count = 0

with open(input_file, "r") as fin, open(output_file, "w") as fout:
    for line in fin:
        fout.write(line)
        count += 1
        if count >= num_lines:
            break

print(f"Done! Saved first {num_lines} lines to {output_file}")
