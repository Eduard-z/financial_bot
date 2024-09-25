FROM python:3.12

WORKDIR /home

COPY . ./
RUN mkdir /home/db
RUN mkdir /home/artefacts

RUN pip install -r requirements.txt

ENTRYPOINT ["python3", "server.py"]