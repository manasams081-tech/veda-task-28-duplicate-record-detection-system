# Task 28 — Interview Answers

### 1. What is deduplication?
Deduplication is the process of finding repeated records and keeping one trusted version so a dataset does not contain unnecessary duplicate entries.

### 2. What is fuzzy matching?
Fuzzy matching compares records by similarity rather than requiring every value to be exactly equal. It is useful for spelling differences, spacing differences, abbreviations, and small data-entry errors.

### 3. Why can duplicate detection be difficult?
The same customer can appear with different spellings, phone formats, email variations, missing fields, or changed addresses. Large datasets also create many possible record pairs.

### 4. How would you validate automatically detected duplicates?
Review the important matching fields, inspect the similarity score, verify the source records, and apply business rules before merging or deleting anything. Uncertain matches should remain available for human review.
