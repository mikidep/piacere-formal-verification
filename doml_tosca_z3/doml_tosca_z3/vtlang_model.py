from textx import metamodel_from_file
import z3

from .z3toscamodel import Z3ToscaModel


class StringNotFoundException(Exception):
    pass


class SymbolNotFoundException(Exception):
    pass


class UndeclaredValException(Exception):
    pass


def _process_vtmodel(vtm,
                     vars: dict[str, z3.DatatypeRef],
                     toscamodel: Z3ToscaModel) -> None:
    def process_node_decl(node_decl):
        varname = node_decl.var[:1]
        vars[varname] = z3.Const(varname, toscamodel.node_type_sort)  # type: ignore

    def process_assertion(assertion):
        assbr = process_bool_expr(assertion.be)
        toscamodel.solver.add(assbr)

    def get_id_ref(id) -> z3.DatatypeRef:
        sym = toscamodel.node_type_sort_dict.get(id)
        if sym is not None:
            pass

    # var starts with $
    def get_var_ref(var) -> z3.DatatypeRef:
        varsym = vars.get(var[:1])
        if varsym is not None:
            return varsym
        else:
            print(f"Undeclared variable '{var}'.")
            raise UndeclaredValException()

    def get_member_ref(ref: z3.DatatypeRef, member: list[str]) -> z3.DatatypeRef:
        pass

    def process_ref(ref) -> z3.DatatypeRef:
        if ref.__class__.__name__ == "TypeOfRef":
            return toscamodel.node_type_f(ref.ref)  # type: ignore
        elif ref.__class__.__name__ == "AccessRef":
            if ref.id is not None:
                root_ref = get_id_ref(ref.id)
            else:  # if ref.var is not None:
                root_ref = get_var_ref(ref.var)
            return get_member_ref(root_ref, ref.member)
        elif type(ref) is int:
            return toscamodel.option_val_sort.some(  # type: ignore
                toscamodel.val_sort.int(z3.IntVal(ref))  # type: ignore
            )
        else:  # if type(ref) is str:
            ssym = toscamodel.stringsym_sort_dict.get(ref)
            if ssym is not None:
                return toscamodel.option_val_sort.some(  # type: ignore
                    toscamodel.val_sort.str(ssym)  # type: ignore
                )
            else:
                print(f"String {repr(ref)} not found in model.")
                raise StringNotFoundException()

    def process_bool_expr(be) -> z3.BoolRef:
        if be.__class__.__name__ == "EqBoolExpr":
            z3lref = process_ref(be.lref)
            z3rref = process_ref(be.rref)
            return z3.And(  # type: ignore
                z3lref == z3rref,
                z3lref != toscamodel.option_val_sort.none  # type: ignore
            )
        else:  # if be.__class__.__name__ == "NeBoolExpr":
            z3lref = process_ref(be.lref)
            z3rref = process_ref(be.rref)
            return z3.Not(z3.And(  # type: ignore
                z3lref == z3rref,
                z3lref != toscamodel.option_val_sort.none  # type: ignore
            ))

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
