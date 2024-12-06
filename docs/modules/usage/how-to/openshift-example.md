# Kubernetes

There are different ways you might run OpenHands on Kubernetes or OpenShift. This guide goes through one possible way:
1. Create a PV "as a cluster admin" to map workspace_base data and docker directory to the pod through the worker node
2. Create a PVC to be able to mount those PVs to the pod
3. Create a pod which contains two containers; the OpenHands and Sandbox containers

## Detailed Steps for the Example Above

> Note: Make sure you are logged in to the cluster first with the proper account for each step. PV creation requires cluster administrator!

> Make sure you have read/write permissions on the hostPath used below (i.e. /tmp/workspace)

1. Create the PV:
Sample yaml file below can be used by a cluster admin to create the PV.
- workspace-pv.yaml

```yamlfile
apiVersion: v1
kind: PersistentVolume
metadata:
  name: workspace-pv
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /tmp/workspace
```

```bash
# apply yaml file
$ oc create -f workspace-pv.yaml
persistentvolume/workspace-pv created

# review:
$ oc get pv
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM                STORAGECLASS     REASON   AGE
workspace-pv                               2Gi        RWO            Retain           Available                                                  7m23s
```

- docker-pv.yaml

```yamlfile
apiVersion: v1
kind: PersistentVolume
metadata:
  name: docker-pv
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /var/run/docker.sock
```

```bash
# apply yaml file
$ oc create -f docker-pv.yaml
persistentvolume/docker-pv created

# review:
oc get pv
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM                STORAGECLASS     REASON   AGE
docker-pv                                  2Gi        RWO            Retain           Available                                                  6m55s
workspace-pv                               2Gi        RWO            Retain           Available                                                  7m23s
```

2. Create the PVC:
Sample PVC yaml file below:

- workspace-pvc.yaml

```yamlfile
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: workspace-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

```bash
# create the pvc
$ oc create -f workspace-pvc.yaml
persistentvolumeclaim/workspace-pvc created

# review
$ oc get pvc
NAME            STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS     AGE
workspace-pvc   Pending                                      hcloud-volumes   4s

$ oc get events
LAST SEEN   TYPE     REASON                 OBJECT                                MESSAGE
8s          Normal   WaitForFirstConsumer   persistentvolumeclaim/workspace-pvc   waiting for first consumer to be created before binding
```

- docker-pvc.yaml

```yamlfile
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: docker-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

```bash
# create pvc
$ oc create -f docker-pvc.yaml
persistentvolumeclaim/docker-pvc created

# review
$ oc get pvc
NAME            STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS     AGE
docker-pvc      Pending                                      hcloud-volumes   4s
workspace-pvc   Pending                                      hcloud-volumes   2m53s

$ oc get events
LAST SEEN   TYPE     REASON                 OBJECT                                MESSAGE
10s         Normal   WaitForFirstConsumer   persistentvolumeclaim/docker-pvc      waiting for first consumer to be created before binding
10s         Normal   WaitForFirstConsumer   persistentvolumeclaim/workspace-pvc   waiting for first consumer to be created before binding
```

3. Create the pod yaml file:
Sample pod yaml file below:

- pod.yaml

```yamlfile
apiVersion: v1
kind: Pod
metadata:
  name: openhands-app-2024
  labels:
    app: openhands-app-2024
spec:
  containers:
  - name: openhands-app-2024
    image: docker.all-hands.dev/all-hands-ai/openhands:main
    env:
    - name: SANDBOX_USER_ID
      value: "1000"
    - name: WORKSPACE_MOUNT_PATH
      value: "/opt/workspace_base"
    volumeMounts:
    - name: workspace-volume
      mountPath: /opt/workspace_base
    - name: docker-sock
      mountPath: /var/run/docker.sock
    ports:
    - containerPort: 3000
  - name: openhands-sandbox-2024
    image: docker.all-hands.dev/all-hands-ai/runtime:main
    ports:
    - containerPort: 51963
    command: ["/usr/sbin/sshd", "-D", "-p 51963", "-o", "PermitRootLogin=yes"]
  volumes:
  - name: workspace-volume
    persistentVolumeClaim:
      claimName: workspace-pvc
  - name: docker-sock
    persistentVolumeClaim:
      claimName: docker-pvc
```


```bash
# create the pod
$ oc create -f pod.yaml
W0716 11:22:07.776271  107626 warnings.go:70] would violate PodSecurity "restricted:v1.24": allowPrivilegeEscalation != false (containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.runAsNonRoot=true), seccompProfile (pod or containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
pod/openhands-app-2024 created

# Above warning can be ignored for now as we will not modify SCC restrictions.

# review
$ oc get pods
NAME                 READY   STATUS    RESTARTS   AGE
openhands-app-2024   0/2     Pending   0          5s

$ oc get pods
NAME                 READY   STATUS              RESTARTS   AGE
openhands-app-2024   0/2     ContainerCreating   0          15s

$ oc get events
LAST SEEN   TYPE     REASON                   OBJECT                                MESSAGE
38s         Normal   WaitForFirstConsumer     persistentvolumeclaim/docker-pvc      waiting for first consumer to be created before binding
23s         Normal   ExternalProvisioning     persistentvolumeclaim/docker-pvc      waiting for a volume to be created, either by external provisioner "csi.hetzner.cloud" or manually created by system administrator
27s         Normal   Provisioning             persistentvolumeclaim/docker-pvc      External provisioner is provisioning volume for claim "openhands/docker-pvc"
17s         Normal   ProvisioningSucceeded    persistentvolumeclaim/docker-pvc      Successfully provisioned volume pvc-2b1d223a-1c8f-4990-8e3d-68061a9ae252
16s         Normal   Scheduled                pod/openhands-app-2024                Successfully assigned All-Hands-AI/OpenHands-app-2024 to worker1.hub.internal.blakane.com
9s          Normal   SuccessfulAttachVolume   pod/openhands-app-2024                AttachVolume.Attach succeeded for volume "pvc-2b1d223a-1c8f-4990-8e3d-68061a9ae252"
9s          Normal   SuccessfulAttachVolume   pod/openhands-app-2024                AttachVolume.Attach succeeded for volume "pvc-31f15b25-faad-4665-a25f-201a530379af"
6s          Normal   AddedInterface           pod/openhands-app-2024                Add eth0 [10.128.2.48/23] from openshift-sdn
6s          Normal   Pulled                   pod/openhands-app-2024                Container image "docker.all-hands.dev/all-hands-ai/openhands:main" already present on machine
6s          Normal   Created                  pod/openhands-app-2024                Created container openhands-app-2024
6s          Normal   Started                  pod/openhands-app-2024                Started container openhands-app-2024
6s          Normal   Pulled                   pod/openhands-app-2024                Container image "docker.all-hands.dev/all-hands-ai/sandbox:main" already present on machine
5s          Normal   Created                  pod/openhands-app-2024                Created container openhands-sandbox-2024
5s          Normal   Started                  pod/openhands-app-2024                Started container openhands-sandbox-2024
83s         Normal   WaitForFirstConsumer     persistentvolumeclaim/workspace-pvc   waiting for first consumer to be created before binding
27s         Normal   Provisioning             persistentvolumeclaim/workspace-pvc   External provisioner is provisioning volume for claim "openhands/workspace-pvc"
17s         Normal   ProvisioningSucceeded    persistentvolumeclaim/workspace-pvc   Successfully provisioned volume pvc-31f15b25-faad-4665-a25f-201a530379af

$ oc get pods
NAME                 READY   STATUS    RESTARTS   AGE
openhands-app-2024   2/2     Running   0          23s

$ oc get pvc
NAME            STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS     AGE
docker-pvc      Bound    pvc-2b1d223a-1c8f-4990-8e3d-68061a9ae252   10Gi       RWO            hcloud-volumes   10m
workspace-pvc   Bound    pvc-31f15b25-faad-4665-a25f-201a530379af   10Gi       RWO            hcloud-volumes   13m

```

4. Create a NodePort service.
Sample service creation command below:

```bash
# create the service of type NodePort
$ oc create svc nodeport  openhands-app-2024  --tcp=3000:3000
service/openhands-app-2024 created

# review

$ oc get svc
NAME                 TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
openhands-app-2024   NodePort   172.30.225.42   <none>        3000:30495/TCP   4s

$ oc describe svc openhands-app-2024
Name:                     openhands-app-2024
Namespace:                openhands
Labels:                   app=openhands-app-2024
Annotations:              <none>
Selector:                 app=openhands-app-2024
Type:                     NodePort
IP Family Policy:         SingleStack
IP Families:              IPv4
IP:                       172.30.225.42
IPs:                      172.30.225.42
Port:                     3000-3000  3000/TCP
TargetPort:               3000/TCP
NodePort:                 3000-3000  30495/TCP
Endpoints:                10.128.2.48:3000
Session Affinity:         None
External Traffic Policy:  Cluster
Events:                   <none>
```

6. Connect to OpenHands UI, configure the Agent, then test:

![image](https://github.com/user-attachments/assets/12f94804-a0c7-4744-b873-e003c9caf40e)



## GCP GKE Openhands deployment

**Warning**: this deployment grants the OpenHands application access to the Kubernetes docker socket, which creates security risk. Use at your own discretion.
1- Create policy for privillege access
2- Create gke credentials(optional)
3- Create openhands deployment
4- Verification and ui access commands
5- Tshoot pod to verify the internal container

1. create policy for privillege access
```bash
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: privileged-role
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["create", "get", "list", "watch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["create", "get", "list", "watch", "delete"]
- apiGroups: [""]
  resources: ["pods/exec"]
  verbs: ["create"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: privileged-role-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: privileged-role
subjects:
- kind: ServiceAccount
  name: default  # Change to your service account name
  namespace: default
```
2. create gke credentials(optional)
```bash
kubectl create secret generic google-cloud-key \
  --from-file=key.json=/path/to/your/google-cloud-key.json
  ```
3. create openhands deployment
## as this is tested for the single worker node if you have multiple specify the flag for the single worker

```bash
kind: Deployment
metadata:
  name: openhands-app-2024
  labels:
    app: openhands-app-2024
spec:
  replicas: 1  # You can increase this number for multiple replicas
  selector:
    matchLabels:
      app: openhands-app-2024
  template:
    metadata:
      labels:
        app: openhands-app-2024
    spec:
      containers:
      - name: openhands-app-2024
        image: docker.all-hands.dev/all-hands-ai/openhands:main
        env:
        - name: SANDBOX_USER_ID
          value: "1000"
        - name: SANDBOX_API_HOSTNAME
          value: '10.164.0.4'
        - name: WORKSPACE_MOUNT_PATH
          value: "/tmp/workspace_base"
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: "/tmp/workspace_base/google-cloud-key.json"
        volumeMounts:
        - name: workspace-volume
          mountPath: /tmp/workspace_base
        - name: docker-sock
          mountPath: /var/run/docker.sock
        - name: google-credentials
          mountPath: "/tmp/workspace_base/google-cloud-key.json"
        securityContext:
          privileged: true  # Add this to allow privileged access
        ports:
        - containerPort: 3000
      - name: openhands-sandbox-2024
        image: docker.all-hands.dev/all-hands-ai/runtime:main
    #    securityContext:
    #      privileged: true  # Add this to allow privileged access
        ports:
        - containerPort: 51963
        command: ["/usr/sbin/sshd", "-D", "-p 51963", "-o", "PermitRootLogin=yes"]
      volumes:
      #- name: workspace-volume
      #  persistentVolumeClaim:
      #    claimName: workspace-pvc
      - name: workspace-volume
        emptyDir: {}
      - name: docker-sock
        hostPath:
          path: /var/run/docker.sock       # Use host's Docker socket
          type: Socket
      - name: google-credentials
        secret:
          secretName: google-cloud-key
---
apiVersion: v1
kind: Service
metadata:
  name: openhands-app-2024-svc
spec:
  selector:
    app: openhands-app-2024
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 3000
  - name: ssh
    protocol: TCP
    port: 51963
    targetPort: 51963
  type: LoadBalancer
  ```

5. Tshoot pod to verify the internal container
### if you want to know more regarding the internal container runtime use below mention pod deployment use kubectl exec -it to enter into container and you can check the contaienr run time using normal docker commands like "docker ps -a"

```bash
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docker-in-docker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: docker-in-docker
  template:
    metadata:
      labels:
        app: docker-in-docker
    spec:
      containers:
      - name: dind
        image: docker:20.10-dind
        securityContext:
          privileged: true
        volumeMounts:
        - name: docker-sock
          mountPath: /var/run/docker.sock
      volumes:
      - name: docker-sock
        hostPath:
          path: /var/run/docker.sock
          type: Socket
```
