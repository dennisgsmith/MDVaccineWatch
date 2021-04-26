FROM python:3.8 AS web


COPY ./requirements.txt /webapp/requirements.txt

WORKDIR /webapp

RUN pip install --upgrade pip \
    && pip install wheel \
    && pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "./gunicorn_starter.sh" ]