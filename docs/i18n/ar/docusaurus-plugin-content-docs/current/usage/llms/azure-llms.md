

# Azure

يستخدم OpenHands LiteLLM لإجراء مكالمات إلى نماذج الدردشة الخاصة بـ Azure. يمكنك العثور على توثيق استخدامها كمزود [هنا](https://docs.litellm.ai/docs/providers/azure).

## تكوين Azure OpenAI

عند تشغيل OpenHands، ستحتاج إلى تعيين متغير البيئة التالي باستخدام `-e` في
[أمر docker run](/modules/usage/installation#start-the-app) :

```
LLM_API_VERSION="<api-version>"              # على سبيل المثال "2023-05-15"
```

مثال:
```bash
docker run -it --pull=always \
    -e LLM_API_VERSION="2023-05-15"
    ...
```

ثم، قم بتعيين العناصر التالية في واجهة المستخدم الخاصة بـ OpenHands عبر الإعدادات:

:::note
ستحتاج إلى اسم نشر ChatGPT الخاص بك الذي يمكنك العثور عليه في صفحة النشرات في Azure. يتم الإشارة إليه كـ
&lt;deployment-name&gt; أدناه.
:::

* قم بتمكين `الخيارات المتقدمة`
* `النموذج المخصص` إلى azure/&lt;deployment-name&gt;
* `عنوان URL الأساسي` إلى عنوان URL الأساسي لواجهة برمجة تطبيقات Azure الخاصة بك (مثل `https://example-endpoint.openai.azure.com`)
* `مفتاح API` إلى مفتاح API الخاص بـ Azure

## التضمينات

يستخدم OpenHands llama-index للتضمينات. يمكنك العثور على توثيق استخدامها على Azure [هنا](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/azure_openai/).

### تكوين Azure OpenAI

عند تشغيل OpenHands، قم بتعيين متغيرات البيئة التالية باستخدام `-e` في
[أمر docker run](/modules/usage/installation#start-the-app) :

```
LLM_EMBEDDING_MODEL="azureopenai"
LLM_EMBEDDING_DEPLOYMENT_NAME="<your-embedding-deployment-name>"   # على سبيل المثال "TextEmbedding...<إلخ>"
LLM_API_VERSION="<api-version>"                                    # على سبيل المثال "2024-02-15-preview"
```