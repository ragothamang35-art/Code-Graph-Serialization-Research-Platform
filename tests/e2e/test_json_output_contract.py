"""E2E Test 4.7: Strict JSON Output Contract & Robustness."""

import json
from graphtrust.prompting import parse_model_response

def test_strict_json_contract_parsing():
    """Assert valid raw JSON parses cleanly into predicted files and reasoning."""
    valid_json = json.dumps({
        "predicted_files": ["src/payment.py", "src/validator.py"],
        "reasoning": "Payment module calls validator on line 45."
    })
    files, reasoning, success = parse_model_response(valid_json)
    assert success is True
    assert files == ["src/payment.py", "src/validator.py"]
    assert "validator" in reasoning

def test_markdown_fence_stripping():
    """
    Assert parser strips markdown fences ```json ... ``` and extracts payload,
    even though fence wrapping violates the zero-fence rule.
    """
    fenced_output = """```json
{
  "predicted_files": ["pkg/client.py"],
  "reasoning": "Transport client handles timeout."
}
```"""
    files, reasoning, success = parse_model_response(fenced_output)
    assert success is True
    assert files == ["pkg/client.py"]

def test_malformed_json_handling():
    """
    Assert malformed or unparseable JSON is safely captured without crashing the pipeline,
    and returns success=False.
    """
    malformed_output = "I think the file is src/payment.py because { broken json"
    files, reasoning, success = parse_model_response(malformed_output)
    # Emergency file extractor may locate src/payment.py, but success must be False
    assert success is False
    assert "src/payment.py" in files or "Failed to parse" in reasoning
