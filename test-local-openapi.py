# from openai import OpenAI

# client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="sk-xxx")
# response = client.chat.completions.create(
#     model="gpt-3.5-turbo",
#     messages=[
#         {
#             "role": "user",
#             "content": "hello",
#         }
#     ],
# )
# print(response)

from litellm.router import Router
router = Router(
            model_list=[{
                "model_name": "gpt-3.5-turbo",
                "litellm_params": {
                    "model": "gpt-3.5-turbo",
                    "api_key": "sk-xxx",
                    "api_base": "http://127.0.0.1:8000/v1"
                }
            }],
            # num_retries=self.num_retries,
            # allowed_fails=self.num_retries, # We allow all retries to fail, so they can retry instead of going into "cooldown"
            # cooldown_time=self.cooldown_time,
            # set_verbose=True,
            # debug_level="DEBUG"
        )
response = router.completion(model="gpt-3.5-turbo", messages=[{"role": "user", "content": "hello"}])
print(response)