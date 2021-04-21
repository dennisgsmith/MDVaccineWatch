FROM python:3.8


COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --upgrade pip \
    && pip install wheel \
    && pip install -r requirements.txt

COPY . .

ENV PORT=8050

CMD [ "/bin/bash" ]

ENTRYPOINT [ "./gunicorn_starter.sh" ]