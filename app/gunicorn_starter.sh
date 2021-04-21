#!/bin/bash
exec gunicorn -w 4 app:server -b 0.0.0.0:8050