#!/bin/sh

# set -o errexit
# set -o nounset
mkdir -p build/python
mkdir -p build/tmp
pip3 install -r ./requirements.txt -t ./build/python
pip3 install -r ./requirements_otel.txt -t ./build/tmp
pip3 freeze --path ./build/python
cp -r ./build/tmp/* ./build/python/
rm -rf ./build/tmp
cp -R asserts_pylambda ./build/python
cp asserts_wrapper.py ./build/python
cp asserts_wrapper ./build/python
rm -rf ./build/python/boto*
rm -rf ./build/python/urllib3*
cd build
zip -r ../asserts-aws-lambda-layer-py-${VERSION}.zip ./python
cd ..
chmod 755 asserts-wrapper
zip -g asserts-aws-lambda-layer-py-${VERSION}.zip asserts-wrapper
rm -fR build
