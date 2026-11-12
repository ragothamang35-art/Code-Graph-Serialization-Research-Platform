"""Generate deterministic synthetic repository fixtures for E2E tests."""
import json
import math
import random
from pathlib import Path

random.seed(1337)

def generate_vector(dim=256, seed_val=0):
    rnd = random.Random(seed_val)
    vec = [rnd.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec))
    return [round(x / norm, 5) for x in vec]

SYNTHETIC_TASKS = [
    {
        "instance_id": "syn__task-001-standard",
        "repo": "synthetic/web-framework",
        "base_commit": "a1b2c3d",
        "created_at": "2024-01-10T12:00:00Z",
        "problem_statement": "PaymentService fails to invoke ClientTransport retry on connection timeout in pkg/service.py and pkg/client.py.",
        "hints_text": "Check retry loop in pkg/client.py line 40 and service.py line 25.",
        "patch": """diff --git a/pkg/service.py b/pkg/service.py
--- a/pkg/service.py
+++ b/pkg/service.py
@@ -25,3 +25,5 @@ class PaymentService:
+        if timeout:
+            self.transport.retry()
diff --git a/pkg/client.py b/pkg/client.py
--- a/pkg/client.py
+++ b/pkg/client.py
@@ -40,2 +40,4 @@ class ClientTransport:
+    def retry(self):
+        return self.connect()
""",
        "test_patch": "diff --git a/tests/test_service.py b/tests/test_service.py\n",
        "gold_files": ["pkg/service.py", "pkg/client.py"]
    },
    {
        "instance_id": "syn__task-002-triple-plus-prefix",
        "repo": "synthetic/web-framework",
        "base_commit": "b2c3d4e",
        "created_at": "2024-01-11T14:30:00Z",
        "problem_statement": "Authentication token validation crashes when token header is empty in pkg/auth.py.",
        "hints_text": "Verify token length before decode.",
        "patch": """--- a/pkg/auth.py
+++ b/pkg/auth.py
@@ -55,3 +55,5 @@ def validate_token(token):
+    if not token:
+        return False
""",
        "test_patch": "",
        "gold_files": ["pkg/auth.py"]
    },
    {
        "instance_id": "syn__task-003-new-file-dev-null",
        "repo": "synthetic/web-framework",
        "base_commit": "c3d4e5f",
        "created_at": "2024-01-12T09:15:00Z",
        "problem_statement": "Add missing telemetry metrics collection module for tracking request durations in pkg/metrics.py.",
        "hints_text": "Create pkg/metrics.py with Timer collector.",
        "patch": """diff --git a/dev/null b/pkg/metrics.py
--- /dev/null
+++ b/pkg/metrics.py
@@ -0,0 +1,6 @@
+class RequestMetrics:
+    def record(self, duration):
+        pass
""",
        "test_patch": "",
        "gold_files": ["pkg/metrics.py"]
    },
    {
        "instance_id": "syn__task-004-rename-diff",
        "repo": "synthetic/web-framework",
        "base_commit": "d4e5f6a",
        "created_at": "2024-01-13T16:00:00Z",
        "problem_statement": "Deprecate legacy session store and rename to modern session engine in pkg/session.py.",
        "hints_text": "Renamed from pkg/old_session.py to pkg/session.py.",
        "patch": """diff --git a/pkg/old_session.py b/pkg/session.py
similarity index 98%
rename from pkg/old_session.py
rename to pkg/session.py
--- a/pkg/old_session.py
+++ b/pkg/session.py
@@ -10,3 +10,4 @@ class SessionEngine:
+    active = True
""",
        "test_patch": "",
        "gold_files": ["pkg/session.py"]
    },
    {
        "instance_id": "syn__task-005-test-exclusion",
        "repo": "synthetic/web-framework",
        "base_commit": "e5f6a7b",
        "created_at": "2024-01-14T11:20:00Z",
        "problem_statement": "Fix NullPointerException in Router dispatch method in pkg/router.py while adding test coverage in tests/test_router.py.",
        "hints_text": "Router should guard against None route.",
        "patch": """diff --git a/pkg/router.py b/pkg/router.py
--- a/pkg/router.py
+++ b/pkg/router.py
@@ -75,3 +75,5 @@ def dispatch(route):
+    if route is None:
+        raise ValueError("Invalid route")
diff --git a/tests/test_router.py b/tests/test_router.py
--- a/tests/test_router.py
+++ b/tests/test_router.py
@@ -10,2 +10,4 @@ def test_null_route():
""",
        "test_patch": "",
        "gold_files": ["pkg/router.py"]
    },
    {
        "instance_id": "syn__task-006-unretrievable-gold",
        "repo": "synthetic/web-framework",
        "base_commit": "f6a7b8c",
        "created_at": "2024-01-15T08:45:00Z",
        "problem_statement": "Fix isolated external third-party plugin loader in pkg/isolated_plugin.py when external manifest is corrupt.",
        "hints_text": "Manifest parser in isolated_plugin.py requires safety check.",
        "patch": """diff --git a/pkg/isolated_plugin.py b/pkg/isolated_plugin.py
--- a/pkg/isolated_plugin.py
+++ b/pkg/isolated_plugin.py
@@ -15,3 +15,5 @@ def load_manifest():
+    if not os.path.exists(path):
+        return {}
""",
        "test_patch": "",
        "gold_files": ["pkg/isolated_plugin.py"]
    },
    {
        "instance_id": "syn__task-007-deep-traversal",
        "repo": "synthetic/web-framework",
        "base_commit": "a7b8c9d",
        "created_at": "2024-01-16T15:10:00Z",
        "problem_statement": "Propagate trace context from Controller through Router to Handler in pkg/controller.py and pkg/handler.py.",
        "hints_text": "Ensure request.trace_id reaches handler execution.",
        "patch": """diff --git a/pkg/controller.py b/pkg/controller.py
--- a/pkg/controller.py
+++ b/pkg/controller.py
@@ -30,2 +30,4 @@ class Controller:
+        ctx = make_trace_context()
diff --git a/pkg/handler.py b/pkg/handler.py
--- a/pkg/handler.py
+++ b/pkg/handler.py
@@ -45,2 +45,4 @@ def handle_request(ctx):
+    logger.info(ctx.trace_id)
""",
        "test_patch": "",
        "gold_files": ["pkg/controller.py", "pkg/handler.py"]
    }
]

SYNTHETIC_NODES = [
    # Payment & client nodes
    {"id": "syn_node_service", "name": "PaymentService", "text": "Handles checkout lifecycle and charges client.", "file": "pkg/service.py", "line": 20},
    {"id": "syn_node_client", "name": "ClientTransport", "text": "Raw TCP/HTTP socket transport with reconnect.", "file": "pkg/client.py", "line": 35},
    {"id": "syn_node_validator", "name": "InvoiceValidator", "text": "Validates invoice lines and currency codes.", "file": "pkg/validator.py", "line": 50},

    # Auth nodes
    {"id": "syn_node_auth_validate", "name": "validate_token", "text": "Verifies JWT or opaque auth bearer token.", "file": "pkg/auth.py", "line": 50},
    {"id": "syn_node_auth_jwt", "name": "decode_jwt_header", "text": "Extracts algorithm and kid from token header.", "file": "pkg/auth.py", "line": 15},

    # Session nodes
    {"id": "syn_node_session_engine", "name": "SessionEngine", "text": "Manages cookie sessions and storage persistence.", "file": "pkg/session.py", "line": 10},
    {"id": "syn_node_session_cookie", "name": "CookieSerializer", "text": "Encrypts and serializes session cookie payloads.", "file": "pkg/session.py", "line": 80},

    # Router & controller nodes
    {"id": "syn_node_controller", "name": "Controller.invoke", "text": "Accepts HTTP request and resolves route match.", "file": "pkg/controller.py", "line": 25},
    {"id": "syn_node_router", "name": "Router.dispatch", "text": "Matches regex URL path against registered routes.", "file": "pkg/router.py", "line": 70},
    {"id": "syn_node_handler", "name": "handle_request", "text": "Executes user handler function with context.", "file": "pkg/handler.py", "line": 40},

    # Config & utility nodes
    {"id": "syn_node_config", "name": "AppConfig.load", "text": "Loads YAML config into typed environment schema.", "file": "pkg/config.py", "line": 12},
    {"id": "syn_node_logger", "name": "Logger.info", "text": "Emits structured JSON log lines to standard out.", "file": "pkg/logger.py", "line": 60},
    {"id": "syn_node_metrics", "name": "RequestMetrics.record", "text": "Records request latency histograms.", "file": "pkg/metrics.py", "line": 5},
    {"id": "syn_node_crypto", "name": "AESGCM.encrypt", "text": "Performs authenticated encryption with associated data.", "file": "pkg/crypto.py", "line": 90},
    {"id": "syn_node_database", "name": "DatabasePool.acquire", "text": "Checks out pooled connection from database cluster.", "file": "pkg/database.py", "line": 110}
]

SYNTHETIC_EDGES = [
    {"source": "syn_node_service", "target": "syn_node_client", "type": "calls"},
    {"source": "syn_node_service", "target": "syn_node_validator", "type": "validates"},
    {"source": "syn_node_client", "target": "syn_node_logger", "type": "logs_to"},
    {"source": "syn_node_auth_validate", "target": "syn_node_auth_jwt", "type": "calls"},
    {"source": "syn_node_auth_validate", "target": "syn_node_crypto", "type": "uses_crypto"},
    {"source": "syn_node_session_engine", "target": "syn_node_session_cookie", "type": "delegates"},
    {"source": "syn_node_session_cookie", "target": "syn_node_crypto", "type": "encrypts_with"},
    {"source": "syn_node_controller", "target": "syn_node_router", "type": "dispatches_to"},
    {"source": "syn_node_router", "target": "syn_node_handler", "type": "routes_to"},
    {"source": "syn_node_handler", "target": "syn_node_database", "type": "queries"},
    {"source": "syn_node_handler", "target": "syn_node_metrics", "type": "emits_metrics"},
    {"source": "syn_node_controller", "target": "syn_node_config", "type": "reads_config"}
]

SYNTHETIC_EMBEDDINGS = {}
for i, n in enumerate(SYNTHETIC_NODES):
    SYNTHETIC_EMBEDDINGS[n["id"]] = generate_vector(dim=256, seed_val=2000 + i * 43)

dest_dir = Path("/app/applet/tests/fixtures/synthetic_repo")
dest_dir.mkdir(parents=True, exist_ok=True)

with open(dest_dir / "tasks.json", "w", encoding="utf-8") as f:
    json.dump(SYNTHETIC_TASKS, f, indent=2)

with open(dest_dir / "nodes.json", "w", encoding="utf-8") as f:
    json.dump(SYNTHETIC_NODES, f, indent=2)

with open(dest_dir / "edges.json", "w", encoding="utf-8") as f:
    json.dump(SYNTHETIC_EDGES, f, indent=2)

with open(dest_dir / "embeddings.json", "w", encoding="utf-8") as f:
    json.dump(SYNTHETIC_EMBEDDINGS, f, indent=2)

print(f"Generated synthetic fixtures: {len(SYNTHETIC_TASKS)} tasks, {len(SYNTHETIC_NODES)} nodes, {len(SYNTHETIC_EDGES)} edges, {len(SYNTHETIC_EMBEDDINGS)} embeddings in {dest_dir}")
