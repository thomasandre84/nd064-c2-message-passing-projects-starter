FROM python:3.7-alpine

WORKDIR .

RUN apk add --no-cache build-base linux-headers geos postgresql-dev
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

EXPOSE 5001 5005

COPY . .
CMD ["flask", "run", "--host", "0.0.0.0"]