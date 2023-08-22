#!/bin/sh

COMMIT_HASH="$(git rev-parse --short HEAD)"
export COMMIT_HASH

COMMIT_FULL_HASH="$(git rev-parse HEAD)"
export COMMIT_FULL_HASH

sed -i '' "s/__layer_version__/$COMMIT_HASH/g" asserts_pylambda/LambdaMetrics.py

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
zip -r ../asserts-aws-lambda-layer-py-${COMMIT_HASH}.zip ./python
cd ..
chmod 755 asserts-wrapper
zip -g asserts-aws-lambda-layer-py-${COMMIT_HASH}.zip asserts-wrapper
rm -fR build

sed -i '' "s/$COMMIT_HASH/__layer_version__/g" asserts_pylambda/LambdaMetrics.py

aws s3 cp "asserts-aws-lambda-layer-py-$COMMIT_HASH.zip" s3://asserts-lambda-layers

LAYER_VERSION=$(aws lambda publish-layer-version --no-paginate --no-cli-pager --output json --layer-name asserts-aws-lambda-layer-py \
  --description "Asserts AWS Lambda Layer for Python created from asserts-aws-lambda-layer-py-$COMMIT_HASH" \
  --compatible-runtimes "python3.7" "python3.8" "python3.9" "python3.8" \
  --content "S3Bucket=asserts-lambda-layers,S3Key=asserts-aws-lambda-layer-py-$COMMIT_HASH.zip" | jq '.Version')
export LAYER_VERSION

aws lambda add-layer-version-permission --no-paginate --no-cli-pager --layer-name asserts-aws-lambda-layer-py \
  --statement-id ReadPublic --action lambda:GetLayerVersion  --principal "*" --version-number "${LAYER_VERSION}" --output json
