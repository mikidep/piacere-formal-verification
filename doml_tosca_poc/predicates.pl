extends_type(TypeA, TypeA).
extends_type(TypeA, TypeB) :-
    node_type(TypeA, ExtTypeA, _, _, _), !,
    ExtTypeA \= none,
    extends_type(ExtTypeA, TypeB).

% capabilities of ancestor types are automatically filled in by tosca-parser,
% so there is no need to use extends_type
type_offers_capability(Type, CapType) :-
    node_type(Type, _, _, Caps, _),
    member(capability(_, CapType), Caps).

% requirements of ancestor types are automatically filled in by tosca-parser,
% so there is no need to use extends_type
type_has_requirement(Type, Req) :-
    node_type(Type, _, _, _, Reqs),
    member(Req, Reqs).

requirement_satisfied(NodeReqs, requirement(ReqName, CapType)) :-
    member(requirement(ReqName, NodeName), NodeReqs),
    node(NodeName, NodeType, _, _, _),
    type_offers_capability(NodeType, CapType).