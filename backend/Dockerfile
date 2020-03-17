FROM python:3.6.0
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y netcat-traditional
WORKDIR /code
RUN pip install --upgrade pip
ADD ./requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt
RUN mkdir -p /data/data_files /data/tf_idf /data/model_pickles /data/code_books
EXPOSE 8000
