FROM python:3.8-slim-buster AS scheduler
RUN useradd --create-home appuser
USER appuser

WORKDIR /home/appuser
COPY . .
RUN pip install --user --upgrade pip \
    && pip install --user wheel \
    && pip install --user -r requirements.txt
CMD [ "python", "main.py" ]