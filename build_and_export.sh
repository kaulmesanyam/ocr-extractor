#!/bin/bash
set -e

IMAGE_NAME="policy-extractor"
TAR_NAME="policy-extractor.tar"

echo "Building Docker image for platform linux/amd64..."
# Using buildx to ensure we can build for amd64 even on arm64 macs
docker buildx build --platform linux/amd64 -t ${IMAGE_NAME}:latest --load .

echo "Saving image to ${TAR_NAME}..."
docker save -o ${TAR_NAME} ${IMAGE_NAME}:latest

echo "Done!"
echo "--------------------------------------------------------"
echo "To run this on the EC2 instance:"
echo "1. Copy ${TAR_NAME} to the EC2 instance."
echo "2. Load the image:"
echo "   docker load -i ${TAR_NAME}"
echo "3. Run the container (assuming .env file is in the current directory):"
echo "   docker run -d -p 8000:8000 --env-file .env ${IMAGE_NAME}:latest"
echo "--------------------------------------------------------"
