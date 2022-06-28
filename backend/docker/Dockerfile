FROM python:3.8-buster
ENV PYTHONUNBUFFERED 1

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update && apt-get install -y netcat-traditional && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    apt-get install -y unixodbc-dev && apt-get install -y cron

# Copy cron-template file to the cron.d directory
COPY ./django/daily-database-cron /etc/cron.d/daily-database-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/daily-database-cron

# Apply cron job
RUN crontab /etc/cron.d/daily-database-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log


WORKDIR /code
ADD ./docker/requirements.txt /code/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir
RUN mkdir -p /data/data_files /data/tf_idf /data/model_pickles /data/code_books /data/external_db
EXPOSE 8000
