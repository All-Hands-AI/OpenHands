import io
import json
import os
from typing import Iterable

import altair as alt
import click
import pandas as pd
from pydantic import BaseModel


class SWEBenchTestReport(BaseModel):
    # Report on test execution status
    empty_generation: bool
    resolved: bool
    failed_apply_patch: bool
    error_eval: bool
    test_timeout: bool


class SWEBenchTestResult(BaseModel):
    # Result of running SWEBench test
    git_patch: str
    report: SWEBenchTestReport


class SWEBenchResult(BaseModel):
    # Top-level result container
    instance_id: str
    test_result: SWEBenchTestResult


class Data(BaseModel):
    # Container for all evaluation data
    filepath: str
    metadata: dict
    output: list[dict]
    results: list[SWEBenchResult]

    @staticmethod
    def from_filepath(filepath: str) -> 'Data':
        with open(os.path.join(filepath, 'metadata.json')) as f:
            metadata = pd.read_json(io.StringIO(f.read()), typ='series').to_dict()

        with open(os.path.join(filepath, 'output.jsonl')) as f:
            output = [pd.read_json(io.StringIO(line), typ='series').to_dict() 
                     for line in f.readlines()]

        with open(os.path.join(filepath, 'output.swebench_eval.jsonl')) as f:
            results = [
                SWEBenchResult.model_validate_json(line) for line in f.readlines()
            ]

        return Data(
            filepath=filepath, metadata=metadata, output=output, results=results
        )

    def experiment(self) -> str:
        return self.filepath[:-6].split('no-hint-')[-1]


def get_total_usage(output: dict) -> tuple[int, int]:
    """Get total token usage for an output."""
    prompt_total = 0
    completion_total = 0
    for step in output['history']:
        try:
            usage = step['tool_call_metadata']['model_response']['usage']
            prompt_total += usage['prompt_tokens']
            completion_total += usage['completion_tokens']
        except KeyError:
            continue
    return prompt_total, completion_total


def usage(output: dict) -> Iterable[dict[str, int]]:
    """Get token usage per iteration."""
    for iteration, step in enumerate(output['history']):
        try:
            prompt_tokens = step['tool_call_metadata']['model_response']['usage'][
                'prompt_tokens'
            ]
            completion_tokens = step['tool_call_metadata']['model_response']['usage'][
                'completion_tokens'
            ]
            yield {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'iteration': iteration / 2,
            }
        except KeyError:
            continue


def save_chart(chart: alt.Chart, output_path: str) -> None:
    """Save chart in the format specified by the output path suffix."""
    suffix = output_path.lower().split('.')[-1]
    if suffix == 'json':
        with open(output_path, 'w') as f:
            json.dump(chart.to_dict(), f, indent=2)
    elif suffix == 'html':
        chart.save(output_path)
    elif suffix == 'svg':
        chart.save(output_path)
    else:
        raise ValueError(f"Unsupported output format: {suffix}")


def plot_token_usage(filepaths: list[str], output_path: str = None, width: int = 300, height: int = 300):
    data = [Data.from_filepath(filepath) for filepath in filepaths]
    
    # Prepare data for plotting
    df_list = []
    for d in data:
        for output in d.output:
            for token_usage in usage(output):
                token_usage['experiment'] = d.experiment()
                df_list.append(token_usage)
    
    df = pd.DataFrame(df_list)
    df_pi = df.groupby(['experiment', 'iteration'])['prompt_tokens'].agg(
        ['mean', 'count', 'std']
    ).reset_index()
    
    # Create confidence intervals
    df_pi['upper_prompt_tokens'] = df_pi['mean'] + df_pi['std']
    df_pi['lower_prompt_tokens'] = df_pi['mean'] - df_pi['std']
    df_pi['center_prompt_tokens'] = df_pi['mean']
    
    # Create the visualization
    chart = (
        alt.Chart(df_pi, title='Average Token Usage per Iteration')
        .mark_errorband(extent='ci')
        .encode(
            x=alt.X('iteration:Q', title='Iteration'),
            y=alt.Y('mean:Q', title='Prompt Tokens'),
            color=alt.Color('experiment:N', title='Experiment')
        )
        .properties(width=width, height=height)
    )
    
    if output_path:
        save_chart(chart, output_path)
    else:
        return chart


@click.group()
def cli():
    """Generate graphs from evaluation data."""
    pass


def plot_cactus_tokens(filepaths: list[str], output_path: str = None, width: int = 400, height: int = 300):
    data = [Data.from_filepath(filepath) for filepath in filepaths]
    
    # Prepare data for plotting
    df_list = []
    for d in data:
        for output in d.output:
            try:
                result = next(r for r in d.results if r.instance_id == output['instance_id'])
                prompt_total, completion_total = get_total_usage(output)
                df_list.append({
                    'experiment': d.experiment(),
                    'resolved': result.test_result.report.resolved,
                    'total_tokens': prompt_total + completion_total
                })
            except StopIteration:
                continue
    
    df = pd.DataFrame(df_list)
    
    # For each experiment, sort by tokens and count cumulative resolved
    cactus_data = []
    for exp in df['experiment'].unique():
        exp_df = df[df['experiment'] == exp]
        sorted_df = exp_df.sort_values('total_tokens')
        cumsum = sorted_df['resolved'].cumsum()
        cactus_data.extend([
            {'experiment': exp, 'total_tokens': tokens, 'resolved_count': count}
            for tokens, count in zip(sorted_df['total_tokens'], cumsum)
        ])
    
    cactus_df = pd.DataFrame(cactus_data)
    
    # Create the visualization
    chart = (
        alt.Chart(cactus_df, title='Resolved Instances by Token Usage')
        .mark_line()
        .encode(
            x=alt.X('total_tokens:Q', title='Total Tokens Used'),
            y=alt.Y('resolved_count:Q', title='Number of Resolved Instances'),
            color=alt.Color('experiment:N', title='Experiment')
        )
        .properties(width=width, height=height)
    )
    
    if output_path:
        save_chart(chart, output_path)
    else:
        return chart


def plot_cactus_iterations(filepaths: list[str], output_path: str = None, width: int = 400, height: int = 300):
    data = [Data.from_filepath(filepath) for filepath in filepaths]
    
    # Prepare data for plotting
    df_list = []
    for d in data:
        for output in d.output:
            try:
                result = next(r for r in d.results if r.instance_id == output['instance_id'])
                iterations = len(output['history']) / 2
                df_list.append({
                    'experiment': d.experiment(),
                    'resolved': result.test_result.report.resolved,
                    'iterations': iterations
                })
            except StopIteration:
                continue
    
    df = pd.DataFrame(df_list)
    
    # For each experiment, sort by iterations and count cumulative resolved
    cactus_data = []
    for exp in df['experiment'].unique():
        exp_df = df[df['experiment'] == exp]
        sorted_df = exp_df.sort_values('iterations')
        cumsum = sorted_df['resolved'].cumsum()
        cactus_data.extend([
            {'experiment': exp, 'iterations': iters, 'resolved_count': count}
            for iters, count in zip(sorted_df['iterations'], cumsum)
        ])
    
    cactus_df = pd.DataFrame(cactus_data)
    
    # Create the visualization
    chart = (
        alt.Chart(cactus_df, title='Resolved Instances by Number of Iterations')
        .mark_line()
        .encode(
            x=alt.X('iterations:Q', title='Number of Iterations'),
            y=alt.Y('resolved_count:Q', title='Number of Resolved Instances'),
            color=alt.Color('experiment:N', title='Experiment')
        )
        .properties(width=width, height=height)
    )
    
    if output_path:
        save_chart(chart, output_path)
    else:
        return chart


def validate_input_dir(ctx, param, value):
    """Validate that input paths are directories and contain required files."""
    for path in value:
        if not os.path.isdir(path):
            raise click.BadParameter(f"Not a directory: {path}")
        for required in ['metadata.json', 'output.jsonl', 'output.swebench_eval.jsonl']:
            if not os.path.exists(os.path.join(path, required)):
                raise click.BadParameter(f"Missing required file {required} in {path}")
    return value


@cli.command()
@click.argument('filepaths', nargs=-1, required=True, callback=validate_input_dir)
@click.option('--output', '-o', type=click.Path(dir_okay=False), help='Output file path (format determined by suffix: .json, .html, or .svg)')
@click.option('--width', type=int, default=300, help='Width of the graph in pixels')
@click.option('--height', type=int, default=300, help='Height of the graph in pixels')
@click.option('--browser/--no-browser', default=False, help='Display chart in browser')
def token_usage(filepaths, output, width, height, browser):
    """Generate token usage graph showing average tokens per iteration."""
    if browser:
        alt.renderers.enable('browser')
    chart = plot_token_usage(list(filepaths), output, width, height)
    if browser and not output:
        chart.show()


@cli.command()
@click.argument('filepaths', nargs=-1, required=True, callback=validate_input_dir)
@click.option('--output', '-o', type=click.Path(dir_okay=False), help='Output file path (format determined by suffix: .json, .html, or .svg)')
@click.option('--width', type=int, default=400, help='Width of the graph in pixels')
@click.option('--height', type=int, default=300, help='Height of the graph in pixels')
@click.option('--browser/--no-browser', default=False, help='Display chart in browser')
def cactus_tokens(filepaths, output, width, height, browser):
    """Generate cactus plot showing resolved instances by token usage."""
    if browser:
        alt.renderers.enable('browser')
    chart = plot_cactus_tokens(list(filepaths), output, width, height)
    if browser and not output:
        chart.show()


@cli.command()
@click.argument('filepaths', nargs=-1, required=True, callback=validate_input_dir)
@click.option('--output', '-o', type=click.Path(dir_okay=False), help='Output file path (format determined by suffix: .json, .html, or .svg)')
@click.option('--width', type=int, default=400, help='Width of the graph in pixels')
@click.option('--height', type=int, default=300, help='Height of the graph in pixels')
@click.option('--browser/--no-browser', default=False, help='Display chart in browser')
def cactus_iterations(filepaths, output, width, height, browser):
    """Generate cactus plot showing resolved instances by iteration count."""
    if browser:
        alt.renderers.enable('browser')
    chart = plot_cactus_iterations(list(filepaths), output, width, height)
    if browser and not output:
        chart.show()


if __name__ == '__main__':
    cli()