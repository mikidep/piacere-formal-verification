import re
from typing import Tuple

var_re = re.compile(r"\$[a-z][A-Za-z0-9_]*")

def get_unique_int() -> int:
    get_unique_int.counter += 1
    return get_unique_int.counter
get_unique_int.counter = -1

def capitalize_first(s: str) -> str:
    if not s:
        return s
    else:
        return s[0].upper() + s[1:]

def is_var(s: str) -> bool:
    return var_re.fullmatch(s) is not None

def atom_or_var(s: str, delimiter="'") -> str:
    if is_var(s):
        return capitalize_first(s[1:])
    elif s == "$_":
        return "_"
    else:
        return delimiter + s + delimiter

def get_vars_from_str(s: str) -> dict[str, str]:
    global var_re
    return {m: atom_or_var(m) for m in var_re.findall(s)}

def build_check_pred(check_yaml) -> Tuple[str, str, dict[str, str], str]:
    name = check_yaml["name"]
    description = check_yaml["description"]
    formula = check_yaml["check"]
    ext_vars_dict = get_vars_from_str(description)
    ext_vars = list(ext_vars_dict.values())
    header = f"{name}({', '.join(ext_vars)})"
    return header, description, ext_vars_dict, f"{header} :- {build_formula_term(formula)}"

def build_term(term) -> str:
    if type(term) is str:
        return atom_or_var(term)
    elif type(term) is list:
        return "[" + ", ".join(build_term(t) for t in term) + "]"
    elif type(term) is dict:
        assert len(term) == 1, "Dict term can only have one key"
        root = list(term)[0]
        assert type(term[root]) is dict \
            and "args" in term[root] \
            and type(term[root]["args"]) is list, \
            "Dict term must have an 'args' key with the list of " \
            + "the arguments of the term"
        return root + "(" + ", ".join(build_term(t) for t in term[root]["args"]) + ")"
    else:
        return str(term)

def build_node_pred(node) -> str:
    node_struct_err = """Node must have structure:
    <node name>:
        [type: <node type>]
        [properties: <properties ...> | $var]
        [capabilities: <capabilities ...> | $var]
        [requirements: <requirements ...> | $var]"""
    
    assert type(node) is dict and len(node) == 1, node_struct_err
    root = list(node)[0]
    node_name = atom_or_var(root)
    assert type(node[root]) is dict, node_struct_err
    node_type = atom_or_var(node[root].get("type", "$_"))
    node_int = get_unique_int()

    def build_props_list(props_dict) -> list[str]:
        res = []
        for pname, pval in props_dict.items():
            pname = atom_or_var(pname)
            if type(pval) is str:
                pval = atom_or_var(pval, delimiter='"')
            res.append(f"property({pname}, {pval})")
        return res

    props_list = []
    props_var = "_"
    if "properties" in node[root]:
        if type(node[root]["properties"]) is str and is_var(node[root]["properties"]):
            props_var = atom_or_var(node[root]["properties"])
        else:
            props_var = f"Props{node_int}"
            props_list = build_props_list(node[root]["properties"])
    
    caps_list = []
    caps_var = "_"
    if "capabilities" in node[root]:
        if type(node[root]["capabilities"]) is str and is_var(node[root]["capabilities"]):
            caps_var = atom_or_var(node[root]["capabilities"])
        else:
            caps_var = f"Caps{node_int}"
            for cname, cdict in node[root]["capabilities"].items():
                cname = atom_or_var(cname)
                assert "properties" in cdict, "Capabilities in node should contain properties"
                cprops_list = build_props_list(cdict["properties"])
                caps_list.append(f"capability({cname}, [{', '.join(cprops_list)}])")

    reqs_list = []
    reqs_var = "_"
    if "requirements" in node[root]:
        if type(node[root]["requirements"]) is str and is_var(node[root]["requirements"]):
            reqs_var = atom_or_var(node[root]["requirements"])
        else:
            reqs_var = f"Reqs{node_int}"
            for req in node[root]["requirements"]:
                rname, rval = list(req.items())[0]
                rname = atom_or_var(rname)
                rval = atom_or_var(rval)
                reqs_list.append(f"requirement({rname}, {rval})")

    preds = [f"node({node_name}, {node_type}, {props_var}, {caps_var}, {reqs_var})"]
    if props_list:
        preds.append(f"subset([{', '.join(props_list)}], {props_var})")
    if caps_list:
        preds.append(f"subset([{', '.join(caps_list)}], {caps_var})")
    if reqs_list:
        preds.append(f"subset([{', '.join(reqs_list)}], {reqs_var})")
    return ", ".join(preds)
    
def build_formula_term(formula) -> str:
    assert type(formula) is dict and len(formula) == 1, \
        "Every formula must be a dictionary with one key"
    root = list(formula)[0]
    op_s = formula[root]
    if root == "and":
        assert type(op_s) is list, "'and' connective requires a list of formulas"
        return ", ".join(build_formula_term(op) for op in op_s)
    elif root == "or":
        assert type(op_s) is list, "'or' connective requires a list of formulas"
        return "(" + "; ".join(build_formula_term(op) for op in op_s) + ")"
    elif root == "not":
        return "\\+ (" + build_formula_term(op_s) + ")"
    elif root == "match":
        assert type(op_s) is list and len(op_s) == 2, "'match' requires two arguments"
        return build_term(op_s[0]) + " = " + build_term(op_s[1])
    elif root == "predicate":
        assert type(op_s) is dict and len(op_s) == 1, "'predicate' requires a single dict term"
        return build_term(op_s)
    elif root == "node":
        return build_node_pred(op_s)
    else:
        return "unsupported"
