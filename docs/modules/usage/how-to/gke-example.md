apiVersion: apps/v1
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
        image: ghcr.io/all-hands-ai/openhands:main
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
        image: ghcr.io/opendevin/sandbox:main
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
