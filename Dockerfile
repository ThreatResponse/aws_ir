FROM python:3-onbuild

RUN mkdir /aws_ir

COPY requirements.txt /aws_ir/requirements.txt

RUN pip install --upgrade pip

ADD . /aws_ir/

WORKDIR /aws_ir
