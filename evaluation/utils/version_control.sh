checkout_eval_branch() {
    if [ -z "$COMMIT_HASH" ]; then
        echo "Commit hash not specified, use current git commit"
        return 0
    fi
    echo "Start to checkout opendevin version to $COMMIT_HASH, but keep current evaluation harness"
    if ! git diff-index --quiet HEAD --; then
        echo "There are uncommitted changes, please stash or commit them first"
        exit 1
    fi
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    echo "Current version is: $current_branch"
    echo "Check out OpenDevin to version: $COMMIT_HASH"
    if ! git checkout $COMMIT_HASH; then
        echo "Failed to check out to $COMMIT_HASH"
        exit 1
    fi
    echo "Revert changes in evaluation folder"
    git checkout $current_branch -- evaluation
}

checkout_original_branch() {
    if [ -z "$current_branch" ]; then
        return 0
    fi
    echo "Checkout back to original branch $current_branch"
    git checkout $current_branch
}

get_agent_version() {
    # IMPORTANT: Because Agent's prompt changes fairly often in the rapidly evolving codebase of OpenDevin
    # We need to track the version of Agent in the evaluation to make sure results are comparable
    AGENT_VERSION=v$(poetry run python -c "import agenthub; from opendevin.controller.agent import Agent; print(Agent.get_cls('$AGENT').VERSION)")
}
