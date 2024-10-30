

# Kubernetes

Il existe différentes façons d'exécuter OpenHands sur Kubernetes ou OpenShift. Ce guide présente une façon possible :
1. Créer un PV "en tant qu'administrateur du cluster" pour mapper les données workspace_base et le répertoire docker au pod via le nœud worker
2. Créer un PVC pour pouvoir monter ces PV sur le pod
3. Créer un pod qui contient deux conteneurs : les conteneurs OpenHands et Sandbox

## Étapes détaillées pour l'exemple ci-dessus

> Remarque : Assurez-vous d'être connecté au cluster avec le compte approprié pour chaque étape. La création de PV nécessite un administrateur de cluster !

> Assurez-vous d'avoir les autorisations de lecture/écriture sur le hostPath utilisé ci-dessous (c'est-à-dire /tmp/workspace)

1. Créer le PV :
Le fichier yaml d'exemple ci-dessous peut être utilisé par un administrateur de cluster pour créer le PV.
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
# appliquer le fichier yaml
$ oc create -f workspace-pv.yaml
persistentvolume/workspace-pv created

# vérifier :
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
# appliquer le fichier yaml
$ oc create -f docker-pv.yaml
persistentvolume/docker-pv created

# vérifier :
oc get pv
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM                STORAGECLASS     REASON   AGE
docker-pv                                  2Gi        RWO            Retain           Available                                                  6m55s
workspace-pv                               2Gi        RWO            Retain           Available                                                  7m23s
```

2. Créer le PVC :
Exemple de fichier yaml PVC ci-dessous :

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
# créer le pvc
$ oc create -f workspace-pvc.yaml
persistentvolumeclaim/workspace-pvc created

# vérifier
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
# créer le pvc
$ oc create -f docker-pvc.yaml
persistentvolumeclaim/docker-pvc created

# vérifier
$ oc get pvc
NAME            STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS     AGE
docker-pvc      Pending                                      hcloud-volumes   4s
workspace-pvc   Pending                                      hcloud-volumes   2m53s

$ oc get events
LAST SEEN   TYPE     REASON                 OBJECT                                MESSAGE
10s         Normal   WaitForFirstConsumer   persistentvolumeclaim/docker-pvc      waiting for first consumer to be created before binding
10s         Normal   WaitForFirstConsumer   persistentvolumeclaim/workspace-pvc   waiting for first consumer to be created before binding
```

3. Créer le fichier yaml du pod :
Exemple de fichier yaml de pod ci-dessous :

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
# créer le pod
$ oc create -f pod.yaml
W0716 11:22:07.776271  107626 warnings.go:70] would violate PodSecurity "restricted:v1.24": allowPrivilegeEscalation != false (containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.runAsNonRoot=true), seccompProfile (pod or containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
pod/openhands-app-2024 created

# L'avertissement ci-dessus peut être ignoré pour l'instant car nous ne modifierons pas les restrictions SCC.

# vérifier
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

4. Créer un service NodePort.
Exemple de commande de création de service ci-dessous :

```bash
# créer le service de type NodePort
$ oc create svc nodeport  openhands-app-2024  --tcp=3000:3000
service/openhands-app-2024 created

# vérifier

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

6. Se connecter à l'interface utilisateur d'OpenHands, configurer l'Agent, puis tester :

![image](https://github.com/user-attachments/assets/12f94804-a0c7-4744-b873-e003c9caf40e)



## Déploiement d'Openhands sur GCP GKE

**Avertissement** : ce déploiement accorde à l'application OpenHands l'accès au socket docker de Kubernetes, ce qui crée un risque de sécurité. Utilisez à vos propres risques.
1- Créer une politique pour l'accès privilégié
2- Créer des informations d'identification gke (facultatif)
3- Créer le déploiement openhands
4- Commandes de vérification et d'accès à l'interface utilisateur
5- Dépanner le pod pour vérifier le conteneur interne

1. créer une politique pour l'accès privilégié
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
  name: default  # Remplacez par le nom de votre compte de service
  namespace: default
```
2. créer des informations d'identification gke (facultatif)
```bash
kubectl create secret generic google-cloud-key \
  --from-file=key.json=/path/to/your/google-cloud-key.json
  ```
3. créer le déploiement openhands
## comme cela est testé pour le nœud worker unique, si vous en avez plusieurs, spécifiez l'indicateur pour le worker unique

```bash
kind: Deployment
metadata:
  name: openhands-app-2024
  labels:
    app: openhands-app-2024
spec:
  replicas: 1  # Vous pouvez augmenter ce nombre pour plusieurs réplicas
  selector:
    matchLabels:
      app: openhands-app-2024
  template:
    metadata:
      labels:
        app: openhands-app-2024
    spec:
      containers:
      -
