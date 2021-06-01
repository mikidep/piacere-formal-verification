import os
import sys
from pyswip import Prolog

from toscaparser.elements.capabilitytype import CapabilityTypeDef
from toscaparser.tosca_template import ToscaTemplate
from toscaparser.elements.nodetype import NodeType
from toscaparser.nodetemplate import NodeTemplate

from tosca2swipl import (
    build_node_type_fact,
    build_node_fact,
    build_policy_fact,
    build_cap_type_fact
)

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

def get_captypes_and_parent_types_for_types(node_types: list[NodeType]) -> list[CapabilityTypeDef]:
    def get_captype_and_parent_types(captype: CapabilityTypeDef) -> list[CapabilityTypeDef]:
        if captype.parent_type is None:
            return [captype]
        else:
            return [captype] + get_captype_and_parent_types(captype.parent_type)
    captypes: list[CapabilityTypeDef] = []
    for ntype in node_types:
        for captype in ntype.get_capabilities_objects():
            cap_names = [captype.type for captype in captypes]
            captypes.extend(captype_
                for captype_ in get_captype_and_parent_types(captype)
                if captype_.type not in cap_names)
    return captypes
        

tosca = ToscaTemplate(sys.argv[1])
prolog = Prolog()

node_types = get_types_and_supertypes_for_nodes(tosca.nodetemplates)
for node_type in node_types:
    prolog.assertz(build_node_type_fact(node_type))
    # print(build_node_type_fact(node_type))

for cap_type in get_captypes_and_parent_types_for_types(node_types):
    prolog.assertz(build_cap_type_fact(cap_type))

for node_tpl in tosca.nodetemplates:
    prolog.assertz(build_node_fact(node_tpl))

for pol in tosca.topology_template.policies:
    prolog.assertz(build_policy_fact(pol))

prolog.consult(os.path.join(sys.path[0], "predicates.pl"))
prolog.consult(os.path.join(sys.path[0], "checks.pl"))

hardcoded_db_passwords = prolog.query("has_hardcoded_db_password(X)")
for res in hardcoded_db_passwords:
    print(f"Node {res['X']} has a hardcoded password") # type: ignore

unsatisfied_requirements = prolog.query("has_unsatisfied_requirements(NodeName, TypeReq)")
if unsatisfied_requirements:
    print("\nUnsatisfied requirements:")
    for res in unsatisfied_requirements:
        print(res)