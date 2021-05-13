# DOML TOSCA Verification PoC

This project uses [Poetry](https://python-poetry.org/) to manage Python dependencies. SWI-Prolog must also be installed to run the project. To install the dependencies run:

```bash
$ poetry install
```

To run the project on the included TOSCA model, run:

```bash
$ poetry run python poc.py doml_tosca.yaml
```

To further query the generated Prolog model, running

```bash
$ poetry run python -i poc.py doml_tosca.yaml
```

opens a Python interpreter, where the `prolog` object can be queried using its [PySwip](https://github.com/yuce/pyswip) interface:

```
$ poetry run python -i poc.py doml_tosca.yaml
>>> results = prolog.query("node(X, T, _, _, _), extends_type(T, 'tosca.nodes.SoftwareComponent')")
>>> for r in results:
...     print(r)
... 
{'X': 'webapp', 'T': 'myapp.nodes.WebApp'}
{'X': 'redis', 'T': 'doml.nodes.Redis'}
>>> 
```