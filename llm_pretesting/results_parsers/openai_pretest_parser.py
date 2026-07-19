from collections import defaultdict
from typing import DefaultDict, Dict, List
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from itertools import product
import argparse
from llm_pretesting.utils import read_file, measure_correlation, find_distribution, find_num_human, add_elem_to_dic_list


def prompt_key_parser(prompt: str):

    prompt_elems = "_".join(prompt.split('_')[1:]).split('##')
    prompt_args = {i.split('#')[0]: i.split('#')[1] for i in prompt_elems[2:]}
    prompt_args['prompt_name'] = prompt_elems[1]
    prompt_args['has_examples'] = prompt_elems[0] == "1"
    return prompt_args


def openai_key_parser(key: str):

    model, prompt, temperature = key.split('__')
    prompt_args = prompt_key_parser(prompt)
    run_args = {i: k for i, k in prompt_args.items()}
    if "diff_sentence" not in run_args:
        run_args["diff_sentence"] = 'yes'
    run_args['model'] = model
    run_args['temperature'] = temperature.split('_')[1]
    return run_args


def first_step_parsing(samples: List):

    results = defaultdict(lambda : list())
    average_humans, variance_humans = list(), list()
    for sample in samples:
        human_mean, human_std, human_var = find_distribution(sample['human_results'])
        average_humans.append(human_mean)
        variance_humans.append(human_var)
        for setup in sample['model_results']:
            if setup == "text_davinci_003__prompt_1##mem_enc##num_ex#3__temp_1.5":
                print("")
            new_res = openai_key_parser(setup)
            model_mean, model_std, model_var = find_distribution(sample['model_results'][setup])
            num_humans = find_num_human(human_std, model_std)
            new_res['average_judgements'] = model_mean
            new_res['var_judgements'] = model_var
            new_res['num_humans'] = num_humans
            new_res['sample_id'] = sample['sample_id']
            results = add_elem_to_dic_list(results, new_res)

    return results, average_humans, variance_humans



def second_step_parsing(df_results: pd.DataFrame, keys_to_add: List, average_humans: List, variance_humans: List):

    all_possible_values = [df_results[key].unique().tolist() for key in keys_to_add]
    all_combinations = list(product(*all_possible_values))

    parsed_results = defaultdict(lambda : list())
    for comb in all_combinations:
        values = dict()
        for i, val in enumerate(comb):
            values[keys_to_add[i]] = val
        curr_df = df_results.loc[(df_results[list(values)] == pd.Series(values)).all(axis=1)]
        if curr_df.shape[0] == 0:
            continue
        correlations = measure_correlation(average_humans, curr_df['average_judgements'].replace(np.nan, 0).clip(upper=7).to_list())
        if "text_davinci_003" in comb[-1]:
            print("")
        values['spearman'] = correlations['spearman']
        values['pearson'] = correlations['pearson']
        values['num_humans_average'] = curr_df['num_humans'].mean()
        values['num_humans_std'] = curr_df['num_humans'].std()
        values['variance'] = curr_df['var_judgements'].mean()
        parsed_results = add_elem_to_dic_list(parsed_results, values)

    for key in parsed_results:
        if key == "model":
            parsed_results[key].append('Human')
        elif key == "variance":
            parsed_results[key].append(np.array(variance_humans).mean())
        else:
            parsed_results[key].append(np.nan)

    return parsed_results


def find_conds(df):

    df_4 = df[df.model == "Human"]
    if "diff_sentence" in df.columns:
        df = df[df.diff_sentence == "yes"]
    df_1 = df[df.has_examples == False]
    df_2 = df[(df.prompt_name == 'global') & (df.num_ex == "4") & (df.has_examples == True)]
    df_3 = df[(df.prompt_name != 'global') & (df.num_ex == "3") & (df.has_examples == True)]
    df_1 = df_1.append(df_2)
    df_1 = df_1.append(df_3)
    return df_1.append(df_4)


def main(input_path: str, output_path: str, keys_to_add: str):

    samples = read_file(input_path)

    results = defaultdict(lambda : list())
    human_averages = [np.array(sample['human_results']).mean() for sample in samples]
    human_vars = [np.array(sample['human_results']).std() for sample in samples]
    for key in samples[0]['openai_model_results']:
        try:
            model_averages = [np.array(sample['openai_model_results'][key]).mean() for sample in samples]
            model_vars = [np.array(sample['openai_model_results'][key]).std() for sample in samples]
        except:
            continue
        corr = pearsonr(human_averages, model_averages).statistic
        model_keys = openai_key_parser(key)
        for mod_key in model_keys:
            results[mod_key].append(model_keys[mod_key])
        results['pearson'].append(corr)
        results['std'].append(np.array(model_vars).mean())

    for key in results:
        if key == "model":
            results[key].append('Human')
        elif key == "std":
            results[key].append(np.array(human_vars).mean())
        else:
            results[key].append(np.nan)

    global_df = pd.DataFrame.from_dict(results)
    global_df = find_conds(global_df)
    global_df.to_csv(output_path)
    return 1


if __name__ == "__main__":

    parser = argparse.ArgumentParser("Openai pretest parser")
    parser.add_argument('-i', '--input_path', type=str, help="Path to where the unparsed results are")
    parser.add_argument('-o', '--output_path', type=str, help="Path to where we will keep the parsed results")
    parser.add_argument('-k', '--keys_to_add', type=str, help="Keys we want to have in the final dats")
    args = parser.parse_args()
    main(**vars(args))