FROM python:3.8 AS scheduler


COPY ./requirements.txt /scheduler/requirements.txt

WORKDIR /scheduler

RUN pip install --upgrade pip \
    && pip install wheel \
    && pip install -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]