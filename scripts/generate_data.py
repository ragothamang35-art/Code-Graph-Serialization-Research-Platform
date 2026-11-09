import json
import math
import random

# Seed for reproducibility
random.seed(42)

def generate_unit_vector(dim=256, seed_val=0):
    rnd = random.Random(seed_val)
    vec = [rnd.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec))
    return [round(x / norm, 5) for x in vec]

TASKS = [
    {
        "instance_id": "flask__flask-4045",
        "repo": "pallets/flask",
        "base_commit": "e8913b4",
        "created_at": "2023-04-12T10:00:00Z",
        "problem_statement": "Blueprint name collision when registering nested blueprints with same endpoint prefix. Blueprint.add_url_rule fails to check if the blueprint name contains dots, leading to ambiguous routing resolution in url_for when nested blueprints share leaf names.",
        "hints_text": "Check blueprint.py line 78 in add_url_rule and app.py register_blueprint endpoint prefix handling.",
        "patch": """diff --git a/src/flask/blueprints.py b/src/flask/blueprints.py
--- a/src/flask/blueprints.py
+++ b/src/flask/blueprints.py
@@ -190,6 +190,9 @@ class Blueprint(Scaffold):
+        if "." in self.name:
+            raise ValueError(f"Blueprint name '{self.name}' may not contain a dot '.'")
         self.name = name
diff --git a/src/flask/app.py b/src/flask/app.py
--- a/src/flask/app.py
+++ b/src/flask/app.py
@@ -1020,4 +1020,7 @@ class Flask(Scaffold):
+        first_bp = self.blueprints.get(blueprint.name)
+        if first_bp is not None and first_bp is not blueprint:
+            raise AssertionError(f"A name collision occurred between blueprints {blueprint!r} and {first_bp!r}")
""",
        "test_patch": """diff --git a/tests/test_blueprints.py b/tests/test_blueprints.py
--- a/tests/test_blueprints.py
+++ b/tests/test_blueprints.py
@@ -50,4 +50,12 @@ def test_nested_blueprint_dot_name():
""",
        "gold_files": ["src/flask/blueprints.py", "src/flask/app.py"]
    },
    {
        "instance_id": "requests__requests-3367",
        "repo": "psf/requests",
        "base_commit": "9bc1210",
        "created_at": "2023-05-18T14:20:00Z",
        "problem_statement": "Session.send does not properly close streaming responses when Content-Length mismatch causes an IncompleteRead or chunked decoding error in HTTPAdapter.build_response.",
        "hints_text": "Make sure response.raw.close() is called inside HTTPAdapter when urllib3 raises ProtocolError or IncompleteRead.",
        "patch": """diff --git a/requests/adapters.py b/requests/adapters.py
--- a/requests/adapters.py
+++ b/requests/adapters.py
@@ -415,6 +415,8 @@ class HTTPAdapter(BaseAdapter):
         except (ProtocolError, DecodeError) as err:
+            response.raw.close()
             raise ContentDecodingError(err, response=response)
diff --git a/requests/sessions.py b/requests/sessions.py
--- a/requests/sessions.py
+++ b/requests/sessions.py
@@ -620,3 +620,6 @@ class Session(SessionRedirectMixin):
+        if getattr(resp.raw, '_pool', None) and not resp.is_closed:
+            resp.close()
""",
        "test_patch": """diff --git a/tests/test_requests.py b/tests/test_requests.py
--- a/tests/test_requests.py
+++ b/tests/test_requests.py
""",
        "gold_files": ["requests/adapters.py", "requests/sessions.py"]
    },
    {
        "instance_id": "django__django-14787",
        "repo": "django/django",
        "base_commit": "4a51e60",
        "created_at": "2023-06-02T08:15:00Z",
        "problem_statement": "method_decorator preservation of function attributes and wrapper __name__ breaks for partial functions and multi-decorator wraps in utils/decorators.py.",
        "hints_text": "Check functools.update_wrapper or _update_method_wrapper in django/utils/decorators.py line 38.",
        "patch": """diff --git a/django/utils/decorators.py b/django/utils/decorators.py
--- a/django/utils/decorators.py
+++ b/django/utils/decorators.py
@@ -38,6 +38,9 @@ def _update_method_wrapper(_wrapper, method):
+    if isinstance(method, functools.partial):
+        method = method.func
+    update_wrapper(_wrapper, method)
""",
        "test_patch": """diff --git a/tests/decorators/tests.py b/tests/decorators/tests.py
""",
        "gold_files": ["django/utils/decorators.py"]
    },
    {
        "instance_id": "fastapi__fastapi-2194",
        "repo": "tiangolo/fastapi",
        "base_commit": "782ca51",
        "created_at": "2023-07-10T11:45:00Z",
        "problem_statement": "Dependency cache key collision when two distinct sub-dependencies share identical function signatures or default arguments in routing.solve_dependencies.",
        "hints_text": "Look into dependant.cache_key in dependencies/utils.py and routing.py.",
        "patch": """diff --git a/fastapi/dependencies/utils.py b/fastapi/dependencies/utils.py
--- a/fastapi/dependencies/utils.py
+++ b/fastapi/dependencies/utils.py
@@ -188,4 +188,7 @@ def get_param_sub_dependant(param, dependant):
+    cache_key = (call, tuple(sorted(param.items())))
+    sub_dependant.cache_key = cache_key
diff --git a/fastapi/routing.py b/fastapi/routing.py
--- a/fastapi/routing.py
+++ b/fastapi/routing.py
@@ -140,3 +140,5 @@ async def run_endpoint_function(dependant, values):
""",
        "gold_files": ["fastapi/dependencies/utils.py", "fastapi/routing.py"]
    },
    {
        "instance_id": "pytest-dev__pytest-7236",
        "repo": "pytest-dev/pytest",
        "base_commit": "5cd723b",
        "created_at": "2023-08-20T16:30:00Z",
        "problem_statement": "unittest.TestCase tearDown execution skipped if setUp raises SkipTest exception in runner.py pytest_runtest_makereport.",
        "hints_text": "Runner should ensure fixture teardown and TestCase.doCleanups still execute on skipped test setups in src/_pytest/unittest.py.",
        "patch": """diff --git a/src/_pytest/unittest.py b/src/_pytest/unittest.py
--- a/src/_pytest/unittest.py
+++ b/src/_pytest/unittest.py
@@ -212,6 +212,9 @@ class TestCaseFunction(Function):
+        if getattr(self._testcase, "_cleanups", None):
+            self._testcase.doCleanups()
diff --git a/src/_pytest/runner.py b/src/_pytest/runner.py
--- a/src/_pytest/runner.py
+++ b/src/_pytest/runner.py
@@ -298,3 +298,6 @@ def pytest_runtest_setup(item):
""",
        "gold_files": ["src/_pytest/unittest.py", "src/_pytest/runner.py"]
    },
    {
        "instance_id": "scikit-learn__scikit-learn-13439",
        "repo": "scikit-learn/scikit-learn",
        "base_commit": "0de51bb",
        "created_at": "2023-09-05T09:12:00Z",
        "problem_statement": "Pipeline length inspection with len(pipeline) fails when steps are provided as tuple or dictionary in sklearn/pipeline.py.",
        "hints_text": "Implement __len__ in Pipeline class in sklearn/pipeline.py returning len(self.steps).",
        "patch": """diff --git a/sklearn/pipeline.py b/sklearn/pipeline.py
--- a/sklearn/pipeline.py
+++ b/sklearn/pipeline.py
@@ -135,4 +135,7 @@ class Pipeline(_BaseComposition):
+    def __len__(self):
+        return len(self.steps)
""",
        "test_patch": """diff --git a/sklearn/tests/test_pipeline.py b/sklearn/tests/test_pipeline.py
""",
        "gold_files": ["sklearn/pipeline.py"]
    }
]

NODES = [
    # Flask nodes
    {"id": "flask_bp_add_url_rule", "name": "Blueprint.add_url_rule", "text": "Register a rule with the blueprint and prefix url endpoint with blueprint name.", "file": "src/flask/blueprints.py", "line": 78},
    {"id": "flask_bp_init", "name": "Blueprint.__init__", "text": "Initialize a Blueprint scaffold instance with name and import_name.", "file": "src/flask/blueprints.py", "line": 45},
    {"id": "flask_app_register_bp", "name": "Flask.register_blueprint", "text": "Register a blueprint on this application and record deferred setup functions.", "file": "src/flask/app.py", "line": 1010},
    {"id": "flask_scaffold", "name": "Scaffold", "text": "Common behavior between Flask application object and Blueprint object.", "file": "src/flask/scaffold.py", "line": 32},
    {"id": "flask_helpers_url_for", "name": "url_for", "text": "Generates a URL to the given endpoint with the given values.", "file": "src/flask/helpers.py", "line": 280},
    {"id": "flask_routing_map", "name": "MapAdapter.match", "text": "Matches request path against registered URL routing map rules.", "file": "src/flask/wrappers.py", "line": 115},

    # Requests nodes
    {"id": "req_adapter_build_response", "name": "HTTPAdapter.build_response", "text": "Builds a Response object from a urllib3 response payload.", "file": "requests/adapters.py", "line": 210},
    {"id": "req_adapter_send", "name": "HTTPAdapter.send", "text": "Sends PreparedRequest object and handles transport exceptions and socket lifecycle.", "file": "requests/adapters.py", "line": 400},
    {"id": "req_session_send", "name": "Session.send", "text": "Send a given PreparedRequest and return Response with connection adapter resolution.", "file": "requests/sessions.py", "line": 615},
    {"id": "req_response_close", "name": "Response.close", "text": "Releases the connection back to the pool and closes underlying urllib3 stream.", "file": "requests/models.py", "line": 850},
    {"id": "req_exceptions_decode", "name": "ContentDecodingError", "text": "Failed to decode response content due to compression or chunked framing failure.", "file": "requests/exceptions.py", "line": 65},

    # Django nodes
    {"id": "django_update_method_wrapper", "name": "_update_method_wrapper", "text": "Copy method attributes and update __name__ and __doc__ onto decorated wrapper.", "file": "django/utils/decorators.py", "line": 35},
    {"id": "django_method_decorator", "name": "method_decorator", "text": "Converts a function decorator into a method decorator on class or instance.", "file": "django/utils/decorators.py", "line": 65},
    {"id": "django_functools_partial", "name": "functools.partial", "text": "Return a new partial object which when called behaves like func with args.", "file": "django/utils/functional.py", "line": 120},
    {"id": "django_view_dispatch", "name": "View.dispatch", "text": "Delegate HTTP request method to get, post, put, etc.", "file": "django/views/generic/base.py", "line": 95},

    # FastAPI nodes
    {"id": "fastapi_param_sub_dep", "name": "get_param_sub_dependant", "text": "Construct nested parameter dependant hierarchy with deterministic cache key.", "file": "fastapi/dependencies/utils.py", "line": 180},
    {"id": "fastapi_solve_dependencies", "name": "solve_dependencies", "text": "Resolve dependency injection tree values and evaluate async sub-dependencies.", "file": "fastapi/dependencies/utils.py", "line": 490},
    {"id": "fastapi_run_endpoint", "name": "run_endpoint_function", "text": "Execute route handler with solved dependencies and validate output model.", "file": "fastapi/routing.py", "line": 135},
    {"id": "fastapi_route_compile", "name": "APIRoute.get_route_handler", "text": "Compile dependency tree into single ASGI callable handler.", "file": "fastapi/routing.py", "line": 280},

    # Pytest nodes
    {"id": "pytest_tc_function", "name": "TestCaseFunction.runtest", "text": "Run unittest.TestCase test method and invoke doCleanups teardown hooks.", "file": "src/_pytest/unittest.py", "line": 205},
    {"id": "pytest_unittest_setup", "name": "pytest_pycollect_makeitem", "text": "Collect unittest TestCase subclasses and map individual test methods.", "file": "src/_pytest/unittest.py", "line": 90},
    {"id": "pytest_runtest_setup", "name": "pytest_runtest_setup", "text": "Execute fixture setup phase and capture SkipTest or test failures.", "file": "src/_pytest/runner.py", "line": 290},
    {"id": "pytest_makereport", "name": "pytest_runtest_makereport", "text": "Construct TestReport object summarizing call outcome, duration and traceback.", "file": "src/_pytest/runner.py", "line": 340},

    # Scikit-learn nodes
    {"id": "sklearn_pipeline_len", "name": "Pipeline.__len__", "text": "Return the count of transformers and estimator in the pipeline chain.", "file": "sklearn/pipeline.py", "line": 135},
    {"id": "sklearn_pipeline_fit", "name": "Pipeline.fit", "text": "Fit all transforms sequentially and transform the data before final estimator fit.", "file": "sklearn/pipeline.py", "line": 250},
    {"id": "sklearn_base_composition", "name": "_BaseComposition", "text": "Base class for meta-estimators and composite models with parameter inspection.", "file": "sklearn/base.py", "line": 85},
    {"id": "sklearn_grid_search", "name": "GridSearchCV.fit", "text": "Run grid search with cross-validation over pipeline parameter candidates.", "file": "sklearn/model_selection/_search.py", "line": 520}
]

EDGES = [
    # Flask edges
    {"source": "flask_bp_init", "target": "flask_scaffold", "type": "inherits"},
    {"source": "flask_app_register_bp", "target": "flask_bp_add_url_rule", "type": "calls"},
    {"source": "flask_bp_add_url_rule", "target": "flask_helpers_url_for", "type": "registers_endpoint"},
    {"source": "flask_helpers_url_for", "target": "flask_routing_map", "type": "queries"},
    {"source": "flask_app_register_bp", "target": "flask_scaffold", "type": "delegates"},

    # Requests edges
    {"source": "req_session_send", "target": "req_adapter_send", "type": "calls"},
    {"source": "req_adapter_send", "target": "req_adapter_build_response", "type": "calls"},
    {"source": "req_adapter_build_response", "target": "req_response_close", "type": "manages_lifecycle"},
    {"source": "req_adapter_send", "target": "req_exceptions_decode", "type": "raises"},
    {"source": "req_session_send", "target": "req_response_close", "type": "closes"},

    # Django edges
    {"source": "django_method_decorator", "target": "django_update_method_wrapper", "type": "calls"},
    {"source": "django_update_method_wrapper", "target": "django_functools_partial", "type": "inspects"},
    {"source": "django_view_dispatch", "target": "django_method_decorator", "type": "decorated_by"},

    # FastAPI edges
    {"source": "fastapi_run_endpoint", "target": "fastapi_solve_dependencies", "type": "calls"},
    {"source": "fastapi_solve_dependencies", "target": "fastapi_param_sub_dep", "type": "evaluates"},
    {"source": "fastapi_route_compile", "target": "fastapi_run_endpoint", "type": "dispatches"},

    # Pytest edges
    {"source": "pytest_runtest_setup", "target": "pytest_tc_function", "type": "prepares"},
    {"source": "pytest_tc_function", "target": "pytest_makereport", "type": "reports_to"},
    {"source": "pytest_unittest_setup", "target": "pytest_tc_function", "type": "instantiates"},

    # Sklearn edges
    {"source": "sklearn_pipeline_len", "target": "sklearn_base_composition", "type": "implements_protocol"},
    {"source": "sklearn_pipeline_fit", "target": "sklearn_pipeline_len", "type": "verifies"},
    {"source": "sklearn_grid_search", "target": "sklearn_pipeline_fit", "type": "invokes"}
]

# Generate node embeddings (256-dimensional)
EMBEDDINGS = {}
for i, node in enumerate(NODES):
    EMBEDDINGS[node["id"]] = generate_unit_vector(dim=256, seed_val=1000 + i * 37)

with open("/app/applet/public/tasks.json", "w") as f:
    json.dump(TASKS, f, indent=2)

with open("/app/applet/public/nodes.json", "w") as f:
    json.dump(NODES, f, indent=2)

with open("/app/applet/public/edges.json", "w") as f:
    json.dump(EDGES, f, indent=2)

with open("/app/applet/public/embeddings.json", "w") as f:
    json.dump(EMBEDDINGS, f, indent=2)

print(f"Generated {len(TASKS)} benchmark tasks, {len(NODES)} code graph nodes, {len(EDGES)} graph edges, and {len(EMBEDDINGS)} 256-d embeddings.")
