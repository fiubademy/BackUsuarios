FROM ubuntu
RUN apt-get -y update 
RUN apt-get -y install python3
RUN apt-get -y install python3-pip
RUN pip3 install uvicorn
RUN pip3 install fastapi
RUN pip3 install sqlalchemy
RUN pip3 install email-validator
RUN pip3 install psycopg2-binary
WORKDIR /app
EXPOSE 8000
COPY Commands.sh /app/
COPY UserService/UserService.py /app/
CMD ./Commands.sh

