FROM --platform=linux/amd64 python:3.11.3-buster

WORKDIR /usr/src/app

ENV PYTHONPATH=/usr/src/app:$PYTHONPATH
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y netcat tzdata && \
    rm -rf /var/lib/apt/lists/*

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN pip install --upgrade pip
COPY ./requirements.txt ./
RUN pip install -r ./requirements.txt

COPY . .

RUN chmod +x /usr/src/app/entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]