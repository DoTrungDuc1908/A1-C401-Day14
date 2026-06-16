import asyncio
import sys
import json
import os
from typing import List, Dict, Any

# Fix Windows console encoding for printing Vietnamese
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class MainAgent:
    """
    Agent RAG sử dụng công cụ tìm kiếm In-Memory bằng keyword overlap.
    """
    def __init__(self, docs_path: str = "data/source_docs.jsonl"):
        self.name = "SupportAgent-v2"
        self.documents = []
        self._load_documents(docs_path)

    def _load_documents(self, filepath: str):
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found. Agent runs without knowledge.")
            return
            
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.documents.append(json.loads(line))
        # Uncomment out to debug
        # print(f"[{self.name}] Loaded {len(self.documents)} documents.")

    def _retrieve(self, question: str, top_k: int = 3) -> List[Dict]:
        """In-Memory Search based on keyword overlap"""
        # Bỏ đi các từ hỏi cơ bản để tránh nhiễu
        stopwords = {"cho", "tôi", "biết", "thông", "tin", "về", "là", "gì", "như", "thế", "nào", "có", "không", "?"}
        q_tokens = set(word for word in question.lower().split() if word not in stopwords)
        
        if not q_tokens:
            return []

        scored_docs = []
        for doc in self.documents:
            content_tokens = set(doc["content"].lower().split())
            title_tokens = set(doc["title"].lower().split())
            # Trọng số title cao hơn
            score = len(q_tokens.intersection(content_tokens)) + len(q_tokens.intersection(title_tokens)) * 2
            scored_docs.append((score, doc))
            
        # Sắp xếp giảm dần theo điểm
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Chỉ lấy doc có score > 0
        results = [doc for score, doc in scored_docs if score > 0]
        return results[:top_k]

    async def query(self, question: str) -> Dict[str, Any]:
        """
        Quy trình RAG: Retrieve context -> Generate answer.
        """
        # Giả lập độ trễ
        await asyncio.sleep(0.05) 
        
        # 1. Retrieval
        retrieved_docs = self._retrieve(question)
        retrieved_ids = [doc["doc_id"] for doc in retrieved_docs]
        contexts = [doc["content"] for doc in retrieved_docs]
        
        # 2. Generation (Mock LLM Response)
        if not retrieved_docs:
            answer = "Tôi không tìm thấy thông tin nào liên quan đến câu hỏi của bạn."
            tokens_used = 15
        else:
            answer = f"Theo thông tin tôi tìm được: {contexts[0][:100]}..."
            tokens_used = 150
            
        return {
            "answer": answer,
            "contexts": contexts,
            "retrieved_ids": retrieved_ids,
            "metadata": {
                "model": "gpt-4o-mini-mock",
                "tokens_used": tokens_used,
                "cost_usd": tokens_used * 0.00000015,
                "sources": [doc["title"] for doc in retrieved_docs]
            }
        }

if __name__ == "__main__":
    agent = MainAgent()
    async def test():
        resp = await agent.query("Nghỉ phép có được cộng dồn không?")
        print(json.dumps(resp, indent=2, ensure_ascii=False))
    asyncio.run(test())
