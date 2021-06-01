% Tested with SWI-Prolog

input(db_user).
input(db_password).
input(ssh_pubkey).

% type(name,
%     extended_type,
%     [properties],
%     [capabilities],
%     [requirements]
% )

type('myapp.nodes.WebApp',
    'tosca.nodes.SoftwareComponent',
    [],
    [],
    [
        requirement(database_endpoint,
            'tosca.capabilities.Endpoint.Database')
    ]).

type('doml.nodes.SQLDatabaseService',
    'doml.nodes.CloudProviderService',
    [],
    [
        capability(dummy_cap, 'dummy.Cap'),
        capability(database_endpoint,
            'tosca.capabilities.Endpoint.Database'
        )
    ],
    []).

% node(name,
%     type,
%     [properties],
%     [capabilities],
%     [requirements]
% )

node(webapp,
    'myapp.nodes.WebApp',
    [
        db_user(input(db_user)),
        db_password(input(db_password))
    ],
    [],
    [
        host(webapp_vm),
        % database_endpoint(db),  % Try removing this requirement
        redis_endpoint(redis)
    ]).

node(redis,
    'doml.nodes.Redis',
    [],
    [],
    [
        host(redis_vm)
    ]).

node(db,
    'doml.nodes.SQLDatabaseService',
    [
        user(input(db_user)),
        password(input(db_password))
        % Try changing the above line to this:
        % password("p4$$w0rd")
    ],
    [],
    []
    ).

% Helper procedures

extends_type(TypeA, TypeA).
extends_type(TypeA, TypeB) :-
    type(TypeA, ExtTypeA, _, _, _), !,
    extends_type(ExtTypeA, TypeB).

type_offers_capability(Type, CapType) :-
    extends_type(Type, EType),
    type(EType, _, _, Caps, _),
    member(capability(_, CapType), Caps).

% Reveals nodes with Endpoint.Database capability that have hardcoded password
has_hardcoded_db_password(X) :-
    node(X, NodeType, Props, _, _),
    type_offers_capability(NodeType, 'tosca.capabilities.Endpoint.Database'),
    member(password(P), Props),
    P \= input(_).

% Reveals nodes with unsatisfied requirements
has_unsatisfied_requirements(NodeName, TypeReq) :-
    node(NodeName, NodeType, _, _, NodeReqs),
    type_has_requirement(NodeType, TypeReq),
    \+ requirement_satisfied(NodeReqs, TypeReq).

type_has_requirement(Type, Req) :-
    extends_type(Type, EType),
    type(EType, _, _, _, Reqs),
    member(Req, Reqs).

requirement_satisfied(NodeReqs, requirement(ReqName, CapType)) :-
    member(NodeReq, NodeReqs),
    NodeReq =.. [ReqName, NodeName],
    node(NodeName, NodeType, _, _, _),
    type_offers_capability(NodeType, CapType).

% Perform all checks
runChecks() :-
    has_unsatisfied_requirements(NodeName, TypeReq),
    format('Node ~q does not satisfy ~q.~n', [NodeName, TypeReq]);
    
    has_hardcoded_db_password(NodeName),
    format('Node ~q seems to be a database with a hardcoded password.~n', [NodeName]).
    