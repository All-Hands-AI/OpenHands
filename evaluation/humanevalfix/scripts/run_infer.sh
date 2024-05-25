#!/bin/bash
MODEL_CONFIG=$1
AGENT=$2
EVAL_LIMIT=$3

echo "
################################################################################
                                  !!!WARNING!!!
################################################################################
The "code_eval" metric executes untrusted model-generated code in Python.
Although it is highly unlikely that model-generated code will do something
overtly malicious in response to this test suite, model-generated code may act
destructively due to a lack of model capability or alignment.
Users are strongly encouraged to sandbox this evaluation suite so that it
does not perform destructive actions on their host or network. For more
information on how OpenAI sandboxes its code, see the paper \"Evaluating Large
Language Models Trained on Code\" (https://arxiv.org/abs/2107.03374).

Once you have read this disclaimer and taken appropriate precautions,
set the environment variable HF_ALLOW_CODE_EVAL="1". Within Python you can to this
with:

>>> import os
>>> os.environ[\"HF_ALLOW_CODE_EVAL\"] = \"1\"

################################################################################
"

echo "WARNING: You are about to enable the execution of untrusted model-generated code by setting the environment variable HF_ALLOW_CODE_EVAL to '1'."
echo "It is highly unlikely that model-generated code will do something overtly malicious in response to this test suite, however, it may act destructively due to a lack of model capability or alignment."
echo "Please confirm that you have read the disclaimer, taken the necessary precautions, and wish to proceed (y/n):"
read user_input

if [ "$user_input" = "y" ]; then
  export HF_ALLOW_CODE_EVAL="1"
  echo "Environment variable HF_ALLOW_CODE_EVAL has been set to '1'."
else
  echo "Operation aborted. Environment variable HF_ALLOW_CODE_EVAL has not been set."
  exit 1
fi

# ################################################################################

if [ -z "$AGENT" ]; then
  echo "Agent not specified, use default CodeActAgent"
  AGENT="CodeActAgent"
fi

# IMPORTANT: Because Agent's prompt changes fairly often in the rapidly evolving codebase of OpenDevin
# We need to track the version of Agent in the evaluation to make sure results are comparable
AGENT_VERSION=v$(poetry run python -c "import agenthub; from opendevin.controller.agent import Agent; print(Agent.get_cls('$AGENT').VERSION)")

echo "AGENT: $AGENT"
echo "AGENT_VERSION: $AGENT_VERSION"
echo "MODEL_CONFIG: $MODEL_CONFIG"

COMMAND="poetry run python evaluation/humanevalfix/run_infer.py \
  --agent-cls $AGENT \
  --llm-config $MODEL_CONFIG \
  --max-iterations 10 \
  --max-chars 10000000 \
  --eval-num-workers 1 \
  --eval-note $AGENT_VERSION"

if [ -n "$EVAL_LIMIT" ]; then
  echo "EVAL_LIMIT: $EVAL_LIMIT"
  COMMAND="$COMMAND --eval-n-limit $EVAL_LIMIT"
fi

# Run the command
eval $COMMAND
