import json

def read_file(file_path: str):

    with open(file_path, 'r') as f:

        if '.jsonl' in file_path:
            samples = list()
            for line in f:
                samples.append(json.loads(line))

        else:
            samples = json.load(f)

    return samples