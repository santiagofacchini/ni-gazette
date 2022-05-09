FROM python:3.11.0a7-alpine3.15

WORKDIR /usr/src/app

RUN apk add ghostscript-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./ni-gazette.py" ]
