FROM python:3.10
LABEL Maintainer="Jan Korinek"

WORKDIR /app

COPY main.py requirements.txt logger_conf.yaml README.md ./

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "./main.py"]