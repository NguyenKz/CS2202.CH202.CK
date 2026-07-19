import os
import argparse
import pandas as pd
import numpy as np
from typing import Dict
from collections import defaultdict
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go

DS_MAPPER = {'mem_enc': 'Ours', 'tal': "Chow et. al.", 'SAP': "Huang et. al.", 'matt': "Rich et. al."}

MODEL_NAME_MAPPER = {"gpt_4": "gpt-4", "gpt_3.5_turbo": "gpt-3.5", "text_davinci_003": "davinci-003",
                     "stablelm_tuned_alpha_7b": "stablelm-7B", "mpt_7B_chat": "mpt-7B", "llama_7b": "llama-7B",
                     "llama_13b": "llama-13B", "llama_65b": "llama-65B", "vicuna_13b": "vicuna-13B",
                     "vicuna_7B_1.1": "vicuna-7B", "alpaca_lora_65B_HF": "alpaca-65B",
                     "tiiuae/falcon_7B_instruct": "falcon-7B", "tiiuae/falcon_40B_instruct": "falcon-40B",
                     "alpaca_13b": "alpaca-13B", "alpaca_lora_7b": "alpaca-7B"}

LLMs = ['stablelm-7B', 'mpt-7B', 'alpaca-7B', 'vicuna-7B', 'llama-7B', 'falcon-7B', 'alpaca-13B', 'vicuna-13B',
        'llama-13B', "falcon-40B", "alpaca-65B", "llama-65B", 'davinci-003', 'gpt-3.5', 'gpt-4']

LLM_HUMANS = ['stablelm-7B', 'mpt-7B', 'alpaca-7B', 'vicuna-7B', 'llama-7B', 'falcon-7B', 'alpaca-13B', 'vicuna-13B',
              'llama-13B', "falcon-40B", "alpaca-65B", "llama-65B", 'davinci-003', 'gpt-3.5', 'gpt-4', 'Human']

CASE_STUDIES = ['llama-13B', 'vicuna-13B', "falcon-40B", "alpaca-65B", "llama-65B", 'gpt-3.5',
                'gpt-4']

DATASETS = ["matt", "tal", "SAP", "mem_enc"]

RENAMED_DATASET = ["Rich et. al.", "Chow et. al.", "Huang et. al.", "Ours"]

COLORS = ['blue', 'orange', 'red', 'green', 'purple', 'brown', 'pink', 'gray']


def adv_diff_sentence(results: pd.DataFrame):

    diff_adv = defaultdict(lambda : list())
    results = results.dropna()

    results = results[results.has_examples == True]
    for model in results.model.unique():
        curr_model = results[results['model'] == model]
        curr_model = curr_model[(curr_model.prompt_name != 'global') & (curr_model.has_examples == True)]
        diff_adv[(model, True)].append(curr_model[curr_model.diff_sentence == "yes"].pearson.mean())
        diff_adv[(model, False)].append(curr_model[curr_model.diff_sentence == "no"].pearson.mean())

    average_diff = defaultdict(lambda : list())
    for key in diff_adv:
        model, diff_ex = key[0], key[1]
        average_diff['model'].append(model)
        example_str = 'diff' if diff_ex else 'same'
        average_diff['diff_ex'].append(example_str)
        average_diff['correlation'].append(np.array(diff_adv[key]).mean())

    return average_diff


def average_max_corr(results: Dict):

    all_corrs = defaultdict(lambda : list())
    for ds in results:
        curr_df = results[ds]
        curr_df = curr_df[(curr_df.prompt_name != 'global') & (curr_df.has_examples == True)]
        curr_df = curr_df.dropna()
        for model in curr_df.model.unique():
            curr_model = curr_df[curr_df['model'] == model]
            all_corrs['model'].append(model)
            all_corrs['dataset'].append(DS_MAPPER[ds])
            all_corrs['correlation'].append(curr_model.pearson.max())

    return all_corrs


def average_max_var(results: Dict):

    all_corrs = defaultdict(lambda : list())
    for ds in results:
        curr_df = results[ds]
        all_corrs['model'].append('Human')
        all_corrs['dataset'].append(DS_MAPPER[ds])
        all_corrs['std'].append(curr_df[curr_df.model == "Human"]['std'].item())
        curr_df = curr_df[(curr_df.prompt_name != 'global') & (curr_df.has_examples == True)]
        for model in curr_df.model.unique():

            curr_model = curr_df[curr_df['model'] == model]
            all_corrs['model'].append(model)
            all_corrs['dataset'].append(DS_MAPPER[ds])
            if model == "Human":
                all_corrs['std'].append(curr_model['std'].item())
            else:
                try:
                    all_corrs['std'].append(curr_model[curr_model.pearson == curr_model.pearson.max()]['std'].item())
                except:
                    all_corrs['std'].append(-1)

    return all_corrs


def average_example_add(results: Dict):

    examples_adv = defaultdict(lambda : list())
    for ds in results:
        curr_df = results[ds]
        curr_df = curr_df[(curr_df.prompt_name != 'global') | (curr_df.has_examples == False)]
        curr_df = curr_df.dropna()
        for model in curr_df.model.unique():
            curr_model = curr_df[curr_df['model'] == model]
            for has_ex in [True, False]:
                examples_adv['model'].append(model)
                examples_adv['dataset'].append(DS_MAPPER[ds])
                examples_adv['has_example'].append(has_ex)
                examples_adv['correlation'].append(curr_model[curr_model.has_examples == has_ex].pearson.max())

    return examples_adv


def num_example_adv(results: Dict):

    global_adv, spec_adv = defaultdict(lambda: list()), defaultdict(lambda: list())
    for ds in results:
        curr_df = results[ds]
        curr_df = curr_df.dropna()
        curr_df = curr_df[curr_df.has_examples == True]
        if ds == "mem_enc":
            curr_df = curr_df[curr_df['diff_sentence'] == 'yes']
        for model in curr_df.model.unique():
            curr_model = curr_df[curr_df['model'] == model]
            for prompt_name in curr_model.prompt_name.unique():
                curr_prompt = curr_model[curr_model['prompt_name'] == prompt_name]
                for num_ex in curr_prompt.num_ex.unique():
                    if prompt_name == 'global':
                        global_adv[(model, num_ex)].append(curr_prompt[curr_prompt.num_ex == num_ex].pearson.item())
                    else:
                        try:
                            spec_adv[(model, num_ex)].append(curr_prompt[curr_prompt.num_ex == num_ex].pearson.item())
                        except:
                            print('Hey')

    average_global_adv, average_spec_adv = defaultdict(lambda: list()), defaultdict(lambda: list())
    for key in global_adv:
        model, num_ex = key[0], key[1]
        average_global_adv['model'].append(model)
        average_global_adv['num_ex'].append(num_ex)
        average_global_adv['correlation'].append(np.array(global_adv[key]).mean())

    for key in spec_adv:
        model, num_ex = key[0], key[1]
        average_spec_adv['model'].append(model)
        average_spec_adv['num_ex'].append(num_ex)
        average_spec_adv['correlation'].append(np.array(spec_adv[key]).mean())

    return average_global_adv, average_spec_adv


def plot_average_var(results: Dict, output_path: str):

    average_vars = average_max_var(results)
    average_vars_df = pd.DataFrame.from_dict(average_vars)

    # Create subplots
    fig = make_subplots(rows=1, cols=4, subplot_titles=RENAMED_DATASET, shared_xaxes=True, shared_yaxes=True)

    # Iterate over each model and create a subplot
    for i, ds_name in enumerate(DATASETS):
        curr_df = average_vars_df[average_vars_df.dataset == DS_MAPPER[ds_name]]
        curr_df['model'] = pd.Categorical(curr_df['model'], categories=LLM_HUMANS, ordered=True)
        curr_df = curr_df.sort_values('model')
        color = COLORS[i]

        fig.add_trace(
            go.Bar(x=curr_df['variance'], y=curr_df['model'], name=DS_MAPPER[ds_name],
                   orientation='h', marker=dict(color=color),),
            row=1,
            col=(i % 4) + 1
        )

        for j, (correlation, model) in enumerate(zip(curr_df['variance'], curr_df['model'])):
            fig.add_annotation(
                x=max(correlation, 0) + 0.20,
                y=model,
                text=f'{correlation:.2f}',
                font=dict(color='black', size=10),
                showarrow=False,
                align='left',
                xshift=5,
                yshift=-5,
                row=1,
                col=(i%4) + 1
            )

    # Update layout
    fig.update_layout(height=600, width=1250, plot_bgcolor='white', yaxis=dict(showgrid=True), showlegend=False,)
    # Update layout

    for i in range(1, 5):
        add_str = str(i) if i != 1 else ""
        fig['layout']['xaxis' + add_str]['title'] = 'Variance'
        if i == 1:
            fig['layout']['yaxis' + add_str]['title'] = "Model name"

    fig.update_annotations(font_size=12)
    fig.update_traces(textposition='outside')
    fig.write_image(output_path)


def plot_average_corr(results: Dict, output_path: str):

    average_corrs = average_max_corr(results)
    average_corrs_df = pd.DataFrame.from_dict(average_corrs)

    # Create subplots
    fig = make_subplots(rows=1, cols=4, subplot_titles=RENAMED_DATASET, shared_xaxes=True, shared_yaxes=True)

    # Iterate over each model and create a subplot
    for i, ds_name in enumerate(DATASETS):
        curr_df = average_corrs_df[average_corrs_df.dataset == DS_MAPPER[ds_name]]
        curr_df['model'] = pd.Categorical(curr_df['model'], categories=CASE_STUDIES, ordered=True)
        curr_df = curr_df.sort_values('model')
        color = COLORS[i]

        fig.add_trace(
            go.Bar(x=curr_df['correlation'], y=curr_df['model'], name=DS_MAPPER[ds_name],
                   orientation='h', marker=dict(color=color),),
            row=1,
            col=(i % 4) + 1
        )

        for j, (correlation, model) in enumerate(zip(curr_df['correlation'], curr_df['model'])):
            if type(model) != str:
                continue
            fig.add_annotation(
                x=max(correlation, 0) + 0.09,
                y=model,
                text=f'{correlation:.2f}',
                font=dict(color='black', size=10),
                showarrow=False,
                align='left',
                xshift=5,
                yshift=-5,
                row=1,
                col=(i%4) + 1
            )

    # Update layout
    fig.update_layout(height=600, width=1250, plot_bgcolor='white', yaxis=dict(showgrid=True), showlegend=False,)
    # Update layout

    for i in range(1, 5):
        add_str = str(i) if i != 1 else ""
        fig['layout']['xaxis' + add_str]['title'] = 'correlation'
        if i == 1:
            fig['layout']['yaxis' + add_str]['title'] = "Model name"

    fig.update_annotations(font_size=12)
    fig.update_traces(textposition='outside')
    fig.write_image(output_path)


def plot_examples_adv(results: Dict, output_path: str):

    average_adv = average_example_add(results)
    df = pd.DataFrame.from_dict(average_adv)
    df = df[df['model'].isin(CASE_STUDIES)]

    # Create subplots
    fig = make_subplots(rows=1, cols=4, subplot_titles=RENAMED_DATASET, shared_xaxes=True, shared_yaxes=True)

    # Iterate over each model and create a subplot
    for i, ds_name in enumerate(DATASETS):
        curr_df = df[df.dataset == DS_MAPPER[ds_name]]
        curr_df['model'] = pd.Categorical(curr_df['model'], categories=CASE_STUDIES, ordered=True)
        curr_df = curr_df.sort_values('model')
        color = COLORS[i]

        pattern = ['1', '0'] if curr_df['has_example'].iloc[0] else ['0', '1']

        for j, pattern_val in enumerate(pattern):
            subset_data = curr_df[curr_df['has_example'] == (pattern_val == '1')]
            shp = '' if pattern_val == '1' else '/'
            fig.add_trace(
                go.Bar(x=subset_data['correlation'], y=subset_data['model'], orientation='h', marker=dict(color=color, pattern=dict(shape=shp)),)
                , row=1, col=i+1)

    # Update layout
    fig.update_layout(height=600, width=1200, plot_bgcolor='white', yaxis=dict(showgrid=True), showlegend=False)
    # Update layout

    for i in range(1, 5):
        add_str = str(i) if i != 1 else ""
        fig['layout']['xaxis' + add_str]['title'] = 'correlation'
        if i == 1:
            fig['layout']['yaxis' + add_str]['title'] = "Model name"

    fig.update_annotations(font_size=12)
    fig.write_image(output_path)


def plot_diff_adv(results: Dict, output_path: str):

    average_adv = adv_diff_sentence(results['mem_enc'])
    df = pd.DataFrame.from_dict(average_adv)

    fig = px.bar(df[df['model'].isin(CASE_STUDIES)], y='model', x='correlation', color='diff_ex',
                 barmode='group')
    fig = fig.update_yaxes(categoryorder='array', categoryarray=CASE_STUDIES)
    # Set the axis labels
    fig.update_layout(
        xaxis_title='Pearson correlation',
        yaxis_title='Model',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        plot_bgcolor='white'
    )
    # Show the plot
    fig.write_image(output_path)


def plot_num_adv(results: Dict, output_path_global: str, output_path_spec: str):

    average_global_adv, average_spec_adv = num_example_adv(results)
    global_df, spec_df = pd.DataFrame.from_dict(average_global_adv), pd.DataFrame.from_dict(average_spec_adv)

    global_df = global_df.sort_values('num_ex')
    spec_df = spec_df.sort_values('num_ex')

    # Create subplots
    fig_glob = make_subplots(rows=2, cols=4, subplot_titles=CASE_STUDIES, shared_yaxes=True)
    fig_spec = make_subplots(rows=2, cols=4, subplot_titles=CASE_STUDIES, shared_yaxes=True)

    # Iterate over each model and create a subplot
    for i, mod_name in enumerate(CASE_STUDIES):
        curr_glob, curr_spec = global_df[global_df['model'] == mod_name], spec_df[spec_df['model'] == mod_name]
        color = COLORS[i]

        fig_glob.add_trace(
            go.Bar(x=curr_glob['num_ex'], y=curr_glob['correlation'], name=mod_name, marker=dict(color=color),),
            row=(i // 4) + 1,
            col=(i % 4) + 1
        )
        fig_spec.add_trace(
            go.Bar(x=curr_spec['num_ex'], y=curr_spec['correlation'], name=mod_name, marker=dict(color=color),),
            row=(i // 4) + 1,
            col=(i % 4) + 1
        )

    # Update layout
    fig_glob.update_layout(height=600, width=1000, plot_bgcolor='white', yaxis=dict(showgrid=True), showlegend=False)
    # Update layout
    fig_spec.update_layout(height=600, width=1000, plot_bgcolor='white', yaxis=dict(showgrid=True), showlegend=False)

    for i in range(1, 9):
        add_str = str(i) if i != 1 else ""
        fig_glob['layout']['xaxis' + add_str]['title'] = '# examples'
        fig_spec['layout']['xaxis' + add_str]['title'] = '# examples'
        if (i - 1) % 4 == 0:
            fig_glob['layout']['yaxis' + add_str]['title'] = "Pearson correlation"
            fig_spec['layout']['yaxis' + add_str]['title'] = "Pearson correlation"

    fig_glob.update_annotations(font_size=12)
    fig_spec.update_annotations(font_size=12)
    fig_glob.write_image(output_path_global)
    fig_spec.write_image(output_path_spec)


def print_best_setups(results: Dict):

    for ds in results:
        curr_df = results[ds]
        curr_df_or = curr_df[np.logical_or(curr_df.has_examples == False, curr_df.prompt_name == 'global')]
        max_setup = curr_df[curr_df.pearson == curr_df_or.pearson.max()]
        print(f"DS: {ds}, global")
        print(f"correlation: {max_setup.pearson.item()}, model: {max_setup.model.item()}, "
              f"prompt: {max_setup.prompt_name.item()}, num ex: {max_setup.num_ex.item()},"
              f"has examples: {(max_setup.has_examples == True).item()}")
        curr_df_and = curr_df[np.logical_and(curr_df.has_examples == True, curr_df.prompt_name != 'global')]
        max_setup = curr_df_and[curr_df_and.pearson == curr_df_and.pearson.max()]
        print(f"DS: {ds}, spec")
        print(f"correlation: {max_setup.pearson.item()}, model: {max_setup.model.item()}, "
              f"prompt: {max_setup.prompt_name.item()}, num ex: {max_setup.num_ex.item()},"
              f"has examples: {(max_setup.has_examples == True).item()}")


def change_model_name(curr_df):

    for mod_name in MODEL_NAME_MAPPER:
        curr_df = curr_df.replace(mod_name, MODEL_NAME_MAPPER[mod_name])
    return curr_df


def main(input_dir: str, output_graphs_dir: str):

    dataset_results = os.listdir(input_dir)
    results = dict()
    for dataset in dataset_results:
        name = dataset.replace('.csv', '').replace('parsed_', '')
        df_data = pd.read_csv(os.path.join(input_dir, dataset))
        df_data = change_model_name(df_data)
        results[name] = df_data

    print_best_setups(results)
    plot_average_corr(results, os.path.join(output_graphs_dir, 'average_max_corr.pdf'))
    plot_average_var(results, os.path.join(output_graphs_dir, 'average_max_var.pdf'))
    plot_examples_adv(results, os.path.join(output_graphs_dir, 'average_example_add.pdf'))
    plot_num_adv(results, os.path.join(output_graphs_dir, 'global_num_ex.pdf'),
                 os.path.join(output_graphs_dir, 'spec_num_ex.pdf'))
    plot_diff_adv(results, os.path.join(output_graphs_dir, 'average_diff_add.pdf'))