import os
import subprocess
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TaskProgressColumn
from rich.live import Live
from rich.layout import Layout
import logging

# Set script directory and other paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CASES_DIR = os.path.join(SCRIPT_DIR, 'cases')
AGENTHUB_DIR = os.path.join(SCRIPT_DIR, '../../agenthub')

# Check if DEBUG variable is already set
DEBUG = os.getenv("DEBUG", "0")
if DEBUG == "0":
    debug_value = input("Enter value for DEBUG (leave blank for default): ")
    os.environ["DEBUG"] = debug_value if debug_value else "0"

# Check if OPENAI_API_KEY variable is already set
if "OPENAI_API_KEY" not in os.environ:
    openai_key = input("Enter value for OPENAI_API_KEY: ")
    os.environ["OPENAI_API_KEY"] = openai_key

# Get the MODEL variable
model = input("Enter value for model running agents: ").strip()
MODEL = model if model else "gpt-4-0125-preview"
print("Running with model:", MODEL)

# Add python path
PYTHONPATH = os.getenv("PYTHONPATH", "")
os.environ["PYTHONPATH"] = f"{PYTHONPATH}:{SCRIPT_DIR}/../../"

# Hardcode pairs for directory to python class mapping
directory_class_pairs = {
    "langchains_agent": "LangchainsAgent",
    "codeact_agent": "CodeActAgent"
}

# Initialize counters for successful and failed test cases
success_count = 0
fail_count = 0

# Create a Rich console
console = Console()

# Create a table for the test results
table = Table(show_header=True, header_style="bold magenta", expand=True)
table.add_column("Test Case", style="dim")
table.add_column("Agent", style="dim")
table.add_column("Status", style="dim")
table.add_column("Task Context", style="dim")

# Get the total number of test cases
total_tests = len(os.listdir(CASES_DIR)) * len([item for item in os.listdir(AGENTHUB_DIR) if item.endswith("agent")])

# Create a layout
layout = Layout(name="root")
layout.split_column(
    Layout(name="header", size=3),
    Layout(name="execution", size=3),
    Layout(name="main"),
    Layout(name="footer", size=3),
    Layout(name="stdout", size=10)
)

layout["header"].split_row(
    Layout(name="time"),
    Layout(name="results")
)

# Create a progress bar
progress = Progress(
    "[progress.description]{task.description}",
    BarColumn(bar_width=None),
    TaskProgressColumn("[progress.percentage]{task.percentage:>3.0f}% | [cyan]{task.completed}[/cyan]/[cyan]{task.total}[/cyan]"),
    TimeElapsedColumn()
)

# Configure logging
logging.basicConfig(
    filename=f"{SCRIPT_DIR}/test_results.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

def run_subprocess(workspace_dir, directory_class, task_context, model):
    process = subprocess.Popen(["python3", f"{SCRIPT_DIR}/../../opendevin/main.py", "-d", f"{workspace_dir}", "-c", f"{directory_class}", "-t", f"{task_context}", "-m", f"{model}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return process

with Live(layout, refresh_per_second=4) as live:
    layout["header"]["time"].update(Panel(f"[bold]Test Results[/bold]"))
    layout["header"]["results"].update(Panel(f"[green]Successful test cases: {success_count}[/green]\t[red]Failed test cases: {fail_count}[/red]"))
    layout["main"].update(table)
    layout["footer"].update(progress)
    
    # Add panel to display stdout
    stdout_panel = Panel("Output will be displayed here", title="[bold]Script Output[/bold]", style="white on black")
    layout["stdout"].update(stdout_panel)
    
    task = progress.add_task("[green]Running tests...", total=total_tests)
    for agent in os.listdir(AGENTHUB_DIR):
        if not agent.endswith("agent"):
            continue

        for case in os.listdir(CASES_DIR):
            layout["header"]["results"].update(Panel(f"[green]Successful test cases: {success_count}[/green]\t[red]Failed test cases: {fail_count}[/red]"))
            execution_panel = Panel(f"Executing [bold]{case}[/bold] with agent [bold]{agent}[/bold]...", style="yellow")
            layout["execution"].update(execution_panel)

            case_dir = os.path.join(CASES_DIR, case)
            task_file = os.path.join(case_dir, "task.txt")
            with open(task_file, "r") as f:
                task_context = f.read().strip()
            outputs_dir = os.path.join(case_dir, "outputs", agent)

            # Create agent directory if it does not exist
            os.makedirs(outputs_dir, exist_ok=True)

            # Remove existing workspace and create new one
            workspace_dir = os.path.join(outputs_dir, "workspace")
            os.makedirs(workspace_dir, exist_ok=True)

            # Copy start directory to workspace if it exists
            start_dir = os.path.join(case_dir, "start")
            if os.path.isdir(start_dir):
                subprocess.run(["cp", "-r", f"{start_dir}/", f"{workspace_dir}"])

            test_script = os.path.join(case_dir, "test.sh")
            if os.path.isfile(test_script):
                # Run main.py and capture output
                main_process = run_subprocess(workspace_dir, directory_class_pairs.get(agent, ''), task_context, MODEL)
                log_file = os.path.join(outputs_dir, "log.txt")
                logging.basicConfig(filename=log_file, filemode="w", format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
                logging.info(f"Running agent {directory_class_pairs.get(agent, '')} (model: {MODEL}, directory: {workspace_dir}) with task: \"{task_context}\"")
                while main_process.poll() is None:
                    stdout_panel.renderable = ""
                    for i in range(15):
                        stdout = main_process.stdout.readline().strip()
                        if stdout:
                            stdout_panel.renderable += f"{stdout}\n"
                            layout["stdout"].update(stdout_panel)
                            logging.info(stdout)

                # Wait for the main.py process to finish
                main_process.wait()

                # Check the exit status of main.py
                if main_process.returncode == 0:
                    # If main.py succeeds, run test.sh
                    test_process = subprocess.run(["bash", test_script, f"{workspace_dir}"])
                    if test_process.returncode == 0:
                        success_count += 1
                        table.add_row(case, agent, f"[green]Passed[/green]", task_context)
                        logging.info(f"Test case '{case}' with agent '{agent}' passed.")
                    else:
                        fail_count += 1
                        table.add_row(case, agent, f"[red]Failed[/red]", task_context)
                        logging.error(f"Test case '{case}' with agent '{agent}' failed.")
                else:
                    # If main.py fails, increment the fail count
                    fail_count += 1
                    table.add_row(case, agent, f"[red]Failed[/red]", task_context)
                    logging.error(f"Test case '{case}' with agent '{agent}' failed.")
            else:
                # If test.sh not found, increment the fail count
                fail_count += 1
                table.add_row(case, agent, f"[red]Failed[/red]", task_context)
                logging.error(f"Test case '{case}' with agent '{agent}' failed (test.sh not found).")

            # Remove .git directory from workspace
            subprocess.run(["rm", "-rf", f"{workspace_dir}/.git"])
            progress.update(task, advance=1)
            live.refresh()

    layout["execution"].update(Panel("Tests finished", style="green"))
    live.refresh()