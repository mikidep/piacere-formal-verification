import os
import sys
import textwrap
from pyswip import Prolog

from toscaparser.tosca_template import ToscaTemplate
from toscaparser.elements.nodetype import NodeType
from toscaparser.elements.property_definition import PropertyDef
from toscaparser.elements.capabilitytype import CapabilityTypeDef
from toscaparser.nodetemplate import NodeTemplate
from toscaparser.properties import Property
from toscaparser.capabilities import Capability
from toscaparser.functions import GetInput

def build_node_type_fact(node_type: NodeType) -> str:
    def build_property_def(prop_def: PropertyDef) -> str:
        requiredness = "true" if prop_def.required else "false"
        return f"property({prop_def.name}, {prop_def.schema['type']}, {requiredness})"
    prop_defs = "[" \
        + ", ".join([build_property_def(prop_def) for prop_def in node_type.get_properties_def_objects()]) \
        + "]"

    def build_capability_def(cap_def: CapabilityTypeDef):
        return f"capability({cap_def.name}, '{cap_def.type}')"
    cap_defs = "[" \
        + ", ".join([build_capability_def(cap_def) for cap_def in node_type.get_capabilities_objects()]) \
        + "]"

    def build_type_requirement(req_name, req_def):
        return f"requirement({req_name}, '{req_def['capability']}')"
    req_l = []
    for req in node_type.requirements:
        req_name = list(req)[0] # Gets the first key of req
        req_def = req[req_name]
        req_l.append(build_type_requirement(req_name, req_def))
    requirements = "[" + ", ".join(req_l) + "]"

    return textwrap.dedent(f"""
    node_type(
        '{node_type.type}',
        '{node_type.parent_type.type if node_type.parent_type is not None else 'none'}',
        {prop_defs},
        {cap_defs},
        {requirements}
    )""")
   

def build_node_fact(node_tpl: NodeTemplate) -> str:
    def build_node_property(prop: Property) -> str:
        if type(prop.value) in [int, float]:
            prop_val_str = str(prop.value)
        elif type(prop.value) is str:
            prop_val_str = '"' + prop.value + '"' # TODO: escaping
        elif type(prop.value) is bool:
            prop_val_str = "true" if prop.value else "false"
        elif type(prop.value) is GetInput:
            prop_val_str = f"input({prop.value.args[0]})"
        else:
            raise ValueError(f"Property type {type(prop.value)} not handled.")
        return f"property({prop.name}, {prop_val_str})"
    properties = "[" \
        + ", ".join([build_node_property(prop) for prop in node_tpl.get_properties_objects()]) \
        + "]"
    
    def build_node_capability(cap: Capability):
        properties = "[" \
            + ", ".join([build_node_property(prop) for prop in cap.get_properties_objects()]) \
            + "]"
        return f"capability({cap.name}, {cap.definition.type}, {properties})"
    capabilities = "[" \
        + ", ".join([build_node_capability(cap) for cap in node_tpl.get_capabilities_objects()]) \
        + "]"

    def build_node_requirement(req):
        req_name = list(req)[0]
        return f"requirement({req_name}, {req[req_name]})"
    requirements = "[" \
        + ", ".join([build_node_requirement(req) for req in node_tpl.requirements]) \
        + "]"

    return textwrap.dedent(f"""
    node(
        {node_tpl.name},
        '{node_tpl.type}',
        {properties},
        {capabilities},
        {requirements}
    )""")

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
            for ntype in get_type_and_supertypes(node_tpl.type_definition) # type: ignore
            if ntype.type not in type_names)
    return types

tosca = ToscaTemplate(sys.argv[1])
prolog = Prolog()

for node_type in get_types_and_supertypes_for_nodes(tosca.nodetemplates):
    prolog.assertz(build_node_type_fact(node_type))

for node_tpl in tosca.nodetemplates:
    prolog.assertz(build_node_fact(node_tpl))

prolog.consult(os.path.join(sys.path[0], "predicates.pl"))
prolog.consult(os.path.join(sys.path[0], "checks.pl"))

hardcoded_db_passwords = prolog.query("has_hardcoded_db_password(X)")
for res in hardcoded_db_passwords:
    print(f"Node {res['X']} has a hardcoded password") # type: ignore