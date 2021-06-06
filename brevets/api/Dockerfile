FROM python:3.8
LABEL maintainer="henrycraddock@gmail.com"
COPY . /api
WORKDIR /api
RUN pip install -r requirements.txt
CMD ["python", "api.py"]
