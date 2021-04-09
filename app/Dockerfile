FROM python:3.8

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

EXPOSE 8050

CMD [ "python", "app.py" ]