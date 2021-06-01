extends_node_type(TypeA, TypeA).
extends_node_type(TypeA, TypeB) :-
    node_type(TypeA, ExtTypeA, _, _, _),
    ExtTypeA \= none,
    extends_node_type(ExtTypeA, TypeB).

extends_cap_type(TypeA, TypeA).
extends_cap_type(TypeA, TypeB) :-
    cap_type(TypeA, ExtTypeA, _),
    ExtTypeA \= none,
    extends_cap_type(ExtTypeA, TypeB).

% capabilities of ancestor types are automatically filled in by tosca-parser,
% so there is no need to use extends_node_type
type_offers_capability(Type, CapType) :-
    node_type(Type, _, _, Caps, _),
    member(capability(_, NCapType), Caps),
    extends_cap_type(NCapType, CapType).

% requirements of ancestor types are automatically filled in by tosca-parser,
% so there is no need to use extends_node_type
type_has_requirement(Type, Req) :-
    node_type(Type, _, _, _, Reqs),
    member(Req, Reqs).

requirement_satisfied(_, requirement(_, _, _, _, occurrences(0, _))) :- !.

requirement_satisfied(NodeReqs, requirement(ReqName, CapType, ReqNodeType, ReqRel, occurrences(OccBot, OccTop))) :-
    select(requirement(ReqName, NodeName), NodeReqs, LeftNodeReqs),
    node(NodeName, NodeType, _, _, _),
    type_offers_capability(NodeType, CapType),
    extends_node_type(NodeType, ReqNodeType),
    NewOccBot is OccBot-1,
    requirement_satisfied(LeftNodeReqs, requirement(ReqName, CapType, ReqNodeType, ReqRel, occurrences(NewOccBot, OccTop))).

