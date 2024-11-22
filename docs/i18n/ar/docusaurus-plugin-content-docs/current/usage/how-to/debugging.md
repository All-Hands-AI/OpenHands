

# تصحيح الأخطاء (Debugging)

الجزء التالي مخصص لتعريفك بأساسيات تصحيح الأخطاء في OpenHands لأغراض التطوير.

## الخادم / VSCode

ملف `launch.json` التالي سيسمح بتصحيح الأخطاء في العناصر مثل العميل، المتحكم، والخادم، ولكنه لا يدعم تصحيح الأخطاء في الـ Sandbox (الذي يعمل داخل Docker). كما أنه سيتجاهل أي تعديلات داخل مجلد `workspace/`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "OpenHands CLI",
            "type": "debugpy",
            "request": "launch",
            "module": "openhands.core.cli",
            "justMyCode": false
        },
        {
            "name": "OpenHands WebApp",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "openhands.server.listen:app",
                "--reload",
                "--reload-exclude",
                "${workspaceFolder}/workspace",
                "--port",
                "3000"
            ],
            "justMyCode": false
        }
    ]
}
```

يمكن تحديد إعدادات تصحيح الأخطاء الأكثر تخصيصًا التي تشمل معلمات إضافية كما يلي:

```json
    ...
    {
      "name": "Debug CodeAct",
      "type": "debugpy",
      "request": "launch",
      "module": "openhands.core.main",
      "args": [
        "-t",
        "Demandez-moi quelle est votre tâche.",
        "-d",
        "${workspaceFolder}/workspace",
        "-c",
        "CodeActAgent",
        "-l",
        "llm.o1",
        "-n",
        "prompts"
      ],
      "justMyCode": false
    }
    ...
```

يمكن تحديث القيم في الجزء السابق بالشكل التالي:

- *t*: المهمة
- *d*: دليل مساحة العمل لـ OpenHands
- *c*: العميل (Agent)
- *l*: إعداد LLM (محددة مسبقًا في `config.toml`)
- *n*: اسم الجلسة (على سبيل المثال، اسم تدفق الأحداث)