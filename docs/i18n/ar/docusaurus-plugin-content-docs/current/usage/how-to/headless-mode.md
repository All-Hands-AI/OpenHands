

# وضع بدون واجهة

يمكنك تشغيل OpenHands باستخدام أمر واحد، دون الحاجة لتشغيل التطبيق على الويب.  
يتيح ذلك كتابة السكربتات وأتمتة المهام باستخدام OpenHands.

هذا يختلف عن [وضع CLI](cli-mode)، الذي يكون تفاعليًا وأكثر ملاءمة للتطوير النشط.

## مع Python

لتشغيل OpenHands في وضع بدون واجهة باستخدام Python،  
[اتبع تعليمات إعداد التطوير](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)،  
ثم نفذ الأمر التالي:

```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

ستحتاج إلى التأكد من تحديد النموذج الخاص بك، مفتاح API، والإعدادات الأخرى عبر المتغيرات البيئية  
[أو من خلال ملف `config.toml`](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml).

## مع Docker

1. حدد `WORKSPACE_BASE` على الدليل الذي تريد أن يقوم OpenHands بتعديله عليه:

```bash
WORKSPACE_BASE=$(pwd)/workspace
```

2. حدد `LLM_MODEL` على النموذج الذي ترغب في استخدامه:

```bash
LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"
```

3. حدد `LLM_API_KEY` على مفتاح API الخاص بك:

```bash
LLM_API_KEY="sk_test_12345"
```

4. نفذ الأمر التالي مع Docker:

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    ghcr.io/all-hands-ai/openhands:0.11 \
    python -m openhands.core.main -t "write a bash script that prints hi"
```