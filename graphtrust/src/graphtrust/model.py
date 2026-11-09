"""Model inference interface supporting Gemma 4 E2B, GGUF/llama-cpp, and validation mode."""

import os
import json
import time
from typing import Dict, Any, List
from graphtrust.schema import ModelPrediction, Task, SerializedGraph
from graphtrust.prompting import build_prompt, parse_model_response

class GemmaAgent:
    def __init__(
        self,
        model_name: str = "Gemma-4-E2B",
        model_path: str = "",
        quantization: str = "Q4_K_M",
        temperature: float = 0.0,
        context_window: int = 4096,
        is_mock: bool = False
    ):
        self.model_name = model_name
        self.model_path = model_path
        self.quantization = quantization
        self.temperature = temperature
        self.context_window = context_window
        self.is_mock = is_mock
        self.backend = "mock" if (is_mock or not model_path) else "llama_cpp"

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_path": self.model_path or "N/A (Mock/Validation Engine)",
            "quantization": self.quantization,
            "temperature": self.temperature,
            "context_window": self.context_window,
            "backend": self.backend,
            "is_mock": self.is_mock
        }

    def predict(
        self,
        task: Task,
        serialized_graph: SerializedGraph,
        max_predictions: int = 5
    ) -> ModelPrediction:
        """
        Execute deterministic inference.
        If running in mock/validation mode, uses deterministic graph-informed heuristic
        to simulate small Gemma agent reasoning without fabricating real findings.
        """
        start_time = time.time()
        prompt = build_prompt(task, serialized_graph, max_predictions=max_predictions)

        raw_output = ""
        predicted_files: List[str] = []
        reasoning = ""
        parsing_success = True

        if self.backend == "llama_cpp" and self.model_path:
            # Here llama-cpp-python is called if model weights exist
            try:
                # Dynamically load if available
                from llama_cpp import Llama
                llm = Llama(model_path=self.model_path, n_ctx=self.context_window, verbose=False)
                resp = llm(
                    prompt,
                    max_tokens=256,
                    temperature=self.temperature,
                    stop=["```", "\n\n\n"]
                )
                raw_output = resp["choices"][0]["text"].strip()
                predicted_files, reasoning, parsing_success = parse_model_response(raw_output)
            except Exception as e:
                raw_output = f'{{"error": "Inference failed: {str(e)}"}}'
                parsing_success = False
        else:
            # Deterministic validation/mock execution
            # Extracts candidate files from serialized text and ranks by frequency/presence
            content = serialized_graph.content
            # Heuristic simulation that reflects serialization differences:
            # In Natural Language, sentences make relations explicit.
            # In JSON, keys 'file' and 'name' are structured.
            # In Adjacency list, arrow chains are grouped by caller.
            found_files = []
            for line in content.splitlines():
                parts = line.split()
                for p in parts:
                    clean = p.strip("[](),'\"")
                    if clean.endswith(".py") and "/" in clean:
                        if clean not in found_files:
                            found_files.append(clean)

            # If no graph was provided, fallback to repo heuristic
            if not found_files and task.repo:
                parts = task.repo.split("/")
                repo_leaf = parts[-1] if parts else "src"
                found_files = [f"src/{repo_leaf}/core.py", f"{repo_leaf}/app.py"]

            predicted_files = found_files[:max_predictions]
            reasoning = (
                f"[MOCK_MODE] Simulated Gemma-4-E2B reasoning for {serialized_graph.format_type}. "
                f"Extracted {len(predicted_files)} candidate files from serialized context."
            )
            raw_output = json.dumps({
                "predicted_files": predicted_files,
                "reasoning": reasoning
            }, indent=2)

        elapsed = round((time.time() - start_time) * 1000.0, 2)

        return ModelPrediction(
            task_id=task.instance_id,
            format_type=serialized_graph.format_type,
            budget=serialized_graph.budget,
            predicted_files=predicted_files,
            reasoning=reasoning,
            raw_output=raw_output,
            parsing_success=parsing_success,
            latency_ms=elapsed
        )
