from llm_pretest.utils import parse_naturalness_args, get_prompt_info, get_key_name
from fastchat.model import load_model, get_conversation_template
from tqdm import tqdm
from typing import Dict
import json
import os
from utils import read_file
import torch
from llm_pretest.prompts_getter import get_prompt


BASE_ARGS = {"sample": True, "max_new_tokens": 10, "temperature": 0.3}


def parse_prediction(pred: str) -> int:

    naturalness_score = None
    found_num = False

    sentences = pred.split('\n')
    for sentence in sentences:
        if found_num:
            break
        words = sentence.split(' ')
        for word in words:
            if word.replace('.', '').isnumeric():
                naturalness_score = int(word.replace('.', ''))
                found_num = True
                break
    return naturalness_score


def retrieve_model_predictions(model, tokenizer, generation_args: Dict, prompt: str, num_predictions: int = 15):

    """
    Retrieves the model naturalness predictions.
    """

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    all_predictions = list()
    with torch.no_grad():
        for i in range(num_predictions):
            inputs_ids = tokenizer.encode(prompt, return_tensors="pt").to(device)
            output = model.generate(inputs_ids, **generation_args)
            decoded_output = tokenizer.decode(output[i, inputs_ids.shape[1]:])
            all_predictions.append(parse_prediction(decoded_output))

    return all_predictions


def main(input_path: str, output_path: str, prompt_info: str, model_names: str, num_predictions: int = 10) -> None:

    samples = read_file(input_path)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    num_devices = torch.cuda.device_count()

    model_names = model_names.split(',')
    prompts = prompt_info.split(',')

    if os.path.exists(output_path):
        done_samples = read_file(output_path)
        for sample in done_samples:
            for new_sample in samples:
                if sample['sample_id'] == new_sample['sample_id'] and 'hf_model_results' in sample:
                    new_sample['hf_model_results'] = sample['hf_model_results']
                    break

    for mod_name in model_names:

        model, tokenizer = load_model(mod_name, device, revision="main", debug=False, num_gpus=num_devices)

        for prompt in prompts:
            add_ex, prompt_name, prompt_args = get_prompt_info(prompt)
            curr_key_name = get_key_name(mod_name, prompt.replace("__", "##"), BASE_ARGS)

            for i, sample in tqdm(enumerate(samples)):

                if "hf_model_results" in sample and curr_key_name in sample["hf_model_results"]:
                    continue

                prompt = get_prompt('completion', prompt_name, prompt_args, sample["sentence"], add_ex)
                prompt = "\n".join(prompt.split("\n")[:-1])

                conv = get_conversation_template(args.model_path)
                conv.append_message(conv.roles[0], prompt)
                conv.append_message(conv.roles[1], None)
                prompt = conv.get_prompt() + "The naturalness score is: "

                scores = retrieve_model_predictions(model, tokenizer, BASE_ARGS, prompt, num_predictions)

                if "hf_model_results" not in sample:
                    sample["hf_model_results"] = dict()

                sample["hf_model_results"][curr_key_name] = scores

                with open(output_path, 'w') as f:
                    for new_sample in samples:
                        f.write(json.dumps(new_sample) + '\n')

    with open(output_path, 'w') as f:
        for new_sample in samples:
            f.write(json.dumps(new_sample) + '\n')


if __name__ == "__main__":

    args = parse_naturalness_args()
    main(**vars(args))