FROM python:3.8

COPY ./requirements.txt /backend/requirements.txt

WORKDIR /backend

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

ADD ./main.py ./main.py

ADD ./pulldata.py ./pulldata.py

CMD [ "python", "main.py" ]