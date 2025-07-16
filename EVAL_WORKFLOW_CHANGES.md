# Run Eval Workflow Changes

## Overview

The `.github/workflows/run-eval.yml` workflow has been modified to support automatic triggering after releases and manual triggering with branch/size selection, while maintaining backward compatibility with PR-based evaluation triggers.

## Key Changes

### 1. New Trigger Types

- **Release Trigger**: Automatically runs evaluation with 50 instances after each GitHub release
- **Manual Trigger**: Allows manual workflow dispatch with customizable branch and instance count
- **Existing PR Trigger**: Maintains existing functionality for PR-based evaluations

### 2. Manual Trigger Inputs

When manually triggering the workflow, users can specify:
- **Branch**: Which branch to evaluate (default: `main`)
- **Evaluation Instances**: Number of instances to run (choices: 1, 2, 50, 100, default: 50)
- **Reason**: Optional reason for the manual trigger

### 3. Master Issue Integration

All evaluation results (from releases, manual triggers, and PRs) can be commented to a centralized GitHub issue by setting the `MASTER_EVAL_ISSUE_NUMBER` repository variable.

## Setup Instructions

### 1. Set Repository Variable

To enable centralized issue commenting, set up the repository variable:

1. Go to your repository settings
2. Navigate to "Secrets and variables" → "Actions"
3. In the "Variables" tab, create a new repository variable:
   - **Name**: `MASTER_EVAL_ISSUE_NUMBER`
   - **Value**: The issue number where you want all evaluation results to be posted (e.g., `1234`)

### 2. Workflow Behavior

#### For PR Triggers (existing behavior):
- Comments on the specific PR
- Uses the PR branch for evaluation
- Instance count determined by label (`run-eval-1`, `run-eval-2`, `run-eval-50`, `run-eval-100`)

#### For Release Triggers (new):
- Comments on the master issue (if `MASTER_EVAL_ISSUE_NUMBER` is set)
- Uses the release tag/branch for evaluation
- Runs 50 instances by default
- Includes release information in Slack notifications

#### For Manual Triggers (new):
- Comments on the master issue (if `MASTER_EVAL_ISSUE_NUMBER` is set)
- Uses user-specified branch and instance count
- Includes manual trigger reason in notifications

## Environment Variables

- `MASTER_EVAL_ISSUE_NUMBER`: Repository variable containing the issue number for centralized result posting
- Existing secrets remain unchanged (`PAT_TOKEN`, `SLACK_TOKEN`)

## Backward Compatibility

The workflow maintains full backward compatibility:
- Existing PR-based evaluation triggers continue to work unchanged
- All existing secrets and configurations remain valid
- PR evaluations still comment on the respective PRs

## Usage Examples

### Manual Trigger
1. Go to Actions tab in your repository
2. Select "Run Eval" workflow
3. Click "Run workflow"
4. Specify:
   - Branch to evaluate
   - Number of instances
   - Reason for evaluation

### Release Trigger
- Automatically triggered when a new release is published
- No manual intervention required
- Results posted to master issue

### PR Trigger (unchanged)
- Add labels `run-eval-1`, `run-eval-2`, `run-eval-50`, or `run-eval-100` to PRs
- Evaluation runs automatically
- Results posted to the PR
