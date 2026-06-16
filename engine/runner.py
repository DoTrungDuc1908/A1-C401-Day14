import asyncio
import inspect
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class BenchmarkRunner:
    def __init__(
        self,
        agent,
        evaluator,
        judge,
        *,
        default_batch_size: int = 5,
        pass_threshold: float = 3.0,
        case_timeout_sec: float = 30.0,
    ):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge
        self.default_batch_size = default_batch_size
        self.pass_threshold = pass_threshold
        self.case_timeout_sec = case_timeout_sec

    async def _maybe_await(self, value: Any) -> Any:
        if inspect.isawaitable(value):
            return await value
        return value

    async def _call_agent(self, question: str) -> Dict[str, Any]:
        return await self._maybe_await(self.agent.query(question))

    async def _score_retrieval(self, test_case: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        return await self._maybe_await(self.evaluator.score(test_case, response))

    async def _judge_answer(self, test_case: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        return await self._maybe_await(
            self.judge.evaluate_multi_judge(
                test_case.get("question", ""),
                response.get("answer", ""),
                test_case.get("expected_answer", ""),
            )
        )

    async def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()
        try:
            response = await asyncio.wait_for(
                self._call_agent(test_case["question"]),
                timeout=self.case_timeout_sec,
            )
            latency = time.perf_counter() - start_time
            ragas_scores, judge_result = await asyncio.gather(
                self._score_retrieval(test_case, response),
                self._judge_answer(test_case, response),
            )
            final_score = float(judge_result.get("final_score", 0.0))
            metadata = response.get("metadata", {})

            return {
                "id": test_case.get("id"),
                "test_case": test_case.get("question", ""),
                "expected_answer": test_case.get("expected_answer", ""),
                "expected_retrieval_ids": test_case.get("expected_retrieval_ids", []),
                "agent_response": response.get("answer", ""),
                "contexts": response.get("contexts", []),
                "retrieved_ids": response.get("retrieved_ids", []),
                "latency": latency,
                "latency_sec": latency,
                "tokens_used": int(metadata.get("tokens_used", 0) or 0),
                "cost_usd": float(metadata.get("cost_usd", 0.0) or 0.0),
                "metadata": metadata,
                "agent_metadata": metadata,
                "ragas": ragas_scores,
                "judge": judge_result,
                "status": "pass" if final_score >= self.pass_threshold else "fail",
                "error": None,
            }
        except Exception as exc:
            latency = time.perf_counter() - start_time
            return {
                "id": test_case.get("id"),
                "test_case": test_case.get("question", ""),
                "expected_answer": test_case.get("expected_answer", ""),
                "expected_retrieval_ids": test_case.get("expected_retrieval_ids", []),
                "agent_response": "",
                "contexts": [],
                "retrieved_ids": [],
                "latency": latency,
                "latency_sec": latency,
                "tokens_used": 0,
                "cost_usd": 0.0,
                "metadata": {},
                "agent_metadata": {},
                "ragas": {
                    "faithfulness": 0.0,
                    "relevancy": 0.0,
                    "retrieval": {
                        "hit_rate": 0.0,
                        "mrr": 0.0,
                        "expected_ids": test_case.get("expected_retrieval_ids", []),
                        "retrieved_ids": [],
                    },
                },
                "judge": {
                    "final_score": 0.0,
                    "agreement_rate": 0.0,
                    "individual_scores": {},
                    "reasoning": f"Case failed before judging: {exc}",
                    "conflict_resolved": False,
                },
                "status": "fail",
                "error": repr(exc),
            }

    async def run_all(self, dataset: List[Dict[str, Any]], batch_size: int = 10) -> List[Dict[str, Any]]:
        if batch_size <= 0:
            batch_size = self.default_batch_size
        results: List[Dict[str, Any]] = []
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]
            tasks = [self.run_single_test(case) for case in batch]
            results.extend(await asyncio.gather(*tasks))
        return results

    def summarize(
        self,
        results: List[Dict[str, Any]],
        *,
        version: str = "Agent_V2_Optimized",
        duration_sec: Optional[float] = None,
        release_decision: Optional[str] = None,
        regression: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        total = len(results)
        metrics = {
            "avg_score": self._avg(results, lambda r: r.get("judge", {}).get("final_score", 0.0)),
            "hit_rate": self._avg(results, lambda r: r.get("ragas", {}).get("retrieval", {}).get("hit_rate", 0.0)),
            "mrr": self._avg(results, lambda r: r.get("ragas", {}).get("retrieval", {}).get("mrr", 0.0)),
            "agreement_rate": self._avg(results, lambda r: r.get("judge", {}).get("agreement_rate", 0.0)),
            "pass_rate": sum(1 for r in results if r.get("status") == "pass") / total if total else 0.0,
            "avg_latency_sec": self._avg(results, lambda r: r.get("latency_sec", r.get("latency", 0.0))),
            "total_tokens": sum(int(r.get("tokens_used", 0) or 0) for r in results),
            "total_cost_usd": sum(float(r.get("cost_usd", 0.0) or 0.0) for r in results),
        }

        return {
            "metadata": {
                "version": version,
                "total": total,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "duration_sec": round(duration_sec if duration_sec is not None else 0.0, 4),
                "judge_models": self._collect_judge_models(results),
                "release_decision": release_decision or "PENDING",
            },
            "metrics": {
                "avg_score": round(metrics["avg_score"], 4),
                "hit_rate": round(metrics["hit_rate"], 4),
                "mrr": round(metrics["mrr"], 4),
                "agreement_rate": round(metrics["agreement_rate"], 4),
                "pass_rate": round(metrics["pass_rate"], 4),
                "avg_latency_sec": round(metrics["avg_latency_sec"], 4),
                "total_tokens": metrics["total_tokens"],
                "total_cost_usd": round(metrics["total_cost_usd"], 8),
            },
            "regression": regression or {},
        }

    async def run_benchmark(
        self,
        dataset: List[Dict[str, Any]],
        *,
        batch_size: Optional[int] = None,
        version: str = "Agent_V2_Optimized",
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        start_time = time.perf_counter()
        results = await self.run_all(dataset, batch_size or self.default_batch_size)
        duration_sec = time.perf_counter() - start_time
        summary = self.summarize(results, version=version, duration_sec=duration_sec)
        return results, summary

    def save_reports(self, results: List[Dict[str, Any]], summary: Dict[str, Any], output_dir: str = "reports") -> None:
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "benchmark_results.json"), "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        with open(os.path.join(output_dir, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_dataset(path: str = "data/golden_set.jsonl") -> List[Dict[str, Any]]:
        with open(path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    @staticmethod
    def _avg(results: List[Dict[str, Any]], getter) -> float:
        values = []
        for result in results:
            try:
                values.append(float(getter(result) or 0.0))
            except (TypeError, ValueError):
                values.append(0.0)
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def _collect_judge_models(results: List[Dict[str, Any]]) -> List[str]:
        models = set()
        for result in results:
            individual_scores = result.get("judge", {}).get("individual_scores", {})
            if isinstance(individual_scores, dict):
                models.update(individual_scores.keys())
        return sorted(models)


async def _demo_run() -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from agent.main_agent import MainAgent
    from engine.llm_judge import LLMJudge
    from engine.retrieval_eval import RetrievalEvaluator

    dataset = BenchmarkRunner.load_dataset()
    runner = BenchmarkRunner(MainAgent(), RetrievalEvaluator(), LLMJudge(), default_batch_size=10)
    results, summary = await runner.run_benchmark(dataset, batch_size=10)
    runner.save_reports(results, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(_demo_run())