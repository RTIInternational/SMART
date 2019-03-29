FROM python:3.5.7
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y netcat-traditional
WORKDIR /code
ADD ./requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt
RUN mkdir -p /data/data_files /data/tf_idf /data/model_pickles /data/code_books
EXPOSE 8000
