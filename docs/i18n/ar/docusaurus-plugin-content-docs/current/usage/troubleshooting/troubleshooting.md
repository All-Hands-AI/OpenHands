

# 🚧 استكشاف الأخطاء وإصلاحها

هناك بعض رسائل الخطأ التي يتم الإبلاغ عنها بشكل متكرر من قبل المستخدمين. سنحاول جعل عملية التثبيت أسهل، ولكن في الوقت الحالي يمكنك البحث عن رسالة الخطأ الخاصة بك أدناه لمعرفة ما إذا كان هناك أي حلول مؤقتة. إذا كنت تجد المزيد من المعلومات أو حلًا مؤقتًا لأحد هذه المشاكل، يرجى فتح *PR* لإضافة التفاصيل إلى هذا الملف.

:::tip
OpenHands يدعم Windows فقط عبر [WSL](https://learn.microsoft.com/en-us/windows/wsl/install). 
يرجى التأكد من تنفيذ جميع الأوامر داخل طرفية WSL الخاصة بك.
راجع [ملاحظات للمستخدمين على WSL في Windows](troubleshooting/windows) للحصول على أدلة استكشاف الأخطاء وإصلاحها.
:::

## المشاكل الشائعة

* [تعذر الاتصال بـ Docker](#تعذر-الاتصال-بـ-docker)
* [404 المورد غير موجود](#404-المورد-غير-موجود)
* [تعليق `make build` أثناء تثبيت الحزم](#تعليق-make-build-أثناء-تثبيت-الحزم)
* [الجلسات لا يتم استعادتها](#الجلسات-لا-يتم-استعادتها)

### تعذر الاتصال بـ Docker

[قضية GitHub](https://github.com/All-Hands-AI/OpenHands/issues/1226)

**الأعراض**

```bash
Error creating controller. Please check Docker is running and visit `https://docs.all-hands.dev/modules/usage/troubleshooting` for more debugging information.
```

```bash
docker.errors.DockerException: Error while fetching server API version: ('Connection aborted.', FileNotFoundError(2, 'No such file or directory'))
```

**التفاصيل**

يستخدم OpenHands حاوية Docker لأداء عمله بشكل آمن، دون المخاطرة بتعطيل جهازك.

**الحلول المؤقتة**

* نفذ `docker ps` للتحقق من أن Docker قيد التشغيل.
* تأكد من أنك لا تحتاج إلى `sudo` لتشغيل Docker [راجع هنا](https://www.baeldung.com/linux/docker-run-without-sudo).
* إذا كنت على جهاز Mac، تحقق من [متطلبات الأذونات](https://docs.docker.com/desktop/mac/permission-requirements/) وخصوصًا فكر في تمكين `Allow the default Docker socket to be used` تحت `Settings > Advanced` في Docker Desktop.
* أيضًا، قم بتحديث Docker إلى أحدث إصدار من خلال خيار `Check for Updates`.

---
### `404 المورد غير موجود`

**الأعراض**

```python
Traceback (most recent call last):
  File "/app/.venv/lib/python3.12/site-packages/litellm/llms/openai.py", line 414, in completion
    raise e
  File "/app/.venv/lib/python3.12/site-packages/litellm/llms/openai.py", line 373, in completion
    response = openai_client.chat.completions.create(**data, timeout=timeout)  # type: ignore
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_utils/_utils.py", line 277, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/resources/chat/completions.py", line 579, in create
    return self._post(
           ^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_base_client.py", line 1232, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_base_client.py", line 921, in request
    return self._request(
           ^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_base_client.py", line 1012, in _request
    raise self._make_status_error_from_response(err.response) from None
openai.NotFoundError: Error code: 404 - {'error': {'code': '404', 'message': 'Resource not found'}}
```

**التفاصيل**

يحدث هذا عندما لا يستطيع LiteLLM (مكتبتنا للاتصال بمزودي LLM) العثور على نقطة النهاية API التي تحاول الاتصال بها. يحدث هذا عادة للمستخدمين الذين يستخدمون Azure أو ollama.

**الحلول المؤقتة**

* تحقق من أنك قمت بتحديد `LLM_BASE_URL` بشكل صحيح.
* تحقق من أن النموذج تم تحديده بشكل صحيح وفقًا لـ [توثيق LiteLLM](https://docs.litellm.ai/docs/providers).
  * إذا كنت تستخدم الواجهة الأمامية، تأكد من تعيين `model` في نافذة الإعدادات.
  * إذا كنت تستخدم الوضع غير المرئي (من خلال `main.py`)، تأكد من تعيين `LLM_MODEL` في البيئة/التكوين الخاص بك.
* تأكد من أنك اتبعت جميع التعليمات الخاصة بمزود LLM الخاص بك.
  * [Azure](/modules/usage/llms/azure-llms)
  * [Google](/modules/usage/llms/google-llms)
* تأكد من أن مفتاح API صحيح.
* حاول الاتصال بـ LLM باستخدام `curl`.
* جرب [الاتصال مباشرة عبر LiteLLM](https://github.com/BerriAI/litellm) لاختبار تكوينك.

---
### تعليق `make build` أثناء تثبيت الحزم

**الأعراض**

تتوقف عملية تثبيت الحزم عند `Pending...` دون أي رسالة خطأ:

```bash
Package operations: 286 installs, 0 updates, 0 removals

  - Installing certifi (2024.2.2): Pending...
  - Installing h11 (0.14.0): Pending...
  - Installing idna (3.7): Pending...
  - Installing sniffio (1.3.1): Pending...
  - Installing typing-extensions (4.11.0): Pending...
```

**التفاصيل**

في حالات نادرة، قد يبدو أن `make build` يتعطل أثناء تثبيت الحزم دون أي رسالة خطأ.

**الحلول المؤقتة**

قد يفتقد مثبت الحزم Poetry معلمة تكوين لمعرفة مكان البحث عن بيانات الاعتماد (keyring).

تحقق أولاً باستخدام `env` إذا كانت هناك قيمة لـ `PYTHON_KEYRING_BACKEND`.
إذا لم تكن موجودة، نفذ الأمر التالي لتعيينها إلى قيمة معروفة وأعد المحاولة:

```bash
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
```

---
### الجلسات لا يتم استعادتها

**الأعراض**

يسأل OpenHands عادةً ما إذا كان يجب استئناف الجلسة أو بدء جلسة جديدة عند فتح واجهة المستخدم.
لكن النقر على "استئناف" يبدأ جلسة جديدة على أي حال.

**التفاصيل**

مع التثبيت القياسي حتى الآن، يتم تخزين بيانات الجلسة في الذاكرة.
حالياً، إذا تم إعادة تشغيل خدمة OpenHands، تصبح الجلسات السابقة غير صالحة (يتم إنشاء سر جديد) وبالتالي لا يمكن استعادتها.

**الحلول المؤقتة**

* قم بتعديل التكوين لجعل الجلسات دائمة عن طريق تحرير ملف `config.toml` (في المجلد الجذري لـ OpenHands) وتحديد `file_store` و `file_store_path` المطلق:

```toml
file_store="local"
file_store_path="/absolute/path/to/openhands/cache/directory"
```

* أضف سر jwt ثابت في `.bashrc`، كما هو موضح أدناه، بحيث تبقى معرّفات الجلسات السابقة مقبولة.

```bash
EXPORT JWT_SECRET=A_CONST_VALUE
```