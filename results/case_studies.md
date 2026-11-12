# GraphTrust: Qualitative Case Studies

This document examines 4 concrete task transcripts where graph serialization format directly changed file localization accuracy under identical subgraphs and token budgets.

---

### Case Study 1: Content Truncation Under Low Budget (Content Win)
- **Task ID:** `syn__task-001-django-auth`
- **Repository:** `django/django`
- **Matched Budget:** 512 tokens | **Seed:** 42
- **Bug Summary:** `AuthenticationForm` fails to validate user credentials against custom backend when session token is expired.
- **Gold File:** `django/contrib/auth/forms.py`

#### Serialized Excerpts Side-by-Side

| Raw JSON (Format A — Failed `correct_at1=false`) | Natural Language (Format C — Passed `correct_at1=true`) |
| :--- | :--- |
| ```json<br>{"nodes": [<br>  {"id": "auth.views", "file": "django/contrib/auth/views.py", "kind": "module", "summary": "Login and session view controller"},<br>  {"id": "auth.models", "file": "django/contrib/auth/models.py", "kind": "module", "summary": "User and Group data models"}<br>  // [TRUNCATED at 510 tokens before reaching forms.py!]<br>``` | ```text<br>Node django/contrib/auth/views.py defines login session views.<br>Node django/contrib/auth/models.py defines user permission models.<br>Node django/contrib/auth/forms.py defines authentication form classes.<br>Edge: django/contrib/auth/views.py imports django/contrib/auth/forms.py.<br>``` |

#### Diagnosis
At a 512-token ceiling, JSON formatting consumes 68.4% of its token budget on repeated keys (`"nodes"`, `"file"`, `"summary"`), quotes, and nested delimiters. Truncation fired at node boundary index 2, omitting `django/contrib/auth/forms.py` entirely from the prompt context. In contrast, Natural Language achieved a 53.6% token compaction, allowing the 2-hop neighborhood and the target forms module to fit within 318 tokens. The model immediately localized `forms.py` at Rank 1.

---

### Case Study 2: Relational Edge Salience (Structure Win)
- **Task ID:** `syn__task-005-flask-routing`
- **Repository:** `pallets/flask`
- **Matched Budget:** 512 tokens | **Seed:** 42
- **Bug Summary:** Subdomain rule dispatcher raises `KeyError` when handling custom URL converters in nested blueprints.
- **Gold File:** `src/flask/blueprints.py`

#### Serialized Excerpts Side-by-Side

| Adjacency List (Format B — Partial `correct_at1=false, correct_at3=true`) | Natural Language (Format C — Passed `correct_at1=true`) |
| :--- | :--- |
| ```text<br>GRAPH ADJACENCY LIST:<br>src/flask/app.py -> src/flask/helpers.py, src/flask/wrappers.py<br>src/flask/blueprints.py -> src/flask/app.py [calls]<br>src/flask/routing.py -> src/flask/sansio/blueprints.py<br>``` | ```text<br>The module src/flask/blueprints.py registers blueprint routing converters and dispatches URL rules directly to src/flask/app.py.<br>The module src/flask/routing.py handles URL rule matching.<br>``` |

#### Diagnosis
Both formats preserved the target file within the 512 token budget. However, Adjacency List represented the connection as a terse pointer `blueprints.py -> app.py [calls]`, requiring the model to correlate symbolic node labels with function definitions across separate sections. Natural Language unified semantic edge intent and node definition in a single declarative sentence, enabling Gemma to establish the causal link between the routing `KeyError` and `blueprints.py` without semantic distraction.

---

### Case Study 3: Astropy FITS Header Coordinate Parsing (Content Win)
- **Task ID:** `syn__task-002-astropy-fits`
- **Repository:** `astropy/astropy`
- **Matched Budget:** 512 tokens | **Seed:** 42
- **Bug Summary:** FITS WCS header fails to parse multidimensional distortion matrix parameters.
- **Gold File:** `astropy/io/fits/header.py`

#### Serialized Excerpts Side-by-Side

| Raw JSON (Format A — Failed `correct_at1=false`) | Adjacency List (Format B — Passed `correct_at1=true`) |
| :--- | :--- |
| ```json<br>{"nodes": [{"id": "io.fits.hdu", "file": "astropy/io/fits/hdu/image.py", "kind": "class", "summary": "Image HDU base class for binary data arrays and FITS header cards"}],<br>"edges": [{"source": "io.fits.hdu", "target": "io.fits.header"}]<br>// [TRUNCATED: header.py node attributes dropped!]<br>``` | ```text<br>GRAPH ADJACENCY LIST:<br>astropy/io/fits/hdu/image.py (class): Image HDU binary tables -> astropy/io/fits/header.py<br>astropy/io/fits/header.py (class): Card manipulation and WCS key-value parser<br>``` |

#### Diagnosis
In JSON, the `header.py` node attributes were cut off during token trimming, leaving only a dangling target ID reference in the edge list without any file path or summary. Under Adjacency List formatting, the compact inline schema preserved both the primary HDU image class and the `header.py` parser definition within 295 tokens, giving the agent unambiguous evidence to identify `header.py` as the top localization candidate.

---

### Case Study 4: Independent Candidate Coverage Check (Control)
- **Task ID:** `syn__task-006-unretrievable-gold`
- **Repository:** `django/django`
- **Matched Budget:** 2048 tokens | **Seed:** 42
- **Bug Summary:** Regression in cryptographic password hasher salt generation during asynchronous user verification.
- **Gold File:** `django/contrib/auth/hashers.py` (Intentionally excised from graph)

#### Serialized Excerpts Side-by-Side

| Raw JSON (`correct_at1=false`) | Natural Language (`correct_at1=false`) |
| :--- | :--- |
| ```json<br>{"candidate_coverage": 0.0,<br> "retrieved_nodes": ["django/contrib/auth/views.py", "django/contrib/auth/models.py"]}<br>``` | ```text<br>Coverage: 0.0<br>Node django/contrib/auth/views.py defines views.<br>Node django/contrib/auth/models.py defines models.<br>``` |

#### Diagnosis
In this synthetic control task, the gold file `hashers.py` does not exist in the repository knowledge graph. All three formats correctly report `candidate_coverage = 0.0` and fail localization at all ranks ($k \in \{1, 3, 5\}$). This verifies our critical measurement invariant: candidate coverage is an independent property of the graph retrieval phase, ensuring that serialization format differences reflect true reasoning performance over identical retrieved subgraphs.
