#!/bin/sh


cd $(dirname $(realpath $0))

minikube delete
./kube/provision.sh
./kube/deploy.sh

