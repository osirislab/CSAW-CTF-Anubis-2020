#!/bin/bash

kubectl config use-context minikube

# remove db
helm uninstall -n mariadb mariadb

# remove anubis
helm uninstall -n anubis anubis

# give time for pvcs to yeet
kubectl delete pvc data-mariadb-0 -n mariadb
until ! kubectl get pvc -n mariadb | grep 'data-mariadb-0' &>/dev/null; do
    sleep 1
done
sleep 1

# re-install mariadb
helm install mariadb \
     --set 'auth.rootPassword=anubis' \
     --set 'volumePermissions.enabled=true' --set 'auth.username=anubis' \
     --set 'auth.database=anubis' \
     --set 'auth.password=e79c890aac3a73416fbcbb31d4f0ce0bcf277592' \
     --set 'replication.enabled=false' \
     --namespace mariadb \
     bitnami/mariadb

# re-install anubis
./kube/deploy.sh
