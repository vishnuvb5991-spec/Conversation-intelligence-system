# Relay portfolio kit

## Portfolio description

**Relay — cited enterprise search** is a full-stack RAG demo built to show how a company-search system can answer employee questions with traceable source evidence. It ingests synthetic collaboration data, uses dense + sparse hybrid retrieval in Qdrant, optionally reranks results, and requires citations in every generated answer.

**Stack:** FastAPI, Qdrant, OpenAI embeddings, optional Cohere Rerank, Docker, Render, Vite.

Add these after deployment:

- Live demo: `https://<your-render-service>.onrender.com`
- GitHub: `https://github.com/<your-user>/relay-enterprise-search`

## Resume bullets

- Built Relay, a cited enterprise-search system that combines dense and sparse Qdrant retrieval, optional reranking, and source-grounded RAG answers across simulated Slack, Jira, Confluence, email, and Drive data.
- Designed a recruiter-facing, Dockerized FastAPI/Vite demo with automatic corpus seeding, rate limiting, health checks, provider fallbacks, and safe synthetic data for public deployment.
- Added retrieval evaluation with context recall@10 and MRR to measure the impact of chunking and retrieval decisions.

## Two-minute demo script

1. Open Relay and point out the “Sample company data” label.
2. Ask: “What is the plan for the enterprise launch?”
3. Show the answer panel, then open source citations to explain that the response is grounded in retrieved passages.
4. Change the source filter to Slack or Jira and repeat the question to demonstrate scoped retrieval.
5. Open “About this demo” and explain the ingest → hybrid retrieval → rerank → cited answer path.
6. Close with the evaluation approach: “I track context recall@10 and MRR so retrieval changes are measurable, not just subjective.”

## Interview prompts

| Question | Concise answer |
| --- | --- |
| Why hybrid retrieval? | Dense vectors capture intent; sparse retrieval preserves exact terms, identifiers, and product names. RRF avoids relying entirely on either signal. |
| How do you prevent hallucinations? | The answer receives only retrieved passages, citations are required, and an uncited model output falls back to an extractive cited response. |
| Why synthetic data? | It makes the demo public and safe while still showing the end-to-end architecture and retrieval behavior. |
| What would change for production? | Add document-level ACL filters, SSO, audit logs, ingestion jobs, observability, and a larger benchmark/evaluation set. |
