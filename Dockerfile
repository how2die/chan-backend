FROM python:3.10.0-slim-buster

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/app

WORKDIR /code/app

# EXPOSE 8000
# ENTRYPOINT [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]