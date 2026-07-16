"""
ROUGE (Recall-Oriented Understudy for Gisting Evaluation) Evaluator

ROUGE is a set of metrics used for evaluating automatic summarization and machine
translation software. Unlike BLEU, which focuses on precision (how many generated n-grams
appear in the reference), ROUGE is recall-oriented (how many reference n-grams
appear in the generated text).

Metrics Implemented:
--------------------
1. ROUGE-1: Overlap of unigrams (single words)
2. ROUGE-2: Overlap of bigrams (pairs of words)
3. ROUGE-L: Overlap of the Longest Common Subsequence (LCS), capturing structural order

Mathematical Foundation:
------------------------
For n-grams (ROUGE-1, ROUGE-2):
- Recall (R) = Overlap_Count / Reference_Ngram_Count
- Precision (P) = Overlap_Count / Candidate_Ngram_Count
- F1-Score = 2 * (P * R) / (P + R)

For ROUGE-L (Longest Common Subsequence):
- Let LCS(Ref, Cand) be the length of the longest common subsequence of words.
- Recall_LCS (R_lcs) = LCS(Ref, Cand) / Ref_Word_Count
- Precision_LCS (P_lcs) = LCS(Ref, Cand) / Cand_Word_Count
- F1_LCS = ((1 + beta^2) * R_lcs * P_lcs) / (R_lcs + beta^2 * P_lcs)
  (Typically, beta = 1, giving equal weight to precision and recall)
"""

import re
from collections import Counter
from typing import Dict, List, Tuple, Any
from rouge_score import rouge_scorer


def tokenize(text: str) -> List[str]:
    """
    Cleans and tokenizes text by lowecasing and splitting on word boundaries.
    """
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    return words


def get_ngrams(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
    """Generates n-grams of size n from a list of tokens."""
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def calculate_lcs(x: List[str], y: List[str]) -> int:
    """
    Computes the length of the Longest Common Subsequence (LCS)
    between two list of tokens using Dynamic Programming.
    Time Complexity: O(len(x) * len(y))
    """
    m, n = len(x), len(y)
    # Create DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                
    return dp[m][n]


def calculate_manual_rouge_n(ref_tokens: List[str], cand_tokens: List[str], n: int) -> Dict[str, float]:
    """Calculates ROUGE-N (Recall, Precision, F1) for a given n-gram size."""
    ref_ngrams = get_ngrams(ref_tokens, n)
    cand_ngrams = get_ngrams(cand_tokens, n)
    
    if not ref_ngrams or not cand_ngrams:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
    ref_counts = Counter(ref_ngrams)
    cand_counts = Counter(cand_ngrams)
    
    # Calculate overlap
    overlap = 0
    for ngram, count in cand_counts.items():
        ref_count = ref_counts.get(ngram, 0)
        overlap += min(count, ref_count)
        
    precision = overlap / len(cand_ngrams)
    recall = overlap / len(ref_ngrams)
    
    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0
        
    return {"precision": precision, "recall": recall, "f1": f1}


def calculate_manual_rouge_l(ref_tokens: List[str], cand_tokens: List[str]) -> Dict[str, float]:
    """Calculates ROUGE-L (LCS-based Precision, Recall, F1) for the sequences."""
    m = len(ref_tokens)
    n = len(cand_tokens)
    
    if m == 0 or n == 0:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
    lcs_len = calculate_lcs(ref_tokens, cand_tokens)
    
    recall = lcs_len / m
    precision = lcs_len / n
    
    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0
        
    return {"precision": precision, "recall": recall, "f1": f1}


def calculate_manual_rouge(reference: str, candidate: str) -> Dict[str, Dict[str, float]]:
    """Calculates ROUGE-1, ROUGE-2, and ROUGE-L scores manually."""
    ref_tokens = tokenize(reference)
    cand_tokens = tokenize(candidate)
    
    return {
        "rouge1": calculate_manual_rouge_n(ref_tokens, cand_tokens, 1),
        "rouge2": calculate_manual_rouge_n(ref_tokens, cand_tokens, 2),
        "rougeL": calculate_manual_rouge_l(ref_tokens, cand_tokens)
    }


def calculate_scorer_rouge(reference: str, candidate: str) -> Dict[str, Dict[str, float]]:
    """
    Calculates ROUGE scores using the google-rouge-score library for validation.
    """
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    
    result = {}
    for metric, score in scores.items():
        result[metric] = {
            "precision": score.precision,
            "recall": score.recall,
            "f1": score.fmeasure
        }
    return result


def calculate_rouge(reference: str, candidate: str) -> Dict[str, Any]:
    """
    Wrapper function that computes both manual and google-rouge-scorer metrics.
    """
    manual = calculate_manual_rouge(reference, candidate)
    library = calculate_scorer_rouge(reference, candidate)
    
    # We return the google-rouge-score values as the main score (usually uses stemming)
    # but include manual calculations for transparent verification.
    return {
        "score": {
            "rouge1": library["rouge1"]["f1"],
            "rouge2": library["rouge2"]["f1"],
            "rougeL": library["rougeL"]["f1"]
        },
        "manual": manual,
        "library_reference": library
    }
