from typing import List, Dict


def remove_equal_dictionaries(p: List[Dict]):
    tmp = {}

    for r in p:
        if r["name"] not in tmp:
            tmp[r["name"]] = r

    return list(tmp.values())