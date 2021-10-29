from typing import Tuple

import z3


def make_enum_sort(name: str, vals: list[str], optional: bool = False) \
        -> Tuple[z3.DatatypeSortRef, dict[str, z3.DatatypeRef]]:
    if optional:
        sort, refs = z3.EnumSort(name, ["some_" + val for val in vals] + ["none"])
        sort.none = refs[-1]  # type: ignore
        refs_dict = {val: ref for val, ref in zip(vals, refs[:-1])}
    else:
        sort, refs = z3.EnumSort(name, vals)
        refs_dict = {val: ref for val, ref in zip(vals, refs)}
    return sort, refs_dict
