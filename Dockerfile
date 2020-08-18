FROM python:3.7

RUN apt-get update && \
      apt-get -y install sudo
RUN sudo apt-get -y install libgl1-mesa-glx

RUN pip install flask
RUN pip install flask_limiter
RUN pip install opencv-python
RUN pip install Pillow
RUN pip install requests

COPY . .

EXPOSE 8000

CMD python3 server.py
