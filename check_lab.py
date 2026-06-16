import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def validate_lab():
    print("Checking submission format...")

    required_files = [
        "reports/summary.json",
        "reports/benchmark_results.json",
        "analysis/failure_analysis.md",
    ]

    missing = []
    for path in required_files:
        if os.path.exists(path):
            print(f"OK: found {path}")
        else:
            print(f"ERROR: missing {path}")
            missing.append(path)

    if missing:
        print(f"\nERROR: missing {len(missing)} required files.")
        return False

    try:
        with open("reports/summary.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: reports/summary.json is invalid JSON: {e}")
        return False

    if "metrics" not in data or "metadata" not in data:
        print("ERROR: summary.json must include metadata and metrics.")
        return False

    metrics = data["metrics"]
    print("\nQuick stats")
    print(f"Total cases: {data['metadata'].get('total', 'N/A')}")
    print(f"Average score: {metrics.get('avg_score', 0):.2f}")

    required_metrics = ["hit_rate", "mrr", "agreement_rate"]
    for metric in required_metrics:
        if metric in metrics:
            print(f"OK: found metric {metric} = {metrics[metric]:.3f}")
        else:
            print(f"WARNING: missing metric {metric}")

    if data["metadata"].get("version"):
        print("OK: found agent version for regression mode")
    if data.get("regression"):
        print(f"OK: found regression gate decision = {data['regression'].get('decision')}")

    print("\nSubmission is ready for grading format checks.")
    return True


if __name__ == "__main__":
    validate_lab()
