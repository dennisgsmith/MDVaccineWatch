FROM python:3.8

USER root

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN python3 -m pip3 install --upgrade pip \
  && python3 -m pip3 install -r requirements.txt

COPY . /app

CMD [ "python3", "app.py" ]