FROM python:3.8 AS worker

COPY ./requirements.txt /backend/requirements.txt

WORKDIR /backend

RUN pip install --upgrade pip \
    && pip install wheel \
    && pip install -r requirements.txt

COPY . .

CMD [ "python", "pulldata.py" ]