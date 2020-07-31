FROM python:3.8.5-buster

# upgrade pip, install dependencies
RUN pip3 install --upgrade pip

COPY . /usr/src/robohash/

WORKDIR /usr/src/robohash

RUN pip install -e .

EXPOSE 80

CMD [ "python3", "./robohash/webfront.py" ]