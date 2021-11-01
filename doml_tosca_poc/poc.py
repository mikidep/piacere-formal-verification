import os
import sys
import re

from pyswip import Prolog

import yaml
from yaml.loader import Loader, SafeLoader

class SafeLineLoader(SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = super(SafeLineLoader, self).construct_mapping(node, deep=deep)
        # Add 1 so line numbering starts at 1
        mapping['__line__'] = node.start_mark.line + 1
        return mapping

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

from check2swipl import build_check_pred, fmt_result

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
with open(sys.argv[1]) as toscaf:
    tosca_yaml = yaml.load(toscaf, Loader=SafeLineLoader)

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

with open("checks.yaml") as checks_yaml_f:
    check_yamls = yaml.load(checks_yaml_f, Loader=Loader)
for check_yaml in check_yamls:
    header, description, ext_vars, pred = build_check_pred(check_yaml)
    prolog.assertz(pred)
    results = prolog.query(header)
    for ext_var in ext_vars:
        description = re.sub(
            re.escape(ext_var) + r"(?!\w)",
            "{" + ext_var + "}",
            description
        )
    for res in results:
        fmt_dict = {ext_var: fmt_result(res[ext_vars[ext_var]]) for ext_var in ext_vars} # type: ignore
        print(description.format(**fmt_dict))

# hardcoded_db_passwords = prolog.query("has_hardcoded_db_password(X)")
# for res in hardcoded_db_passwords:
#     nodename = res['X'] # type: ignore
#     line = tosca_yaml['topology_template']['node_templates'][nodename]['properties']['__line__']
#     print(f"At line {line}: node {nodename} has a hardcoded password") # type: ignore

# unsatisfied_requirements = prolog.query("has_unsatisfied_requirements(NodeName, TypeReq)")
# if unsatisfied_requirements:
#     print("\nUnsatisfied requirements:")
#     for res in unsatisfied_requirements:
#         nodename = res['NodeName'] # type: ignore
#         line = tosca_yaml['topology_template']['node_templates'][nodename]['__line__']
#         req = res['TypeReq'] # type: ignore
#         print(f"At line {line}: node {nodename} has unsatisfied {req}")