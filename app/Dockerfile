FROM python:3.8-slim-buster AS web
RUN useradd --create-home appuser
USER appuser

WORKDIR /home/appuser
COPY . .
RUN pip install --user --upgrade pip \
    && pip install --user wheel \
    && pip install --user -r requirements.txt
ENV PORT=8050
ENTRYPOINT [ "./gunicorn_starter.sh" ]