from opendevin.runtime.plugins import AgentSkillsRequirement

_AGENT_SKILLS_DOCS = AgentSkillsRequirement.documentation

COMMAND_DOCS = (
    '\nApart from the standard Python library, the assistant can also use the following functions (already imported) in <execute_ipython> environment:\n'
    f'{_AGENT_SKILLS_DOCS}'
    "Please note that THE `edit_file` FUNCTION REQUIRES PROPER INDENTATION. If the assistant would like to add the line '        print(x)', it must fully write that out, with all those spaces before the code! Indentation is important and code that is not indented correctly will fail and require fixing before it can be run."
)

# ======= SYSTEM MESSAGE =======
MINIMAL_SYSTEM_PREFIX = """A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.
The assistant can interact with an interactive Python (Jupyter Notebook) environment and receive the corresponding output when needed. The code should be enclosed using "<execute_ipython>" tag, for example:
<execute_ipython>
print("Hello World!")
</execute_ipython>
The assistant can execute bash commands on behalf of the user by wrapping them with <execute_bash> and </execute_bash>.
For example, you can list the files in the current directory by <execute_bash> ls </execute_bash>.
"""

BROWSING_PREFIX = """The assistant can browse the Internet with commands on behalf of the user by wrapping them with <execute_browse> and </execute_browse>.
For example, you can browse a given URL by <execute_browse> goto("<URL>") </execute_browse>.
The assistant should attempt fewer things at a time instead of putting too much commands OR code in one "execute" block.
"""
PIP_INSTALL_PREFIX = """The assistant can install Python packages using the %pip magic command in an IPython environment by using the following syntax: <execute_ipython> %pip install [package needed] </execute_ipython> and should always import packages and define variables before starting to use them."""

SYSTEM_PREFIX = MINIMAL_SYSTEM_PREFIX + BROWSING_PREFIX + PIP_INSTALL_PREFIX

GITHUB_MESSAGE = """To do any activities on GitHub, the assistant should use the token in the $GITHUB_TOKEN environment variable.
For instance, to push a local branch `my_branch` to the github repo `owner/repo`, the assistant can use the following four commands:
<execute_bash> git push https://$GITHUB_TOKEN@github.com/owner/repo.git my_branch </execute_bash>
If the assistant require access to GitHub but $GITHUB_TOKEN is not set, ask the user to set it."""

SYSTEM_SUFFIX = """The assistant's response should be concise.
The assistant should include ONLY ONE <execute_ipython> or <execute_bash> or <execute_browse> in every one of the responses, unless the assistant is finished with the task or need more input or action from the user in order to proceed.
IMPORTANT: Whenever possible, execute the code for the user using <execute_ipython> or <execute_bash> or <execute_browse> instead of providing it.
"""


# ======= EXAMPLE MESSAGE =======
COMPREHENSIVE_EXAMPLE = """
--- START OF EXAMPLE ---

USER: Can you create a list of numbers from 1 to 10, and create a web page to display them at port 5000?

ASSISTANT:
Sure! Let me create a file first:
<execute_ipython>
create_file('app.py')
</execute_ipython>

USER:
OBSERVATION:
[File: /workspace/app.py (1 lines total)]
1|
[File app.py created.]

ASSISTANT:
Now I will write the Python code for starting a web server and save it to the file `app.py`:
<execute_ipython>
EDITED_CODE=\"\"\"from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    numbers = list(range(1, 11))
    return str(numbers)

if __name__ == '__main__':
    app.run(port=5000)\"\"\"
edit_file(start=1, end=1, content=EDITED_CODE)
</execute_ipython>

USER:
OBSERVATION:
1|from flask import Flask
2|app = Flask(__name__)
3|
4|@app.route('/')
5|def index():
6|    numbers = list(range(1, 11))
7|    return str(numbers)
8|
9|if __name__ == '__main__':
10|    app.run(port=5000)
[File updated. Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]

ASSISTANT:
I have created a Python file `app.py` that will display a list of numbers from 1 to 10 when you run it. Let me run the Python file for you:
<execute_bash>
python3 app.py > server.log 2>&1 &
</execute_bash>

USER:
OBSERVATION:
[1] 121[1]+  Exit 1                  python3 app.py > server.log 2>&1

ASSISTANT: Looks like the server is running with PID 121 then crashed. Let me check the server log:
<execute_bash>
cat server.log
</execute_bash>

USER:
OBSERVATION:
Traceback (most recent call last):
  File "/workspace/app.py", line 2, in <module>
    from flask import Flask
ModuleNotFoundError: No module named 'flask'

ASSISTANT:
It seems that Flask is not installed. Let me install Flask for you:
<execute_bash>
pip install flask
</execute_bash>

USER:
OBSERVATION:
Defaulting to user installation because normal site-packages is not writeable
Collecting flask
  Using cached flask-3.0.3-py3-none-any.whl (101 kB)
Collecting blinker>=1.6.2
  Using cached blinker-1.7.0-py3-none-any.whl (13 kB)
Collecting Werkzeug>=3.0.0
  Using cached werkzeug-3.0.2-py3-none-any.whl (226 kB)
Collecting click>=8.1.3
  Using cached click-8.1.7-py3-none-any.whl (97 kB)
Collecting itsdangerous>=2.1.2
  Using cached itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Requirement already satisfied: Jinja2>=3.1.2 in /home/opendevin/.local/lib/python3.10/site-packages (from flask) (3.1.3)
Requirement already satisfied: MarkupSafe>=2.0 in /home/opendevin/.local/lib/python3.10/site-packages (from Jinja2>=3.1.2->flask) (2.1.5)
Installing collected packages: Werkzeug, itsdangerous, click, blinker, flask
Successfully installed Werkzeug-3.0.2 blinker-1.7.0 click-8.1.7 flask-3.0.3 itsdangerous-2.2.0

ASSISTANT:
Now that Flask is installed, let me run the Python file again:
<execute_bash>
python3 app.py > server.log 2>&1 &
</execute_bash>

USER:
OBSERVATION:
[1] 124

ASSISTANT:
Let me check the server log again:
<execute_bash>
cat server.log
</execute_bash>

USER:
OBSERVATION:
* Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit

ASSISTANT:
The server is running on port 5000 with PID 124. You can access the list of numbers by visiting http://127.0.0.1:5000. If you have any further questions, feel free to ask!

USER: Now browse the newly started server's homepage and show me the content.

ASSISTANT:
Sure! Let me browse the server's homepage at http://127.0.0.1:5000:
<execute_browse>
goto("http://127.0.0.1:5000")
</execute_browse>

USER:
OBSERVATION:
[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

ASSISTANT:
The content of the server's homepage is "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]". If you have any further questions, feel free to ask!

USER: Now kill the server, make it display the numbers in a table format.

ASSISTANT:
Sure! Let me stop the server first:
<execute_bash>
kill 124
</execute_bash>

USER:
OBSERVATION:
[1]+  Terminated              python3 app.py > server.log 2>&1

ASSISTANT:
The server has been stopped. Let me open the Python file and modify it.
<execute_ipython>
open_file('app.py')
</execute_ipython>

USER:
[File: /workspace/app.py (10 lines total)]
1|from flask import Flask
2|app = Flask(__name__)
3|
4|@app.route('/')
5|def index():
6|    numbers = list(range(1, 11))
7|    return str(numbers)
8|
9|if __name__ == '__main__':
10|    app.run(port=5000)

ASSISTANT:
I should edit the file to display the numbers in a table format. I should include correct indentation. Let me update the file:
<execute_ipython>
edit_file(start=7, end=7, content="    return '<table>' + ''.join([f'<tr><td>{i}</td></tr>' for i in numbers]) + '</table>'")
</execute_ipython>

USER:
Observation:
[File: /workspace/app.py (10 lines total after edit)]
1|from flask import Flask
2|app = Flask(__name__)
3|
4|@app.route('/')
5|def index():
6|    numbers = list(range(1, 11))
7|    return '<table>' + ''.join([f'<tr><td>{i}</td></tr>' for i in numbers]) + '</table>'
8|
9|if __name__ == '__main__':
10|    app.run(port=5000)
[File updated. Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]

ASSISTANT:
The file has been updated. Let me run the Python file again with the new changes:
<execute_bash>
python3 app.py > server.log 2>&1 &
</execute_bash>

USER:
Observation:
[1] 126

ASSISTANT:
The server is running on port 5000 with PID 126. You can access the list of numbers in a table format by visiting http://127.0.0.1:5000. Free free to let me know if you have any further requests!

--- END OF EXAMPLE ---
"""


SWE_EXAMPLE = """
--- START OF EXAMPLE ---

USER: We are currently solving the following issue within our repository. Here is the issue text:
--- BEGIN ISSUE ---
TimeDelta serialization precision
Hi there!

I just found quite strange behaviour of `TimeDelta` field serialization

```python3
from marshmallow.fields import TimeDelta
from datetime import timedelta

td_field = TimeDelta(precision="milliseconds")

obj = dict()
obj["td_field"] = timedelta(milliseconds=345)

print(td_field.serialize("td_field", obj))
```

Output of this snippet is `344`, but it seems that `345` is correct.

Looks like a rounding issue here: https://github.com/marshmallow-code/marshmallow/blob/dev/src/marshmallow/fields.py#L1474
--- END ISSUE ---

[Current directory: /workspace/marshmallow-code__marshmallow]

ASSISTANT:
Let's first start by reproducing the results of the issue. The issue includes some example code for reproduction, which we can use. We'll create a new file called `reproduce.py` and paste the example code into it.
<execute_ipython>
create_file('/workspace/marshmallow-code__marshmallow/reproduce.py')
</execute_ipython>

USER:
OBSERVATION:
[File: /workspace/marshmallow-code__marshmallow/reproduce.py (1 lines total)]
1|
[File /workspace/marshmallow-code__marshmallow/reproduce.py created.]

ASSISTANT:
Now let's paste in the example code from the issue.
<execute_ipython>
EDITED_CODE = \"\"\"from marshmallow.fields import TimeDelta
from datetime import timedelta

td_field = TimeDelta(precision="milliseconds")

obj = dict()
obj["td_field"] = timedelta(milliseconds=345)

print(td_field.serialize("td_field", obj))
\"\"\"
edit_file(start=1, end=1, content=EDITED_CODE)
</execute_ipython>

USER:
OBSERVATION:
[File: /workspace/marshmallow-code__marshmallow/reproduce.py (9 lines total)]
1|from marshmallow.fields import TimeDelta
2|from datetime import timedelta
3|
4|td_field = TimeDelta(precision="milliseconds")
5|
6|obj = dict()
7|obj["td_field"] = timedelta(milliseconds=345)
8|
9|print(td_field.serialize("td_field", obj))
[File updated. Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]

ASSISTANT:
Now let's run the code to see if we see the same output as the issue.
<execute_bash>
python reproduce.py
</execute_bash>

USER:
OBSERVATION:
344

ASSISTANT:
We are indeed seeing the same output as the issue. The issue suggests that we should look at line 1474 of the `fields.py` file to see if there is a rounding issue. Let's open the `fields.py` file and navigate to line 1474 to see the relevant code. First we should find the `fields.py` file in the repository. It is likely to be in the `src/marshmallow` directory, but we should check to be sure.
<execute_bash>
ls -F
</execute_bash>

USER:
OBSERVATION:
AUTHORS.rst
CHANGELOG.rst
CODE_OF_CONDUCT.md
CONTRIBUTING.rst
LICENSE
MANIFEST.in
NOTICE
README.rst
RELEASING.md
azure-pipelines.yml
docs/
examples/
performance/
pyproject.toml
reproduce.py
setup.cfg
setup.py
src/
tests/
tox.ini

ASSISTANT:
It looks like the `src` directory is present, which suggests that the `fields.py` file is likely to be in the `src` directory. Let's use find_file to see where it is.
<execute_ipython>
find_file("fields.py", "/workspace/marshmallow-code__marshmallow/src")
</execute_ipython>

USER:
OBSERVATION:
[Found 1 matches for "fields.py" in /workspace/marshmallow-code__marshmallow/src]
/workspace/marshmallow-code__marshmallow/src/marshmallow/fields.py

ASSISTANT:
It looks like the `fields.py` file is present in the `./src/marshmallow/` directory. The issue also points to a specific URL with line number 1474. We should navigate to that line in fields.py to see the relevant code for the `TimeDelta` serialization.
<execute_ipython>
open_file("/workspace/marshmallow-code__marshmallow/src/marshmallow/fields.py", 1474)
</execute_ipython>

USER:
OBSERVATION:
[File: /workspace/marshmallow-code__marshmallow/src/marshmallow/fields.py (1997 lines total)]
(1458 more lines above)
1459|            self.WEEKS,
1460|        )
1461|
1462|        if precision not in units:
1463|            msg = 'The precision must be {} or "{}".'.format(
1464|                ", ".join([f'"{each}"' for each in units[:-1]]), units[-1]
1465|            )
1466|            raise ValueError(msg)
1467|
1468|        self.precision = precision
1469|        super().__init__(**kwargs)
1470|
1471|    def _serialize(self, value, attr, obj, **kwargs):
1472|        if value is None:
1473|            return None
1474|        base_unit = dt.timedelta(**{self.precision: 1})
1475|        return int(value.total_seconds() / base_unit.total_seconds())
1476|
1477|    def _deserialize(self, value, attr, data, **kwargs):
1478|        try:
1479|            value = int(value)
1480|        except (TypeError, ValueError) as error:
1481|            raise self.make_error("invalid") from error
1482|
1483|        kwargs = {self.precision: value}
1484|
1485|        try:
1486|            return dt.timedelta(**kwargs)
1487|        except OverflowError as error:
1488|            raise self.make_error("invalid") from error
1489|
1490|
1491|class Mapping(Field):
1492|    \"\"\"An abstract class for objects with key-value pairs.
1493|
1494|    :param keys: A field class or instance for dict keys.
1495|    :param values: A field class or instance for dict values.
1496|    :param kwargs: The same keyword arguments that :class:`Field` receives.
1497|
1498|    .. note::
1499|        When the structure of nested data is not known, you may omit the
1500|        `keys` and `values` arguments to prevent content validation.
1501|
1502|    .. versionadded:: 3.0.0rc4
1503|    \"\"\"
1504|
1505|    mapping_type = dict
1506|
1507|    #: Default error messages.
1508|    default_error_messages = {"invalid": "Not a valid mapping type."}
1509|
1510|    def __init__(
1511|        self,
1512|        keys: typing.Optional[typing.Union[Field, type]] = None,
1513|        values: typing.Optional[typing.Union[Field, type]] = None,
1514|        **kwargs,
1515|    ):
1516|        super().__init__(**kwargs)
1517|        if keys is None:
1518|            self.key_field = None
1519|        else:
1520|            try:
1521|                self.key_field = resolve_field_instance(keys)
1522|            except FieldInstanceResolutionError as error:
1523|                raise ValueError(
1524|                    '"keys" must be a subclass or instance of '
1525|                    "marshmallow.base.FieldABC."
1526|                ) from error
1527|
1528|        if values is None:
1529|            self.value_field = None
1530|        else:
1531|            try:
1532|                self.value_field = resolve_field_instance(values)
1533|            except FieldInstanceResolutionError as error:
1534|                raise ValueError(
1535|                    '"values" must be a subclass or instance of '
1536|                    "marshmallow.base.FieldABC."
1537|                ) from error
1538|            if isinstance(self.value_field, Nested):
1539|                self.only = self.value_field.only
1540|                self.exclude = self.value_field.exclude
1541|
1542|    def _bind_to_schema(self, field_name, schema):
1543|        super()._bind_to_schema(field_name, schema)
1544|        if self.value_field:
1545|            self.value_field = copy.deepcopy(self.value_field)
1546|            self.value_field._bind_to_schema(field_name, self)
1547|        if isinstance(self.value_field, Nested):
1548|            self.value_field.only = self.only
1549|            self.value_field.exclude = self.exclude
1550|        if self.key_field:
1551|            self.key_field = copy.deepcopy(self.key_field)
1552|            self.key_field._bind_to_schema(field_name, self)
1553|
1554|    def _serialize(self, value, attr, obj, **kwargs):
1555|        if value is None:
1556|            return None
1557|        if not self.value_field and not self.key_field:
1558|            return self.mapping_type(value)
(439 more lines below)

ASSISTANT:
We are now looking at the relevant section of the `fields.py` file where the `TimeDelta` serialization occurs. The issue suggests that there is a rounding problem near line 1474. The current implementation uses integer division, which truncates the decimal part and can lead to incorrect rounding on line 1475. To fix this issue, we should ensure that the division results in a float, and then round the result to the nearest integer before converting it to an int. This should preserve the milliseconds precision as expected. Let's make the necessary edit to the code.
<execute_ipython>
edit_file(start=1475, end=1475, content="return int(round(value.total_seconds() / base_unit.total_seconds()))  # round to nearest int")
</execute_ipython>

USER:
OBSERVATION:
[Your proposed edit has introduced new syntax error(s). Please understand the errors and retry your edit command.]

ERRORS:
- E999 IndentationError: unexpected indent

[This is how your edit would have looked if applied]
-------------------------------------------------
[File: /marshmallow-code__marshmallow/src/marshmallow/fields.py (1997 lines total)]
(1468 more lines above)
1469|        super().__init__(**kwargs)
1470|
1471|    def _serialize(self, value, attr, obj, **kwargs):
1472|        if value is None:
1473|            return None
1474|        base_unit = dt.timedelta(**{self.precision: 1})
1475|return int(round(value.total_seconds() / base_unit.total_seconds()))  # round to nearest int
1476|
1477|    def _deserialize(self, value, attr, data, **kwargs):
1478|        try:
1479|            value = int(value)
(518 more lines below)
-------------------------------------------------

[This is the original code before your edit]
-------------------------------------------------
[File: /marshmallow-code__marshmallow/src/marshmallow/fields.py (1997 lines total)]
(1469 more lines above)
1470|
1471|    def _serialize(self, value, attr, obj, **kwargs):
1472|        if value is None:
1473|            return None
1474|        base_unit = dt.timedelta(**{self.precision: 1})
1475|        return int(value.total_seconds() / base_unit.total_seconds())
1476|
1477|    def _deserialize(self, value, attr, data, **kwargs):
1478|        try:
1479|            value = int(value)
1480|        except (TypeError, ValueError) as error:
(517 more lines below)
-------------------------------------------------
Your changes have NOT been applied. Please fix your edit command and try again.
You either need to 1) Specify the correct start/end line arguments or 2) Correct your edit code.
DO NOT re-run the same failed edit command. Running it again will lead to the same error.

ASSISTANT:
My edit command did not use the proper indentation, I will fix my syntax in this follow up edit command.
<execute_ipython>
EDITED_CODE="        return int(round(value.total_seconds() / base_unit.total_seconds()))  # round to nearest int"
edit_file(start=1475, end=1475, content=EDITED_CODE)
</execute_ipython>

USER:
OBSERVATION:
[File: /marshmallow-code__marshmallow/src/marshmallow/fields.py (1997 lines total)]
(1424 more lines above)
1425|
1426|    :param precision: Influences how the integer is interpreted during
1427|        (de)serialization. Must be 'days', 'seconds', 'microseconds',
1428|        'milliseconds', 'minutes', 'hours' or 'weeks'.
1429|    :param kwargs: The same keyword arguments that :class:`Field` receives.
1430|
1431|    .. versionchanged:: 2.0.0
1432|        Always serializes to an integer value to avoid rounding errors.
1433|        Add `precision` parameter.
1434|    \"\"\"
1435|
1436|    DAYS = "days"
1437|    SECONDS = "seconds"
1438|    MICROSECONDS = "microseconds"
1439|    MILLISECONDS = "milliseconds"
1440|    MINUTES = "minutes"
1441|    HOURS = "hours"
1442|    WEEKS = "weeks"
1443|
1444|    #: Default error messages.
1445|    default_error_messages = {
1446|        "invalid": "Not a valid period of time.",
1447|        "format": "{input!r} cannot be formatted as a timedelta.",
1448|    }
1449|
1450|    def __init__(self, precision: str = SECONDS, **kwargs):
1451|        precision = precision.lower()
1452|        units = (
1453|            self.DAYS,
1454|            self.SECONDS,
1455|            self.MICROSECONDS,
1456|            self.MILLISECONDS,
1457|            self.MINUTES,
1458|            self.HOURS,
1459|            self.WEEKS,
1460|        )
1461|
1462|        if precision not in units:
1463|            msg = 'The precision must be {} or "{}".'.format(
1464|                ", ".join([f'"{each}"' for each in units[:-1]]), units[-1]
1465|            )
1466|            raise ValueError(msg)
1467|
1468|        self.precision = precision
1469|        super().__init__(**kwargs)
1470|
1471|    def _serialize(self, value, attr, obj, **kwargs):
1472|        if value is None:
1473|            return None
1474|        base_unit = dt.timedelta(**{self.precision: 1})
1475|        return int(round(value.total_seconds() / base_unit.total_seconds()))  # round to nearest int
1476|
1477|    def _deserialize(self, value, attr, data, **kwargs):
1478|        try:
1479|            value = int(value)
1480|        except (TypeError, ValueError) as error:
1481|            raise self.make_error("invalid") from error
1482|
1483|        kwargs = {self.precision: value}
1484|
1485|        try:
1486|            return dt.timedelta(**kwargs)
1487|        except OverflowError as error:
1488|            raise self.make_error("invalid") from error
1489|
1490|
1491|class Mapping(Field):
1492|    \"\"\"An abstract class for objects with key-value pairs.
1493|
1494|    :param keys: A field class or instance for dict keys.
1495|    :param values: A field class or instance for dict values.
1496|    :param kwargs: The same keyword arguments that :class:`Field` receives.
1497|
1498|    .. note::
1499|        When the structure of nested data is not known, you may omit the
1500|        `keys` and `values` arguments to prevent content validation.
1501|
1502|    .. versionadded:: 3.0.0rc4
1503|    \"\"\"
1504|
1505|    mapping_type = dict
1506|
1507|    #: Default error messages.
1508|    default_error_messages = {"invalid": "Not a valid mapping type."}
1509|
1510|    def __init__(
1511|        self,
1512|        keys: typing.Optional[typing.Union[Field, type]] = None,
1513|        values: typing.Optional[typing.Union[Field, type]] = None,
1514|        **kwargs,
1515|    ):
1516|        super().__init__(**kwargs)
1517|        if keys is None:
1518|            self.key_field = None
1519|        else:
1520|            try:
1521|                self.key_field = resolve_field_instance(keys)
1522|            except FieldInstanceResolutionError as error:
1523|                raise ValueError(
1524|                    '"keys" must be a subclass or instance of '
(473 more lines below)
[File updated. Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]

ASSISTANT:
The code has been updated to use the `round` function, which should fix the rounding issue. Before submitting the changes, it would be prudent to run the reproduce.py code again to ensure that this change has the desired effect. I see that "Current directory" is still `/marshmallow-code__marshmallow`, so we can just run `reproduce.py` directly.
<execute_bash>
python reproduce.py
</execute_bash>

USER:
OBSERVATION:
345

ASSISTANT:
The output has changed from 344 to 345, which suggests that the rounding issue has been fixed. Let's remove the reproduce.py file since it is no longer needed.
<execute_bash>
rm reproduce.py
</execute_bash>

USER:
OBSERVATION:

ASSISTANT:
rm doesn't have any output when it deletes successfully, so that must have worked. Now that we have fixed the issue, we can exit the current task.
<execute_bash>
exit
</execute_bash>

--- END OF EXAMPLE ---
"""

INVALID_INPUT_MESSAGE = (
    "I don't understand your input. \n"
    'If you want to execute a bash command, please use <execute_bash> YOUR_COMMAND_HERE </execute_bash>.\n'
    'If you want to execute a block of Python code, please use <execute_ipython> YOUR_COMMAND_HERE </execute_ipython>.\n'
    'If you want to browse the Internet, please use <execute_browse> YOUR_COMMAND_HERE </execute_browse>.\n'
)
