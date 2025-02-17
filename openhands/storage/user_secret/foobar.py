import asyncio
from uuid import uuid4

from openhands.server.shared import config
from openhands.storage.data_models.token_factory import ApiKey
from openhands.storage.data_models.user_secret import UserSecret
from openhands.storage.user_secret.file_user_secret_store import FileUserSecretStore


async def main():
    token_factory = ApiKey(secret_value='not-a-secret')
    slack_api_key = UserSecret(
        id=str(uuid4()),
        key='PHALANGE_API_KEY',
        user_id=None,
        description='An API key for Regina to use when accessing the Phalange API',
        token_factory=token_factory,
    )
    user_secret_store = await FileUserSecretStore.get_instance(config, None)
    await user_secret_store.save_secret(slack_api_key)

    loaded_secret = await user_secret_store.load_secret(slack_api_key.id)
    print(loaded_secret)

    result_set = await user_secret_store.search()
    print(result_set)


if __name__ == '__main__':
    asyncio.run(main())
