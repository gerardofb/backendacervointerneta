FROM python:3.10
ENV PYTHONUNBUFFERED 1
WORKDIR /admin_interneta_site
RUN mkdir -pv config/gunicorn
RUN mkdir /var/log/nginx/
RUN mkdir /var/log/gunicorn/
RUN mkdir /var/run/gunicorn/
RUN mkdir staticfiles
RUN apt-get update
RUN apt-get install -y default-libmysqlclient-dev libjpeg-dev python-dev
COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt -vvv
COPY . .

