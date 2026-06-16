import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple

from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator
from engine.runner import BenchmarkRunner

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATASET_PATH = "data/golden_set.jsonl"
REPORT_DIR = "reports"


def load_dataset(path: str = DATASET_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}. Run: python data/synthetic_gen.py")
    with open(path, "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]
    if not dataset:
        raise ValueError(f"{path} is empty")
    return dataset


def average(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_summary(version: str, results: List[Dict[str, Any]], duration_sec: float, judge: LLMJudge) -> Dict[str, Any]:
    total = len(results)
    pass_count = sum(1 for r in results if r.get("status") == "pass")

    metrics = {
        "avg_score": average([r["judge"].get("final_score", 0.0) for r in results]),
        "hit_rate": average([r["ragas"].get("retrieval", {}).get("hit_rate", 0.0) for r in results]),
        "mrr": average([r["ragas"].get("retrieval", {}).get("mrr", 0.0) for r in results]),
        "agreement_rate": average([r["judge"].get("agreement_rate", 0.0) for r in results]),
        "pass_rate": pass_count / total if total else 0.0,
        "avg_latency_sec": average([r.get("latency", 0.0) for r in results]),
        "total_tokens": sum(r.get("tokens_used", 0) for r in results),
        "total_cost_usd": round(sum(r.get("cost_usd", 0.0) for r in results), 8),
    }

    return {
        "metadata": {
            "version": version,
            "total": total,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_sec": round(duration_sec, 3),
            "judge_models": judge.judge_models,
            "release_decision": "PENDING",
        },
        "metrics": metrics,
    }


async def run_benchmark_with_results(agent_version: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    print(f"Starting benchmark for {agent_version}...")
    dataset = load_dataset()
    agent = MainAgent()
    evaluator = RetrievalEvaluator()
    judge = LLMJudge()
    runner = BenchmarkRunner(agent, evaluator, judge)

    start = time.perf_counter()
    results = await runner.run_all(dataset, batch_size=10)
    duration = time.perf_counter() - start
    summary = build_summary(agent_version, results, duration, judge)
    return results, summary


def apply_regression_gate(v1_summary: Dict[str, Any], v2_summary: Dict[str, Any]) -> Dict[str, Any]:
    v1_score = v1_summary["metrics"]["avg_score"]
    v2_score = v2_summary["metrics"]["avg_score"]
    delta = v2_score - v1_score
    metrics = v2_summary["metrics"]
    duration = v2_summary["metadata"].get("duration_sec", 0.0)

    checks = {
        "delta_score_non_negative": delta >= 0,
        "hit_rate_at_least_0_8": metrics.get("hit_rate", 0.0) >= 0.8,
        "agreement_rate_at_least_0_7": metrics.get("agreement_rate", 0.0) >= 0.7,
        "duration_under_120_sec": duration < 120,
    }
    decision = "APPROVE" if all(checks.values()) else "BLOCK"
    failed = [name for name, ok in checks.items() if not ok]

    regression = {
        "v1_avg_score": round(v1_score, 4),
        "v2_avg_score": round(v2_score, 4),
        "delta_score": round(delta, 4),
        "decision": decision,
        "checks": checks,
        "reason": "All release gate checks passed." if decision == "APPROVE" else "Failed checks: " + ", ".join(failed),
    }
    v2_summary["regression"] = regression
    v2_summary["metadata"]["release_decision"] = decision
    return regression


async def main() -> None:
    if not os.path.exists(DATASET_PATH):
        print("Missing data/golden_set.jsonl. Generating dataset first...")
        import data.synthetic_gen as synthetic_gen
        synthetic_gen.generate_source_docs()
        synthetic_gen.generate_golden_dataset()

    v1_results, v1_summary = await run_benchmark_with_results("Agent_V1_Base")
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized")
    regression = apply_regression_gate(v1_summary, v2_summary)

    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(os.path.join(REPORT_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open(os.path.join(REPORT_DIR, "benchmark_results.json"), "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    print("\nRegression result")
    print(f"V1 score: {regression['v1_avg_score']:.2f}")
    print(f"V2 score: {regression['v2_avg_score']:.2f}")
    print(f"Delta: {regression['delta_score']:+.2f}")
    print(f"Decision: {regression['decision']}")
    print("Saved reports/summary.json and reports/benchmark_results.json")


if __name__ == "__main__":
    asyncio.run(main())
