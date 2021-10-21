# syntax=docker/dockerfile:1

FROM python:3.10.0-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
ENTRYPOINT [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
