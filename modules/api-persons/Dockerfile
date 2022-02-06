FROM python:3.7-alpine

WORKDIR .

RUN apk add --no-cache build-base linux-headers
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

EXPOSE 5000

COPY . .
CMD ["flask", "run", "--host", "0.0.0.0"]