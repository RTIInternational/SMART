FROM --platform=linux/amd64 python:3.8-buster
ENV PYTHONUNBUFFERED 1

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update && apt-get install -y netcat-traditional && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    apt-get install -y unixodbc-dev

WORKDIR /code
ADD ./docker/requirements.txt /code/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir
RUN mkdir -p /data/data_files /data/tf_idf /data/model_pickles /data/code_books /data/external_db
EXPOSE 8000
