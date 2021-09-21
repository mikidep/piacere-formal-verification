from toscaparser.elements.capabilitytype import CapabilityTypeDef
from toscaparser.tosca_template import ToscaTemplate
from toscaparser.elements.nodetype import NodeType
from toscaparser.nodetemplate import NodeTemplate
from toscaparser.properties import Property
from toscaparser.capabilities import Capability
from toscaparser.functions import Function


def get_types_and_supertypes_for_nodes(node_tpls: list[NodeTemplate]):
    def get_type_and_supertypes(ntype: NodeType) -> list[NodeType]:
        if ntype.parent_type is None:
            return [ntype]
        else:
            return [ntype] + get_type_and_supertypes(ntype.parent_type)
    types: list[NodeType] = []
    for node_tpl in node_tpls:
        # Extend with new types that are not already in `types`
        # checking by type name
        type_names = [ntype.type for ntype in types]
        types.extend(ntype
                     for ntype in get_type_and_supertypes(node_tpl.type_definition)  # type: ignore
                     if ntype.type not in type_names)
    return types


def get_captypes_and_parent_types_for_types(node_types: list[NodeType]) \
        -> list[CapabilityTypeDef]:
    def get_captype_and_parent_types(captype: CapabilityTypeDef) \
            -> list[CapabilityTypeDef]:
        if captype.parent_type is None:
            return [captype]
        else:
            return [captype] \
                + get_captype_and_parent_types(captype.parent_type)
    captypes: list[CapabilityTypeDef] = []
    for ntype in node_types:
        for captype in ntype.get_capabilities_objects():
            cap_names = [captype.type for captype in captypes]
            captypes.extend(captype_
                            for captype_ in get_captype_and_parent_types(captype)
                            if captype_.type not in cap_names)
    return captypes


def get_node_names(tpl: ToscaTemplate) -> list[str]:
    return [n.name for n in tpl.nodetemplates]


def get_node_type_names(tpl: ToscaTemplate) -> list[str]:
    return [t.ntype
            for t in get_types_and_supertypes_for_nodes(tpl.nodetemplates)]


def get_node_prop_names(tpl: ToscaTemplate) -> list[str]:
    res = [p.name
           for t in get_types_and_supertypes_for_nodes(tpl.nodetemplates)
           for p in t.get_properties_def_objects()]
    return list(set(res))


def iterate_vals(tpl: ToscaTemplate):
    def iter_vs_from_val(v):
        yield v
        if isinstance(v, Function):
            yield from (av
                        for a in v.args
                        for av in iter_vs_from_val(a))

    def iter_vs_from_prop(p: Property):
        yield from iter_vs_from_val(p.value)

    def iter_vs_from_cap(c: Capability):
        yield from (v
                    for p in c.get_properties_objects()
                    for v in iter_vs_from_prop(p))

    def iter_vs_from_node(n: NodeTemplate):
        yield from (v
                    for p in n.get_properties_objects()
                    for v in iter_vs_from_prop(p))
        yield from (v
                    for c in n.get_capabilities_objects()
                    for v in iter_vs_from_cap(c))

    yield from (v
                for n in tpl.nodetemplates
                for v in iter_vs_from_node(n))


def get_strings(tpl: ToscaTemplate) -> list[str]:
    it = (v for v in iterate_vals(tpl) if isinstance(v, str))
    return list(set(it))


def get_function_names(tpl: ToscaTemplate) -> list[str]:
    it = (v.name for v in iterate_vals(tpl) if isinstance(v, Function))
    return list(set(it))
