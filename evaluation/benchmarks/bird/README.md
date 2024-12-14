# BIRD Evaluation with OpenHands

Implements evaluation of agents on BIRD introduced in [Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs](https://arxiv.org/abs/2305.03111). Please see [here](https://bird-bench.github.io/) for the reference implementation used in the paper.

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Run Inference on Bird

```bash
./evaluation/benchmarks/bird/scripts/run_infer.sh [model_config] [git-version]
```

- `model_config`, e.g. `eval_gpt4_1106_preview`, is the config group name for your
LLM settings, as defined in your `config.toml`.

- `git-version`, e.g. `HEAD`, is the git commit hash of the OpenHands version you would
like to evaluate. It could also be a release tag like `0.6.2`.

## Examples

For each problem, OpenHands is given a set number of iterations to fix the failing code. The history field shows each iteration's response to correct its code that fails any test case.

```json
{
  "task_id": "0",
  "instruction": "You are a SQL expert and need to complete the following text-to-SQL tasks.\n\nCREATE TABLE frpm\n(\n    CDSCode                                       TEXT not null\n        primary key,\n    `Academic Year`                               TEXT  null,\n    `County Code`                                 TEXT  null,\n    `District Code`                               INTEGER         null,\n    `School Code`                                 TEXT  null,\n    `County Name`                                 TEXT null,\n    `District Name`                               TEXT null,\n    `School Name`                                 TEXT null,\n    `District Type`                               TEXT null,\n    `School Type`                                 TEXT null,\n    `Educational Option Type`                     TEXT null,\n    `NSLP Provision Status`                       TEXT null,\n    `Charter School (Y/N)`                        INTEGER    null,\n    `Charter School Number`                       TEXT  null,\n    `Charter Funding Type`                        TEXT null,\n    IRC                                           INTEGER    null,\n    `Low Grade`                                   TEXT  null,\n    `High Grade`                                  TEXT null,\n    `Enrollment (K-12)`                           REAL      null,\n    `Free Meal Count (K-12)`                      REAL       null,\n    `Percent (%) Eligible Free (K-12)`            REAL       null,\n    `FRPM Count (K-12)`                           REAL       null,\n    `Percent (%) Eligible FRPM (K-12)`            REAL       null,\n    `Enrollment (Ages 5-17)`                      REAL       null,\n    `Free Meal Count (Ages 5-17)`                 REAL       null,\n    `Percent (%) Eligible Free (Ages 5-17)`       REAL       null,\n    `FRPM Count (Ages 5-17)`                      REAL       null,\n    `Percent (%) Eligible FRPM (Ages 5-17)`       REAL       null,\n    `2013-14 CALPADS Fall 1 Certification Status` INTEGER    null,\n    foreign key (CDSCode) references schools (CDSCode)\n);\n\nCREATE TABLE satscores\n(\n    cds         TEXT not null\n        primary key,\n    rtype       TEXT  not null,\n    sname       TEXT null,\n    dname       TEXT null,\n    cname       TEXT null,\n    enroll12    INTEGER         not null,\n    NumTstTakr  INTEGER          not null,\n    AvgScrRead  INTEGER          null,\n    AvgScrMath  INTEGER          null,\n    AvgScrWrite INTEGER          null,\n    NumGE1500   INTEGER          null,\n--     PctGE1500   double      null,\n        foreign key (cds) references schools (CDSCode)\n);\n\nCREATE TABLE schools\n(\n    CDSCode     TEXT not null\n        primary key,\n    NCESDist    TEXT  null,\n    NCESSchool  TEXT  null,\n    StatusType  TEXT  not null,\n    County      TEXT not null,\n    District    TEXT not null,\n    School      TEXT null,\n    Street      TEXT null,\n    StreetAbr   TEXT null,\n    City        TEXT null,\n    Zip         TEXT null,\n    State       TEXT  null,\n    MailStreet  TEXT null,\n    MailStrAbr  TEXT null,\n    MailCity    TEXT null,\n    MailZip     TEXT null,\n    MailState   TEXT  null,\n    Phone       TEXT null,\n    Ext         TEXT  null,\n    Website     TEXT null,\n    OpenDate    DATE        null,\n    ClosedDate  DATE        null,\n    Charter     INTEGER    null,\n    CharterNum  TEXT  null,\n    FundingType TEXT null,\n    DOC         TEXT  not null,\n    DOCType     TEXT not null,\n    SOC         TEXT  null,\n    SOCType     TEXT null,\n    EdOpsCode   TEXT  null,\n    EdOpsName   TEXT null,\n    EILCode     TEXT  null,\n    EILName     TEXT null,\n    GSoffered   TEXT null,\n    GSserved    TEXT  null,\n    Virtual     TEXT  null,\n    Magnet      INTEGER   null,\n    Latitude    REAL      null,\n    Longitude   REAL      null,\n    AdmFName1   TEXT null,\n    AdmLName1   TEXT null,\n    AdmEmail1   TEXT null,\n    AdmFName2   TEXT null,\n    AdmLName2   TEXT null,\n    AdmEmail2   TEXT null,\n    AdmFName3   TEXT  null,\n    AdmLName3   TEXT null,\n    AdmEmail3   TEXT null,\n    LastUpdate  DATE        not null\n);\n\n-- External Knowledge: Eligible free rate for K-12 = `Free Meal Count (K-12)` / `Enrollment (K-12)`\n\n-- Using valid SQLite and understanding External Knowledge, answer the following questions for the tables provided above.\n\n-- Using valid SQLite, answer the following questions for the tables provided above.\nQuestion: What is the highest eligible free rate for K-12 students in the schools in Alameda County?\n\n\nPlease write the SQL in one line without line breaks.And write a new python file named 0.py to call the SQL you wrote.You need to follow the code template below:\n\n\n    import sqlite3\n    def execute_sql(db_path, sql):\n        with sqlite3.connect(db_path) as conn:\n            cursor = conn.cursor()\n            cursor.execute(sql)\n            result = cursor.fetchall()\n            return result\n\n    if __name__ == '__main__':\n        sql = \"\" # filling your SQL here\n        db_path = \"california_schools/california_schools.sqlite\"\n        print(db_path)\n        result = execute_sql(db_path, sql)\n        print(result)\n    \n\nEnvironment has been set up for you to start working.You may assume all necessary tools are installed.\n\nIMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\nYou SHOULD INCLUDE PROPER INDENTATION in your edit commands.\nWhen you think you have fixed the issue through code changes, please finish the interaction using the "finish" tool.\n",
  "metadata": {
    "agent_class": "CodeActAgent",
    "model_name": "gpt-4-1106-preview",
    "max_iterations": 5,
    "eval_output_dir": "evaluation/evaluation_outputs/outputs/bird/CodeActAgent/gpt-4-1106-preview_maxiter_5_N_v1.5",
    "start_time": "2024-05-29 02:00:22",
    "git_commit": "ae105c2fafc64ad3eeb7a8bea09119fcb5865bc4"
  },
  "history": [
    [
      {
        "id": 0,
        "timestamp": "2024-05-29T02:00:46.498136",
        "source": "user",
        "message": "You are a SQL expert and need to complete the following text-to-SQL tasks.\n\nCREATE TABLE frpm\n(\n    CDSCode                                       TEXT not null\n        primary key,\n    `Academic Year`                               TEXT  null,\n    `County Code`                                 TEXT  null,\n    `District Code`                               INTEGER         null,\n    `School Code`                                 TEXT  null,\n    `County Name`                                 TEXT null,\n    `District Name`                               TEXT null,\n    `School Name`                                 TEXT null,\n    `District Type`                               TEXT null,\n    `School Type`                                 TEXT null,\n    `Educational Option Type`                     TEXT null,\n    `NSLP Provision Status`                       TEXT null,\n    `Charter School (Y/N)`                        INTEGER    null,\n    `Charter School Number`                       TEXT  null,\n    `Charter Funding Type`                        TEXT null,\n    IRC                                           INTEGER    null,\n    `Low Grade`                                   TEXT  null,\n    `High Grade`                                  TEXT null,\n    `Enrollment (K-12)`                           REAL      null,\n    `Free Meal Count (K-12)`                      REAL       null,\n    `Percent (%) Eligible Free (K-12)`            REAL       null,\n    `FRPM Count (K-12)`                           REAL       null,\n    `Percent (%) Eligible FRPM (K-12)`            REAL       null,\n    `Enrollment (Ages 5-17)`                      REAL       null,\n    `Free Meal Count (Ages 5-17)`                 REAL       null,\n    `Percent (%) Eligible Free (Ages 5-17)`       REAL       null,\n    `FRPM Count (Ages 5-17)`                      REAL       null,\n    `Percent (%) Eligible FRPM (Ages 5-17)`       REAL       null,\n    `2013-14 CALPADS Fall 1 Certification Status` INTEGER    null,\n    foreign key (CDSCode) references schools (CDSCode)\n);\n\nCREATE TABLE satscores\n(\n    cds         TEXT not null\n        primary key,\n    rtype       TEXT  not null,\n    sname       TEXT null,\n    dname       TEXT null,\n    cname       TEXT null,\n    enroll12    INTEGER         not null,\n    NumTstTakr  INTEGER          not null,\n    AvgScrRead  INTEGER          null,\n    AvgScrMath  INTEGER          null,\n    AvgScrWrite INTEGER          null,\n    NumGE1500   INTEGER          null,\n--     PctGE1500   double      null,\n        foreign key (cds) references schools (CDSCode)\n);\n\nCREATE TABLE schools\n(\n    CDSCode     TEXT not null\n        primary key,\n    NCESDist    TEXT  null,\n    NCESSchool  TEXT  null,\n    StatusType  TEXT  not null,\n    County      TEXT not null,\n    District    TEXT not null,\n    School      TEXT null,\n    Street      TEXT null,\n    StreetAbr   TEXT null,\n    City        TEXT null,\n    Zip         TEXT null,\n    State       TEXT  null,\n    MailStreet  TEXT null,\n    MailStrAbr  TEXT null,\n    MailCity    TEXT null,\n    MailZip     TEXT null,\n    MailState   TEXT  null,\n    Phone       TEXT null,\n    Ext         TEXT  null,\n    Website     TEXT null,\n    OpenDate    DATE        null,\n    ClosedDate  DATE        null,\n    Charter     INTEGER    null,\n    CharterNum  TEXT  null,\n    FundingType TEXT null,\n    DOC         TEXT  not null,\n    DOCType     TEXT not null,\n    SOC         TEXT  null,\n    SOCType     TEXT null,\n    EdOpsCode   TEXT  null,\n    EdOpsName   TEXT null,\n    EILCode     TEXT  null,\n    EILName     TEXT null,\n    GSoffered   TEXT null,\n    GSserved    TEXT  null,\n    Virtual     TEXT  null,\n    Magnet      INTEGER   null,\n    Latitude    REAL      null,\n    Longitude   REAL      null,\n    AdmFName1   TEXT null,\n    AdmLName1   TEXT null,\n    AdmEmail1   TEXT null,\n    AdmFName2   TEXT null,\n    AdmLName2   TEXT null,\n    AdmEmail2   TEXT null,\n    AdmFName3   TEXT  null,\n    AdmLName3   TEXT null,\n    AdmEmail3   TEXT null,\n    LastUpdate  DATE        not null\n);\n\n-- External Knowledge: Eligible free rate for K-12 = `Free Meal Count (K-12)` / `Enrollment (K-12)`\n\n-- Using valid SQLite and understanding External Knowledge, answer the following questions for the tables provided above.\n\n-- Using valid SQLite, answer the following questions for the tables provided above.\nQuestion: What is the highest eligible free rate for K-12 students in the schools in Alameda County?\n\n\nPlease write the SQL in one line without line breaks.And write a new python file named 0.py to call the SQL you wrote.You need to follow the code template below:\n\n\n    import sqlite3\n    def execute_sql(db_path, sql):\n        with sqlite3.connect(db_path) as conn:\n            cursor = conn.cursor()\n            cursor.execute(sql)\n            result = cursor.fetchall()\n            return result\n\n    if __name__ == '__main__':\n        sql = \"\" # filling your SQL here\n        db_path = \"california_schools/california_schools.sqlite\"\n        print(db_path)\n        result = execute_sql(db_path, sql)\n        print(result)\n    \n\nEnvironment has been set up for you to start working.You may assume all necessary tools are installed.\n\nIMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\nYou SHOULD INCLUDE PROPER INDENTATION in your edit commands.\nWhen you think you have fixed the issue through code changes, please finish the interaction using the "finish" tool.\n",
        "action": "message",
        "args": {
          "content": "You are a SQL expert and need to complete the following text-to-SQL tasks.\n\nCREATE TABLE frpm\n(\n    CDSCode                                       TEXT not null\n        primary key,\n    `Academic Year`                               TEXT  null,\n    `County Code`                                 TEXT  null,\n    `District Code`                               INTEGER         null,\n    `School Code`                                 TEXT  null,\n    `County Name`                                 TEXT null,\n    `District Name`                               TEXT null,\n    `School Name`                                 TEXT null,\n    `District Type`                               TEXT null,\n    `School Type`                                 TEXT null,\n    `Educational Option Type`                     TEXT null,\n    `NSLP Provision Status`                       TEXT null,\n    `Charter School (Y/N)`                        INTEGER    null,\n    `Charter School Number`                       TEXT  null,\n    `Charter Funding Type`                        TEXT null,\n    IRC                                           INTEGER    null,\n    `Low Grade`                                   TEXT  null,\n    `High Grade`                                  TEXT null,\n    `Enrollment (K-12)`                           REAL      null,\n    `Free Meal Count (K-12)`                      REAL       null,\n    `Percent (%) Eligible Free (K-12)`            REAL       null,\n    `FRPM Count (K-12)`                           REAL       null,\n    `Percent (%) Eligible FRPM (K-12)`            REAL       null,\n    `Enrollment (Ages 5-17)`                      REAL       null,\n    `Free Meal Count (Ages 5-17)`                 REAL       null,\n    `Percent (%) Eligible Free (Ages 5-17)`       REAL       null,\n    `FRPM Count (Ages 5-17)`                      REAL       null,\n    `Percent (%) Eligible FRPM (Ages 5-17)`       REAL       null,\n    `2013-14 CALPADS Fall 1 Certification Status` INTEGER    null,\n    foreign key (CDSCode) references schools (CDSCode)\n);\n\nCREATE TABLE satscores\n(\n    cds         TEXT not null\n        primary key,\n    rtype       TEXT  not null,\n    sname       TEXT null,\n    dname       TEXT null,\n    cname       TEXT null,\n    enroll12    INTEGER         not null,\n    NumTstTakr  INTEGER          not null,\n    AvgScrRead  INTEGER          null,\n    AvgScrMath  INTEGER          null,\n    AvgScrWrite INTEGER          null,\n    NumGE1500   INTEGER          null,\n--     PctGE1500   double      null,\n        foreign key (cds) references schools (CDSCode)\n);\n\nCREATE TABLE schools\n(\n    CDSCode     TEXT not null\n        primary key,\n    NCESDist    TEXT  null,\n    NCESSchool  TEXT  null,\n    StatusType  TEXT  not null,\n    County      TEXT not null,\n    District    TEXT not null,\n    School      TEXT null,\n    Street      TEXT null,\n    StreetAbr   TEXT null,\n    City        TEXT null,\n    Zip         TEXT null,\n    State       TEXT  null,\n    MailStreet  TEXT null,\n    MailStrAbr  TEXT null,\n    MailCity    TEXT null,\n    MailZip     TEXT null,\n    MailState   TEXT  null,\n    Phone       TEXT null,\n    Ext         TEXT  null,\n    Website     TEXT null,\n    OpenDate    DATE        null,\n    ClosedDate  DATE        null,\n    Charter     INTEGER    null,\n    CharterNum  TEXT  null,\n    FundingType TEXT null,\n    DOC         TEXT  not null,\n    DOCType     TEXT not null,\n    SOC         TEXT  null,\n    SOCType     TEXT null,\n    EdOpsCode   TEXT  null,\n    EdOpsName   TEXT null,\n    EILCode     TEXT  null,\n    EILName     TEXT null,\n    GSoffered   TEXT null,\n    GSserved    TEXT  null,\n    Virtual     TEXT  null,\n    Magnet      INTEGER   null,\n    Latitude    REAL      null,\n    Longitude   REAL      null,\n    AdmFName1   TEXT null,\n    AdmLName1   TEXT null,\n    AdmEmail1   TEXT null,\n    AdmFName2   TEXT null,\n    AdmLName2   TEXT null,\n    AdmEmail2   TEXT null,\n    AdmFName3   TEXT  null,\n    AdmLName3   TEXT null,\n    AdmEmail3   TEXT null,\n    LastUpdate  DATE        not null\n);\n\n-- External Knowledge: Eligible free rate for K-12 = `Free Meal Count (K-12)` / `Enrollment (K-12)`\n\n-- Using valid SQLite and understanding External Knowledge, answer the following questions for the tables provided above.\n\n-- Using valid SQLite, answer the following questions for the tables provided above.\nQuestion: What is the highest eligible free rate for K-12 students in the schools in Alameda County?\n\n\nPlease write the SQL in one line without line breaks.And write a new python file named 0.py to call the SQL you wrote.You need to follow the code template below:\n\n\n    import sqlite3\n    def execute_sql(db_path, sql):\n        with sqlite3.connect(db_path) as conn:\n            cursor = conn.cursor()\n            cursor.execute(sql)\n            result = cursor.fetchall()\n            return result\n\n    if __name__ == '__main__':\n        sql = \"\" # filling your SQL here\n        db_path = \"california_schools/california_schools.sqlite\"\n        print(db_path)\n        result = execute_sql(db_path, sql)\n        print(result)\n    \n\nEnvironment has been set up for you to start working.You may assume all necessary tools are installed.\n\nIMPORTANT: You should ONLY interact with the environment provided to you AND NEVER ASK FOR HUMAN HELP.\nYou SHOULD INCLUDE PROPER INDENTATION in your edit commands.\nWhen you think you have fixed the issue through code changes, please finish the interaction using the "finish" tool.\n",
          "wait_for_response": false
        }
      },
      {
        "message": "No observation",
        "observation": "null",
        "content": "",
        "extras": {}
      }
    ],
    [
      {
        "id": 5,
        "timestamp": "2024-05-29T02:00:49.776373",
        "source": "agent",
        "message": "Running Python code interactively: create_file('0.py')",
        "action": "run_ipython",
        "args": {
          "code": "create_file('0.py')",
          "thought": "Let's start by creating the Python file `0.py` with the provided template. Then, I will fill in the SQL query to find the highest eligible free rate for K-12 students in the schools in Alameda County.",
          "kernel_init_code": "from agentskills import *"
        }
      },
      {
        "id": 6,
        "timestamp": "2024-05-29T02:00:50.218391",
        "source": "agent",
        "message": "Code executed in IPython cell.",
        "cause": 5,
        "observation": "run_ipython",
        "content": "[File: /workspace/0.py (1 lines total)]\r\n1|\r\n[File 0.py created.]\r\n",
        "extras": {
          "code": "create_file('0.py')"
        }
      }
    ],
    [
      {
        "id": 7,
        "timestamp": "2024-05-29T02:01:02.238250",
        "source": "agent",
        "message": "Running Python code interactively: EDITED_CODE = \"\"\"import sqlite3\n\ndef execute_sql(db_path, sql):\n    with sqlite3.connect(db_path) as conn:\n        cursor = conn.cursor()\n        cursor.execute(sql)\n        result = cursor.fetchall()\n        return result\n\nif __name__ == '__main__':\n    sql = \"SELECT MAX(\\`Free Meal Count (K-12)\\` / \\`Enrollment (K-12)\\`) AS highest_eligible_free_rate FROM frpm JOIN schools ON frpm.CDSCode = schools.CDSCode WHERE \\`County Name\\` = 'Alameda'\"\n    db_path = \"california_schools/california_schools.sqlite\"\n    print(db_path)\n    result = execute_sql(db_path, sql)\n    print(result)\n\"\"\"\nedit_file(start=1, end=1, content=EDITED_CODE)",
        "action": "run_ipython",
        "args": {
          "code": "EDITED_CODE = \"\"\"import sqlite3\n\ndef execute_sql(db_path, sql):\n    with sqlite3.connect(db_path) as conn:\n        cursor = conn.cursor()\n        cursor.execute(sql)\n        result = cursor.fetchall()\n        return result\n\nif __name__ == '__main__':\n    sql = \"SELECT MAX(\\`Free Meal Count (K-12)\\` / \\`Enrollment (K-12)\\`) AS highest_eligible_free_rate FROM frpm JOIN schools ON frpm.CDSCode = schools.CDSCode WHERE \\`County Name\\` = 'Alameda'\"\n    db_path = \"california_schools/california_schools.sqlite\"\n    print(db_path)\n    result = execute_sql(db_path, sql)\n    print(result)\n\"\"\"\nedit_file(start=1, end=1, content=EDITED_CODE)",
          "thought": "Now I will write the Python code with the SQL query to find the highest eligible free rate for K-12 students in Alameda County and save it to the file `0.py`.",
          "kernel_init_code": "from agentskills import *"
        }
      },
      {
        "id": 8,
        "timestamp": "2024-05-29T02:01:02.775798",
        "source": "agent",
        "message": "Code executed in IPython cell.",
        "cause": 7,
        "observation": "run_ipython",
        "content": "[File: /workspace/0.py (16 lines total after edit)]\r\n1|import sqlite3\r\n2|\r\n3|def execute_sql(db_path, sql):\r\n4|    with sqlite3.connect(db_path) as conn:\r\n5|        cursor = conn.cursor()\r\n6|        cursor.execute(sql)\r\n7|        result = cursor.fetchall()\r\n8|        return result\r\n9|\r\n10|if __name__ == '__main__':\r\n11|    sql = \"SELECT MAX(`Free Meal Count (K-12)` / `Enrollment (K-12)`) AS highest_eligible_free_rate FROM frpm JOIN schools ON frpm.CDSCode = schools.CDSCode WHERE `County Name` = 'Alameda'\"\r\n12|    db_path = \"california_schools/california_schools.sqlite\"\r\n13|    print(db_path)\r\n14|    result = execute_sql(db_path, sql)\r\n15|    print(result)\r\n16|\r\n[File updated. Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary.]\r\n",
        "extras": {
          "code": "EDITED_CODE = \"\"\"import sqlite3\n\ndef execute_sql(db_path, sql):\n    with sqlite3.connect(db_path) as conn:\n        cursor = conn.cursor()\n        cursor.execute(sql)\n        result = cursor.fetchall()\n        return result\n\nif __name__ == '__main__':\n    sql = \"SELECT MAX(\\`Free Meal Count (K-12)\\` / \\`Enrollment (K-12)\\`) AS highest_eligible_free_rate FROM frpm JOIN schools ON frpm.CDSCode = schools.CDSCode WHERE \\`County Name\\` = 'Alameda'\"\n    db_path = \"california_schools/california_schools.sqlite\"\n    print(db_path)\n    result = execute_sql(db_path, sql)\n    print(result)\n\"\"\"\nedit_file(start=1, end=1, content=EDITED_CODE)"
        }
      }
    ],
    [
      {
        "id": 9,
        "timestamp": "2024-05-29T02:01:13.053834",
        "source": "agent",
        "message": "Running command: python3 0.py",
        "action": "run",
        "args": {
          "command": "python3 0.py",
          "thought": "The Python code with the SQL query has been written to the file `0.py`. Now, let's run the Python script to execute the SQL query and get the result."
        }
      },
      {
        "id": 10,
        "timestamp": "2024-05-29T02:01:13.222204",
        "source": "agent",
        "message": "Command `python3 0.py` executed with exit code 0.",
        "cause": 9,
        "observation": "run",
        "content": "california_schools/california_schools.sqlite\r\n[(1.0,)]",
        "extras": {
          "command_id": -1,
          "command": "python3 0.py",
          "exit_code": 0
        }
      }
    ],
    [
      {
        "id": 11,
        "timestamp": "2024-05-29T02:01:18.663380",
        "source": "agent",
        "message": "All done! What's next on the agenda?",
        "action": "finish",
        "args": {
          "outputs": {},
          "thought": ""
        }
      },
      {
        "message": "No observation",
        "observation": "null",
        "content": "",
        "extras": {}
      }
    ]
  ],
  "error": null,
  "test_result": {
    "result": {
      "passed": 1,
      "status": "success"
    },
    "metadata": {
      "timeout": 10,
      "gen_sql": "SELECT MAX(`Free Meal Count (K-12)` / `Enrollment (K-12)`) AS highest_eligible_free_rate FROM frpm JOIN schools ON frpm.CDSCode = schools.CDSCode WHERE `County Name` = 'Alameda'",
      "gold_sql": "SELECT `Free Meal Count (K-12)` / `Enrollment (K-12)` FROM frpm WHERE `County Name` = 'Alameda' ORDER BY (CAST(`Free Meal Count (K-12)` AS REAL) / `Enrollment (K-12)`) DESC LIMIT 1"
    }
  }
}
```
