import textwrap

from toscaparser.elements.nodetype import NodeType
from toscaparser.elements.property_definition import PropertyDef
from toscaparser.elements.capabilitytype import CapabilityTypeDef
from toscaparser.nodetemplate import NodeTemplate
from toscaparser.policy import Policy
from toscaparser.properties import Property
from toscaparser.capabilities import Capability
from toscaparser.functions import GetInput

def build_property_def(prop_def: PropertyDef) -> str:
    requiredness = "true" if prop_def.required else "false"
    return f"property({prop_def.name}, {prop_def.schema['type']}, {requiredness})"


def build_node_type_fact(node_type: NodeType) -> str:
    prop_defs = "[" \
        + ", ".join([build_property_def(prop_def) for prop_def in node_type.get_properties_def_objects()]) \
        + "]"

    def build_capability_def(cap_def: CapabilityTypeDef):
        return f"capability({cap_def.name}, '{cap_def.type}')"
    cap_defs = "[" \
        + ", ".join([build_capability_def(cap_def) for cap_def in node_type.get_capabilities_objects()]) \
        + "]"

    def build_type_requirement(req_name, req_def):
        req_cap = req_def.get("capability", "tosca.capabilities.Root")
        req_node = req_def.get("node", "tosca.nodes.Root")
        req_rel = req_def.get("relationship", "tosca.relationships.Root")
        occ = req_def.get("occurrences")
        if occ is None:
            req_occ = "occurrences(1, unbounded)"
        else:
            req_occ = f"occurrences({occ[0]}, {'unbounded' if occ[1] == 'UNBOUNDED' else occ[1]})"
        return f"requirement({req_name}, '{req_cap}', '{req_node}', '{req_rel}', {req_occ})"
    req_l = []
    for req in node_type.requirements:  # type: ignore
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


def build_cap_type_fact(captype: CapabilityTypeDef) -> str:
    prop_defs = "[" \
        + ", ".join([build_property_def(prop_def) for prop_def in captype.get_properties_def_objects()]) \
        + "]"
    
    return textwrap.dedent(f"""
    cap_type(
        '{captype.type}',
        '{captype.parent_type.type if captype.parent_type is not None else 'none'}',
        {prop_defs}
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
            prop_val_str = f"get_input({prop.value.args[0]})"
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
        return f"capability({cap.name}, {properties})"
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


def build_policy_fact(pol: Policy) -> str:
    return textwrap.dedent(f"""
    policy(
        {pol.name},
        '{pol.type}',
        [{", ".join(pol.targets)}]
    )""")
