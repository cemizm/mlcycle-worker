FROM python:3

WORKDIR /app/

COPY . /app

RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED 1

ENV MLCYCLE_VOLUME worker_workdir
ENV MLCYCLE_WORKDIR /tmp/mlcycle
ENV MLCYCLE_RUNTIME nvidia
ENV MLCYCLE_VISIBLE_GPUS all

CMD python run.py