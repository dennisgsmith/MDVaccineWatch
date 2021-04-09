FROM python:3.8

COPY ./requirements.txt /backend/requirements.txt

WORKDIR /backend

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]