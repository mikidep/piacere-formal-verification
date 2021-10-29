from typing import Tuple

from toscaparser.tosca_template import ToscaTemplate
from toscaparser.nodetemplate import NodeTemplate
from toscaparser.functions import Function as ToscaFunc
import z3

from .z3_utils import make_enum_sort
from .tosca_utils import get_node_names, get_node_prop_names, get_node_type_names, get_strings, get_function_names


def _declare_stringsym_sort(tpl: ToscaTemplate, ) \
        -> Tuple[z3.DatatypeSortRef, dict[str, z3.DatatypeRef]]:
    def symbolize(s: str) -> str:
        return "".join([c.lower() if c.isalnum() else "_"
                        for c in s[:16]])

    strings = get_strings(tpl)
    ss_list = [f"ss_{i}_{symbolize(s)}"
               for i, s in enumerate(strings)]
    stringsym_sort, ss_refs_dict = \
        make_enum_sort("StringSym", ss_list)
    stringsym_sort_dict = \
        {s: ss_refs_dict[ss] for s, ss in zip(strings, ss_list)}
    return stringsym_sort, stringsym_sort_dict


def _declare_val_sort(stringsym_sort: z3.DatatypeSortRef, funcsym_sort: z3.DatatypeSortRef) \
        -> Tuple[z3.DatatypeSortRef, z3.DatatypeSortRef]:
    val_sort = z3.Datatype("Val")
    list_val_sort = z3.Datatype("List_Val")

    val_sort.declare("int", ("intval", z3.IntSort()))
    val_sort.declare("float", ("floatval", z3.RealSort()))
    val_sort.declare("str", ("strval", stringsym_sort))
    val_sort.declare("list", ("listval", list_val_sort))
    val_sort.declare("func", ("funcsymval", funcsym_sort), ("fargsval", list_val_sort))
    val_sort.declare("none")
    # TODO: map

    list_val_sort.declare("nil")
    list_val_sort.declare("cons", ("car", val_sort), ("cdr", list_val_sort))

    return z3.CreateDatatypes(val_sort, list_val_sort)  # type: ignore


def _convert_val_to_z3(v,
                       val_sort: z3.DatatypeSortRef,
                       list_val_sort: z3.DatatypeSortRef,
                       stringsym_sort_dict: dict[str, z3.DatatypeRef],
                       funcsym_sort_dict: dict[str, z3.DatatypeRef]) \
        -> z3.DatatypeRef:

    class UnsupportedToscaValException(Exception):
        pass

    def construct_val_list(val_l: list) -> z3.DatatypeRef:
        res = list_val_sort.nil  # type: ignore
        for v in reversed(val_l):
            res = list_val_sort.cons(_convert_val_to_z3(  # type: ignore
                v,
                val_sort,
                list_val_sort,
                stringsym_sort_dict,
                funcsym_sort_dict
            ), res)
        return res

    if isinstance(v, int):
        return val_sort.int(v)  # type: ignore
    elif isinstance(v, float):
        return val_sort.float(v)  # type: ignore
    elif isinstance(v, str):
        return val_sort.str(stringsym_sort_dict[v])  # type: ignore
    elif isinstance(v, list):
        return construct_val_list(v)
    elif isinstance(v, ToscaFunc):
        fsym = funcsym_sort_dict[v.name]
        arglist = construct_val_list(v.args)
        return val_sort.func(fsym, arglist)  # type: ignore
    else:
        raise UnsupportedToscaValException()


def _declare_node_type_f(tpl: ToscaTemplate,
                         node_sort: z3.DatatypeSortRef,
                         node_sort_dict: dict[str, z3.DatatypeRef],
                         node_type_sort: z3.DatatypeSortRef,
                         node_type_sort_dict: dict[str, z3.DatatypeRef]) \
        -> Tuple[z3.FuncDeclRef, z3.BoolRef]:
    node_type_f = z3.Function("node_type", node_sort, node_type_sort)
    assertions = [
        node_type_f(node_sort_dict[n.name]) == node_type_sort_dict[n.type]
        for n in tpl.nodetemplates
    ] + [node_type_f(node_sort.none) == node_type_sort.none]  # type: ignore
    return node_type_f, z3.And(*assertions)  # type: ignore


def _declare_node_prop_f(tpl: ToscaTemplate,
                         node_sort: z3.DatatypeSortRef,
                         node_sort_dict: dict[str, z3.DatatypeRef],
                         val_sort: z3.DatatypeSortRef,
                         list_val_sort: z3.DatatypeSortRef,
                         stringsym_sort_dict: dict[str, z3.DatatypeRef],
                         funcsym_sort_dict: dict[str, z3.DatatypeRef],
                         node_prop_sort: z3.DatatypeSortRef,
                         node_prop_sort_dict: dict[str, z3.DatatypeRef]) \
        -> Tuple[z3.FuncDeclRef, z3.BoolRef]:
    node_prop_f = z3.Function("node_prop", node_sort, node_prop_sort, val_sort)

    def make_node_prop_assertion(node: NodeTemplate, prop_name: str) -> z3.BoolRef:
        if prop_name in node.get_properties():
            return node_prop_f(node_sort_dict[node.name], node_prop_sort_dict[prop_name]) == \
                _convert_val_to_z3(node.get_property_value(prop_name),  # type: ignore
                                   val_sort,
                                   list_val_sort,
                                   stringsym_sort_dict,
                                   funcsym_sort_dict)
        else:
            return node_prop_f(node_sort_dict[node.name], node_prop_sort_dict[prop_name]) == \
                val_sort.none  # type: ignore

    assertions = [
        make_node_prop_assertion(node, prop_name)
        for node in tpl.nodetemplates
        for prop_name in get_node_prop_names(tpl)
    ] + [
        node_prop_f(node_sort.none, node_prop_sort_dict[prop_name]) == val_sort.none  # type: ignore
        for prop_name in get_node_prop_names(tpl)
    ]
    return node_prop_f, z3.And(*assertions)  # type: ignore


class Z3ToscaModel:
    def __init__(self, tpl: ToscaTemplate) -> None:
        self.tpl = tpl

        self.stringsym_sort, self.stringsym_sort_dict = \
            _declare_stringsym_sort(self.tpl)
        self.funcsym_sort, self.funcsym_sort_dict = \
            make_enum_sort("FuncSym", get_function_names(tpl))
        self.val_sort, self.list_val_sort = \
            _declare_val_sort(self.stringsym_sort, self.funcsym_sort)
        self.node_sort, self.node_sort_dict = \
            make_enum_sort("Node", get_node_names(tpl), optional=True)
        self.node_type_sort, self.node_type_sort_dict = \
            make_enum_sort("NodeType", get_node_type_names(tpl), optional=True)
        self.node_prop_sort, self.node_prop_sort_dict = \
            make_enum_sort("NodeProp", get_node_prop_names(tpl))
        self.solver = z3.Solver()
        self.node_type_f, node_type_f_ass = \
            _declare_node_type_f(
                self.tpl,
                self.node_sort,
                self.node_sort_dict,
                self.node_type_sort,
                self.node_type_sort_dict
            )
        self.solver.add(node_type_f_ass)
        self.node_prop_f, self.node_prop_f_ass = \
            _declare_node_prop_f(
                self.tpl,
                self.node_sort,
                self.node_sort_dict,
                self.val_sort,
                self.list_val_sort,
                self.stringsym_sort_dict,
                self.funcsym_sort_dict,
                self.node_prop_sort,
                self.node_prop_sort_dict
            )
        self.solver.add(self.node_prop_f_ass)
