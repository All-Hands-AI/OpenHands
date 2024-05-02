import boto3

from opendevin import config
from opendevin.logger import opendevin_logger as logger
from opendevin.schema import ConfigType

AWS_ACCESS_KEY_ID = config.get(ConfigType.AWS_ACCESS_KEY_ID)
AWS_SECRET_ACCESS_KEY = config.get(ConfigType.AWS_SECRET_ACCESS_KEY)
AWS_REGION_NAME = config.get(ConfigType.AWS_REGION_NAME)


def list_foundation_models():
    try:
        client = boto3.client(service_name='bedrock',
                              region_name=AWS_REGION_NAME,
                              aws_access_key_id=AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        foundation_models_list = client.list_foundation_models(byOutputModality='TEXT', byInferenceType='ON_DEMAND')
        model_summaries = foundation_models_list['modelSummaries']
        return ['bedrock/' + model['modelId'] for model in model_summaries]
    except Exception as err:
        logger.warning('%s. Please config AWS_REGION_NAME AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY'
                       ' if you want use bedrock model.', err)

def remove_error_modelId(model_list):
    return list(filter(lambda m: not m.startswith('bedrock'), model_list))
