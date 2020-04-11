FROM python:3.7.5

ENV FLASK_APP manage.py
ENV FLASK_CONFIG production



COPY requirements requirements
RUN python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple some-package

RUN pip --default-timeout=100 install -r requirements/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple some-package
COPY management management
COPY migrations migrations
COPY config.py manage.py boot.sh ./

# run-time configuration
EXPOSE 5000

ENTRYPOINT ["./boot.sh"]
