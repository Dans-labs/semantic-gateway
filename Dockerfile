FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
COPY ./app /app
COPY ./conf /app/conf
COPY ./static/ /app/static
COPY ./templates /app/templates
COPY ./app/gateway.py ./app/main.py
RUN pip install -r /app/requirements.txt
