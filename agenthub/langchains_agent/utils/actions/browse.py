import requests

def browse(url):
    response = requests.get(url)
    return response.text

