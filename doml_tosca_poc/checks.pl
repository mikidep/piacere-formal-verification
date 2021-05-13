% Reveals nodes with unsatisfied requirements
has_unsatisfied_requirements(NodeName, TypeReq) :-
    node(NodeName, NodeType, _, _, NodeReqs),
    type_has_requirement(NodeType, TypeReq),
    \+ requirement_satisfied(NodeReqs, TypeReq).

% Reveals nodes with Endpoint.Database capability that have hardcoded password
has_hardcoded_db_password(X) :-
    node(X, NodeType, Props, _, _),
    type_offers_capability(NodeType, 'tosca.capabilities.Endpoint.Database'),
    member(property(password, P), Props),
    P \= input(_).
