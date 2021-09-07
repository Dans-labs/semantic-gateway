FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
RUN apt update
RUN apt-get -y install curl gnupg
RUN curl -sL https://deb.nodesource.com/setup_14.x  | bash -
RUN apt-get -y install nodejs wget bash git

RUN npm install -g wikidata-taxonomy
RUN npm install -g wikibase-cli
COPY ./app /app
COPY ./conf /app/conf
COPY ./static/ /app/static
COPY ./templates /app/templates
COPY ./app/gateway.py ./app/main.py
RUN pip install -r /app/requirements.txt
