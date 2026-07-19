import argparse
from typing import Dict


def get_key_name(model_name: str, prompt_info: str, base_args: Dict):

    """
    Creates a unique key_name based on the model name, prompt and the temperature.
    """
    temperature = base_args['temperature'] if 'temperature' in base_args else 1
    return f'{model_name.replace("-", "_").replace("_0613", "")}__prompt_{prompt_info}__temp_{temperature}'


def get_prompt_info(prompt_info: str):

    prompt_element = prompt_info.split('__')
    add_ex = prompt_element[0] == '1'
    prompt_name = prompt_element[1]
    prompt_args = {i.split('#')[0]: i.split('#')[1] for i in prompt_element[2:]}
    return add_ex, prompt_name, prompt_args


def parse_naturalness_args():

    parser = argparse.ArgumentParser("Pretest runner")
    parser.add_argument('-i', '--input_path', type=str, help="Path to where the inputs are")
    parser.add_argument('-o', '--output_path', type=str, help="Path to where the results are kept")
    parser.add_argument('-n', '--num_predictions', type=int, default=20, help="Num of naturalness scores we want")
    parser.add_argument('-m', '--model_names', type=str, default='gpt-4', help='Name of the model we use')
    parser.add_argument('-p', '--prompt_info', type=str, default='1__global__num_ex#4', help="Num of examples per score")
    args = parser.parse_args()
    return args