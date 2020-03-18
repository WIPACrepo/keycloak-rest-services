#!/bin/sh
FILE=$1
docker run --rm -it -v $PWD:/opt circleci/python:3.8 sh -c "PYTHONPATH=/opt/lib python /opt/$FILE"
