# Failure Analysis Report

**Nhóm A1-C401**

| Thành viên | MSSV | Vai trò |
|---|---|---|
| Lê Quang Thọ | 2A202600597 | Data Processing & Analysis Support |
| Phạm Mai Anh | 2A202600644 | Data Preparation & Golden Dataset |
| Đỗ Trung Đức | 2A202600918 | Team Lead, Core Engine |
| Phạm Ngọc Hải Dương (Shiner-2) | 2A202600629 | Judge Runner, Reports |
| Vương Nguyệt Bình | 2A202600932 | Testing & Quality Assurance |
| Nguyễn Văn Sáng | 2A202600598 | Retrieval Evaluation |

## 1. Benchmark Overview

- Total cases: 50
- Pass/Fail: 39 pass / 11 fail
- Average metrics:
  - LLM-judge score: 3.84 / 5.0
  - Hit Rate@3: 0.90
  - MRR: 0.84
  - Agreement Rate: 0.898
  - Pass Rate: 0.78
  - Average latency: 0.057 seconds/case
  - Total tokens: 7,500
  - Total cost: 0.001125 USD
- Regression gate: APPROVE
  - V1 average score: 3.8352
  - V2 average score: 3.8352
  - Delta score: 0.0
  - Duration: 0.32 seconds

## 2. Failure Clustering

| Failure group | Count | Evidence | Likely root cause |
| --- | ---: | --- | --- |
| Out-of-context false retrieval | 5 | `ooc_001` to `ooc_005` retrieved `doc_010`, `doc_004`, `doc_002` even though expected ids were empty | Retriever has no confidence threshold, so it always returns weak keyword matches |
| Wrong top-1 retrieval for normal cases | 6 | WFH and sick-leave questions retrieved `doc_001` before the correct document, causing the generated answer to use the wrong first context | Keyword overlap overweights generic words such as policy/leave and lacks exact-title boosting/reranking |
| Low answer completeness | Observed in failed normal cases | Correct document was sometimes present at rank 2, but generation only used `contexts[0]` | Generator ignores lower-ranked relevant contexts instead of synthesizing all retrieved evidence |

## 3. 5 Whys Analysis

### Case #1: Out-of-context phone allowance question

1. Symptom: Agent answered from unrelated company policy docs instead of saying the knowledge base does not contain phone allowance information.
2. Why 1: Retriever returned documents with weak keyword overlap.
3. Why 2: Retrieval logic has no minimum score or confidence threshold.
4. Why 3: Out-of-context cases are represented with `expected_retrieval_ids = []`, but the agent does not use that style of behavior during retrieval.
5. Why 4: The generation step trusts any retrieved context and does not verify whether the match is strong enough.
6. Root cause: Missing no-answer detection between retrieval and generation.

### Case #2: WFH policy question

1. Symptom: The correct WFH document appeared at rank 2, while leave policy appeared at rank 1.
2. Why 1: Generic terms in the question matched the leave-policy title/content strongly.
3. Why 2: The tokenizer uses simple whitespace splitting and does not normalize domain terms like WFH.
4. Why 3: Ranking does not add enough boost for exact title keywords or rare terms.
5. Why 4: The generator only uses the first context, so a rank-2 hit still produces a poor answer.
6. Root cause: Retrieval ranking and answer synthesis both depend too heavily on top-1 context.

### Case #3: Sick-leave question

1. Symptom: The sick-leave document was retrieved, but rank 2; answer used annual leave policy first.
2. Why 1: Both documents share leave-related wording.
3. Why 2: The retriever does not distinguish different leave categories with phrase matching.
4. Why 3: There is no reranker to compare the full question against document titles.
5. Why 4: The response builder does not combine multiple contexts when the correct source is not top-1.
6. Root cause: Lack of semantic/phrase-aware reranking for closely related HR policy documents.

## 4. Improvement Action Plan

- Add a retrieval confidence threshold; if top score is too low, return no context and answer that the document set has no supporting information.
- Add exact-title and rare-token boosts for terms such as WFH, sick leave, insurance, equipment, and business trip.
- Use all retrieved contexts that pass the threshold instead of only `contexts[0]`.
- Add a lightweight reranker after initial keyword retrieval.
- Add regression checks that specifically track out-of-context accuracy and top-1 retrieval accuracy, not only Hit Rate@3.