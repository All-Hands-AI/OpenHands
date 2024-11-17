

# ملاحظات لمستخدمي WSL على ويندوز

يدعم OpenHands نظام ويندوز فقط عبر [WSL](https://learn.microsoft.com/en-us/windows/wsl/install).
يرجى التأكد من أنك تنفذ جميع الأوامر داخل الطرفية الخاصة بـ WSL.

## استكشاف الأخطاء وإصلاحها

### التوصية: عدم التنفيذ كـ مستخدم root

لأسباب أمنية، يُوصى بشدة بعدم تشغيل OpenHands كمستخدم root، بل كمستخدم يحمل UID غير صفري.

المراجع:

* [لماذا من السيء تسجيل الدخول كمستخدم root](https://askubuntu.com/questions/16178/why-is-it-bad-to-log-in-as-root)
* [تحديد المستخدم الافتراضي في WSL](https://www.tenforums.com/tutorials/128152-set-default-user-windows-subsystem-linux-distro-windows-10-a.html#option2)
نصيحة بخصوص المرجع الثاني: لمستخدمي Ubuntu، قد تكون الأمر الفعلي هو "ubuntupreview" بدلاً من "ubuntu".

---
### الخطأ: 'docker' لم يتم العثور عليه في توزيع WSL 2.

إذا كنت تستخدم Docker Desktop، تأكد من تشغيله قبل استدعاء أي أمر docker من WSL.
يجب أيضًا تمكين خيار تكامل WSL في Docker.

---
### تثبيت Poetry

* إذا واجهت مشكلات في تشغيل Poetry حتى بعد تثبيته أثناء عملية البناء، قد تحتاج إلى إضافة مسارها الثنائي إلى بيئتك:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

* إذا توقف `make build` عند خطأ مثل هذا:

```sh
ModuleNotFoundError: no module named <module-name>
```

قد يكون هذا بسبب مشكلة في ذاكرة التخزين المؤقت لـ Poetry.
حاول تنفيذ الأوامر التالية واحدة تلو الأخرى:

```sh
rm -r ~/.cache/pypoetry
make build
```

---
### الكائن NoneType ليس له سمة 'request'

إذا واجهت مشكلات متعلقة بالشبكة مثل `NoneType object has no attribute 'request'` أثناء تنفيذ `make run`, قد تحتاج إلى تكوين إعدادات الشبكة في WSL2. اتبع هذه الخطوات:

* افتح أو أنشئ الملف `.wslconfig` الموجود في `C:\Users\%username%\.wslconfig` على جهاز ويندوز المضيف.
* أضف التكوين التالي إلى الملف `.wslconfig`:

```sh
[wsl2]
networkingMode=mirrored
localhostForwarding=true
```

* احفظ الملف `.wslconfig`.
* أعد تشغيل WSL2 بالكامل من خلال إغلاق جميع مثيلات WSL2 الحالية وتنفيذ الأمر `wsl --shutdown` في موجه الأوامر أو الطرفية.
* بعد إعادة تشغيل WSL، حاول تنفيذ `make run` مرة أخرى.
يجب أن يتم حل مشكلة الشبكة.