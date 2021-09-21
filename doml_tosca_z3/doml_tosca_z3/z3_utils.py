from typing import Tuple

import z3

option: dict[z3.SortRef, z3.DatatypeSortRef] = {}


def create_option_datatype(sort: z3.SortRef) -> z3.DatatypeSortRef:
    global option
    optsort = z3.Datatype("Option_" + sort.name())
    optsort.declare("some", ("val", sort))
    optsort.declare("none")
    optsort = optsort.create()
    option[sort] = optsort
    return optsort


def make_enum_sort(name: str, vals: list[str]) \
        -> Tuple[z3.DatatypeSortRef, dict[str, z3.DatatypeRef]]:
    sort, refs = z3.EnumSort(name, vals)
    refs_dict = {val: ref for val, ref in zip(vals, refs)}
    return sort, refs_dict
