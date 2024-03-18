from python:3.12-bookworm

ENV OPENAI_API_KEY=""
ENV OPENAI_MODEL="gpt-4-0125-preview"

RUN git config --global user.email "devin@opendevin.com"
RUN git config --global user.name "Devin Abierto"

RUN apt-get update
RUN apt-get install -y git sudo curl

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN python -m pip install -r requirements.txt

COPY lib ./lib
COPY main.py ./main.py

WORKDIR /workspace

CMD ["python", "/app/main.py", "/workspace"]

