

# وضع سطر الأوامر (CLI)

يمكن تشغيل OpenHands في وضع سطر الأوامر التفاعلي (CLI)، مما يتيح للمستخدمين بدء جلسة تفاعلية عبر سطر الأوامر.

هذا الوضع يختلف عن [وضع بدون واجهة رسومية](headless-mode)، الذي يكون غير تفاعلي وأفضل للاستخدام في السكربتات.

## باستخدام Python

لتشغيل جلسة تفاعلية لـ OpenHands عبر سطر الأوامر، اتبع هذه الخطوات:

1. تأكد من أنك قد اتبعت [تعليمات إعداد بيئة التطوير](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).
   
2. نفذ الأمر التالي:

```bash
poetry run python -m openhands.core.cli
```

سيؤدي هذا الأمر إلى بدء جلسة تفاعلية حيث يمكنك إدخال المهام واستلام الردود من OpenHands.

تأكد من إعداد النموذج الخاص بك، ومفتاح الـ API، والمعلمات الأخرى عبر المتغيرات البيئية
[أو عبر ملف `config.toml`](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml).

## باستخدام Docker

لتشغيل OpenHands في وضع سطر الأوامر باستخدام Docker، اتبع هذه الخطوات:

1. قم بتحديد `WORKSPACE_BASE` إلى الدليل الذي ترغب في أن يعدله OpenHands:

```bash
WORKSPACE_BASE=$(pwd)/workspace
```

2. حدد `LLM_MODEL` إلى النموذج الذي ترغب في استخدامه:

```bash
LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"
```

3. حدد `LLM_API_KEY` إلى مفتاح API الخاص بك:

```bash
LLM_API_KEY="sk_test_12345"
```

4. نفذ الأمر التالي في Docker:

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
    python -m openhands.core.cli
```

سيؤدي هذا الأمر إلى بدء جلسة تفاعلية في Docker حيث يمكنك إدخال المهام واستلام الردود من OpenHands.

## أمثلة لأوامر CLI والمخرجات المتوقعة

إليك بعض الأمثلة لأوامر CLI والمخرجات المتوقعة:

### المثال 1: مهمة بسيطة

```bash
كيف يمكنني مساعدتك؟ >> اكتب سكربت Python يعرض "Hello, World!"
```

المخرجات المتوقعة:

```bash
🤖 بالطبع! إليك سكربت Python يعرض "Hello, World!":

❯ print("Hello, World!")
```

### المثال 2: أمر Bash

```bash
كيف يمكنني مساعدتك؟ >> أنشئ مجلد باسم "test_dir"
```

المخرجات المتوقعة:

```bash
🤖 إنشاء مجلد باسم "test_dir":

❯ mkdir test_dir
```

### المثال 3: إدارة الأخطاء

```bash
كيف يمكنني مساعدتك؟ >> احذف ملف غير موجود
```

المخرجات المتوقعة:

```bash
🤖 حدث خطأ. يرجى المحاولة مرة أخرى.
```