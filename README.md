# Anubis

### Overview

### Solve

I hand everyone rce in c++ in a locked down submissions pod. Those pods have network policies that lock them to connecting to an internal reporting api and redis. If they look at the keys and stuff that are in redis, they should easily see that there is rq running for rpc. They can then just throw a job into redis, and let a worker pick it up. The rq workers have a misconfigured service account that they can use to read the flag kube secret from the kubernetes api.

At pretty much each step, you need to poke around at the files that you can see to figure out what other services are running.

submission pipeline -> redis -> rq worker -> kubernetes rest api

### Flag

```
flag{memenetes_b6ce000dd1}
```
