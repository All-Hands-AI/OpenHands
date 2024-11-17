

# Google Gemini/Vertex

يستخدم OpenHands LiteLLM لإجراء مكالمات إلى نماذج الدردشة الخاصة بـ Google. يمكنك العثور على توثيق استخدام Google كمزود على الروابط التالية:

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

## تكوينات Gemini - Google AI Studio

عند تشغيل OpenHands، ستحتاج إلى تعيين العناصر التالية في واجهة المستخدم عبر الإعدادات:
* `LLM Provider` إلى `Gemini`
* `LLM Model` إلى النموذج الذي ستستخدمه.
إذا لم يكن النموذج في القائمة، قم بتفعيل `Advanced Options` وأدخل اسم النموذج في `Custom Model` (على سبيل المثال، gemini/&lt;اسم النموذج&gt; مثل `gemini/gemini-1.5-pro`).
* `API Key` إلى مفتاح API الخاص بك لـ Gemini

## تكوينات VertexAI - Google Cloud Platform

لاستخدام Vertex AI عبر Google Cloud Platform عند تشغيل OpenHands، ستحتاج إلى تعيين متغيرات البيئة التالية باستخدام `-e` في [أمر docker run](/modules/usage/installation#start-the-app):

```
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-of-gcp-service-account-json>"
VERTEXAI_PROJECT="<معرف-مشروع-gcp الخاص بك>"
VERTEXAI_LOCATION="<موقع-gcp الخاص بك>"
```

ثم، قم بتعيين العناصر التالية في واجهة المستخدم عبر الإعدادات:
* `LLM Provider` إلى `VertexAI`
* `LLM Model` إلى النموذج الذي ستستخدمه.
إذا لم يكن النموذج في القائمة، قم بتفعيل `Advanced Options` وأدخل اسم النموذج في `Custom Model` (على سبيل المثال، vertex_ai/&lt;اسم النموذج&gt;).