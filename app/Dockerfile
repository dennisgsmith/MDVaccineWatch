FROM python:3.8 AS web


COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --upgrade pip \
    && pip install wheel \
    && pip install -r requirements.txt

COPY . .

ENV PORT=8050

ENTRYPOINT [ "./gunicorn_starter.sh" ]