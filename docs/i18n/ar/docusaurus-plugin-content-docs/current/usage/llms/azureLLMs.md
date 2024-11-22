

# Azure OpenAI LLM

## الإكمال

يستخدم OpenHands LiteLLM لإجراء مكالمات الإكمال. يمكنك العثور على توثيق استخدامها على Azure [هنا](https://docs.litellm.ai/docs/providers/azure)

### تكوينات OpenAI Azure

عند تشغيل صورة Docker لـ OpenHands، ستحتاج إلى تعيين متغيرات البيئة التالية باستخدام `-e`:

```
LLM_BASE_URL="<azure-api-base-url>"          # على سبيل المثال "https://openai-gpt-4-test-v-1.openai.azure.com/"
LLM_API_KEY="<azure-api-key>"
LLM_MODEL="azure/<your-gpt-deployment-name>"
LLM_API_VERSION = "<api-version>"          # على سبيل المثال "2024-02-15-preview"
```

:::note
يمكنك العثور على اسم نشر ChatGPT الخاص بك في صفحة النشرات على Azure. بشكل افتراضي أو في البداية، قد يكون نفس اسم نموذج الدردشة (مثل "GPT4-1106-preview")، ولكن ليس من الضروري أن يكون كذلك. قم بتشغيل OpenHands، وبعد تحميله في المتصفح، اذهب إلى الإعدادات وعيّن النموذج كما يلي: "azure/&lt;اسم نشر GPT الفعلي الخاص بك&gt;". إذا لم يكن في القائمة، أدخل نصك الخاص واحفظه.
:::

## التضمينات

يستخدم OpenHands llama-index للتضمينات. يمكنك العثور على توثيق استخدامها على Azure [هنا](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/azure_openai/)

### تكوينات OpenAI Azure

النموذج المستخدم للتضمينات في Azure OpenAI هو "text-embedding-ada-002".
تحتاج إلى اسم النشر الصحيح لهذا النموذج في حسابك على Azure.

عند تشغيل OpenHands في Docker، قم بتعيين متغيرات البيئة التالية باستخدام `-e`:

```
LLM_EMBEDDING_MODEL="azureopenai"
LLM_EMBEDDING_DEPLOYMENT_NAME = "<your-embedding-deployment-name>"        # على سبيل المثال "TextEmbedding...<إلخ>"
LLM_API_VERSION = "<api-version>"         # على سبيل المثال "2024-02-15-preview"
```