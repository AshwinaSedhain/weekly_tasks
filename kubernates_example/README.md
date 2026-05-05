# Kubernetes Demo – FastAPI App

This project shows how to run a simple FastAPI application on Kubernetes. It covers the core concepts you need to know: Deployments, Services, ConfigMaps, Scaling, Rolling Updates, and Self-Healing. Everything runs locally using Minikube or Kind, so  we dont need any cloud account.


## What You Need

Before starting, make sure you have Docker, kubectl, and either Minikube or Kind installed on your machine. Docker is used to build the image. kubectl is the command-line tool to talk to your cluster. Minikube or Kind gives you a local Kubernetes cluster to work with.


## Step 1 – Start Your Local Cluster

If you are using Minikube, run the following commands. The second command points your terminal's Docker to Minikube's internal Docker engine, so the image you build is available inside the cluster.

```bash
minikube start
eval $(minikube docker-env)
```

If you prefer Kind, just run:

```bash
kind create cluster --name k8s-demo
```

## Step 2 – Build the Docker Image

This command builds the app image and tags it as `fastapi-demo:v1`. Make sure you run it after the `eval` command if you are on Minikube.

```bash
docker build -t fastapi-demo:v1 .
```

## Step 3 – Deploy to Kubernetes

Apply the three manifest files in this order. The ConfigMap goes first because the Deployment depends on it.

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

## Step 4 – Check That Everything Is Running

These commands let you see what is happening inside the cluster.

```bash
# See all running pods
kubectl get pods

# See the service
kubectl get services

# Get details about the deployment
kubectl describe deployment fastapi-demo

# Read logs from a pod (replace <pod-name> with the actual name)
kubectl logs <pod-name>
```

You should see two pods with status `Running`.

## Step 5 – Open the App in Your Browser

If you are on Minikube, this command opens the app automatically:

```bash
minikube service fastapi-demo-svc
```

If you are on Kind, get the node IP with `kubectl get nodes -o wide` and then visit `http://<NODE_IP>:30080/`.

You should see this response:

```json
{ "message": "Hello from ConfigMap", "version": "v1" }
```



## Step 6 – Scale Up

Right now you have 2 pods. This command increases it to 4. Kubernetes will start the extra pods automatically.

```bash
kubectl scale deployment fastapi-demo --replicas=4
kubectl get pods -w
```

You will see two new pods appear within seconds. To scale back down, just change the number to 2.

## Step 7 – Rolling Update (v1 → v2)

First, build the v2 image:

```bash
docker build -t fastapi-demo:v2 .
```

Then apply the updated ConfigMap so the new message takes effect:

```bash
kubectl apply -f k8s/configmap-v2.yaml
```

Now tell Kubernetes to use the new image:

```bash
kubectl set image deployment/fastapi-demo fastapi-demo=fastapi-demo:v2
```

Watch the update happen without any downtime:

```bash
kubectl rollout status deployment/fastapi-demo
```

After the update, the app will return:

```json
{ "message": "Hello from ConfigMap v2 – Rolling Update complete!", "version": "v2" }
```

If something goes wrong, you can roll back with:

```bash
kubectl rollout undo deployment/fastapi-demo
```

## Step 8 – Self-Healing

Delete one of the running pods and watch Kubernetes bring it back automatically. This is self-healing in action.

```bash
kubectl delete pod <pod-name>
kubectl get pods -w
```

Within a few seconds a new pod will appear with a new name. The Deployment controller always makes sure the desired number of pods is running.

## Step 9 – Clean Up

When you are done, remove everything with these commands:

```bash
kubectl delete -f k8s/
minikube stop
```

For Kind:

```bash
kubectl delete -f k8s/
kind delete cluster --name k8s-demo
```

## API Endpoints

The app has four endpoints. `/` returns the message and version. `/version` returns just the version. `/health` is used by the liveness probe to check if the container is alive. `/ready` is used by the readiness probe to check if the container is ready to receive traffic.

## Concepts Covered

A Deployment manages your pods and keeps the desired number running at all times. A Service gives your app a stable network address so you can reach it from outside the cluster. A ConfigMap lets you store configuration separately from your code and inject it as environment variables. Scaling lets you increase or decrease the number of running pods with a single command. Rolling updates let you ship a new version without taking the app offline. Self-healing means Kubernetes automatically replaces any pod that crashes or gets deleted.
