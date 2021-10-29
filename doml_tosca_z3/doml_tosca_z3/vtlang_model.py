from typing import Tuple

from textx import metamodel_from_file
import z3

from .z3toscamodel import Z3ToscaModel


class StringNotFoundException(Exception):
    pass


class SymbolNotFoundException(Exception):
    pass


class UndeclaredValException(Exception):
    pass


class InvalidAccessException(Exception):
    pass


class TypeMismatchException(Exception):
    pass


def _process_vtmodel(vtm,
                     vars: dict[str, Tuple[z3.DatatypeRef, str]],
                     toscamodel: Z3ToscaModel) -> None:
    def process_node_decl(node_decl):
        varname = node_decl.var[1:]
        vars[varname] = z3.Const(varname, toscamodel.node_sort), "Node"  # type: ignore

    def process_assertion(assertion):
        assbr = process_bool_expr(assertion.be)
        toscamodel.solver.add(assbr)

    def get_id_ref(id) -> Tuple[z3.DatatypeRef, str]:
        sym = toscamodel.node_type_sort_dict.get(id)
        if sym is not None:
            return sym, "NodeType"
        else:
            sym = toscamodel.node_sort_dict.get(id)
            if sym is not None:
                return sym, "Node"
            else:
                print(f"Symbol '{id}' not found in model.")
                raise SymbolNotFoundException()

    # var starts with $
    def get_var_ref(var) -> Tuple[z3.DatatypeRef, str]:
        varsym = vars.get(var[1:])
        if varsym is not None:
            return varsym
        else:
            print(f"Undeclared variable '{var}'.")
            raise UndeclaredValException()

    def get_member_ref(ref: Tuple[z3.DatatypeRef, str], member: list[str]) -> Tuple[z3.DatatypeRef, str]:
        if not member:
            return ref
        else:
            mem, *memtail = member
            refref, reftype = ref
            if reftype == "Node":
                propsym = toscamodel.node_prop_sort_dict.get(mem)
                if propsym is not None:
                    return get_member_ref(
                        (toscamodel.node_prop_f(refref, propsym), "Val"),  # type: ignore
                        memtail
                    )
                else:
                    print(f"Property '{mem}' not found in model.")
                    raise SymbolNotFoundException()
            else:
                print(f"Cannot access properties of values of type '{reftype}'")
                raise InvalidAccessException()

    def process_ref(ref) -> Tuple[z3.DatatypeRef, str]:
        if ref.__class__.__name__ == "TypeOfRef":
            refref, reftype = process_ref(ref.ref)
            if reftype == "Node":
                return toscamodel.node_type_f(refref), "NodeType"  # type: ignore
            else:
                print(f"Cannot evaluate type() of value of type {reftype}")
                raise TypeMismatchException()
        elif ref.__class__.__name__ == "AccessRef":
            if ref.id is not None:
                root_ref = get_id_ref(ref.id)
            else:  # if ref.var is not None:
                root_ref = get_var_ref(ref.var)
            return get_member_ref(root_ref, ref.member)
        elif type(ref) is int:
            return toscamodel.val_sort.int(z3.IntVal(ref)), "Val"  # type: ignore
        else:  # if type(ref) is str:
            ssym = toscamodel.stringsym_sort_dict.get(ref)
            if ssym is not None:
                return toscamodel.val_sort.str(ssym), "Val"  # type: ignore
            else:
                print(f"String {repr(ref)} not found in model.")
                raise StringNotFoundException()

    def process_bool_expr(be) -> z3.BoolRef:
        # if be.__class__.__name__ in ["EqBoolExpr", "NeBoolExpr"]:
        z3lref, ltype = process_ref(be.lref)
        z3rref, rtype = process_ref(be.rref)

        if ltype != rtype:
            print(f"Cannot compare values of types {ltype} and {rtype}")
            raise TypeMismatchException()

        if ltype == "Node":
            not_none = z3lref != toscamodel.node_sort.none  # type: ignore
        elif ltype == "NodeType":
            not_none = z3lref != toscamodel.node_type_sort.none  # type: ignore
        else:  # if ltype == "Val"
            not_none = z3lref != toscamodel.val_sort.none  # type: ignore

        res = z3.And(
            z3lref == z3rref,
            not_none
        )

        if be.__class__.__name__ == "NeBoolExpr":
            res = z3.Not(res)

        return res  # type: ignore

    for statement in vtm.statements:
        stmt = statement.stmt
        if stmt.__class__.__name__ == "NodeDecl":
            process_node_decl(stmt)
        elif stmt.__class__.__name__ == "Assertion":
            process_assertion(stmt)


class VTLangModel:
    def __init__(self, filename: str, toscamodel: Z3ToscaModel) -> None:
        self.toscamodel = toscamodel
        vtmm = metamodel_from_file("vtlang.tx")
        vtm = vtmm.model_from_file(filename)
        self.solver = toscamodel.solver

        self.vars = {}
        _process_vtmodel(vtm, self.vars, self.toscamodel)
