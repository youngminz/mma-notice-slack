FROM python:3.7.1

COPY requirements/development.txt requirements/production.txt ./

ENV PYTHONIOENCODING utf-8
ENV PYTHONUNBUFFERED 1
ENV TZ Asia/Seoul

RUN mkdir /app && \
    chown www-data:www-data /app
WORKDIR /app

COPY . .
RUN chown www-data:www-data . && \
    pip install -r requirements/production.txt -i http://mirror.kakao.com/pypi/simple --trusted-host mirror.kakao.com

ENTRYPOINT fab load_secrets:development && python manage.py work_mma_scrap
