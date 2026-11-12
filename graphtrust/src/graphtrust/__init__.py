"""GraphTrust: Same Subgraph, Different Story.
Controlled empirical evaluation of code graph serialization formats in small Gemma agents.
"""

__version__ = "0.1.0"

from graphtrust.significance import mcnemar_test, bootstrap_ci

__all__ = ["__version__", "mcnemar_test", "bootstrap_ci"]
