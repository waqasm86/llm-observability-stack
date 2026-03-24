# kubectl command catalog (llm-observability focus)

This catalog consolidates high-value `kubectl` command patterns mapped to Kubernetes-in-Action domains and your local stack.

## Cluster and API discovery

```bash
kubectl version
kubectl cluster-info
kubectl config current-context
kubectl config get-contexts
kubectl api-versions
kubectl api-resources --sort-by=name
kubectl explain pod.spec
kubectl explain deployment.spec.strategy
kubectl explain service.spec
```

## Namespace and core workloads

```bash
kubectl get ns --show-labels
kubectl -n llm-observability get all
kubectl -n llm-observability get deploy,rs,sts,ds,pod,job,cronjob -o wide
kubectl -n llm-observability describe deploy/langchain-demo
kubectl -n llm-observability rollout status deploy/open-webui
kubectl -n llm-observability rollout status sts/ollama
```

## Pod lifecycle and debugging

```bash
kubectl -n llm-observability get pods -o wide
kubectl -n llm-observability describe pod/<pod-name>
kubectl -n llm-observability logs <pod-name> --all-containers --tail=200
kubectl -n llm-observability exec -it <pod-name> -- sh
kubectl -n llm-observability cp <pod-name>:/path/in/pod ./local-path
kubectl -n llm-observability debug -it <pod-name> --image=busybox:1.36 --target=<container>
kubectl -n llm-observability get events --sort-by=.metadata.creationTimestamp
kubectl top nodes
kubectl -n llm-observability top pods
```

## ConfigMaps and Secrets

```bash
kubectl -n llm-observability get cm,secret
kubectl -n llm-observability describe cm/ollama-local-modelfile
kubectl -n llm-observability create configmap demo-cm --from-literal=mode=dev --dry-run=client -o yaml
kubectl -n llm-observability create secret generic demo-secret --from-literal=token=replace-me --dry-run=client -o yaml
kubectl -n llm-observability get secret -o go-template='{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}'
```

## Storage

```bash
kubectl get storageclass
kubectl get pv
kubectl -n llm-observability get pvc -o wide
kubectl -n llm-observability describe pvc/<claim-name>
kubectl get volumeattachments.storage.k8s.io
```

## Networking core

```bash
kubectl -n llm-observability get svc -o wide
kubectl -n llm-observability get endpoints,endpointslices.discovery.k8s.io
kubectl -n llm-observability describe svc/open-webui
kubectl -n llm-observability get ingress
kubectl -n llm-observability get networkpolicy
kubectl -n llm-observability port-forward svc/open-webui 8080:8080
kubectl -n llm-observability port-forward svc/ollama 11434:11434
kubectl -n llm-observability port-forward svc/langchain-demo 8000:8000
```

## Networking advanced / gateway API

```bash
kubectl get gatewayclass
kubectl get gateway -A
kubectl get httproute -A
kubectl get tcproute -A
kubectl get referencegrant -A
kubectl -n kube-system get pods -o wide
kubectl get nodes -o wide
```

## Security and RBAC

```bash
kubectl -n llm-observability get sa
kubectl -n llm-observability get role,rolebinding
kubectl get clusterrole,clusterrolebinding
kubectl auth can-i get pods -n llm-observability
kubectl auth can-i --as=system:serviceaccount:llm-observability:default list secrets -n llm-observability
```

## Batch workloads

```bash
kubectl -n llm-observability get jobs,cronjobs
kubectl -n llm-observability describe job/<job-name>
kubectl -n llm-observability logs job/<job-name>
```

## Node operations (use carefully)

```bash
kubectl cordon <node-name>
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
kubectl uncordon <node-name>
kubectl taint nodes <node-name> key=value:NoSchedule
```

## Apply/patch patterns

```bash
kubectl -n llm-observability apply -f file.yaml
kubectl -n llm-observability delete -f file.yaml
kubectl -n llm-observability patch deploy/open-webui --type merge -p '{"spec":{"replicas":1}}'
kubectl -n llm-observability set image deploy/langchain-demo langchain-demo=langchain-demo:0.1.1
kubectl -n llm-observability scale deploy/langchain-demo --replicas=1
```
