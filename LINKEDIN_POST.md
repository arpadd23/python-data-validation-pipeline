# LinkedIn post (draft)

---

I recently completed a client project where I processed and validated **millions of
semi-structured text records** — and it turned into a great example of practical data
automation.

The client had tens of thousands of files (~11.6M records) that were too large, too noisy,
and too unreliable to analyze in their software. I built an automated Python pipeline that:

🔎 **Audited** the dataset and surfaced hidden duplicate folders the client hadn't noticed
📉 **Reduced** it ~17× to a distribution-preserving representative sample
🔁 **Transformed** it through several stages for a third-party analytics tool
✅ **Validated every step** — finishing with **zero validation mismatches**, and never
touching the original data

The most interesting part wasn't the code — it was the detective work: I traced a
"numbers don't match" problem to a **silent deduplication behaviour in the third-party
software**, proved my output was bit-for-bit correct, and designed a workaround so the
client's analysis came out right.

Final deliverable: a clean, trusted, import-ready ~1.13M-record dataset, plus reusable,
documented scripts.

This project strengthened my focus on **Python automation, data validation, and AI/data
workflow engineering** — turning messy, large-scale data into something a client can
actually trust and use.

#Python #DataEngineering #DataAutomation #DataValidation

---

*(~190 words. Tip: pair it with the pipeline diagram and a screenshot of the audit report
for a stronger post.)*
