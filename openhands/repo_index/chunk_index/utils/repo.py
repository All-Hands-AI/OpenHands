import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def setup_github_repo(repo: str, base_commit: str, base_dir: str = '/tmp/repos') -> str:
    repo_name = get_repo_dir_name(repo)
    repo_url = f'https://github.com/{repo}.git'

    path = f'{base_dir}/{repo_name}'
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Directory '{path}' was created.")
    maybe_clone(repo_url, path)
    checkout_commit(path, base_commit)

    return path


def get_repo_dir_name(repo: str):
    return repo.replace('/', '_')


def maybe_clone(repo_url, repo_dir):
    if not os.path.exists(f'{repo_dir}/.git'):
        logger.info(f"Cloning repo '{repo_url}'")
        # Clone the repo if the directory doesn't exist
        result = subprocess.run(
            ['git', 'clone', repo_url, repo_dir],
            check=True,
            text=True,
            capture_output=True,
        )

        if result.returncode == 0:
            logger.info(f"Repo '{repo_url}' was cloned to '{repo_dir}'")
        else:
            logger.info(f"Failed to clone repo '{repo_url}' to '{repo_dir}'")
            raise ValueError(f"Failed to clone repo '{repo_url}' to '{repo_dir}'")


def pull_latest(repo_dir):
    subprocess.run(
        ['git', 'pull'],
        cwd=repo_dir,
        check=True,
        text=True,
        capture_output=True,
    )


def clean_and_reset_state(repo_dir):
    subprocess.run(
        ['git', 'clean', '-fd'],
        cwd=repo_dir,
        check=True,
        text=True,
        capture_output=True,
    )
    subprocess.run(
        ['git', 'reset', '--hard'],
        cwd=repo_dir,
        check=True,
        text=True,
        capture_output=True,
    )


def create_branch(repo_dir, branch_name):
    try:
        subprocess.run(
            ['git', 'branch', branch_name],
            cwd=repo_dir,
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise e


def create_and_checkout_branch(repo_dir, branch_name):
    try:
        branches = subprocess.run(
            ['git', 'branch'],
            cwd=repo_dir,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.split('\n')
        branches = [branch.strip() for branch in branches]
        if branch_name in branches:
            subprocess.run(
                ['git', 'checkout', branch_name],
                cwd=repo_dir,
                check=True,
                text=True,
                capture_output=True,
            )
        else:
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=repo_dir,
                check=True,
                text=True,
                capture_output=True,
            )  # output =
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise e


def commit_changes(repo_dir, commit_message):
    subprocess.run(
        ['git', 'commit', '-m', commit_message, '--no-verify'],
        cwd=repo_dir,
        check=True,
        text=True,
        capture_output=True,
    )


def checkout_branch(repo_dir, branch_name):
    subprocess.run(
        ['git', 'checkout', branch_name],
        cwd=repo_dir,
        check=True,
        text=True,
        capture_output=True,
    )


def push_branch(repo_dir, branch_name):
    subprocess.run(
        ['git', 'push', 'origin', branch_name, '--no-verify'],
        cwd=repo_dir,
        check=True,
        text=True,
        capture_output=True,
    )


def get_diff(repo_dir):
    output = subprocess.run(
        ['git', 'diff'], cwd=repo_dir, check=True, text=True, capture_output=True
    )

    return output.stdout


def stage_all_files(repo_dir):
    subprocess.run(
        ['git', 'add', '.'], cwd=repo_dir, check=True, text=True, capture_output=True
    )


def checkout_commit(repo_dir, commit_hash):
    try:
        subprocess.run(
            ['git', 'reset', '--hard', commit_hash],
            cwd=repo_dir,
            check=True,
            text=True,
            capture_output=True,
        )  # output =
    except subprocess.CalledProcessError as e:
        logger.error(e.stderr)
        raise e


def setup_repo(repo_url, repo_dir, branch_name='master'):
    maybe_clone(repo_url, repo_dir)
    clean_and_reset_state(repo_dir)
    checkout_branch(repo_dir, branch_name)
    pull_latest(repo_dir)


def clean_and_reset_repo(repo_dir, branch_name='master'):
    clean_and_reset_state(repo_dir)
    checkout_branch(repo_dir, branch_name)
    pull_latest(repo_dir)
