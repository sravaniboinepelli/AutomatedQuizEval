FROM tiangolo/uwsgi-nginx-flask:python3.6
# Copy req file
COPY requirements.txt /tmp/

RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt
COPY ./app /app

ENV SemanticSimilarity_PORT "80"
