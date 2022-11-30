# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY flask_app/ flask_app/
COPY migrations/ migrations/

EXPOSE 8000
CMD flask db upgrade && gunicorn -w 4 flask_app:app -b 0.0.0.0:8000
