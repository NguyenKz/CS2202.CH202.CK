import random
from time import sleep
import openai
from llm_pretest.utils import parse_naturalness_args, get_prompt_info, get_key_name
from llm_pretest.openai.utils import MODEL_TYPE_MAPPING
from copy import deepcopy
from typing import Dict
import os
from tqdm import tqdm
from llm_pretesting.utils import read_file
import json
from llm_pretest.prompts_getter import get_prompt

completion_func = {'chat': openai.ChatCompletion.create, 'completion': openai.Completion.create}

CHAT_ARGS = {"temperature": 1.5,
             "max_tokens": 20}

COMPLETION_ARGS = {"temperature": 1.5,
                   "max_tokens": 20,
                   "top_p": 1}


def parse_prediction(pred: Dict) -> int:

    naturalness_score = None
    found_num = False

    sentences = pred.split('\n')
    for sentence in sentences:
        if found_num:
            break
        words = sentence.split(' ')
        for word in words:
            if word.replace('.', '').isnumeric():
                naturalness_score = int(word.replace('.', '')[0])
                found_num = True
                break
    return naturalness_score


def retrieve_model_predictions(completion_args: str, model_type: str, num_predictions: int = 15):

    """
    Retrieves the model naturalness predictions.
    """

    all_predictions, i = list(), 0
    completion_args['n'] = num_predictions
    try:
        response = completion_func[model_type](**completion_args)
    except:
        sleep(random.randint(100,3000) / 1000.)
        try:
            response = completion_func[model_type](**completion_args)
        except:
            sleep(random.randint(100, 3000) / 1000.)
            response = completion_func[model_type](**completion_args)

    for i in range(len(response['choices'])):
        if 'text' in response['choices'][i]:
            curr_response = response['choices'][i]['text']
        else:
            curr_response = response['choices'][i]['message']['content']

        score = parse_prediction(curr_response)
        if score is not None:
            all_predictions.append(score)

    return all_predictions


def get_base_args(model_type: str, model_name: str):

    if model_type == 'chat':
        base_args = deepcopy(CHAT_ARGS)
    else:
        base_args = deepcopy(COMPLETION_ARGS)
    base_args['model'] = model_name
    return base_args


def get_model_args(sentence: str, base_args: Dict, prompt_name: str, model_type: str, example_args: Dict,
                   add_examples: bool = True):

    prompt = get_prompt(model_type, prompt_name, example_args, sentence, add_examples)
    if model_type == 'chat':
        base_args['messages'] = prompt
    else:
        base_args['prompt'] = prompt
    return base_args


def main(input_path: str, output_path: str, prompt_info: str, model_names: str, num_predictions: int = 10,
         **kwargs) -> None:

    samples = read_file(input_path)

    model_names = model_names.split(',')
    prompts = prompt_info.split(',')

    if os.path.exists(output_path):
        done_samples = read_file(output_path)
        for sample in done_samples:
            for new_sample in samples:
                if sample['sample_id'] == new_sample['sample_id'] and 'openai_model_results' in sample:
                    new_sample['openai_model_results'] = sample['openai_model_results']
                    break

    for mod_name in model_names:
        base_args = get_base_args(MODEL_TYPE_MAPPING[mod_name], mod_name)

        for prompt in prompts:
            add_ex, prompt_name, prompt_args = get_prompt_info(prompt)
            curr_key_name = get_key_name(mod_name, prompt.replace("__", "##"), base_args)

            for i, sample in tqdm(enumerate(samples)):

                if "openai_model_results" in sample and curr_key_name in sample["openai_model_results"]:
                    continue

                model_args = get_model_args(sample["sentence"], base_args, prompt_name, MODEL_TYPE_MAPPING[mod_name],
                                            prompt_args, add_ex)
                scores = retrieve_model_predictions(model_args, MODEL_TYPE_MAPPING[mod_name], num_predictions)

                if "openai_model_results" not in sample:
                    sample["openai_model_results"] = dict()

                sample["openai_model_results"][curr_key_name] = scores

                with open(output_path, 'w') as f:
                    for new_sample in samples:
                        f.write(json.dumps(new_sample) + '\n')

    with open(output_path, 'w') as f:
        for new_sample in samples:
            f.write(json.dumps(new_sample) + '\n')


if __name__ == "__main__":

    args = parse_naturalness_args()
    main(**vars(args))