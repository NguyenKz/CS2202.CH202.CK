import math
from scipy.stats import ttest_ind, pearsonr
from collections import defaultdict
import os
from typing import Dict, List
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import random
import numpy as np
from utils import read_file
from sklearn.metrics import precision_score, recall_score
from sklearn.linear_model import LinearRegression

BEST_MAPPINGS = {"matts": 'gpt_4__prompt_1##steph##num_ex#3__temp_1.5', 'tals': 'gpt_4__prompt_1##tal##num_ex#3__temp_1.5',
              'SAP': 'gpt_4__prompt_0##global##num_ex#3__temp_1.5',
              "mem_enc": 'gpt_3.5_turbo__prompt_1##global##num_ex#4__temp_1.5'}

GLOBAL_MAPPINGS = {"matts": 'gpt_4__prompt_1##steph##num_ex#3__temp_1.5',
                 'tals': 'gpt_4__prompt_1##tal##num_ex#3__temp_1.5',
                 'SAP': 'gpt_4__prompt_1##sap##num_ex#3__temp_1.5',
                 "mem_enc": 'gpt_4__prompt_1##mem_enc##num_ex#3__temp_1.5'}

models_list = {'matts': ['tals', 'mem_enc', 'SAP'], 'tals': ['SAP', 'mem_enc', 'matts'],
               'SAP': ['mem_enc', 'matts', 'tals'], 'mem_enc': ['SAP', 'matts', 'tals']}

DATA_MAPPINGS = {'mem_enc': "Ours", "matts": "Rich et. al.", "tals": "Chow et. al.", "SAP": "Huang et. al."}

THRESH_UB = {"matts": {"w.o": {"x": 0.432, "y": 0.864, "value": 6.2}, "glob": {"x": 0.545, "y": 0.814, "value": 5.7}},
              "tals": {"w.o": {"x": 0.822, "y": 0.925, "value": 5.}, "glob": {"x": 0.822, "y": 0.925, "value": 4.5}},
             "SAP": {"w.o": {"x": 0.902, "y": 0.923, "value": 5.0}, "glob": {"x": 0.913, "y": 0.915, "value": 4.5}}}

THRESH_LB = {"matts": {"w.o": {"x": 0.656, "y": 0.952, "value": 3.1}, "glob": {"x": 0.656, "y": 0.905, "value": 2.8}},
              "tals": {"w.o": {"x": 0.917, "y": 0.917, "value": 3.6}, "glob": {"x": 0.876, "y": 0.914, "value": 3.4}}}


def get_relevant_samples_matt(results: List, plausible: bool = True):

    all_samples = list()
    for sample in results:
        if not plausible and '_con' in sample['sample_id']:
            all_samples.append(sample)
        elif plausible and '_con' not in sample['sample_id']:
            all_samples.append(sample)

    return all_samples


def get_relevant_samples_tal(results: List, plausible: bool = True):

    all_samples = list()
    for sample in results:
        if not plausible and '_b' in sample['sample_id']:
            all_samples.append(sample)
        elif plausible and '_a' not in sample['sample_id']:
            all_samples.append(sample)

    return all_samples


def plot_single_threshold_recall_precision(results: List, model_key: str, reg: LinearRegression, threshold: float = 5.0,
                                           upper_bound: bool = True):

    human_pred = [np.array(sample['human_results']).mean() for sample in results]
    model_pred_glob = [np.array(sample['model_results'][model_key['global']]).mean() for sample in results]
    model_pred_glob = reg['global'].predict(np.array(model_pred_glob).reshape(-1,1))

    model_pred_spec = [np.array(sample['model_results'][model_key['specific']]).mean() for sample in results]
    model_pred_spec = reg['specific'].predict(np.array(model_pred_spec).reshape(-1,1))

    model_pred_glob, model_pred_spec = np.array(model_pred_glob), np.array(model_pred_spec)
    human_pred = np.array(human_pred)

    true_labels = (human_pred >= threshold) if upper_bound else (human_pred < threshold)
    x_range = np.linspace(0, 7, 28)

    if upper_bound:
        recall_rate_spec = [recall_score(true_labels, model_pred_spec >= i) for i in x_range]
        precision_rate_spec = [precision_score(true_labels, model_pred_spec >= i) if recall_rate_spec[num] != 0 else 1 for num, i in enumerate(x_range)]
        recall_rate_glob = [recall_score(true_labels, model_pred_glob >= i) for i in x_range]
        precision_rate_glob = [precision_score(true_labels, model_pred_glob >= i) if recall_rate_glob[num] != 0 else 1 for num, i in enumerate(x_range)]
    else:
        recall_rate_spec = [recall_score(true_labels, model_pred_spec < i) for i in x_range]
        precision_rate_spec = [precision_score(true_labels, model_pred_spec < i) if recall_rate_spec[num] != 0 else 1 for num, i in enumerate(x_range)]
        recall_rate_glob = [recall_score(true_labels, model_pred_glob < i) for i in x_range]
        precision_rate_glob = [precision_score(true_labels, model_pred_glob < i) if recall_rate_glob[num] != 0 else 1 for num, i in enumerate(x_range)]

#    x_range = np.append(np.array([0]), x_range)
    rec_prec = {'diff': np.append(x_range, x_range), 'recall': recall_rate_spec + recall_rate_glob,
                'precision': precision_rate_spec + precision_rate_glob,
                'setup': (['With examples'] * len(recall_rate_spec)) + (['W/o examples'] * len(recall_rate_glob))}

    return rec_prec


def plot_all_lb_threshold(results, model_reg, output_dir: str, threshold: Dict = None):

    figures = list()
    subplot_titles = ["matts", "tals"]
    titles = [DATA_MAPPINGS[key] for key in subplot_titles]

    fig = make_subplots(rows=2, cols=1, subplot_titles=titles, vertical_spacing=0.11)

    for i,key in enumerate(subplot_titles):

        titles.append(DATA_MAPPINGS[key])
        curr_model_reg = {'global': model_reg['global'][key], 'specific': model_reg['specific'][key]}
        curr_model_key = {'global': GLOBAL_MAPPINGS[key], 'specific': BEST_MAPPINGS[key]}
        curr_threshold = threshold[key] if threshold is not None else 3.0
        curr_upper = False

        curr_results = results[key]
        if key == "matts":
            curr_results = get_relevant_samples_matt(curr_results, curr_upper)
        elif key == "tals":
            curr_results = get_relevant_samples_tal(curr_results, curr_upper)
        rec_prec = plot_single_threshold_recall_precision(curr_results, curr_model_key, curr_model_reg, curr_threshold,
                                                          curr_upper)
        fig.append_trace(go.Scatter(
            x=[x for x, y in zip(rec_prec['recall'], rec_prec['setup']) if y == "With examples"],
            y=[x for x, y in zip(rec_prec['precision'], rec_prec['setup']) if y == "With examples"],
            mode='lines',
            name="With examples",
            legendgroup="examples",
            showlegend= (i == 0),
            line = dict(color='#636EFA'),
        ), row=(i % 2)+1, col=1)

        fig.append_trace(go.Line(
            x=[x for x, y in zip(rec_prec['recall'], rec_prec['setup']) if y == "W/o examples"],
            y=[x for x, y in zip(rec_prec['precision'], rec_prec['setup']) if y == "W/o examples"],
            mode='lines',
            name="W/o examples",
            legendgroup="examples",
            showlegend=(i == 0),
            line=dict(color="#EF553B"),
        ), row=(i % 2) + 1, col=1)

        for type in THRESH_LB[subplot_titles[i]]:
            color = '#636EFA' if type != 'glob' else "#EF553B"
            ay = -20 if type == "w.o" else 20
            fig.add_annotation(
                x=THRESH_LB[subplot_titles[i]][type]['x'],
                y=THRESH_LB[subplot_titles[i]][type]['y'],
                text=f'{THRESH_LB[subplot_titles[i]][type]["value"]:.2f}',
                font=dict(color=color, size=10),
                showarrow=True,
                align='right',
                ay = ay,
                xshift=1,
                yshift=-1,
                row=(i % 3)+1,
                col=1
            )

    for i in range(1, 3):
        add_str = str(i) if i != 1 else ""
        fig['layout']['yaxis' + add_str]['title'] = dict(text='Precision', standoff=2, font=dict(size=12))
        fig['layout']['xaxis' + add_str]['title'] = dict(text='Recall', standoff=2, font=dict(size=12))

    fig.update_layout(height=650, width=400, showlegend=True,)
    fig.update_layout(legend=dict(yanchor="top", y=-0.03, xanchor="left", x=0.3))

    fig.write_image(output_dir)


def plot_all_ub_threshold(results, model_reg, output_dir: str, threshold: Dict = None,
                          is_upper_bound: Dict = None):

    figures = list()
    subplot_titles = ["matts", "tals", "SAP"]
    titles = [DATA_MAPPINGS[key] for key in subplot_titles]

    fig = make_subplots(rows=3, cols=1, subplot_titles=titles, vertical_spacing=0.07)
    for i,key in enumerate(subplot_titles):
        curr_model_reg = {'global': model_reg['global'][key], 'specific': model_reg['specific'][key]}
        curr_model_key = {'global': GLOBAL_MAPPINGS[key], 'specific': BEST_MAPPINGS[key]}
        curr_threshold = threshold[key] if threshold is not None else 5.0
        curr_upper = is_upper_bound[key] if is_upper_bound is not None else True

        curr_results = results[key]
        if key == "matts":
            curr_results = get_relevant_samples_matt(curr_results, curr_upper)
        elif key == "tals":
            curr_results = get_relevant_samples_tal(curr_results, curr_upper)
        rec_prec = plot_single_threshold_recall_precision(curr_results, curr_model_key, curr_model_reg, curr_threshold,
                                                          curr_upper)
        fig.append_trace(go.Scatter(
            x=[x for x, y in zip(rec_prec['recall'], rec_prec['setup']) if y == "With examples"],
            y=[x for x, y in zip(rec_prec['precision'], rec_prec['setup']) if y == "With examples"],
            mode='lines',
            name="With examples",
            legendgroup="examples",
            showlegend= (i == 0),
            line = dict(color='#636EFA'),
        ), row=(i % 3)+1, col=1)

        fig.append_trace(go.Line(
            x=[x for x, y in zip(rec_prec['recall'], rec_prec['setup']) if y == "W/o examples"],
            y=[x for x, y in zip(rec_prec['precision'], rec_prec['setup']) if y == "W/o examples"],
            mode='lines',
            name="W/o examples",
            legendgroup="examples",
            showlegend=(i == 0),
            line=dict(color="#EF553B"),
        ), row=(i % 3) + 1, col=1)

        for type in THRESH_UB[subplot_titles[i]]:
            color = '#636EFA' if type != 'glob' else "#EF553B"
            ay = -20 if type == "w.o" else 20
            fig.add_annotation(
                x=THRESH_UB[subplot_titles[i]][type]['x'],
                y=THRESH_UB[subplot_titles[i]][type]['y'],
                text=f'{THRESH_UB[subplot_titles[i]][type]["value"]:.2f}',
                font=dict(color=color, size=10),
                showarrow=True,
                align='right',
                ay = ay,
                xshift=1,
                yshift=-1,
                row=(i % 3)+1,
                col=1
            )

    for i in range(1, 4):
        add_str = str(i) if i != 1 else ""
        fig['layout']['yaxis' + add_str]['title'] = dict(text='Precision', standoff=2, font=dict(size=12))
        fig['layout']['xaxis' + add_str]['title'] = dict(text='Recall', standoff=2, font=dict(size=12))

    fig.update_layout(height=950, width=400, showlegend=True,)
    fig.update_layout(legend=dict(yanchor="top", y=-0.03, xanchor="left", x=0.3))

    fig.write_image(output_dir)


def plot_crosses_dots_average(results: List, model_key: str, model_reg: LinearRegression, output_dir: str):

    humans_avg = [np.array(sample['human_results']).mean() for sample in results]
    models_avg = [np.array(sample['model_results'][model_key]).mean() for sample in results]

    models_avg = model_reg.predict(np.array(models_avg).reshape(-1, 1))
    x_values = np.arange(1, len(humans_avg) + 1)

    # Create scatter trace for humans
    humans_trace = go.Scatter(
        x=x_values,
        y=humans_avg,
        mode='markers',
        name='Humans',
        marker=dict(
            symbol='circle',
            color='blue',
            size=8
        )
    )

    # Create scatter trace for models
    models_trace = go.Scatter(
        x=x_values,
        y=models_avg,
        mode='markers',
        name='Models',
        marker=dict(
            symbol='cross',
            color='red',
            size=10
        )
    )

    # Create layout
    layout = go.Layout(
        xaxis=dict(title='Couple'),
        yaxis=dict(title='Average')
    )

    # Create figure and add traces
    fig = go.Figure(data=[humans_trace, models_trace], layout=layout)

    # Show the plot
    fig.write_image(output_dir)



def get_global_reg_model(results: Dict):

    reg_models = dict()
    for key in results:
        averages = list()
        for model in models_list[key]:
            factor = (7. / 6) if key == "model" else 1.0
            for sample in results[model]:
                averages.append([np.array(sample['human_results']).mean() * factor,
                                np.array(sample['model_results'][BEST_MAPPINGS[model]]).mean()])

        Xs, ys = list(), list()
        for average in averages:
            Xs.append(average[1])
            ys.append(average[0])
        reg = LinearRegression().fit(np.array(ys).reshape(-1, 1), Xs)
        reg_models[key] = reg
    return reg_models


def get_spcific_reg_model(results: Dict):

    reg_models = dict()
    for key in results:
        averages = list()
        factor = (7. / 6) if key == "matts" else 1.0
        min_num = max(len(results) * 0.1, 50)
        random.shuffle(results[key])
        for i in range(min_num):
            averages.append([np.array(results[key][i]['human_results']).mean() * factor,
                             np.array(results[key][i]['model_results'][BEST_MAPPINGS[key]]).mean()])

        Xs, ys = list(), list()
        for average in averages:
            Xs.append(average[1])
            ys.append(average[0])
        reg = LinearRegression().fit(np.array(ys).reshape(-1, 1), Xs)
        reg_models[key] = reg
    return reg_models


def plot_single_model(results, key, model_reg):

    humans_results = np.array([np.array(sample['human_results']).mean() for sample in results])
    model_results = np.array([np.array(sample['model_results'][key]).mean() for sample in results])
    new_x, new_y = zip(*sorted(zip(humans_results, model_results)))
    global_results = defaultdict(lambda: list())
    for i in range(len(new_x)):
        global_results['human'].append(new_x[i])
        global_results['model'].append(new_y[i])

    x_range = np.linspace(0, 7, 100)
    y_range = model_reg.predict(x_range.reshape(-1, 1))
    fig = px.scatter(global_results, x='human', y='model', opacity=0.65)
    curr_name = f"Slope: {round(model_reg.coef_[0], 3)}, Intercept: {round(model_reg.intercept_, 3)}"
    fig.add_traces(go.Scatter(x=x_range, y=y_range, name=curr_name))
    return fig


def plot_all_models(results, model_reg, output_dir: str):

    figures = list()
    subplot_titles = ["matts", "tals", "SAP", "mem_enc"]
    titles = list()
    for key in subplot_titles:
        titles.append(DATA_MAPPINGS[key])
        curr_model_reg = model_reg[key] if type(model_reg) == dict else model_reg
        curr_fig = plot_single_model(results[key], BEST_MAPPINGS[key], curr_model_reg)
        figures.append(curr_fig)

    fig = make_subplots(rows=2, cols=2, subplot_titles=titles, vertical_spacing=0.12)
    for i, figure in enumerate(figures):
        for trace in range(len(figure["data"])):
            fig.append_trace(figure["data"][trace], row=(i // 2) + 1, col=(i % 2)+1)

            human_results = [np.array(sample['human_results']).mean() for sample in results[subplot_titles[i]]]
            mod_results = [np.array(sample['model_results'][BEST_MAPPINGS[subplot_titles[i]]]).mean() for sample in results[subplot_titles[i]]]
            corr = pearsonr(human_results, mod_results)
            fig.add_annotation(
                x=1.5,  # X coordinate of the annotation
                y=6.5,  # Y coordinate of the annotation
                text=f'Pearson r: {round(corr.statistic, 3)}',  # Text of the annotation
                showarrow=False,  # Hide the arrow
                font=dict(size=14, color='black'),  # Font settings
                row=(i // 2) + 1,
                col=(i % 2) + 1
            )


    for i in range(1, 5):
        add_str = str(i) if i != 1 else ""
        fig['layout']['xaxis' + add_str]['title'] = dict(text='Human prediction', standoff=2, font=dict(size=12))
        fig['layout']['yaxis' + add_str]['title'] = dict(text='Model prediction', standoff=2, font=dict(size=12))
        # fig['layout']['xaxis' + add_str]['gridcolor'] = "grey"
        # fig['layout']['yaxis' + add_str]['gridcolor'] = "grey"

    fig.update_layout(height=500, width=1250, showlegend=True,  )

#    fig.write_image(output_dir)


def first_pass_ttest(results: List):

    new_results = dict()
    for sample in results:
        if '_all' in sample['sample_id']:
            key = sample['sample_id'].replace('_all', '')
            new_results[key] = {'human': sample['human_results'],
                            'model': sample['model_results'][BEST_MAPPINGS['mem_enc']]}

    return new_results


def ttest_diff(model_reg, results: List):

    is_sig, diff_models, diff_human = list(), list(), list()
    first_pass = first_pass_ttest(results)

    for sample in results:
        if '_all' not in sample['sample_id']:
            ttest = ttest_ind(first_pass[sample['sample_id'].split('_')[0]]['human'], sample['human_results'])
            diff_human.append(math.fabs(np.array(first_pass[sample['sample_id'].split('_')[0]]['human']).mean() - np.array(sample['human_results']).mean()))
            m1 = model_reg.predict(np.array(first_pass[sample['sample_id'].split('_')[0]]['model']).mean().reshape(-1, 1))
            m2 = model_reg.predict(np.array(sample['model_results'][BEST_MAPPINGS["mem_enc"]]).mean().reshape(-1, 1))
            diff_model = math.fabs(m1 - m2)
            is_sig.append(ttest.pvalue >= 0.05)
            diff_models.append(diff_model)
    crosses = ['cross' if val == True else 'circle' for val in is_sig]
    is_sig = np.array(is_sig)
    diff_models = np.array(diff_models)
    return np.count_nonzero((diff_models[is_sig == True]) < 1) / len(diff_models[is_sig == True])

def main(input_path: str, output_path: str):

    dir_list = os.listdir(input_path)
    dir_list = [dir_name for dir_name in dir_list if '.jsonl' in dir_name]

    results = dict()
    for dir_name in dir_list:
        key = dir_name.replace('_data.jsonl', '')
        results[key] = read_file(os.path.join(input_path, dir_name))

    global_reg_model = get_global_reg_model(results)
    spec_reg_model = get_spcific_reg_model(results)
    plot_all_ub_threshold(results, {'global': global_reg_model,
                                   'specific': spec_reg_model}, os.path.join(output_path, 'upperbounds_rec_prec_2.pdf'))
    plot_all_lb_threshold(results, {'global': global_reg_model,
                                   'specific': spec_reg_model}, os.path.join(output_path, 'lowerbounds_rec_prec_2.pdf'))
    plot_crosses_dots_average(results['tals'], BEST_MAPPINGS['tals'], spec_reg_model['tals'],
                             os.path.join(output_path, 'average_same_couple.pdf'))
    ttest_diff(global_reg_model, results['mem_enc'])
    plot_all_models(results, spec_reg_model, os.path.join(output_path, 'model_pred_human_pred.pdf'))
    ttest_diff(global_reg_model['mem_enc'], results['mem_enc'])