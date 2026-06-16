from typing import List, Dict

class RetrievalEvaluator:
    def __init__(self):
        pass

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        """
        Tính toán xem ít nhất 1 trong expected_ids có nằm trong top_k của retrieved_ids không.
        """
        if not expected_ids or not retrieved_ids:
            return 0.0
        top_retrieved = retrieved_ids[:top_k]
        top_retrieved_set = {str(x).strip() for x in top_retrieved}
        for doc_id in expected_ids:
            if str(doc_id).strip() in top_retrieved_set:
                return 1.0
        return 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        Tính Mean Reciprocal Rank.
        Tìm vị trí đầu tiên của một expected_id trong retrieved_ids.
        MRR = 1 / position (vị trí 1-indexed). Nếu không thấy thì là 0.
        """
        if not expected_ids or not retrieved_ids:
            return 0.0
        expected_set = {str(x).strip() for x in expected_ids}
        for i, doc_id in enumerate(retrieved_ids):
            if str(doc_id).strip() in expected_set:
                return 1.0 / (i + 1)
        return 0.0

    async def score(self, test_case: Dict, response: Dict) -> Dict:
        """
        Tính toán độc lập để trả về kết quả Retrieval cho Runner.
        Chấp nhận test_case chứa 'expected_retrieval_ids' và response chứa 'retrieved_ids'.
        """
        expected_ids = test_case.get("expected_retrieval_ids") or test_case.get("expected_ids") or []
        retrieved_ids = response.get("retrieved_ids") or response.get("retrieved_doc_ids") or []
        
        hit_rate = self.calculate_hit_rate(expected_ids, retrieved_ids, top_k=3)
        mrr = self.calculate_mrr(expected_ids, retrieved_ids)
        
        return {
            "retrieval": {
                "hit_rate": hit_rate,
                "mrr": mrr
            }
        }

    async def evaluate_batch(self, dataset: List[Dict]) -> Dict:
        """
        Chạy eval cho toàn bộ bộ dữ liệu.
        Dataset cần có trường 'expected_retrieval_ids' và Agent trả về 'retrieved_ids'.
        """
        if not dataset:
            return {"avg_hit_rate": 0.0, "avg_mrr": 0.0}
            
        total_hit_rate = 0.0
        total_mrr = 0.0
        count = 0
        
        for item in dataset:
            if "test_case" in item and "agent_response" in item:
                expected_ids = item.get("test_case", {}).get("expected_retrieval_ids", [])
                retrieved_ids = item.get("agent_response", {}).get("retrieved_ids", [])
            else:
                expected_ids = item.get("expected_retrieval_ids") or item.get("expected_ids") or []
                retrieved_ids = item.get("retrieved_ids") or item.get("retrieved_doc_ids") or []
                
            hit_rate = self.calculate_hit_rate(expected_ids, retrieved_ids, top_k=3)
            mrr = self.calculate_mrr(expected_ids, retrieved_ids)
            
            total_hit_rate += hit_rate
            total_mrr += mrr
            count += 1
            
        avg_hit_rate = total_hit_rate / count if count > 0 else 0.0
        avg_mrr = total_mrr / count if count > 0 else 0.0
        
        return {
            "avg_hit_rate": avg_hit_rate,
            "avg_mrr": avg_mrr
        }
