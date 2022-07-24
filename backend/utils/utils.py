from typing import List, Dict


def remove_equal_dictionaries(p: List[Dict], key: str = "product"):
    tmp = {}

    for r in p:
        if r[key] not in tmp:
            tmp[r[key]] = r

    return list(tmp.values())
