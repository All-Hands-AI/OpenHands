

# LLM المحلي مع Ollama

:::warning
عند استخدام LLM محلي، قد تكون بعض ميزات OpenHands محدودة.
:::

تأكد من أن خادم Ollama يعمل.
لإرشادات مفصلة حول كيفية البدء، يمكنك الرجوع إلى [هنا](https://github.com/ollama/ollama).

يفترض هذا الدليل أنك قد قمت بتشغيل Ollama باستخدام `ollama serve`. إذا كنت تشغل Ollama بطريقة مختلفة (على سبيل المثال، داخل Docker)، فقد تحتاج التعليمات إلى تعديلات. يرجى ملاحظة أنه إذا كنت تستخدم WSL، فإن الإعداد الافتراضي لـ Ollama يحظر الطلبات القادمة من الحاويات Docker. راجع [هنا](#configuring-ollama-service-wsl-fr).

## استرداد النماذج

يمكنك العثور على أسماء نماذج Ollama [هنا](https://ollama.com/library). كمثال صغير، يمكنك استخدام النموذج `codellama:7b`. النماذج الأكبر عادةً ما توفر أداءً أفضل.

```bash
ollama pull codellama:7b
```

يمكنك التحقق من النماذج التي قمت بتنزيلها كما يلي:

```bash
~$ ollama list
NAME                            ID              SIZE    MODIFIED
codellama:7b                    8fdf8f752f6e    3.8 GB  6 weeks ago
mistral:7b-instruct-v0.2-q4_K_M eb14864c7427    4.4 GB  2 weeks ago
starcoder2:latest               f67ae0f64584    1.7 GB  19 hours ago
```

## تشغيل OpenHands باستخدام Docker

### بدء OpenHands
استخدم التعليمات [هنا](../getting-started) لبدء تشغيل OpenHands باستخدام Docker.
لكن عند تنفيذ `docker run`، ستحتاج إلى إضافة بعض المعاملات الإضافية:

```bash
--add-host host.docker.internal:host-gateway \
-e LLM_OLLAMA_BASE_URL="http://host.docker.internal:11434" \
```

`LLM_OLLAMA_BASE_URL` اختياري. إذا قمت بتحديده، سيتم استخدامه لعرض النماذج المثبتة المتاحة في واجهة المستخدم.

مثال:

```bash
# الدليل الذي ترغب أن يعدله OpenHands. يجب أن يكون مساراً مطلقاً!
export WORKSPACE_BASE=$(pwd)/workspace

docker run \
    -it \
    --pull=always \
    --add-host host.docker.internal:host-gateway \
    -e SANDBOX_USER_ID=$(id -u) \
    -e LLM_OLLAMA_BASE_URL="http://host.docker.internal:11434" \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    ghcr.io/all-hands-ai/openhands:main
```

الآن يجب أن تتمكن من الوصول إلى `http://localhost:3000/`

### تكوين التطبيق على الويب

عند تشغيل `openhands`، ستحتاج إلى تحديد العناصر التالية في واجهة المستخدم عبر الإعدادات:
- النموذج إلى "ollama/&lt;اسم-النموذج&gt;"
- URL الأساسي إلى `http://host.docker.internal:11434`
- مفتاح API اختياري، يمكنك استخدام أي سلسلة نصية، مثل `ollama`.

## تشغيل OpenHands في وضع التطوير

### البناء من المصدر

استخدم التعليمات في [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) لبناء OpenHands.
تأكد من وجود `config.toml` عبر تنفيذ `make setup-config` والذي سيقوم بإنشائه لك. في `config.toml`، أدخل ما يلي:

```
[core]
workspace_base="./workspace"

[llm]
embedding_model="local"
ollama_base_url="http://localhost:11434"
```

انتهى! يمكنك الآن تشغيل OpenHands باستخدام: `make run`. يجب أن تتمكن الآن من الوصول إلى `http://localhost:3000/`

### تكوين التطبيق على الويب

في واجهة المستخدم لـ OpenHands، انقر على رمز الإعدادات في أسفل اليسار.
ثم، في حقل `Model`، أدخل `ollama/codellama:7b`، أو اسم النموذج الذي استردته مسبقاً.
إذا لم يظهر في القائمة المنسدلة، فعّل `Advanced Settings` واكتبه. يرجى ملاحظة: تحتاج إلى اسم النموذج كما هو مذكور في قائمة `ollama list`، مع بادئة `ollama/`.

في حقل مفتاح API، أدخل `ollama` أو أي قيمة أخرى، حيث لا تحتاج إلى مفتاح معين.

في حقل Base URL، أدخل `http://localhost:11434`.

والآن، أنت جاهز للبدء!

## تكوين خدمة Ollama (WSL) {#configuring-ollama-service-wsl-fr}

الإعداد الافتراضي لـ Ollama في WSL يخدم فقط localhost. وهذا يعني أنه لا يمكنك الوصول إليه من حاوية Docker. على سبيل المثال، لن يعمل مع OpenHands. دعنا نختبر أولاً أن Ollama يعمل بشكل صحيح.

```bash
ollama list # الحصول على قائمة النماذج المثبتة
curl http://localhost:11434/api/generate -d '{"model":"[NOM]","prompt":"hi"}'
#مثال. curl http://localhost:11434/api/generate -d '{"model":"codellama:7b","prompt":"hi"}'
#مثال. curl http://localhost:11434/api/generate -d '{"model":"codellama","prompt":"hi"}' #العلامة اختيارية إذا كان هناك نموذج واحد فقط
```

بعد ذلك، اختبر أنه يسمح بالطلبات "الخارجية"، مثل تلك القادمة من حاوية Docker.

```bash
docker ps # الحصول على قائمة الحاويات التي تعمل، لاختبار دقيق، اختر حاوية sandbox الخاصة بـ OpenHands.
docker exec [ID الحاوية] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NOM]","prompt":"hi"}'
#مثال. docker exec cd9cc82f7a11 curl http://host.docker.internal:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'
```

## إصلاح المشكلة

الآن، دعنا نصلح المشكلة. عدّل `/etc/systemd/system/ollama.service` باستخدام صلاحيات sudo. (قد يختلف المسار حسب توزيعة Linux)

```bash
sudo vi /etc/systemd/system/ollama.service
```

أو

```bash
sudo nano /etc/systemd/system/ollama.service
```

في القسم [Service]، أضف هذه الأسطر:

```
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
```

ثم، احفظ التغييرات، أعد تحميل الإعدادات وأعد تشغيل الخدمة.

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

أخيراً، اختبر أن Ollama متاح من داخل الحاوية:

```bash
ollama list # الحصول على قائمة النماذج المثبتة
docker ps # الحصول على قائمة الحاويات التي تعمل، لاختبار دقيق، اختر حاوية sandbox الخاصة بـ OpenHands.
docker exec [ID الحاوية] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NOM]","prompt":"hi"}'
```

# LLM المحلي مع LM Studio

خطوات إعداد LM Studio:
1. افتح LM Studio
2. اذهب إلى تبويب الخادم المحلي.
3. اضغط على زر "بدء الخادم".
4. اختر النموذج الذي ترغب في استخدامه من القائمة المنسدلة.

حدد الإعدادات التالية:
```bash
LLM_MODEL="openai/lmstudio"
LLM_BASE_URL="http://localhost:1234/v1"
CUSTOM_LLM_PROVIDER="openai"
```

### Docker

```bash
docker run \
    -it \
    --pull=always \
    -e SANDBOX_USER_ID=$(id -u) \
    -e LLM_MODEL="openai/lmstudio" \
    -e LLM_BASE_URL="http://host.docker.internal:1234/v1" \
    -e CUSTOM_LLM_PROVIDER="openai" \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    ghcr.io/all-hands-ai/openhands:main
```

يجب أن تتمكن الآن من الوصول إلى `http://localhost:3000/`

في بيئة التطوير، يمكنك تحديد الإعدادات التالية في ملف `config.toml`:

```
[core]
workspace_base="./workspace"

[llm]
model="openai/lmstudio"
base_url="http://localhost:1234/v1"
custom_llm_provider="openai"
```

تم! يمكنك الآن تشغيل OpenHands باستخدام: `make run` دون Docker. يجب أن تتمكن الآن من الوصول إلى `http://localhost:3000/`

# ملاحظة

لـ WSL، نفذ الأوامر التالية في cmd لتكوين وضع

 الجسر:

```bash
netsh interface portproxy add v4tov4 listenport=11434 listenaddress=0.0.0.0 connectport=11434 connectaddress=localhost
```