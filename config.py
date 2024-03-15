import os

os.environ["platform"]    = ""    # specify the platform. openai, claude, gemini, baidu or so
os.environ["model"]       = ""    # specify the main model to use
os.environ["submodel"]    = ""    # specify a model with lower cost and reduced intelligence, to save tokens for some easier work
os.environ["embed_model"] = ""    # model for embedding
os.environ["access_key"]  = ""    # specify the access key. if username and password exist simultaneously, put them in a single string