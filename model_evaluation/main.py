#!/usr/bin/env python3
"""
Model Evaluation CLI Framework

Orchestrates evaluation of sample outputs using:
1. BLEU (Manual & NLTK)
2. ROUGE (Manual & google-rouge-score)
3. LLM as Judge (using local Ollama models)

Generates beautiful terminal comparisons and outputs a detailed Markdown report.
"""

import os
import json
import yaml
import argparse
from typing import Dict, Any, List
from tabulate import tabulate

# Import our custom evaluation modules
from bleu.evaluator import calculate_bleu
from rouge.evaluator import calculate_rouge
from llm_as_judge.evaluator import LLMAsJudgeEvaluator


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Loads configuration parameters from a YAML file."""
    if not os.path.exists(config_path):
        print(f"Warning: Configuration file {config_path} not found. Using defaults.")
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_samples(samples_path: str) -> List[Dict[str, Any]]:
    """Loads evaluation samples from a JSON file."""
    if not os.path.exists(samples_path):
        raise FileNotFoundError(f"Samples file not found at: {samples_path}")
    with open(samples_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_markdown_report(results: List[Dict[str, Any]], judge_model: str, report_path: str = "evaluation_report.md"):
    """
    Generates a beautifully formatted Markdown report containing all evaluation scores,
    comparisons between manual and library metrics, LLM reasoning, and commentary.
    """
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Model Evaluation Report\n\n")
        f.write(f"This report evaluates candidate answers against ground-truth references using standard NLP metrics and a local LLM Judge model (`{judge_model}`).\n\n")
        
        f.write("## Summary Table\n\n")
        
        # Build Markdown table
        headers = [
            "ID", "BLEU Score (Manual/NLTK)", "ROUGE-1 (F1)", "ROUGE-L (F1)",
            "LLM Correctness", "LLM Completeness", "LLM Clarity",
            "LLM Safety", "LLM Helpfulness", "LLM Relevance"
        ]
        rows = []
        for res in results:
            bleu_str = f"{res['bleu']['manual']['score']:.3f} / {res['bleu']['nltk_reference']:.3f}"
            rouge1 = f"{res['rouge']['score']['rouge1']:.3f}"
            rougeL = f"{res['rouge']['score']['rougeL']:.3f}"

            if res['llm']['success']:
                scores = res['llm']['scores']
                llm_corr = f"{scores.get('correctness',  {}).get('score', 'N/A')}/5"
                llm_comp = f"{scores.get('completeness', {}).get('score', 'N/A')}/5"
                llm_clar = f"{scores.get('clarity',      {}).get('score', 'N/A')}/5"
                llm_safe = f"{scores.get('safety',       {}).get('score', 'N/A')}/5"
                llm_help = f"{scores.get('helpfulness',  {}).get('score', 'N/A')}/5"
                llm_rel  = f"{scores.get('relevance',    {}).get('score', 'N/A')}/5"
            else:
                llm_corr = llm_comp = llm_clar = llm_safe = llm_help = llm_rel = "Skipped (Ollama Offline)"

            rows.append([res['id'], bleu_str, rouge1, rougeL, llm_corr, llm_comp, llm_clar, llm_safe, llm_help, llm_rel])
            
        f.write(tabulate(rows, headers=headers, tablefmt="github") + "\n\n")
        
        f.write("## Detailed Analysis & Educational Breakdown\n\n")
        
        for res in results:
            f.write(f"### Example {res['id']}\n\n")
            f.write(f"**Prompt:**\n> {res['prompt']}\n\n")
            f.write(f"**Reference Response:**\n> {res['reference']}\n\n")
            f.write(f"**Candidate Response:**\n> {res['candidate']}\n\n")
            
            f.write("#### 1. BLEU Score Analysis\n")
            f.write(f"- **Final BLEU Score:** {res['bleu']['score']:.4f}\n")
            f.write(f"- **Brevity Penalty (BP):** {res['bleu']['brevity_penalty']:.4f} (Candidate len: {res['bleu']['manual']['candidate_len']}, Reference len: {res['bleu']['manual']['reference_len']})\n")
            f.write("- **N-Gram Precision Breakdown:**\n")
            for ngram, detail in res['bleu']['manual']['details'].items():
                f.write(f"  - **{ngram}:** Precision = {detail['precision']:.4f} ({detail['overlap']} overlap out of {detail['total']} candidate n-grams)\n")
            f.write(f"- **NLTK Reference (with method 1 smoothing):** {res['bleu']['nltk_reference']:.4f}\n\n")
            
            f.write("#### 2. ROUGE Score Analysis\n")
            f.write("- **F1-Scores (Google Rouge-Score Library):**\n")
            f.write(f"  - **ROUGE-1 (Unigrams):** {res['rouge']['score']['rouge1']:.4f} (P: {res['rouge']['library_reference']['rouge1']['precision']:.4f}, R: {res['rouge']['library_reference']['rouge1']['recall']:.4f})\n")
            f.write(f"  - **ROUGE-2 (Bigrams):** {res['rouge']['score']['rouge2']:.4f} (P: {res['rouge']['library_reference']['rouge2']['precision']:.4f}, R: {res['rouge']['library_reference']['rouge2']['recall']:.4f})\n")
            f.write(f"  - **ROUGE-L (Longest Common Subsequence):** {res['rouge']['score']['rougeL']:.4f} (P: {res['rouge']['library_reference']['rougeL']['precision']:.4f}, R: {res['rouge']['library_reference']['rougeL']['recall']:.4f})\n")
            f.write("- **Manual Calculation (without stemming comparison):**\n")
            f.write(f"  - **ROUGE-1 F1:** {res['rouge']['manual']['rouge1']['f1']:.4f}\n")
            f.write(f"  - **ROUGE-2 F1:** {res['rouge']['manual']['rouge2']['f1']:.4f}\n")
            f.write(f"  - **ROUGE-L F1:** {res['rouge']['manual']['rougeL']['f1']:.4f}\n\n")
            
            f.write("#### 3. LLM as Judge Evaluation\n")
            if res['llm']['success']:
                f.write(f"**Judge Model:** `{res['llm']['model_used']}`\n\n")
                f.write("| Metric | Score | Reasoning |\n")
                f.write("| --- | --- | --- |\n")
                for metric, detail in res['llm']['scores'].items():
                    f.write(f"| **{metric.capitalize()}** | {detail.get('score')}/5 | {detail.get('reasoning')} |\n")
                f.write("\n")
                f.write(f"**Overall Synthesis:**\n{res['llm']['overall_explanation']}\n\n")
            else:
                f.write(f"> **Warning / Error:** Could not perform LLM evaluation. Reason: *{res['llm']['error']}*\n\n")
                
            f.write("#### 4. Educational Takeaway / Commentary\n")
            f.write(f"*{res['commentary']}*\n\n")
            f.write("---\n\n")

    print(f"\n[Success] Detailed Markdown report written to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Run BLEU, ROUGE and LLM-as-Judge model evaluation.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml file")
    parser.add_argument("--samples", default="data/samples.json", help="Path to samples.json data file")
    parser.add_argument("--judge-model", help="Override the LLM judge model configured in config.yaml")
    args = parser.parse_args()

    # Load configurations
    config = load_yaml_config(args.config)
    
    # Extract configs with defaults
    ollama_cfg = config.get("ollama", {})
    host = ollama_cfg.get("host", "http://localhost:11434")
    
    # Model resolution: CLI arg overrides config.yaml
    judge_model = args.judge_model or ollama_cfg.get("judge_model") or "llama3.1:latest"
    
    eval_cfg = config.get("evaluation", {})
    bleu_weights = eval_cfg.get("bleu", {}).get("weights", [0.25, 0.25, 0.25, 0.25])
    llm_metrics = eval_cfg.get("llm_as_judge", {}).get("metrics", [])
    
    # Load samples
    try:
        samples = load_samples(args.samples)
    except Exception as e:
        print(f"Error loading samples: {e}")
        return

    # Initialize LLM judge
    judge = LLMAsJudgeEvaluator(host=host, model=judge_model)
    
    # Run status check for Ollama to display status before running evaluation
    is_ready, status_msg = judge.check_ollama_status()
    print("=" * 60)
    print(" MODEL EVALUATION FRAMEWORK RUNNER ")
    print("=" * 60)
    print(f"Ollama Endpoint: {host}")
    print(f"Target Judge Model: {judge_model}")
    print(f"Ollama Status: {status_msg}")
    print("-" * 60)

    results = []
    
    for sample in samples:
        sample_id = sample["id"]
        print(f"Evaluating Sample {sample_id}...")
        
        # Calculate BLEU
        bleu_res = calculate_bleu(sample["reference"], sample["candidate"], weights=bleu_weights)
        
        # Calculate ROUGE
        rouge_res = calculate_rouge(sample["reference"], sample["candidate"])
        
        # Run LLM as Judge
        print(f" -> Querying LLM judge ({judge_model})...")
        llm_res = judge.evaluate(
            prompt=sample["prompt"],
            reference=sample["reference"],
            candidate=sample["candidate"],
            metrics=llm_metrics
        )
        
        results.append({
            "id": sample_id,
            "prompt": sample["prompt"],
            "reference": sample["reference"],
            "candidate": sample["candidate"],
            "commentary": sample["commentary"],
            "bleu": bleu_res,
            "rouge": rouge_res,
            "llm": llm_res
        })
        
    # Print terminal summary
    print("\n" + "=" * 60)
    print(" EVALUATION RESULTS SUMMARY ")
    print("=" * 60)
    
    headers = [
        "ID",
        "BLEU Score\n(Manual/NLTK)",
        "ROUGE-1\n(F1)",
        "ROUGE-L\n(F1)",
        "LLM\nCorrectness",
        "LLM\nCompleteness",
        "LLM\nClarity",
        "LLM\nSafety",
        "LLM\nHelpfulness",
        "LLM\nRelevance",
    ]
    rows = []
    for res in results:
        bleu_str = f"{res['bleu']['manual']['score']:.2f}/{res['bleu']['nltk_reference']:.2f}"
        rouge1 = f"{res['rouge']['score']['rouge1']:.2f}"
        rougeL = f"{res['rouge']['score']['rougeL']:.2f}"

        if res['llm']['success']:
            scores = res['llm']['scores']
            llm_corr  = f"{scores.get('correctness',  {}).get('score', '-')}/5"
            llm_comp  = f"{scores.get('completeness', {}).get('score', '-')}/5"
            llm_clar  = f"{scores.get('clarity',      {}).get('score', '-')}/5"
            llm_safe  = f"{scores.get('safety',       {}).get('score', '-')}/5"
            llm_help  = f"{scores.get('helpfulness',  {}).get('score', '-')}/5"
            llm_rel   = f"{scores.get('relevance',    {}).get('score', '-')}/5"
        else:
            llm_corr = llm_comp = llm_clar = llm_safe = llm_help = llm_rel = "Offline"

        rows.append([res['id'], bleu_str, rouge1, rougeL, llm_corr, llm_comp, llm_clar, llm_safe, llm_help, llm_rel])
        
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    
    # Generate the Markdown report
    generate_markdown_report(results, judge_model)
    print("=" * 60)


if __name__ == "__main__":
    main()
