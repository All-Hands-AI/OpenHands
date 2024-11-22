

# التقييم

يقدم هذا الدليل نظرة عامة حول كيفية دمج معيار التقييم الخاص بك في إطار العمل OpenHands.

## إعداد البيئة وتكوين LLM

يرجى اتباع التعليمات [هنا](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) لإعداد بيئة التطوير المحلية الخاصة بك. يستخدم OpenHands في وضع التطوير ملف `config.toml` لتتبع معظم الإعدادات.

إليك مثال على ملف تكوين يمكنك استخدامه لتحديد واستخدام عدة LLMs:

```toml
[llm]
# هام: أضف مفتاح API الخاص بك هنا وحدد النموذج الذي ترغب في تقييمه
model = "claude-3-5-sonnet-20241022"

api_key = "sk-XXX"

[llm.eval_gpt4_1106_preview_llm]
model = "gpt-4-1106-preview"
api_key = "XXX"
temperature = 0.0

[llm.eval_some_openai_compatible_model_llm]
model = "openai/MODEL_NAME"
base_url = "https://OPENAI_COMPATIBLE_URL/v1"
api_key = "XXX"
temperature = 0.0
```

## كيفية استخدام OpenHands من خلال سطر الأوامر

يمكن تشغيل OpenHands من خلال سطر الأوامر باستخدام التنسيق التالي:

```bash
poetry run python ./openhands/core/main.py \
        -i <max_iterations> \
        -t "<task_description>" \
        -c <agent_class> \
        -l <llm_config>
```

على سبيل المثال:

```bash
poetry run python ./openhands/core/main.py \
        -i 10 \
        -t "اكتب لي سكربت bash يعرض hello world." \
        -c CodeActAgent \
        -l llm
```

تنفذ هذه الأمر OpenHands مع:
- حد أقصى لـ 10 تكرارات
- وصف المهمة المحددة
- باستخدام CodeActAgent
- مع تكوين LLM المحدد في قسم `llm` من ملف `config.toml`

## كيفية عمل OpenHands

النقطة الرئيسية في OpenHands توجد في `openhands/core/main.py`. إليك سير العمل المبسط لكيفية عمله:

1. تحليل معلمات سطر الأوامر وتحميل التكوين
2. إنشاء بيئة التشغيل باستخدام `create_runtime()`
3. تهيئة العميل المحدد
4. تنفيذ المتحكم باستخدام `run_controller()`، الذي:
   - يربط بيئة التشغيل بالعميل
   - ينفذ مهمة العميل
   - يعيد الحالة النهائية بمجرد الانتهاء

وظيفة `run_controller()` هي قلب تنفيذ OpenHands. فهي تدير التفاعل بين العميل، بيئة التشغيل، والمهمة، وتتعامل مع أشياء مثل محاكاة إدخال المستخدم ومعالجة الأحداث.

## أسهل طريقة للبدء: استكشاف المعايير الموجودة

نحن نشجعك على فحص المعايير المختلفة المتاحة في [دليل `evaluation/`](https://github.com/All-Hands-AI/OpenHands/blob/main/evaluation) في مستودعنا.

لتضمين معيار التقييم الخاص بك، نوصيك بالبدء بالمعيار الذي يتشابه أكثر مع احتياجاتك. هذه الطريقة يمكن أن تسهل كثيرًا عملية الدمج، مما يتيح لك الاستفادة من الهياكل الحالية وتكييفها مع متطلباتك الخاصة.

## كيفية إنشاء سير عمل للتقييم

لإنشاء سير عمل لتقييم معيارك، اتبع الخطوات التالية:

1. استيراد الأدوات المساعدة ذات الصلة بـ OpenHands:
   ```python
    import openhands.agenthub
    from evaluation.utils.shared import (
        EvalMetadata,
        EvalOutput,
        make_metadata,
        prepare_dataset,
        reset_logger_for_multiprocessing,
        run_evaluation,
    )
    from openhands.controller.state.state import State
    from openhands.core.config import (
        AppConfig,
        SandboxConfig,
        get_llm_config_arg,
        parse_arguments,
    )
    from openhands.core.logger import openhands_logger as logger
    from openhands.core.main import create_runtime, run_controller
    from openhands.events.action import CmdRunAction
    from openhands.events.observation import CmdOutputObservation, ErrorObservation
    from openhands.runtime.runtime import Runtime
   ```

2. أنشئ تكوينًا:
   ```python
   def get_config(instance: pd.Series, metadata: EvalMetadata) -> AppConfig:
       config = AppConfig(
           default_agent=metadata.agent_class,
           runtime='eventstream',
           max_iterations=metadata.max_iterations,
           sandbox=SandboxConfig(
               base_container_image='your_container_image',
               enable_auto_lint=True,
               timeout=300,
           ),
       )
       config.set_llm_config(metadata.llm_config)
       return config
   ```

3. تهيئة بيئة التشغيل وتكوين بيئة التقييم:
   ```python
   def initialize_runtime(runtime: Runtime, instance: pd.Series):
       # قم بإعداد بيئة التقييم هنا
       # على سبيل المثال، تعيين المتغيرات البيئية، تحضير الملفات، إلخ.
       pass
   ```

4. أنشئ دالة لمعالجة كل حالة:
   ```python
   from openhands.utils.async_utils import call_async_from_sync
   def process_instance(instance: pd.Series, metadata: EvalMetadata) -> EvalOutput:
       config = get_config(instance, metadata)
       runtime = create_runtime(config)
       call_async_from_sync(runtime.connect)
       initialize_runtime(runtime, instance)

       instruction = get_instruction(instance, metadata)

       state = run_controller(
           config=config,
           task_str=instruction,
           runtime=runtime,
           fake_user_response_fn=your_user_response_function,
       )

       # قيّم إجراءات العميل
       evaluation_result = await evaluate_agent_actions(runtime, instance)

       return EvalOutput(
           instance_id=instance.instance_id,
           instruction=instruction,
           test_result=evaluation_result,
           metadata=metadata,
           history=compatibility_for_eval_history_pairs(state.history),
           metrics=state.metrics.get() if state.metrics else None,
           error=state.last_error if state and state.last_error else None,
       )
   ```

5. نفذ التقييم:
   ```python
   metadata = make_metadata(llm_config, dataset_name, agent_class, max_iterations, eval_note, eval_output_dir)
   output_file = os.path.join(metadata.eval_output_dir, 'output.jsonl')
   instances = prepare_dataset(your_dataset, output_file, eval_n_limit)

   await run_evaluation(
       instances,
       metadata,
       output_file,
       num_workers,
       process_instance
   )
   ```

يقوم هذا سير العمل بإعداد التكوين، تهيئة بيئة التشغيل، معالجة كل حالة عن طريق تنفيذ العميل وتقييم إجراءاته، ثم جمع النتائج في كائن `EvalOutput`. وظيفة `run_evaluation` تدير التوازي وتتبع التقدم.

لا تنس تخصيص دوال `get_instruction`، `your_user_response_function` و `evaluate_agent_actions` وفقًا لمتطلبات معيارك المحددة.

باتباع هذا الهيكل، يمكنك إنشاء سير عمل تقييم قوي للمعيار الخاص بك في إطار العمل OpenHands.

## فهم `user_response_fn`

تعد `user_response_fn` مكونًا حيويًا في سير العمل الخاص بتقييم OpenHands. فهي تحاكي التفاعل مع العميل، مما يتيح تقديم إجابات آلية أثناء عملية التقييم. تعتبر هذه الوظيفة مفيدة بشكل خاص عندما تريد تقديم إجابات متسقة ومحددة مسبقًا للاستفسارات أو الإجراءات من العميل.

### سير العمل والتفاعل

السير العمل الصحيح لإدارة الإجراءات و `user_response_fn` هو كما يلي:

1. يتلقى العميل مهمة ويبدأ في معالجتها
2. يصدر العميل إجراءً
3. إذا كان الإجراء قابلًا للتنفيذ (مثل CmdRunAction، IPythonRunCellAction):
   - يقوم Runtime بمعالجة الإجراء
   - يعيد Runtime ملاحظة
4. إذا كان الإجراء غير قابل للتنفيذ (عادةً يكون MessageAction):
   - يتم استدعاء `user_response_fn`
   - ترجع وظيفة محاكاة استجابة المستخدم
5. يتلقى العميل إما الملاحظة أو الاستجابة المحاكاة
6. تتكرر الخطوات من 2 إلى 5 حتى تكتمل المهمة أو يتم الوصول إلى الحد الأقصى للتكرارات

إليك تمثيلًا مرئيًا أكثر دقة:

```
                 [العميل]
                    |
                    v
               [إصدار إجراء]
                    |
                    v
            [هل الإجراء قابل للتنفيذ؟]
           /                       \
         نعم                        لا
          |                          |
          v                          v
     [Runtime]               [user_response_fn]
          |                          |
          v                          v
  [إرجاع ملاحظة]           [استجابة محاكاة]
           \                        /
            \                      /
             v                    v
           [يتلقى العميل الرد]
                    |
                    v
         [استمرار أو إنهاء المهمة]
```

في هذا السير العمل:

- الإجراءات القابلة للتنفيذ (مثل تنفيذ الأوامر أو الأكواد) تتم معالجتها مباشرة بواسطة Runtime
- الإجراءات غير القابلة للتنفيذ (عادة عندما يريد العميل التواصل أو طلب توضيحات) يتم معالجتها بواسطة `user_response_fn`
- ثم يعالج العميل الرد، سواء كانت ملاحظة من Runtime أو استجابة محاكاة من `user_response_fn`

تسمح هذه الطريقة بالإدارة الآلية للإجراءات الملموسة والتفاعلات المحاكاة للمستخدم، مما يجعلها مناسبة لسيناريوهات التقييم حيث تريد اختبار قدرة العميل على إتمام المهام مع الحد

 الأدنى من التدخل البشري.

## خاتمة

بهذا الشكل، يوفر OpenHands بيئة مرنة وفعّالة لإجراء التقييمات عبر معايير مختلفة، مما يتيح لك دمج معيار التقييم الخاص بك مع الكثير من الأدوات المساعدة المتوفرة في إطار العمل.