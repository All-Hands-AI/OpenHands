

# Google Gemini/Vertex LLM

## الإكمال

يستخدم OpenHands LiteLLM لإجراء مكالمات الإكمال. الموارد التالية ذات صلة لاستخدام OpenHands مع LLMs من Google:

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

### تكوينات Gemini - Google AI Studio

لاستخدام Gemini عبر Google AI Studio عند تشغيل صورة Docker لـ OpenHands، يجب تعيين متغيرات البيئة التالية باستخدام `-e`:

```
GEMINI_API_KEY="<مفتاح-API-جوجل-الخاص-بك>"
LLM_MODEL="gemini/gemini-1.5-pro"
```

### تكوينات Vertex AI - Google Cloud Platform

لاستخدام Vertex AI عبر Google Cloud Platform عند تشغيل صورة Docker لـ OpenHands، يجب تعيين متغيرات البيئة التالية باستخدام `-e`:

```
GOOGLE_APPLICATION_CREDENTIALS="<تفريغ-json-لحساب-الخدمة-gcp-json>"
VERTEXAI_PROJECT="<معرف-مشروع-gcp-الخاص-بك>"
VERTEXAI_LOCATION="<موقع-gcp-الخاص-بك>"
LLM_MODEL="vertex_ai/<النموذج-الذي-تريده-LLM>"
```