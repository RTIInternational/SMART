FROM python:3.5.7
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y netcat-traditional mysql-client
WORKDIR /code
ADD ./requirements.txt /code/requirements.txt
RUN pip install  -r requirements.txt
RUN pip install gunicorn
ADD ./smart/ /code/
RUN mkdir -p /data/data_files /data/tf_idf /data/model_pickles /data/code_books
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "--timeout", "75", "--worker-class", "gevent", "config.wsgi"]
