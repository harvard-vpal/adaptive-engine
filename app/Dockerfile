FROM python:2.7
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app

COPY ./requirements.txt /app/
RUN pip install -r requirements.txt
COPY ./entrypoint.sh /app/
COPY . /app/

ENTRYPOINT ["./entrypoint.sh"]
EXPOSE 8000