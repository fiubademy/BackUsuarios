FROM ubuntu
RUN apt-get -y update 
RUN apt-get -y install python3
RUN apt-get -y install python3-pip
RUN pip3 install uvicorn
RUN pip3 install fastapi
RUN pip3 install email-validator
WORKDIR /app
EXPOSE 8000
COPY Commands.sh /app/
COPY service/. /app/
CMD ./Commands.sh

