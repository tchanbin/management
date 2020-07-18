FROM python:3.7.5

ENV FLASK_APP manage.py
ENV FLASK_CONFIG production
ENV FLASK_code mycode

COPY requirements.txt requirements.txt
RUN python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple some-package

RUN pip --default-timeout=100 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
COPY management management
COPY migrations migrations
COPY config.py manage.py boot.sh ./

RUN touch boot.sh
EXPOSE 6000

ENTRYPOINT ["sh","./boot.sh"]
