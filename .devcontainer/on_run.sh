#!/usr/bin/env bash
#USE_HOST_NETWORK=True nohup bash -c '(litellm --config my-configs/litellm.yaml &) ; make run' &> output.log &
export USE_HOST_NETWORK=True
bash -c '(nohup bash -c "make run") &> output.log'
