FROM python:3.5.3
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y netcat-traditional mysql-client
WORKDIR /code
ADD ./requirements.txt /code/requirements.txt
RUN pip install --use-wheel -r requirements.txt
EXPOSE 8000
