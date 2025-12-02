#!/usr/bin/env python3
"""
ZON LLM Retrieval Accuracy Benchmark

Compares ZON against JSON, CSV, and other formats for LLM retrieval accuracy.
"""

import os
import sys
import json
import time
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import zon
from validators import validate_answer, extract_answer
from csv_encoder import encode_to_csv, encode_to_tsv

# Use tiktoken for token counting
try:
    import tiktoken
    enc = tiktoken.get_encoding("o200k_base")
    def count_tokens(text):
        return len(enc.encode(text))
except ImportError:
    print("⚠️  tiktoken not installed. Token counting will be disabled.")
    print("   Install with: pip install tiktoken")
    def count_tokens(text):
        return 0

# LLM Client
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from zon.llm_client import AzureAIClient

OUTPUT_FILE = Path(__file__).parent.parent / 'results' / 'accuracy_results.json'
CONCURRENCY = 1


def encode_data(data, format_name):
    """Encodes data into specified format.
    
    Args:
        data: Data to encode
        format_name: Format name
        
    Returns:
        Encoded data or None if failed
    """
    try:
        if format_name == 'ZON':
            return zon.encode(data)
        elif format_name == 'CSV':
            return encode_to_csv(data)
        elif format_name == 'TSV':
            return encode_to_tsv(data)
        elif format_name == 'JSON':
            return json.dumps(data, indent=2)
        elif format_name == 'JSON (Minified)':
            return json.dumps(data, separators=(',', ':'))
        else:
            raise ValueError(f"Unknown format: {format_name}")
    except Exception as e:
        print(f"Error encoding {format_name}: {e}")
        return None


def build_prompt(data, format_name, question):
    """Builds prompt for LLM.
    
    Args:
        data: Encoded data
        format_name: Format name
        question: Question text
        
    Returns:
        Formatted prompt
    """
    header = f"Data format: {format_name}"
    
    if format_name == 'ZON':
        header += "\nIMPORTANT: Columns in brackets like [id] indicate sequential values. These [id] items ARE valid fields and MUST be included when listing available fields. Top-level sections starting with @ (e.g. @users) are also keys."
    
    prompt = f"""{header}
Data:
{data}

Question: {question}

Provide ONLY the direct answer value. Do not include full sentences, explanations, or units unless requested.
Example: for "What is the salary?", answer "95000" not "The salary is 95000".
Answer:"""
    
    return prompt


def run_benchmark():
    """Run the benchmark."""
    
    cache_dir = Path(__file__).parent.parent.parent / '.cache'
    print('🧹 Clearing cache...')
    if cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    print('✅ Cache cleared\n')
    
    print('╔' + '═' * 78 + '╗')
    print('🚀 Starting LLM Retrieval Accuracy Benchmark')
    print('═' * 80)
    
    client = AzureAIClient()
    models = ['deepseek-v3.1', 'grok-3', 'Llama-3.3-70B-Instruct']
    
    data_path = Path(__file__).parent.parent / 'data' / 'unified_dataset.json'
    with open(data_path) as f:
        data = json.load(f)
    
    questions_path = Path(__file__).parent.parent / 'data' / 'questions_309.json'
    with open(questions_path) as f:
        questions = json.load(f)
    
    formats = ['ZON', 'JSON', 'JSON (Minified)', 'CSV']
    
    results = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'models': {},
        'summary': {}
    }
    
    for model in models:
        results['models'][model] = {}
        for fmt in formats:
            results['models'][model][fmt] = {
                'correct': 0,
                'total': 0,
                'tokens': 0,
                'errors': 0
            }
    
    print(f"\n📂 Dataset: UNIFIED")
    
    encoded_data = {}
    data_tokens = {}
    
    for fmt in formats:
        encoded_data[fmt] = encode_data(data, fmt)
        if encoded_data[fmt]:
            data_tokens[fmt] = count_tokens(encoded_data[fmt])
    
    if 'ZON' in encoded_data and encoded_data['ZON']:
        print('   🛡️  Validating ZON data...')
        try:
            decoded = zon.decode(encoded_data['ZON'])
            re_encoded = zon.encode(decoded)
            if re_encoded == encoded_data['ZON']:
                print('      ✅ ZON Roundtrip Successful (Lossless)')
            else:
                print('      ❌ ZON Roundtrip Mismatch!')
        except Exception as e:
            print(f'      ❌ ZON Roundtrip Failed: {e}')
    
    for model in models:
        print(f"   🤖 Model: {model}")
        
        for fmt in formats:
            if not encoded_data.get(fmt):
                print(f"      ⚠️  {fmt}: Skipped (encoding failed)")
                continue
            
            sys.stdout.write(f"      {fmt.ljust(18)}: ")
            sys.stdout.flush()
            
            correct_count = 0
            total_tokens = 0
            
            test_questions = questions[:20]
            
            for q in test_questions:
                time.sleep(2)
                
                prompt = build_prompt(encoded_data[fmt], fmt, q['q'])
                
                try:
                    result = client.query(model, prompt, 2000)
                    extracted = extract_answer(result['answer'])
                    is_correct = validate_answer(extracted, q['a'], q['type'])
                    
                    results['models'][model][fmt]['total'] += 1
                    results['models'][model][fmt]['tokens'] += result['tokensUsed']
                    total_tokens += result['tokensUsed']
                    
                    if is_correct:
                        results['models'][model][fmt]['correct'] += 1
                        correct_count += 1
                        sys.stdout.write('.')
                    else:
                        sys.stdout.write('x')
                        print(f"\n[DEBUG] Q: \"{q['q']}\"")
                        print(f"        Expected: \"{q['a']}\"")
                        print(f"        Actual:   \"{result['answer']}\"")
                        print(f"        Extracted: \"{extracted}\"")
                    
                    sys.stdout.flush()
                    
                except Exception as e:
                    results['models'][model][fmt]['errors'] += 1
                    sys.stdout.write('E')
                    sys.stdout.flush()
            
            accuracy = (correct_count / len(test_questions)) * 100 if test_questions else 0
            print(f" {correct_count}/{len(test_questions)} ({accuracy:.1f}%)")
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to {OUTPUT_FILE}")
    
    print('\n📊 FINAL RESULTS SUMMARY')
    print('═' * 80)
    
    for model in models:
        print(f"\n🤖 {model}")
        model_results = results['models'][model]
        
        sorted_formats = []
        for fmt in formats:
            r = model_results[fmt]
            accuracy = (r['correct'] / r['total']) * 100 if r['total'] > 0 else 0
            tokens = data_tokens.get(fmt, 0)
            efficiency = (accuracy / tokens) * 1000 if tokens > 0 else 0
            
            sorted_formats.append({
                'format': fmt,
                **r,
                'accuracy': accuracy,
                'efficiency': efficiency,
                'dataTokens': tokens
            })
        
        sorted_formats.sort(key=lambda x: x['efficiency'], reverse=True)
        
        print('\nEfficiency Ranking (Accuracy per 1K Tokens):')
        for r in sorted_formats:
            bar = '█' * min(int(r['efficiency']), 20)
            bar = bar.ljust(20, '░')
            print(f"  {r['format'].ljust(18)} {bar} {r['efficiency']:.1f} acc%/1K tok | {r['accuracy']:.1f}% acc | {r['dataTokens']:,} tokens")
 
 
if __name__ == "__main__":
    run_benchmark()
