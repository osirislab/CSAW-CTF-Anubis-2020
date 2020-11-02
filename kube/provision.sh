#!/bin/sh

# set -e

cd $(dirname $(realpath $0))

echo 'This script will provision your cluster for debugging'

if ! minikube status | grep 'kubelet: Running' &> /dev/null; then
    echo 'staring minikube...' 1>&2
    minikube start \
             --feature-gates=TTLAfterFinished=true \
             --ports=80:80,443:443 \
             --network-plugin=cni \
             --cni=calico \
             --cpus=$(( $(nproc) - 2 )) \
             --memory=$(free -m | grep mem -i | awk '{print ($2)-2000}')
    sleep 1
fi

if ! kubectl config current-context | grep 'minikube' &> /dev/null; then
    echo 'Setting context to minikube' 1>&2
    kubectl config use-context minikube
fi

echo 'Adding traefik ingress label to minikube node...'
kubectl label node minikube traefik=ingress --overwrite

echo 'Adding networking label to kube-system namespace...'
kubectl label ns kube-system networking/namespace=kube-system --overwrite

echo 'Adding traefik resources...'
kubectl apply -f ./traefik.yml

helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

echo 'Adding mariadb'
kubectl create namespace mariadb
helm install mariadb \
     --set 'auth.rootPassword=anubis' \
     --set 'volumePermissions.enabled=true' --set 'auth.username=anubis' \
     --set 'auth.database=anubis' \
     --set 'auth.password=e79c890aac3a73416fbcbb31d4f0ce0bcf277592' \
     --set 'replication.enabled=false' \
     --namespace mariadb \
     bitnami/mariadb

if ! kubectl get secret -n anubis flag &> /dev/null; then
    kubectl create ns anubis
    kubectl create secret generic flag -n anubis --from-literal=flag='flag{memenetes_b6ce000dd1}'
fi

