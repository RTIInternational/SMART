FROM python:3.9

WORKDIR /code

ADD ./requirements.txt /code/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

EXPOSE 8001
CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8001", "--reload"]
