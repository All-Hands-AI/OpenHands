#!/usr/bin/env bash


# Exit on any error would be useful for debugging
if [ -n "$DEBUG" ]; then
    set -e
fi

# OUTPUTS_PATH is the path to save trajectories and evaluation results
SUBMISSIONS_PATH="outputs/submissions"


# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --submissions-path)
            SUBMISSIONS_PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# Convert outputs_path to absolute path
if [[ ! "$SUBMISSIONS_PATH" = /* ]]; then
    # If path is not already absolute (doesn't start with /), make it absolute
    SUBMISSIONS_PATH="$(cd "$(dirname "$SUBMISSIONS_PATH")" 2>/dev/null && pwd)/$(basename "$SUBMISSIONS_PATH")"
fi

#For each file in SUBMISSIONS_PATH/{task_name}/{xyz}.zip -> unzip it to SUBMISSIONS_PATH/{task_name}/{xyz}
for task_name in $(ls -d $SUBMISSIONS_PATH/*); do
    for zip_file in $(ls $task_name/*.zip); do
        unzip -d $task_name $(basename $zip_file) && rm $zip_file
    done
done

echo "Using submissions path: $SUBMISSIONS_PATH"

COMMAND = "uv run python -m paperbench.nano.entrypoint \
    paperbench.paper_split=all \
    paperbench.solver=paperbench.solvers.direct_submission.solver:PBDirectSubmissionSolver \
    paperbench.solver.submissions_dir=$SUBMISSIONS_PATH \
    paperbench.solver.cluster_config=alcatraz.clusters.local:LocalConfig \
    paperbench.solver.cluster_config.image=pb-env:latest \
    runner.recorder=nanoeval.json_recorder:json_recorder"

export PYTHONPATH=evaluation/benchmarks/paper_bench:$PYTHONPATH && \
        eval "$COMMAND"

echo "All evaluation completed successfully!"
