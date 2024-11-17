

# Groq

يستخدم OpenHands LiteLLM لإجراء مكالمات إلى نماذج الدردشة على Groq. يمكنك العثور على الوثائق الخاصة باستخدام Groq كمزود [هنا](https://docs.litellm.ai/docs/providers/groq).

## التكوين

عند تشغيل OpenHands، يجب عليك تعيين العناصر التالية في واجهة المستخدم عبر الإعدادات:
* `LLM Provider` إلى `Groq`
* `LLM Model` إلى النموذج الذي ستستخدمه. [قم بزيارة هنا لرؤية قائمة النماذج المستضافة من قبل Groq](https://console.groq.com/docs/models). إذا لم يكن النموذج في القائمة، قم بتفعيل `Advanced Options` وأدخله في `Custom Model` (على سبيل المثال، groq/&lt;اسم-النموذج&gt; مثل `groq/llama3-70b-8192`).
* `API key` إلى مفتاح API الخاص بك في Groq. للعثور على مفتاح API الخاص بك أو لإنشائه، [شاهد هنا](https://console.groq.com/keys).

## استخدام Groq كنقطة نهاية متوافقة مع OpenAI

نقطة النهاية في Groq لإكمال الدردشة هي [متوافقة في الأساس مع OpenAI](https://console.groq.com/docs/openai). لذلك، يمكنك الوصول إلى نماذج Groq كما لو كنت تتعامل مع أي نقطة نهاية متوافقة مع OpenAI. يمكنك تعيين العناصر التالية في واجهة المستخدم عبر الإعدادات:
* تفعيل `Advanced Options`
* `Custom Model` مع بادئة `openai/` + النموذج الذي ستستخدمه (على سبيل المثال، `openai/llama3-70b-8192`)
* `Base URL` إلى `https://api.groq.com/openai/v1`
* `API Key` إلى مفتاح API الخاص بك في Groq