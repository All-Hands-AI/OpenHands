ANALYZE_PROMPT = """Analyze this prompt to see if it already contains a step-by-step plan or requires more detailed plan generation:

---
{message}
---

Only respond with 0 for no plan generation required or 1 for plan generation required.
"""
