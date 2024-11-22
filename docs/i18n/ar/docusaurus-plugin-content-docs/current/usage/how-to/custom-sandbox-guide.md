

# Sandbox مخصص

الـ Sandbox هو المكان الذي يقوم فيه العميل بأداء مهامه. بدلاً من تنفيذ الأوامر مباشرة على جهازك (مما قد يكون محفوفًا بالمخاطر)، يقوم العميل بتنفيذها داخل حاوية Docker.

يأتي الـ Sandbox الافتراضي لـ OpenHands (`python-nodejs:python3.12-nodejs22` من [nikolaik/python-nodejs](https://hub.docker.com/r/nikolaik/python-nodejs)) مع بعض الحزم المثبتة مثل Python وNode.js، ولكن قد يتطلب تثبيت برامج أخرى بشكل افتراضي.

لديك خياران لتخصيصه:

1. استخدام صورة موجودة تحتوي على البرامج المطلوبة.
2. إنشاء صورة Docker مخصصة خاصة بك.

إذا اخترت الخيار الأول، يمكنك تجاوز قسم "إنشاء صورة Docker الخاصة بك".

## إنشاء صورة Docker الخاصة بك

لإنشاء صورة Docker مخصصة، يجب أن تكون الصورة مبنية على Debian.

على سبيل المثال، إذا كنت تريد أن يحتوي OpenHands على `ruby` مثبتًا، أنشئ ملف `Dockerfile` يحتوي على المحتوى التالي:

```dockerfile
FROM debian:latest

# تثبيت الحزم المطلوبة
RUN apt-get update && apt-get install -y ruby
```

احفظ هذا الملف في مجلد. ثم، قم ببناء صورة Docker الخاصة بك (على سبيل المثال، باسم custom-image) عن طريق التنقل إلى المجلد في الطرفية وتنفيذ:

```bash
docker build -t custom-image .
```

سيؤدي ذلك إلى إنتاج صورة جديدة تسمى `custom-image` ستكون متاحة في Docker.

> لاحظ أنه في التكوين الموضح في هذا المستند، سيعمل OpenHands كمستخدم "openhands" داخل الـ Sandbox، وبالتالي يجب أن تكون جميع الحزم المثبتة عبر ملف الـ Docker متاحة لجميع مستخدمي النظام، وليس فقط الجذر (root).

## استخدام سير العمل الخاص بالتطوير

### التكوين

أولاً، تأكد من أنه يمكنك تشغيل OpenHands باتباع التعليمات في [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

### تحديد صورة الـ Sandbox الأساسية

في ملف `config.toml` في دليل OpenHands، حدد `sandbox_base_container_image` إلى الصورة التي ترغب في استخدامها. يمكن أن تكون صورة قد قمت بسحبها مسبقًا أو التي قمت بإنشائها:

```bash
[core]
...
sandbox_base_container_image="custom-image"
```

### التشغيل

قم بتشغيل OpenHands بتنفيذ الأمر `make run` في الدليل العلوي.

## شرح تقني

يرجى الرجوع إلى [قسم صورة Docker المخصصة في وثائق التنفيذ](https://docs.all-hands.dev/modules/usage/architecture/runtime#advanced-how-openhands-builds-and-maintains-od-runtime-images) للحصول على مزيد من التفاصيل.

## استكشاف الأخطاء / الأخطاء

### خطأ: `useradd: UID 1000 is not unique`

إذا رأيت هذا الخطأ في مخرجات وحدة التحكم، فهذا لأن OpenHands يحاول إنشاء المستخدم openhands في الـ Sandbox باستخدام UID 1000، ولكن هذا الـ UID مستخدم بالفعل في الصورة (لسبب ما). لتصحيح ذلك، قم بتغيير الحقل `sandbox_user_id` في ملف `config.toml` إلى قيمة مختلفة:

```toml
[core]
workspace_base="./workspace"
run_as_openhands=true
sandbox_base_container_image="custom_image"
sandbox_user_id="1001"
```

### أخطاء استخدام المنفذ

إذا رأيت خطأ يتعلق بمنفذ مستخدم بالفعل أو غير متاح، حاول إزالة جميع الحاويات الجارية (نفذ `docker ps` و `docker rm` على الحاويات المعنية) ثم أعد تنفيذ `make run`.

## المناقشة

لأي مشاكل أو أسئلة أخرى، انضم إلى [Slack](https://join.slack.com/t/opendevin/shared_invite/zt-2oikve2hu-UDxHeo8nsE69y6T7yFX_BA) أو [Discord](https://discord.gg/ESHStjSjD4) واطرح سؤالك!