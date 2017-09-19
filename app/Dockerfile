FROM python:2.7
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app
ADD ./requirements.txt /app/
RUN pip install -r requirements.txt
ADD . /app/

EXPOSE 80

CMD ["python","manage.py","runserver","0.0.0.0:80","--settings=config.settings.aws"]
