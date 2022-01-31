#!/bin/sh

# set -o errexit
# set -o nounset
mkdir -p build/python
pip3 install -t ./build/python prometheus-client
pip3 install -t ./build/python boto3
cp -R asserts_pylambda ./build/python
cd build
zip -r ../asserts-sdk-python-1.0.0.zip ./python
cd ..
rm -fR build
