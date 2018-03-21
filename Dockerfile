FROM python:3

WORKDIR /src
COPY requirements.txt setup.py ./
RUN pip install -r requirements.txt

