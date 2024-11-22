

# Kubernetes

هناك طرق مختلفة لتشغيل OpenHands على Kubernetes أو OpenShift. يعرض هذا الدليل إحدى الطرق الممكنة:
1. إنشاء PV "كمدير للمجموعة" لربط بيانات `workspace_base` ودليل Docker بـ pod عبر العقدة العاملة.
2. إنشاء PVC لتتمكن من ربط هذه PV بالـ pod.
3. إنشاء pod يحتوي على حاويتين: حاوية OpenHands وحاوية Sandbox.

## خطوات مفصلة للمثال أعلاه

> ملاحظة: تأكد من أنك متصل بالمجموعة باستخدام الحساب المناسب لكل خطوة. إنشاء PV يتطلب صلاحيات مدير مجموعة!

> تأكد من أن لديك صلاحيات القراءة/الكتابة على `hostPath` المستخدم أدناه (أي /tmp/workspace).

1. إنشاء PV:
ملف yaml المثال أدناه يمكن أن يستخدمه مدير المجموعة لإنشاء PV.
- workspace-pv.yaml

```yaml
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
# تطبيق ملف yaml
$ oc create -f workspace-pv.yaml
persistentvolume/workspace-pv created

# التحقق:
$ oc get pv
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM                STORAGECLASS     REASON   AGE
workspace-pv                               2Gi        RWO            Retain           Available                                                  7m23s
```

- docker-pv.yaml

```yaml
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
# تطبيق ملف yaml
$ oc create -f docker-pv.yaml
persistentvolume/docker-pv created

# التحقق:
$ oc get pv
NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM                STORAGECLASS     REASON   AGE
docker-pv                                  2Gi        RWO            Retain           Available                                                  6m55s
workspace-pv                               2Gi        RWO            Retain           Available                                                  7m23s
```

2. إنشاء PVC:
مثال على ملف yaml لـ PVC أدناه:

- workspace-pvc.yaml

```yaml
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
# إنشاء الـ PVC
$ oc create -f workspace-pvc.yaml
persistentvolumeclaim/workspace-pvc created

# التحقق
$ oc get pvc
NAME            STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS     AGE
workspace-pvc   Pending                                      hcloud-volumes   4s

$ oc get events
LAST SEEN   TYPE     REASON                 OBJECT                                MESSAGE
8s          Normal   WaitForFirstConsumer   persistentvolumeclaim/workspace-pvc   waiting for first consumer to be created before binding
```

- docker-pvc.yaml

```yaml
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
# إنشاء الـ PVC
$ oc create -f docker-pvc.yaml
persistentvolumeclaim/docker-pvc created

# التحقق
$ oc get pvc
NAME            STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS     AGE
docker-pvc      Pending                                      hcloud-volumes   4s
workspace-pvc   Pending                                      hcloud-volumes   2m53s

$ oc get events
LAST SEEN   TYPE     REASON                 OBJECT                                MESSAGE
10s         Normal   WaitForFirstConsumer   persistentvolumeclaim/docker-pvc      waiting for first consumer to be created before binding
10s         Normal   WaitForFirstConsumer   persistentvolumeclaim/workspace-pvc   waiting for first consumer to be created before binding
```

3. إنشاء ملف YAML للـ Pod:
مثال على ملف YAML للـ Pod أدناه:

- pod.yaml

```yaml
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
# إنشاء الـ Pod
$ oc create -f pod.yaml
W0716 11:22:07.776271  107626 warnings.go:70] would violate PodSecurity "restricted:v1.24": allowPrivilegeEscalation != false (containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.runAsNonRoot=true), seccompProfile (pod or containers "openhands-app-2024", "openhands-sandbox-2024" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
pod/openhands-app-2024 created

# التحذير أعلاه يمكن تجاهله في الوقت الحالي لأننا لن نعدل القيود SCC.

# التحقق
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
5s          Normal   Started                  pod

/openhands-app-2024                Started container openhands-sandbox-2024
```

## متطلبات أخرى:

لربط البيانات المدمجة داخل بيئة الإنتاج الخاصة بك، قد ترغب في استخدام `StatefulSets` أو `Deployment` وأدوات أو أنظمة أخرى مثل `Helm` لجعل هذه البيئة أكثر تفاعلًا.