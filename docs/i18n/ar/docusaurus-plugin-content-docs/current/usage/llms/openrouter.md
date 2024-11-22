

# OpenRouter

يستخدم OpenHands LiteLLM لإجراء استدعاءات إلى نماذج الدردشة عبر OpenRouter. يمكنك العثور على وثائق حول كيفية استخدام OpenRouter كمزود [هنا](https://docs.litellm.ai/docs/providers/openrouter).

## التكوين

عند تشغيل OpenHands، ستحتاج إلى ضبط العناصر التالية في واجهة المستخدم الخاصة بـ OpenHands عبر الإعدادات:
* `LLM Provider` إلى `OpenRouter`
* `LLM Model` إلى النموذج الذي ستستخدمه.
[قم بزيارة هنا للاطلاع على قائمة كاملة من نماذج OpenRouter](https://openrouter.ai/models).
إذا لم يكن النموذج مدرجًا في القائمة، قم بتمكين `Advanced Options` وأدخل النموذج في `Custom Model` (على سبيل المثال، `openrouter/<model-name>` مثل `openrouter/anthropic/claude-3.5-sonnet`).
* `API Key` إلى مفتاح API الخاص بـ OpenRouter.