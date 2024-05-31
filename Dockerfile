FROM python:3.12

RUN apt-get update && apt-get install -y less \
    vim jq
RUN pip install poetry

COPY . .

RUN poetry install --with dev