#!/bin/sh

# set -o errexit
# set -o nounset
mkdir -p build/python
pip3 install -t ./build/python prometheus-client
cp -R asserts_pylambda ./build/python
cd build
zip -r ../asserts-aws-lambda-layer-py-${VERSION}.zip ./python
cd ..
chmod 755 asserts-wrapper
zip -g asserts-aws-lambda-layer-py-${VERSION}.zip asserts-wrapper
zip -g asserts-aws-lambda-layer-py-${VERSION}.zip asserts_wrapper.py
rm -fR build
