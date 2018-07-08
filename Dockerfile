FROM python:3.4

RUN mkdir /aws_ir
ADD . /aws_ir/
WORKDIR /aws_ir
