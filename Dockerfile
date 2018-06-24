FROM python:3.6

RUN mkdir /aws_ir
ADD . /aws_ir/
WORKDIR /aws_ir
