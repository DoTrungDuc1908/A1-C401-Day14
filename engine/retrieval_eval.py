import asyncio
from typing import List, Dict, Any

class RetrievalEvaluator:
    def __init__(self):
        pass

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        """
        Tính toán xem ít nhất 1 trong expected_ids có nằm trong top_k của retrieved_ids không.
        """
        if not expected_ids:
            # Out of context case expects empty
            return 1.0 if not retrieved_ids else 0.0
            
        top_retrieved = retrieved_ids[:top_k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        Tính Mean Reciprocal Rank.
        Tìm vị trí đầu tiên của một expected_id trong retrieved_ids.
        MRR = 1 / position (vị trí 1-indexed). Nếu không thấy thì là 0.
        """
        if not expected_ids:
            return 1.0 if not retrieved_ids else 0.0
            
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    async def score(self, test_case: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hàm chính để đánh giá 1 case, dùng cho Runner.
        """
        expected_ids = test_case.get("expected_retrieval_ids", [])
        retrieved_ids = response.get("retrieved_ids", [])
        
        hit_rate = self.calculate_hit_rate(expected_ids, retrieved_ids)
        mrr = self.calculate_mrr(expected_ids, retrieved_ids)
        
        # Mock LLM generation metrics (faithfulness, relevancy)
        # Trong thực tế, bạn sẽ phải dùng prompt và gội API LLM để chấm phần text này.
        return {
            "faithfulness": 0.9,
            "relevancy": 0.85,
            "retrieval": {
                "hit_rate": hit_rate,
                "mrr": mrr,
                "expected_ids": expected_ids,
                "retrieved_ids": retrieved_ids
            }
        }

if __name__ == "__main__":
    evaluator = RetrievalEvaluator()
    tc = {"expected_retrieval_ids": ["doc1", "doc2"]}
    resp = {"retrieved_ids": ["doc3", "doc1", "doc4"]}
    res = asyncio.run(evaluator.score(tc, resp))
    print("Test Score Retrieval:", res)
