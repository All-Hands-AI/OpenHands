def compare_results(check_method: str, model_answer: str, final_ans: str) -> bool:
    try:
        match check_method:
            case 'check/integer-match.py':
                return int(model_answer) == int(final_ans)
            case 'check/string-match.py':
                return (model_answer.replace('\r\n', '\n').replace('\r', '\n').strip()
                        == final_ans.replace('\r\n', '\n').replace('\r', '\n').strip())
        return False
    except Exception:
        return False


def get_pre_cmd(instance: dict) -> str:
    if 'create' in instance:
        if 'init' in instance['create']:
            if 'file' in instance['create']['init']:
                sh_file = instance['create']['init']['file']
                return f'bash ./os_interaction/scripts/{instance["task_idx"]}/{sh_file}'
    return ''


def get_post_cmd(instance: dict) -> str:
    if 'evaluation' in instance:
        if 'example' in instance['evaluation']:
            if 'code' in instance['evaluation']['example']:
                return instance['evaluation']['example']['code']
    return ''


def get_check_method(instance: dict) -> str:
    if 'evaluation' in instance:
        if 'check' in instance['evaluation']:
            for v in instance['evaluation']['check']:
                if v is None:
                    continue
                if 'file' in v:
                    return v['file']
    return ''
