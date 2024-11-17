

# LLM المحلي مع Ollama

تأكد من أن خادم Ollama يعمل.
لإرشادات مفصلة حول كيفية البدء، يمكنك الرجوع إلى [هنا](https://github.com/ollama/ollama).

يفترض هذا الدليل أنك قد قمت بتشغيل Ollama باستخدام `ollama serve`. إذا كنت تشغل Ollama بطريقة مختلفة (على سبيل المثال، داخل Docker)، فقد تحتاج التعليمات إلى تعديلات. يرجى ملاحظة أنه إذا كنت تستخدم WSL، فإن الإعداد الافتراضي لـ Ollama يحظر الطلبات القادمة من الحاويات Docker. راجع [هنا](#configuring-ollama-service-fr).

## تحميل النماذج

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

## بدء OpenHands

### Docker

استخدم التعليمات [هنا](../intro) لبدء تشغيل OpenHands باستخدام Docker.
لكن عند تنفيذ `docker run`، ستحتاج إلى إضافة بعض المعاملات الإضافية:

```bash
--add-host host.docker.internal:host-gateway \
-e LLM_API_KEY="ollama" \
-e LLM_BASE_URL="http://host.docker.internal:11434" \
```

على سبيل المثال:

```bash
# الدليل الذي ترغب أن يعدله OpenHands. يجب أن يكون مساراً مطلقاً!
export WORKSPACE_BASE=$(pwd)/workspace

docker run \
    -it \
    --pull=always \
    --add-host host.docker.internal:host-gateway \
    -e SANDBOX_USER_ID=$(id -u) \
    -e LLM_API_KEY="ollama" \
    -e LLM_BASE_URL="http://host.docker.internal:11434" \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    ghcr.io/all-hands-ai/openhands:main
```

يجب أن تتمكن الآن من الاتصال بـ `http://localhost:3000/`

### بناء OpenHands من المصدر

استخدم التعليمات في [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) لبناء OpenHands.
تأكد من وجود ملف `config.toml` عبر تنفيذ `make setup-config` والذي سيقوم بإنشائه لك. في `config.toml`، أدخل ما يلي:

```
LLM_MODEL="ollama/codellama:7b"
LLM_API_KEY="ollama"
LLM_EMBEDDING_MODEL="local"
LLM_BASE_URL="http://localhost:11434"
WORKSPACE_BASE="./workspace"
WORKSPACE_DIR="$(pwd)/workspace"
```

استبدل `LLM_MODEL` بالنموذج الذي ترغب فيه إذا لزم الأمر.

انتهى! يمكنك الآن بدء تشغيل OpenHands باستخدام: `make run` دون Docker. يجب أن تتمكن الآن من الاتصال بـ `http://localhost:3000/`

## اختيار النموذج الخاص بك

في واجهة OpenHands، انقر على أيقونة الإعدادات في أسفل اليسار.
ثم، في خانة `Model`، أدخل `ollama/codellama:7b`، أو اسم النموذج الذي قمت بتحميله سابقاً.
إذا لم يظهر في القائمة المنسدلة، لا بأس، فقط اكتب الاسم يدوياً. اضغط على حفظ عند الانتهاء.

الآن، أنت جاهز للبدء!

## تكوين خدمة Ollama (WSL) {#configuring-ollama-service-fr}

الإعداد الافتراضي لـ Ollama في WSL يخدم فقط localhost. وهذا يعني أنه لا يمكنك الوصول إليه من داخل حاوية Docker. على سبيل المثال، لن يعمل مع OpenHands. دعنا نختبر أولاً أن Ollama يعمل بشكل صحيح.

```bash
ollama list # الحصول على قائمة النماذج المثبتة
curl http://localhost:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#مثال. curl http://localhost:11434/api/generate -d '{"model":"codellama:7b","prompt":"hi"}'
#مثال. curl http://localhost:11434/api/generate -d '{"model":"codellama","prompt":"hi"}' #العلامة اختيارية إذا كان هناك نموذج واحد فقط
```

بعد ذلك، اختبر أنه يسمح بالطلبات "الخارجية"، مثل تلك القادمة من حاوية Docker.

```bash
docker ps # الحصول على قائمة الحاويات التي تعمل، لاختبار دقيق، اختر حاوية sandbox الخاصة بـ OpenHands.
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
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
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
```