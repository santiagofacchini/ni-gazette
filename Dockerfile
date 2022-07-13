FROM python:3.11.0b4-alpine3.16

WORKDIR /usr/src/app

RUN apk add ghostscript-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "/usr/src/app/ni-gazette.py" ]
