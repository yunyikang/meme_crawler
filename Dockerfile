ARG PYTHON_VERSION=3.11.9
FROM python:${PYTHON_VERSION}-slim 

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN apt-get install -y cron
RUN apt-get install -y procps
RUN apt-get -y install libicu-dev


WORKDIR /app

COPY . .
RUN mkdir logs
RUN mkdir out

RUN chmod +x scripts/job.sh
RUN chmod +x scripts/start_cron.sh

RUN crontab cron/cron.txt
RUN pip3 install -r requirements.txt

CMD scripts/start_cron.sh && python3 bot.py
