#!/bin/bash

DOMAIN="autograder.chal.csaw.io"

set -e
cd $(dirname $(realpath $0))

kubectl config set-context minikube
eval $(minikube -p minikube docker-env)

if ! minikube kubectl -- get namespace | grep anubis &> /dev/null; then
    minikube kubectl -- create namespace anubis
fi

if ! minikube kubectl -- get secrets -n anubis | grep api &> /dev/null; then
    minikube kubectl -- create secret generic api \
             --from-literal=database-uri=mysql+pymysql://anubis:e79c890aac3a73416fbcbb31d4f0ce0bcf277592@mariadb.mariadb.svc.cluster.local/anubis \
             --from-literal=secret-key=$(head -c10 /dev/urandom | openssl sha1 -hex | awk '{print $2}') \
             -n anubis
fi



pushd ..
docker-compose build --parallel api web
popd

../assignment/build.sh

if helm list -n anubis | grep anubis &> /dev/null; then
    helm upgrade anubis . -n anubis \
         --set "debug=false" \
         --set "imagePullPolicy=IfNotPresent" \
         --set "domain=${DOMAIN}"
else
    helm install anubis . -n anubis \
         --set "debug=false" \
         --set "imagePullPolicy=IfNotPresent" \
         --set "domain=${DOMAIN}"
fi


