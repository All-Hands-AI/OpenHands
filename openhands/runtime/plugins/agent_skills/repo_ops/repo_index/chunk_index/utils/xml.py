import re
from typing import List


def extract_between_tags(tag: str, string: str, strip: bool = False) -> List[str]:
    ext_list = re.findall(f'<{tag}>(.+?)</{tag}>', string, re.DOTALL)
    if strip:
        ext_list = [e.strip() for e in ext_list]
    return ext_list


def contains_tag(tag: str, string: str) -> bool:
    return bool(re.search(f'<{tag}>', string, re.DOTALL))


# def contains_tag(tag: str, string: str) -> bool:
#    return bool(re.search(f"<{tag}>(.+?)</{tag}>", string, re.DOTALL))
