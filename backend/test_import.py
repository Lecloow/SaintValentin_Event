#!/usr/bin/env python3
"""Test script to verify XLSX import with answer parsing."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from main import parse_answer, ANSWER_MAPPINGS, QUESTION_TO_COLUMN
import pandas as pd

# Test parse_answer function
def test_parse_answer():
    print("Testing parse_answer function...")
    
    test_cases = [
        ("Quel est ton style de musique préféré ?", "Pop", 2),
        ("Quel est ton style de musique préféré ?", "Pop ", 2),  # with space
        ("Quel est ton style de musique préféré ?", "pop", 2),   # lowercase
        ("Quel est ton style de musique préféré ?", "Rap", 1),
        ("Quel est pour toi le voyage idéal ?", "Voyage en couple", 3),
        ("Quelle est ta destination de rêve ?", "Marrakech", 3),
        ("Quel est ton genre de film/série préféré ?", "Drame", 2),
        ("Tu passes le plus de temps sur :", "Snapchat", 2),
    ]
    
    passed = 0
    failed = 0
    
    for question, answer, expected in test_cases:
        result = parse_answer(question, answer)
        if result == expected:
            print(f"✓ {answer} → {result}")
            passed += 1
        else:
            print(f"✗ {answer} → {result} (expected {expected})")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed\n")
    return failed == 0

# Test with actual XLSX file
def test_xlsx_import():
    print("Testing XLSX import...")
    
    if not os.path.exists('input.xlsx'):
        print("✗ input.xlsx not found")
        return False
    
    df = pd.read_excel('input.xlsx', dtype=object)
    print(f"✓ Loaded {len(df)} rows from XLSX")
    
    if len(df) == 0:
        print("✗ No data in XLSX")
        return False
    
    # Check first row
    row = df.iloc[0]
    print(f"\nTesting first row (ID: {row.get('ID', 'N/A')}):")
    
    parsed_count = 0
    for question_text, column_name in QUESTION_TO_COLUMN.items():
        # Find the question in the dataframe (handle spacing variations)
        answer_text = None
        for col in df.columns:
            if col and question_text.replace(" ", "").lower() == col.replace(" ", "").lower():
                answer_text = row[col]
                break
        
        if answer_text and not pd.isna(answer_text):
            parsed_value = parse_answer(question_text, answer_text)
            if parsed_value:
                print(f"  {column_name}: {answer_text} → {parsed_value}")
                parsed_count += 1
            else:
                print(f"  {column_name}: {answer_text} → FAILED TO PARSE")
        else:
            print(f"  {column_name}: NO ANSWER")
    
    print(f"\nParsed {parsed_count}/15 answers")
    return parsed_count >= 10  # At least 10 answers should be parseable

if __name__ == "__main__":
    print("=" * 60)
    print("XLSX Import Test Suite")
    print("=" * 60 + "\n")
    
    success = True
    
    success = test_parse_answer() and success
    success = test_xlsx_import() and success
    
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
