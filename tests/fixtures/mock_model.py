"""Deterministic Mock Gemma Backend for Hermetic E2E Testing."""

import json
import re
from typing import Dict, Any, List, Optional
from graphtrust.schema import ModelPrediction, Task, SerializedGraph
from graphtrust.prompting import parse_model_response

class MockGemmaAgent:
    """
    Hermetic, deterministic mock agent mimicking Gemma 4 E2B behavior
    without requiring external model weights or network access.
    """
    def __init__(
        self,
        model_name: str = "Gemma-4-E2B-MOCK",
        temperature: float = 0.0,
        context_window: int = 4096,
        inject_malformed: bool = False,
        inject_fences: bool = False
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.context_window = context_window
        self.inject_malformed = inject_malformed
        self.inject_fences = inject_fences
        self.backend = "mock"
        self.mode = "mock"  # Explicit MOCK marker per research integrity rules

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "backend": "mock",
            "mode": "mock",
            "quantization": "Q4_K_M-MOCK",
            "temperature": self.temperature,
            "context_window": self.context_window,
            "is_mock": True
        }

    def predict(
        self,
        task: Task,
        serialized_graph: SerializedGraph,
        max_predictions: int = 5
    ) -> ModelPrediction:
        """
        Produce deterministic predictions derived purely from candidate files
        present in serialized graph content.
        """
        # Check if task requests deliberate malformed output
        if self.inject_malformed or "malformed" in task.instance_id:
            raw_output = "THIS IS NOT VALID JSON {malformed: true, invalid...}"
            predicted, reasoning, success = parse_model_response(raw_output)
            return ModelPrediction(
                task_id=task.instance_id,
                format_type=serialized_graph.format_type,
                budget=serialized_graph.budget,
                predicted_files=predicted,
                reasoning="MOCK: Injected malformed response for failure handling test",
                raw_output=raw_output,
                parsing_success=success,
                latency_ms=1.5
            )

        # Extract file paths from serialized graph content
        found_files: List[str] = []
        for line in serialized_graph.content.splitlines():
            # Match python paths
            matches = re.findall(r"([A-Za-z0-9_\-./]+\.py)", line)
            for m in matches:
                clean = m.strip("[](),'\"").lstrip("./")
                if clean not in found_files:
                    found_files.append(clean)

        # If no files found in context (e.g. no_graph), fallback to repo heuristic
        if not found_files and task.repo:
            repo_name = task.repo.split("/")[-1]
            found_files = [f"src/{repo_name}/main.py"]

        predicted = found_files[:max_predictions]
        reasoning = (
            f"[MOCK_RUN] Traceable deterministic prediction for task {task.instance_id} "
            f"under {serialized_graph.format_type} ({len(predicted)} candidate files)."
        )

        output_obj = {
            "predicted_files": predicted,
            "reasoning": reasoning,
            "mode": "mock"
        }
        json_text = json.dumps(output_obj, indent=2)

        # Optional fence injection
        if self.inject_fences or "fenced" in task.instance_id:
            raw_output = f"```json\n{json_text}\n```"
        else:
            raw_output = json_text

        predicted_files, parsed_reasoning, parsing_success = parse_model_response(raw_output)

        return ModelPrediction(
            task_id=task.instance_id,
            format_type=serialized_graph.format_type,
            budget=serialized_graph.budget,
            predicted_files=predicted_files,
            reasoning=parsed_reasoning,
            raw_output=raw_output,
            parsing_success=parsing_success,
            latency_ms=2.0
        )
