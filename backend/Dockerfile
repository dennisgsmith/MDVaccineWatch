FROM python:3.8

WORKDIR /data

COPY ./requirements.txt /data/requirements.txt

RUN python3 -m pip3 install --upgrade pip \
  && python3 -m pip3 install -r requirements.txt

COPY . /data

CMD [ "python3", "-u", "main.py" ]