"""Prompt construction and strict JSON output parsing for Gemma agents."""

import re
import json
from typing import Dict, Any, Tuple, List
from graphtrust.schema import Task, SerializedGraph

BASE_INSTRUCTION = """You are a senior software engineering localization agent.
Your objective is to identify the source code files that need to be modified to resolve the reported software issue.
Base your prediction solely on the provided problem description, repository metadata, and retrieved code graph context.
Do NOT modify code or propose patches. Your output must be strictly valid JSON with no markdown formatting or commentary."""

OUTPUT_SCHEMA = """{
  "predicted_files": [
    "path/to/source_file_1.py",
    "path/to/source_file_2.py"
  ],
  "reasoning": "Brief explanation based only on the provided evidence."
}"""

def build_prompt(task: Task, serialized_graph: SerializedGraph, max_predictions: int = 5) -> str:
    """
    Construct the standardized prompt.
    The instruction, task description, and output constraints remain 100% IDENTICAL across all conditions.
    Only the graph context block varies depending on the serialization format.
    """
    graph_section = ""
    if serialized_graph.format_type == "no_graph":
        graph_section = "No code graph context is provided."
    elif serialized_graph.format_type == "keyword_match":
        graph_section = f"--- RETRIEVED CANDIDATE FILES ---\n{serialized_graph.content}"
    else:
        format_label = {
            "json": "RAW JSON CODE GRAPH",
            "adjacency_list": "STRUCTURED ADJACENCY LIST GRAPH",
            "natural_language": "NATURAL LANGUAGE RELATIONSHIP STATEMENTS"
        }.get(serialized_graph.format_type, "RETRIEVED CODE GRAPH")
        graph_section = f"--- {format_label} ---\n{serialized_graph.content}"

    prompt = f"""{BASE_INSTRUCTION}

--- REPOSITORY ---
{task.repo}

--- PROBLEM STATEMENT ---
{task.problem_statement}

{f"--- HINTS ---" + chr(10) + task.hints_text if task.hints_text else ""}

{graph_section}

--- OUTPUT REQUIREMENT ---
Return a strictly valid JSON object adhering to this schema:
{OUTPUT_SCHEMA}

Return at most {max_predictions} predicted files in descending order of relevance.
Do not wrap your response in markdown code blocks (such as ```json). Output raw JSON only."""
    return prompt

def parse_model_response(raw_text: str) -> Tuple[List[str], str, bool]:
    """
    Robust JSON parser for Gemma agent outputs.
    Handles potential markdown fences, leading/trailing whitespace, and JSON repair.
    """
    if not raw_text:
        return [], "Empty model response", False

    text = raw_text.strip()
    
    # Strip markdown fences if present
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    # Try direct parse
    try:
        data = json.loads(text)
        files = data.get("predicted_files", [])
        reasoning = data.get("reasoning", "")
        # Clean paths
        cleaned = [f.strip().lstrip("./") for f in files if isinstance(f, str) and f.strip()]
        return cleaned, str(reasoning), True
    except Exception:
        pass

    # Fallback regex extraction of JSON object
    obj_match = re.search(r"\{[\s\S]*\}", text)
    if obj_match:
        try:
            data = json.loads(obj_match.group(0))
            files = data.get("predicted_files", [])
            reasoning = data.get("reasoning", "")
            cleaned = [f.strip().lstrip("./") for f in files if isinstance(f, str) and f.strip()]
            return cleaned, str(reasoning), True
        except Exception:
            pass

    # Extract any python/source file mentions as emergency fallback
    file_candidates = re.findall(r"([A-Za-z0-9_\-./]+\.(?:py|js|ts|java|c|cpp|go|rs))", text)
    if file_candidates:
        unique_files = list(dict.fromkeys(file_candidates))
        return unique_files[:5], f"Extracted from unparsed output: {text[:100]}...", False

    return [], f"Failed to parse JSON: {text[:120]}", False
