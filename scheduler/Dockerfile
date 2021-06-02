FROM amazon/aws-lambda-python:3.8.2021.05.27.08 AS scheduler

WORKDIR /scheduler
COPY . .
RUN pip install --upgrade pip \
    && pip install wheel \
    && pip install -r requirements.txt
CMD [ "main.main" ]