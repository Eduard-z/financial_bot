FROM python:3.12

WORKDIR /home

COPY *.py ./
COPY createdb.sql ./
COPY requirements.txt ./
COPY .env ./
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "server.py"]