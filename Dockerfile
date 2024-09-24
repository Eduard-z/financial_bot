FROM python:3.12

WORKDIR /home

COPY . ./

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "server.py"]