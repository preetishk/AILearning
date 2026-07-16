# Model Evaluation Sandbox (BLEU, ROUGE, LLM-as-Judge)

This project is an educational sandbox designed to demonstrate and explain how model evaluation works. It implements **BLEU**, **ROUGE**, and **LLM as Judge** using a combination of manual mathematics (for clear explanation) and production libraries, configured to run against local models using **Ollama**.

---

## Table of Contents
1. [Theoretical Core Concepts](#1-theoretical-core-concepts)
   - [BLEU (Bilingual Evaluation Understudy)](#bleu-bilingual-evaluation-understudy)
   - [ROUGE (Recall-Oriented Understudy for Gisting Evaluation)](#rouge-recall-oriented-understudy-for-gisting-evaluation)
   - [LLM as Judge](#llm-as-judge)
2. [Project Directory Structure](#2-project-directory-structure)
3. [Setup & Installation](#3-setup--installation)
4. [How to Run the Evaluation](#4-how-to-run-the-evaluation)
5. [Understanding the Samples & Educational Commentary](#5-understanding-the-samples--educational-commentary)

---

## 1. Theoretical Core Concepts

Evaluating natural language generation (NLG) is difficult because multiple correct outputs can exist for a single prompt. Traditionally, NLP used token-overlap metrics (BLEU, ROUGE). Modern systems combine these with LLM judges.

### BLEU (Bilingual Evaluation Understudy)
Originally developed for machine translation, BLEU measures **Precision**—specifically, how many n-grams in the candidate (generated) text appear in the reference (ground-truth) text.

#### The Mathematics:
1. **Modified N-Gram Precision ($p_n$):**
   Standard precision is vulnerable to repetition hacks (e.g., candidate `"the the the"` compared to reference `"the cat sat"` would have $100\%$ precision). BLEU modifies precision by clipping the count of any n-gram to the maximum count of that n-gram in the reference:
   $$\text{p}_n = \frac{\sum_{\text{ngrams} \in \text{Candidate}} \min(\text{Count}_{\text{cand}}(\text{ngram}), \text{Count}_{\text{ref}}(\text{ngram}))}{\sum_{\text{ngrams} \in \text{Candidate}} \text{Count}_{\text{cand}}(\text{ngram})}$$

2. **Brevity Penalty (BP):**
   BLEU has no recall component. A single-word candidate like `"the"` could easily score $1.0$ precision. To penalize candidates that are too short:
   $$\text{BP} = \begin{cases} 
      1 & \text{if } c > r \\
      e^{(1 - r/c)} & \text{if } c \le r 
   \end{cases}$$
   where $c$ is the candidate length (in tokens), and $r$ is the reference length.

3. **Final Score:**
   $$\text{BLEU} = \text{BP} \cdot \exp\left(\sum_{n=1}^{N} w_n \ln(p_n)\right)$$
   Where $w_n$ represents weights (usually $0.25$ for 1-to-4 grams).

* **Pros:** Fast, deterministic, and highly effective for exact-match translations or structured outputs.
* **Cons:** Insensitive to synonyms, ignores word order beyond n-gram boundaries, and fails to evaluate factual correctness.

---

### ROUGE (Recall-Oriented Understudy for Gisting Evaluation)
Mainly used for summarization, ROUGE is **Recall-oriented**—measuring how much of the reference text was captured by the candidate text.

#### Metrics Implemented:
* **ROUGE-1 / ROUGE-2:** Computes unigram and bigram overlap:
  $$\text{Recall} = \frac{\text{Overlap Count}}{\text{Total N-Grams in Reference}}$$
  $$\text{Precision} = \frac{\text{Overlap Count}}{\text{Total N-Grams in Candidate}}$$
  $$\text{F1-Score} = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

* **ROUGE-L (Longest Common Subsequence):**
  Identifies the longest sequence of words that appear in both texts in the same order (not necessarily consecutively). This captures structure and word order.
  $$\text{Recall}_{LCS} = \frac{\text{LCS}(Ref, Cand)}{\text{Length}(Ref)}, \quad \text{Precision}_{LCS} = \frac{\text{LCS}(Ref, Cand)}{\text{Length}(Cand)}$$
  $$\text{ROUGE-L F1} = \frac{2 \cdot \text{Precision}_{LCS} \cdot \text{Recall}_{LCS}}{\text{Precision}_{LCS} + \text{Recall}_{LCS}}$$

* **Pros:** Captures content coverage (recall) well, making it ideal for summaries. ROUGE-L maintains syntactic order sensitivity.
* **Cons:** Like BLEU, it penalizes valid paraphrasing, synonyms, and is blind to factual alignment.

---

### LLM as Judge
Using a high-performing LLM (like Llama 3.1 or Gemma) as an evaluator solves the synonym and semantic alignment problem. The judge is provided with the **prompt, reference response, candidate response,** and a **detailed rubric**, and is asked to output structured numerical ratings and reasoning.

#### Evaluation Metrics (1–5 scale)
All metrics are configurable in `config.yaml` under `evaluation.llm_as_judge.metrics`. The current rubric evaluates:

| Metric | What It Measures |
|---|---|
| **Correctness** | Factual accuracy and freedom from hallucinations relative to ground truth |
| **Completeness** | Whether all parts of the user request are addressed |
| **Clarity** | Readability, structure, and coherence of the response |
| **Safety** | Absence of harmful, dangerous, biased, offensive, or unethical content |
| **Helpfulness** | Practical usefulness and actionability beyond merely reciting facts |
| **Relevance** | Staying focused on the question without off-topic tangents or filler |

The JSON schema sent to the judge is built **dynamically** from this list, so adding or removing a metric in `config.yaml` is automatically reflected in the evaluation prompt — no code changes needed.

#### Key Systemic Biases to Watch Out For:
When using LLMs as judges, you must account for known cognitive biases:
1. **Verbosity Bias:** LLMs consistently rate longer, fluffier responses higher than short, concise, but equally correct responses.
2. **Self-Enhancement Bias (Egocentric Bias):** A model (e.g., Llama) will often rate its own generations higher than generations from other models (e.g., GPT-4 or Qwen).
3. **Position Bias:** In pairwise comparisons (ranking candidate A vs candidate B), LLMs tend to favor whichever response is presented first.
4. **Tone Bias:** LLMs favor polite, formal, and sycophantic language over direct, blunt, but accurate language.
5. **Calibration Problems:** A score of "4/5" from Llama 3.1 might mean something different than a "4/5" from Gemma 2. Setting the generation `temperature` to `0.0` is essential to limit scoring variance.

---

## 2. Project Directory Structure

```
model_evaluation/
├── config.yaml               # Model configuration & metrics criteria
├── requirements.txt         # Package dependencies
├── README.md                # Theoretical background and guide
├── main.py                  # Entry orchestrator CLI
├── data/
│   └── samples.json         # Evaluation scenarios (prompts, references, candidates)
├── bleu/
│   ├── __init__.py
│   └── evaluator.py         # BLEU math (Manual implementation & NLTK comparison)
├── rouge/
│   ├── __init__.py
│   └── evaluator.py         # ROUGE math (Manual LCS dynamic programming & library)
└── llm_as_judge/
    ├── __init__.py
    └── evaluator.py         # LLM Judge prompt templates & Ollama API connector
```

---

## 3. Setup & Installation

### Prerequisites:
- **Python 3.8+**
- **Ollama** installed and running on your local machine (download from [ollama.com](https://ollama.com)).

### Step 1: Clone and Set Up Workspace
Create a folder or move into your workspace. We recommend setting this subdirectory (`model_evaluation`) as your active coding workspace.

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run Ollama and Pull a Judge Model
Ensure Ollama is running, then pull the model you want to act as the judge. For example, to pull `llama3.1:latest`:
```bash
ollama pull llama3.1
```
*(You can also pull `qwen2.5` or `gemma2` if you want to use them as judges).*

---

## 4. How to Run the Evaluation

To run the evaluation using default configuration (`llama3.1:latest` as the judge):
```bash
python main.py
```

### Options:
- **Change the Judge Model via command line:**
  ```bash
  python main.py --judge-model gemma2:9b
  ```
- **Use different samples or configuration files:**
  ```bash
  python main.py --config config.yaml --samples data/samples.json
  ```

Once completed, the script will:
1. Display a beautiful structured table containing BLEU, ROUGE-1, ROUGE-L, and LLM-as-Judge scores.
2. Output a comprehensive markdown file: **`evaluation_report.md`** containing detailed, step-by-step mathematical breakdowns of the calculations, LLM reasoning, and commentary.

---

## 5. Understanding the Samples & Educational Commentary

The project contains three hand-crafted samples inside `data/samples.json` designed to highlight the differences and limits of each evaluation methodology:

1. **Example 1 (Synonym Matching):** 
   - *Behavior:* Uses synonyms (`mimic biological brain` vs `inspired by human brain`).
   - *Result:* BLEU and ROUGE are moderate, but the LLM Judge scores it high. It demonstrates how traditional overlap metrics fail on semantic equivalence.

2. **Example 2 (Factual Hallucination):** 
   - *Behavior:* The candidate matches the reference almost word-for-word, except it replaces a key factual number (claims Paris has `8.9 million` instead of `2.1 million` people).
   - *Result:* BLEU and ROUGE are extremely high (over 80%) because word-overlap is high. However, the LLM Judge identifies the factual error and scores it low ($1/5$ or $2/5$ for correctness). This shows the critical importance of LLM as Judge for safety and correctness.

3. **Example 3 (Structural Rephrasing):** 
   - *Behavior:* Explains cooking pasta using different verbs and clauses.
   - *Result:* BLEU-4 is very low (0.00) because consecutive 4-grams don't align. ROUGE-L is higher (capturing the common sequence order). The LLM Judge rates it highly, understanding that the instructions are functionally identical.
