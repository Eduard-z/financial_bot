FROM python:3.12

WORKDIR /home

COPY . ./
RUN mkdir -p /home/db
RUN mkdir -p /home/artefacts

RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "server.py"]