FROM python:2.7
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app
ADD ./requirements.txt /app/
RUN pip install -r requirements.txt
ADD . /app/
RUN ["chmod", "+x", "run_container.sh"]

EXPOSE 8000

CMD ["./run_container.sh"]
