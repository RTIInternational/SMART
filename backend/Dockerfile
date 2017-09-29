FROM python:3.5.3
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y netcat-traditional
WORKDIR /code
ADD ./requirements.txt /code/requirements.txt
RUN pip install --use-wheel -r requirements.txt
RUN mkdir -p /data/data_files /data/tf_idf /data/model_pickles
EXPOSE 8000
