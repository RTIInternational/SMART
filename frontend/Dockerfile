FROM node:6
RUN mkdir /code
ADD ./package.json /code/package.json
ADD ./yarn.lock /code/yarn.lock
WORKDIR /code
RUN yarn install
RUN yarn add --force node-sass
