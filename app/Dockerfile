FROM python:3.8-slim-buster AS web

COPY . /webapp
WORKDIR /webapp
RUN pip install --upgrade pip \
    && pip install wheel \
    && pip install -r requirements.txt
# CMD gunicorn --bind 0.0.0.0:80 wsgi
CMD [ "python", "app.py" ]