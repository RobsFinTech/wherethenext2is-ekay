FROM python:3.11.5
COPY requirements.txt /
RUN pip install -r requirements.txt
CMD python main.py