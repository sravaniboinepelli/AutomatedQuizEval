FROM tiangolo/uwsgi-nginx-flask:python3.6
# Copy req file
COPY requirements.txt /tmp/

RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt
RUN sudo apt-get update
RUN sudo apt-get install tesseract-ocr
COPY ./app /app

ENV OCR_PORT "80"
