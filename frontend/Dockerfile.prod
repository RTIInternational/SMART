FROM node:latest
RUN apt-get update && apt-get install -y nginx
WORKDIR /code
RUN yarn install
RUN yarn global add webpack
ADD . /code
ENV NODE_ENV production
RUN webpack
EXPOSE 8080