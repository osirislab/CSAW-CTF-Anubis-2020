#!/bin/bash

cd $(dirname $(realpath $0))


minikube kubectl -- config use-context minikube
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
docker-compose build --parallel anubis-api anubis-web assignment-1
popd

kubectl config set-context minikube
if helm list -n anubis | grep anubis &> /dev/null; then
    helm upgrade anubis . -n anubis \
         --set "imagePullPolicy=IfNotPresent" \
         --set "debug=true" \
         --set "domain=localhost" \
         --set "api.replicas=1" \
         --set "pipeline_api.replicas=1" \
         --set "web.replicas=1" \
         --set "rpc_workers.replicas=1"
else
    helm install anubis . -n anubis \
         --set "imagePullPolicy=IfNotPresent" \
         --set "debug=true" \
         --set "domain=localhost" \
         --set "api.replicas=1" \
         --set "pipeline_api.replicas=1" \
         --set "web.replicas=1" \
         --set "rpc_workers.replicas=1"
fi

kubectl rollout restart deployments.apps/anubis-api -n anubis
kubectl rollout restart deployments.apps/anubis-pipeline-api -n anubis
kubectl rollout restart deployments.apps/anubis-rpc-workers  -n anubis
