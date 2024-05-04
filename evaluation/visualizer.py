"""Streamlit visualizer for the evaluation model outputs.

Run the following command to start the visualizer:
    streamlit run evaluation/visualizer.py --server.port 8571 --server.address 0.0.0.0
NOTE: YOU SHOULD BE AT THE ROOT OF THE REPOSITORY TO RUN THIS COMMAND.

Mostly borrow from: https://github.com/xingyaoww/mint-bench/blob/main/scripts/visualizer.py
"""

import json
import random
import re
from glob import glob

import altair as alt
import pandas as pd
import streamlit as st
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

# default wide mode
st.set_page_config(layout='wide', page_title='OpenDevin SWE-Bench Output Visualizer')

st.title('OpenDevin SWE-Bench Output Visualizer')

# Select your data directory
glob_pattern = 'evaluation/outputs/**/output.jsonl'
filepaths = list(set(glob(glob_pattern, recursive=True)))
st.write(f'Matching glob pattern: `{glob_pattern}`. **{len(filepaths)}** files found.')


def parse_filepath(filepath: str):
    splited = (
        filepath.removeprefix('evaluation/outputs/')
        .removesuffix('output.jsonl')
        .strip('/')
        .split('/')
    )
    try:
        benchmark = splited[0]
        agent_name = splited[1]
        # gpt-4-turbo-2024-04-09_maxiter_50
        # use regex to match the model name & maxiter
        matched = re.match(r'(.+)_maxiter_(\d+)', splited[2])
        model_name = matched.group(1)
        maxiter = matched.group(2)
        assert len(splited) == 3
        return {
            'benchmark': benchmark,
            'agent_name': agent_name,
            'model_name': model_name,
            'maxiter': maxiter,
            'filepath': filepath,
        }
    except Exception as e:
        st.write([filepath, e, splited])


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox('Add filters')

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect('Filter dataframe on', df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f'Values for {column}',
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f'Values for {column}',
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f'Values for {column}',
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f'Substring or regex in {column}',
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df


def dataframe_with_selections(
    df,
    selected_values=None,
    selected_col='filepath',
):
    # https://docs.streamlit.io/knowledge-base/using-streamlit/how-to-get-row-selections
    df_with_selections = df.copy()
    df_with_selections.insert(0, 'Select', False)

    # Set the initial state of "Select" column based on query parameters
    if selected_values:
        df_with_selections.loc[
            df_with_selections[selected_col].isin(selected_values), 'Select'
        ] = True

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={'Select': st.column_config.CheckboxColumn(required=True)},
        disabled=df.columns,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)


filepaths = pd.DataFrame(list(map(parse_filepath, filepaths)))

# ===== Select a file to visualize =====

filepaths = filepaths.sort_values(
    [
        'benchmark',
        'agent_name',
        'model_name',
        'maxiter',
    ]
)

st.markdown('**Select file(s) to visualize**')
filepaths = filter_dataframe(filepaths)
# Make these two buttons are on the same row
# col1, col2 = st.columns(2)
col1, col2 = st.columns([0.15, 1])
select_all = col1.button('Select all')
deselect_all = col2.button('Deselect all')
selected_values = st.query_params.get('filepaths', '').split(',')
selected_values = filepaths['filepath'].tolist() if select_all else selected_values
selected_values = [] if deselect_all else selected_values

selection = dataframe_with_selections(
    filepaths,
    selected_values=selected_values,
    selected_col='filepath',
)
# st.write("Your selection:")
# st.write(selection)
select_filepaths = selection['filepath'].tolist()
# update query params
st.query_params['filepaths'] = select_filepaths

data = []
for filepath in select_filepaths:
    with open(filepath, 'r') as f:
        for line in f.readlines():
            data.append(json.loads(line))
df = pd.DataFrame(data)
st.write(f'{len(data)} rows found.')

# ===== Task-level dashboard =====


def agg_stats(data):
    stats = []
    for idx, entry in enumerate(data):
        history = entry['history']
        test_result = entry['test_result']['result']

        # additional metrircs:
        empty_generation = bool(entry['git_patch'].strip() == '')
        test_cmd_exit_error = bool(
            not entry['test_result']['metadata']['4_run_test_command_success']
        )

        # resolved: if the test is successful and the agent has generated a non-empty patch
        test_result['resolved_script'] = bool(test_result['resolved'])  # most loose
        test_result['resolved'] = (
            test_result['resolved_script'] and not empty_generation
        )
        test_result['resolved_strict'] = (
            test_result['resolved_script']
            and not empty_generation
            and not test_cmd_exit_error
        )
        # avg,std obs length
        obs_lengths = []
        for _, (_, obs) in enumerate(history):
            if 'content' in obs:
                obs_lengths.append(len(obs['content']))
        obs_lengths = pd.Series(obs_lengths)

        d = {
            'idx': idx,
            'instance_id': entry['instance_id'],
            'agent_class': entry['metadata']['agent_class'],
            'model_name': entry['metadata']['model_name'],
            'n_turns': len(history),
            **test_result,
            'empty_generation': empty_generation,
            'test_cmd_exit_error': test_cmd_exit_error,
            'obs_len_avg': obs_lengths.mean().round(0),
            'obs_len_std': obs_lengths.std().round(0),
            'obs_len_max': obs_lengths.max().round(0),
        }
        if 'swe_instance' in entry:
            d.update(
                {
                    'repo': entry['swe_instance']['repo'],
                }
            )
        stats.append(d)
    return pd.DataFrame(stats)


st.markdown('---')
st.markdown('## Aggregated Stats')
stats_df = agg_stats(data)
if len(stats_df) == 0:
    st.write('No data to visualize.')
    st.stop()

resolved_rate = stats_df['resolved'].sum() / len(stats_df)
resolved_strict_rate = stats_df['resolved_strict'].sum() / len(stats_df)
resolved_script_rate = stats_df['resolved_script'].sum() / len(stats_df)

# visualize these number in a table
agg_stat = pd.DataFrame(
    {
        'Resolved Rate': {
            'Rate': resolved_rate,
            'Count': stats_df['resolved'].sum(),
            'Total': len(data),
        },
        'Strict Resolved Rate': {
            'Rate': resolved_strict_rate,
            'Count': stats_df['resolved_strict'].sum(),
            'Total': len(data),
        },
        'Script Resolved Rate': {
            'Rate': resolved_script_rate,
            'Count': stats_df['resolved_script'].sum(),
            'Total': len(data),
        },
    },
).T
st.dataframe(
    agg_stat.style.format('{:.2%}', subset=['Rate'])
    .format('{:.0f}', subset=['Count', 'Total'])
    .set_caption('Resolved Rate (by different metrics)'),
    width=400,
)
st.markdown(
    f'### Explanation of different resolved rate metrics:\n'
    f'- **Resolved Rate**: **{resolved_rate:2%}** : {stats_df["resolved"].sum()} / {len(data)}\n'
    f'- **Strict Resolved Rate** (*most strict*, any error in test command exit will be considered as unresolved): **{resolved_strict_rate:2%}** : {stats_df["resolved_strict"].sum()} / {len(data)}\n'
    f'- **Script Resolved Rate** (*most loose*, solely based on log parsing script from SWE-Bench): **{resolved_script_rate:2%}** : {stats_df["resolved_script"].sum()} / {len(data)}\n'
)


def plot_stats(stats_df, data):
    st.write('### Distribution of Number of Turns (by Resolved)')
    _stat = stats_df.groupby('resolved')['n_turns'].describe()
    # append a row for the whole dataset
    _stat.loc['all'] = stats_df['n_turns'].describe()
    st.dataframe(_stat, use_container_width=True)
    chart = (
        alt.Chart(stats_df, title='Distribution of Number of Turns by Resolved')
        .mark_bar()
        .encode(
            x=alt.X(
                'n_turns', type='quantitative', title='Number of Turns', bin={'step': 1}
            ),
            y=alt.Y('count()', type='quantitative', title='Count'),
            color=alt.Color('resolved', type='nominal', title='Resolved'),
        )
        .properties(width=400)
    )
    st.altair_chart(chart, use_container_width=True)

    if 'repo' in stats_df.columns:
        st.markdown('### Count of Resolved by Repo')
        col1, col2 = st.columns([0.2, 0.8])
        with col1:
            resolved_by_repo = stats_df.groupby('repo')['resolved'].sum()
            total_by_repo = stats_df.groupby('repo')['resolved'].count()
            resolved_rate_by_repo = resolved_by_repo / total_by_repo
            resolved_by_repo_df = pd.DataFrame(
                {
                    'Resolved': resolved_by_repo,
                    'Total': total_by_repo,
                    'Resolved Rate': resolved_rate_by_repo,
                }
            ).sort_values('Resolved Rate', ascending=False)
            st.dataframe(
                resolved_by_repo_df.style.format('{:.2%}', subset=['Resolved Rate'])
                .format('{:.0f}', subset=['Resolved', 'Total'])
                .set_caption('Count of Resolved by Repo'),
                height=400,
            )
        with col2:
            chart = (
                alt.Chart(
                    resolved_by_repo_df.reset_index(), title='Count of Resolved by Repo'
                )
                .mark_bar()
                .encode(
                    x=alt.X(
                        'Resolved Rate',
                        type='quantitative',
                        title='Resolved Rate',
                        axis=alt.Axis(format='%'),
                        scale=alt.Scale(domain=(0, 1)),
                    ),
                    y=alt.Y('repo', type='nominal', title='Repo', sort='-x'),
                    color=alt.Color(
                        'Resolved Rate', type='quantitative', title='Resolved Rate'
                    ),
                )
                .properties(height=400)
            )
            st.altair_chart(chart, use_container_width=True)

    # visualize a histogram of #char of observation content
    obs_lengths = []
    for entry in data:
        for _, (_, obs) in enumerate(entry['history']):
            if 'content' in obs:
                obs_lengths.append(len(obs['content']))
    st.write('### Distribution of #char of Observation Content')
    obs_lengths = pd.Series(obs_lengths).to_frame().rename(columns={0: 'value'})
    # st.dataframe(obs_lengths.describe())
    # add more quantile stats 75%, 90%, 95%, 99%
    quantiles = [0.7, 0.8, 0.9, 0.95, 0.97, 0.99]
    quantile_stats = obs_lengths['value'].quantile(quantiles).to_frame()
    # change name to %
    quantile_stats.index = [f'{q*100:.0f}%' for q in quantiles]
    # combine with .describe()
    quantile_stats = pd.concat([obs_lengths.describe(), quantile_stats]).sort_index()
    st.dataframe(quantile_stats.T, use_container_width=True)


with st.expander('See stats', expanded=True):
    plot_stats(stats_df, data)

# # ===== Select a row to visualize =====
st.markdown('---')
st.markdown('## Visualize a Row')
# Add a button to randomly select a row
if st.button('Randomly Select a Row'):
    row_id = random.choice(stats_df['idx'].values)
    st.query_params['row_idx'] = str(row_id)

if st.button('Clear Selection'):
    st.query_params['row_idx'] = ''

selected_row = dataframe_with_selections(
    stats_df,
    list(
        filter(
            lambda x: x is not None,
            map(
                lambda x: int(x) if x else None,
                st.query_params.get('row_idx', '').split(','),
            ),
        )
    ),
    selected_col='idx',
)
if len(selected_row) == 0:
    st.write('No row selected.')
    st.stop()
elif len(selected_row) > 1:
    st.write('More than one row selected.')
    st.stop()
row_id = selected_row['idx'].values[0]

# update query params
st.query_params['filepaths'] = select_filepaths
st.query_params['row_idx'] = str(row_id)

row_id = st.number_input(
    'Select a row to visualize', min_value=0, max_value=len(data) - 1, value=row_id
)
row = df.iloc[row_id]

# ===== Visualize the row =====
st.write(f'Visualizing row `{row_id}`')
row_dict = data[row_id]

n_turns = len(row_dict['history'])
st.write(f'Number of turns: {n_turns}')

with st.expander('Raw JSON', expanded=False):
    st.markdown('### Raw JSON')
    st.json(row_dict)


def visualize_action(action):
    if action['action'] == 'run':
        thought = action['args'].get('thought', '')
        if thought:
            st.markdown(thought)
        st.code(action['args']['command'], language='bash')
    elif action['action'] == 'run_ipython':
        thought = action['args'].get('thought', '')
        if thought:
            st.markdown(thought)
        st.code(action['args']['code'], language='python')
    elif action['action'] == 'talk':
        st.markdown(action['args']['content'])
    else:
        st.json(action)


def visualize_obs(observation):
    if 'content' in observation:
        num_char = len(observation['content'])
        st.markdown(rf'\# characters: {num_char}')
    if observation['observation'] == 'run':
        st.code(observation['content'], language='plaintext')
    elif observation['observation'] == 'run_ipython':
        st.code(observation['content'], language='python')
    elif observation['observation'] == 'message':
        st.markdown(observation['content'])
    else:
        st.json(observation)


def visualize_row(row_dict):
    st.markdown('### Test Result')
    test_result = row_dict['test_result']['result']
    st.write(pd.DataFrame([test_result]))

    st.markdown('### Interaction History')
    with st.expander('Interaction History', expanded=True):
        st.code(row_dict['instruction'], language='plaintext')
        history = row['history']
        for i, (action, observation) in enumerate(history):
            st.markdown(f'#### Turn {i + 1}')
            st.markdown('##### Action')
            visualize_action(action)
            st.markdown('##### Observation')
            visualize_obs(observation)

    st.markdown('### Agent Patch')
    with st.expander('Agent Patch', expanded=False):
        st.code(row_dict['git_patch'], language='diff')

    st.markdown('### Test Output')
    with st.expander('Test Output', expanded=False):
        st.code(row_dict['test_result']['test_output'], language='plaintext')


visualize_row(row_dict)


def visualize_swe_instance(row_dict):
    st.markdown('### SWE Instance')
    swe_instance = row_dict['swe_instance']
    st.markdown(f'Repo: `{swe_instance["repo"]}`')
    st.markdown(f'Instance ID: `{swe_instance["instance_id"]}`')
    st.markdown(f'Base Commit: `{swe_instance["base_commit"]}`')
    st.markdown('#### PASS_TO_PASS')
    st.write(pd.Series(json.loads(swe_instance['PASS_TO_PASS'])))
    st.markdown('#### FAIL_TO_PASS')
    st.write(pd.Series(json.loads(swe_instance['FAIL_TO_PASS'])))


NAV_MD = """
## Navigation
- [Home](#opendevin-swe-bench-output-visualizer)
- [Aggregated Stats](#aggregated-stats)
- [Visualize a Row](#visualize-a-row)
    - [Raw JSON](#raw-json)
    - [Test Result](#test-result)
    - [Interaction History](#interaction-history)
    - [Agent Patch](#agent-patch)
    - [Test Output](#test-output)
"""

if 'swe_instance' in row_dict:
    visualize_swe_instance(row_dict)
    NAV_MD += (
        '- [SWE Instance](#swe-instance)\n'
        '  - [PASS_TO_PASS](#pass-to-pass)\n'
        '  - [FAIL_TO_PASS](#fail-to-pass)\n'
    )

with st.sidebar:
    st.markdown(NAV_MD)
