

# 💿 كيفية إنشاء دعم مخصص باستخدام Docker

**OpenHands** توفر بيئة تشغيل افتراضية تعتمد على إعداد Ubuntu مبسط، لكن بعض الحالات قد تتطلب تثبيت برامج إضافية افتراضيًا. هذه المقالة تشرح كيفية إنشاء صورة Docker مخصصة لتلبية متطلباتك.

---

## الإعداد الأساسي

تأكد من أنك قادر على تشغيل OpenHands باتباع الإرشادات المتوفرة في [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

---

## خطوات إنشاء صورة Docker

لإضافة البرامج المطلوبة، يمكنك إنشاء **صورة Docker مخصصة** استنادًا إلى Ubuntu أو Debian. على سبيل المثال، لإضافة Node.js، استخدم هذا **Dockerfile**:

```dockerfile
# استخدام أحدث إصدار من Ubuntu
FROM ubuntu:latest

# تحديث الحزم
RUN apt-get update && apt-get install -y nodejs
```

### إنشاء الصورة

1. قم بإنشاء ملف نصي باسم `Dockerfile` في دليل جديد.
2. قم بتشغيل الأمر التالي لإنشاء الصورة:

```bash
docker build -t image_personnalisée .
```

> هذا ينشئ صورة جديدة باسم `image_personnalisée` متوفرة داخل Docker Engine.

> **ملاحظة:** جميع البرامج المثبتة ستكون متوفرة لكل المستخدمين داخل الـ Sandbox الخاص بـ OpenHands.

---

## إعداد ملف `config.toml`

أضف اسم الصورة المخصصة إلى ملف الإعداد الخاص بـ OpenHands كالتالي:

```toml
[core]
workspace_base="./workspace"
run_as_openhands=true
sandbox_base_container_image="image_personnalisée"
```

---

## تشغيل OpenHands باستخدام الصورة المخصصة

1. قم بتنفيذ الأمر التالي لتشغيل OpenHands:

```bash
make run
```

2. افتح المتصفح على العنوان `localhost:3001` للتحقق من البيئة.

> على سبيل المثال، إذا كانت الصورة تحتوي على Node.js، يمكن تنفيذ `node -v` للتحقق من الإصدار.

---

## نظرة تقنية

عند استخدام صورة مخصصة لأول مرة:  
1. **يتم بناء الصورة تلقائيًا** باستخدام وظيفة `_build_sandbox_image` في OpenHands.  
2. الصورة تُعدل لتناسب بيئة OpenHands بإضافة بعض الإعدادات اللازمة مثل Miniforge و SSH.  

### مقتطف الكود

```python
dockerfile_content = (
        f'FROM {base_image}\n'
        'RUN apt update && apt install -y openssh-server wget sudo\n'
        'RUN mkdir -p /openhands && chmod 777 /openhands/logs\n'
        'RUN wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"\n'
        'RUN bash Miniforge3-$(uname)-$(uname -m).sh -b -p /openhands/miniforge3\n'
        'RUN echo "export PATH=/openhands/miniforge3/bin:$PATH" >> ~/.bashrc\n'
    ).strip()
```

> يتم استخدام الاسم المعدل للصورة عبر وظيفة [_get_new_image_name](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/docker/image_agnostic_util.py#L63).

---

## استكشاف الأخطاء

### **UID 1000 مستخدم بالفعل**

إذا ظهرت الرسالة:

```bash
useradd: UID 1000 est non unique
```

عدل ملف `config.toml` لتغيير `sandbox_user_id` كما يلي:

```toml
[core]
workspace_base="./workspace"
run_as_openhands=true
sandbox_base_container_image="image_personnalisée"
sandbox_user_id="1001"
```

---

### **أخطاء منفذ قيد الاستخدام**

لحل مشكلة المنافذ:  
1. استخدم `docker ps` لتحديد الحاويات الجارية.  
2. أوقف الحاويات باستخدام `docker rm`.  
3. أعد تشغيل OpenHands.

---

## المساعدة والدعم

للحصول على دعم إضافي، يمكنك الانضمام إلى [Slack](https://join.slack.com/t/opendevin/shared_invite/zt-2oikve2hu-UDxHeo8nsE69y6T7yFX_BA) أو [Discord](https://discord.gg/ESHStjSjD4).