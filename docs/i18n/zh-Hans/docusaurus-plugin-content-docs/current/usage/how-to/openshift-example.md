以下是翻译后的内容:

# Kubernetes

在 Kubernetes 或 OpenShift 上运行 OpenHands 有不同的方式。本指南介绍了一种可能的方式:
1. 作为集群管理员,创建一个 PV 将 workspace_base 数据和 docker 目录映射到 worker 节点上的 pod
2. 创建一个 PVC 以便将这些 PV 挂载到 pod
3. 创建一个包含两个容器的 pod:OpenHands 和 Sandbox 容器

## 上述示例的详细步骤

> 注意:确保首先使用适当的帐户登录到集群以执行每个步骤。创建 PV 需要集群管理员权限!

> 确保你对下面使用的 hostPath(即 /tmp/workspace)有读写权限

1. 创建 PV:
集群管理员可以使用下面的示例 yaml 文件创建 PV。
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
# 应用 yaml 文件
$ oc create -f workspace-pv.yaml
persistentvolume/workspace-pv created

# 查看:
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
# 应用 yaml 文件
$ oc create -f docker-pv.yaml
persistentvolume/docker-pv created

# 查看:
oc get pv
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM                STORAGECLASS     REASON   AGE
docker-pv                                  2Gi        RWO            Retain           Available                                                  6m55s
workspace-pv                               2Gi        RWO            Retain           Available                                                  7m23s
```

2. 创建 PVC:
下面是示例 PVC yaml 文件:

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
# 创建 pvc
$ oc create -f workspace-pvc.yaml
persistentvolumeclaim/workspace-pvc created

# 查看
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
# 创建 pvc
$ oc create -f docker-pvc.yaml
persistentvolumeclaim/docker-pvc created

# 查看
$ oc get pvc
NAME            STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS     AGE
docker-pvc      Pending                                      hcloud-volumes   4s
workspace-pvc   Pending                                      hcloud-volumes   2m53s

$ oc get events
LAST SEEN   TYPE     REASON                 OBJECT                                MESSAGE
10s         Normal   WaitForFirstConsumer   persistentvolumeclaim/docker-pvc      waiting for first consumer to be created before binding
10s         Normal   WaitForFirstConsumer   persistentvolumeclaim/workspace-pvc   waiting for first consumer to be created before binding
```

3. 创建 pod yaml 文件:
下面是示例 pod yaml 文件:

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
    image: ghcr.io/all-hands-ai/openhands:main
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
    image: ghcr.io/all-hands-ai/sandbox:main
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
# 创建 pod
$ oc create -f pod.yaml
W0716 11:22:07.776271  107626 warnings.go:70] would violate PodSecurity "restricted:v1.24": allowPrivilegeEscalation != false (containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.runAsNonRoot=true), seccompProfile (pod or containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
pod/openhands-app-2024 created

# 上面的警告可以暂时忽略,因为我们不会修改 SCC 限制。

# 查看
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
6s          Normal   Pulled                   pod/openhands-app-2024                Container image "ghcr.io/all-hands-ai/openhands:main" already present on machine
6s          Normal   Created                  pod/openhands-app-2024                Created container openhands-app-2024
6s          Normal   Started                  pod/openhands-app-2024                Started container openhands-app-2024
6s          Normal   Pulled                   pod/openhands-app-2024                Container image "ghcr.io/all-hands-ai/sandbox:main" already present on machine
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

4. 创建一个 NodePort 服务。
下面是示例服务创建命令:

```bash
# 创建 NodePort 类型的服务
$ oc create svc nodeport  openhands-app-2024  --tcp=3000:3000
service/openhands-app-2024 created

# 查看

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

6. 连接到 OpenHands UI,配置 Agent,然后测试:

![image](https://github.com/user-attachments/assets/12f94804-a0c7-4744-b873-e003c9caf40e)



## GCP GKE OpenHands 部署

**警告**:此部署授予 OpenHands 应用程序访问 Kubernetes docker socket 的权限,这会带来安全风险。请自行决定是否使用。
1- 创建特权访问策略
2- 创建 gke 凭证(可选)
3- 创建 openhands 部署
4- 验证和 UI 访问命令
5- 排查 pod 以验证内部容器

1. 创建特权访问策略
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
  name: default  # 更改为你的服务帐户名称
  namespace: default
```
2. 创建 gke 凭证(可选)
```bash
kubectl create secret generic google-cloud-key \
  --from-file=key.json=/path/to/your/google-cloud-key.json
  ```
3. 创建 openhands 部署
## 由于这是针对单个工作节点进行测试的,如果你有多个节点,请指定单个工作节点的标志

```bash
kind: Deployment
metadata:
  name: openhands-app-2024
  labels:
    app: openhands-app-2024
spec:
  replicas: 1  # 你可以增加这个数字以获得多个副本
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
        image: ghcr.io/all-hands-ai/openhands:main
        env:
        - name: SANDBOX_USER_ID
          value: "1000"
        - name: SANDBOX_API
