#!/bin/sh

set -e

cd $(dirname $(realpath $0))

docker build -t assignment-1:latest .

