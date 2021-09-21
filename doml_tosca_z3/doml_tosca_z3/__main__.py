__version__ = '0.1.0'

import sys

from toscaparser.tosca_template import ToscaTemplate

from .z3toscamodel import Z3ToscaModel

tosca = ToscaTemplate(sys.argv[1])
model = Z3ToscaModel(tosca)
