from g4f.client import Client

client = Client()
response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)