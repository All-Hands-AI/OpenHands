

# OpenAI

يستخدم OpenHands LiteLLM لإجراء استدعاءات إلى نماذج الدردشة من OpenAI. يمكنك العثور على وثائق حول كيفية استخدام OpenAI كمزود [هنا](https://docs.litellm.ai/docs/providers/openai).

## التكوين

عند تشغيل OpenHands، ستحتاج إلى ضبط العناصر التالية في واجهة المستخدم الخاصة بـ OpenHands عبر الإعدادات:
* `LLM Provider` إلى `OpenAI`
* `LLM Model` إلى النموذج الذي ستستخدمه.
[قم بزيارة هذا الرابط للاطلاع على قائمة كاملة من نماذج OpenAI المدعومة من LiteLLM.](https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models)
إذا لم يكن النموذج مدرجًا في القائمة، قم بتمكين `Advanced Options` وأدخل النموذج في `Custom Model` (على سبيل المثال، `openai/<model-name>` مثل `openai/gpt-4o`).
* `API Key` إلى مفتاح API الخاص بـ OpenAI. للعثور على أو إنشاء مفتاح API لمشروع OpenAI الخاص بك، [انظر هنا](https://platform.openai.com/api-keys).

## استخدام نقاط النهاية المتوافقة مع OpenAI

تمامًا مثل استكمالات الدردشة من OpenAI، نستخدم LiteLLM للنقاط النهائية المتوافقة مع OpenAI. يمكنك العثور على وثائق كاملة حول هذا الموضوع [هنا](https://docs.litellm.ai/docs/providers/openai_compatible).

## استخدام وكيل لـ OpenAI

إذا كنت تستخدم وكيلًا لـ OpenAI، ستحتاج إلى ضبط العناصر التالية في واجهة المستخدم الخاصة بـ OpenHands عبر الإعدادات:
* قم بتمكين `Advanced Options`
* `Custom Model` إلى `openai/<model-name>` (على سبيل المثال، `openai/gpt-4o` أو `openai/<proxy-prefix>/<model-name>`)
* `Base URL` إلى عنوان URL الخاص بوكيل OpenAI
* `API Key` إلى مفتاح API الخاص بـ OpenAI