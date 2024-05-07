import os

import boto3

from opendevin.core.config import config
from opendevin.core.logger import opendevin_logger as logger

AWS_ACCESS_KEY_ID = config.llm.aws_access_key_id
AWS_SECRET_ACCESS_KEY = config.llm.aws_secret_access_key
AWS_REGION_NAME = config.llm.aws_region_name

# It needs to be set as an environment variable, if the variable is configured in the Config file.
if AWS_ACCESS_KEY_ID is not None:
    os.environ['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY_ID
if AWS_SECRET_ACCESS_KEY is not None:
    os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_ACCESS_KEY
if AWS_REGION_NAME is not None:
    os.environ['AWS_REGION_NAME'] = AWS_REGION_NAME


def list_foundation_models():
    try:
        # The AWS bedrock model id is not queried, if no AWS parameters are configured.
        if (
            AWS_REGION_NAME is None
            or AWS_ACCESS_KEY_ID is None
            or AWS_SECRET_ACCESS_KEY is None
        ):
            return []

        client = boto3.client(
            service_name='bedrock',
            region_name=AWS_REGION_NAME,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
        foundation_models_list = client.list_foundation_models(
            byOutputModality='TEXT', byInferenceType='ON_DEMAND'
        )
        model_summaries = foundation_models_list['modelSummaries']
        return ['bedrock/' + model['modelId'] for model in model_summaries]
    except Exception as err:
        logger.warning(
            '%s. Please config AWS_REGION_NAME AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY'
            ' if you want use bedrock model.',
            err,
        )
        return []


def remove_error_modelId(model_list):
    return list(filter(lambda m: not m.startswith('bedrock'), model_list))
