#!/usr/bin/env python3
"""Standalone test for answer parsing without DB connection."""

import pandas as pd

# Answer mapping: Maps question text answers to integer values (1-4)
ANSWER_MAPPINGS = {
    "Quel est ton style de musique préféré ?": {
        "Rap": 1,
        "Pop": 2,
        "Rock": 3,
        "Autre": 4,
    },
    "Quel est pour toi le voyage idéal ?": {
        "Voyage en famille": 1,
        "Voyage entre amis": 2,
        "Voyage en couple": 3,
        "Voyage solo": 4,
    },
    "Quelle est ta destination de rêve ?": {
        "Londres": 1,
        "Séoul": 2,
        "Marrakech": 3,
        "Rio de Janeiro": 4,
    },
    "Quel est ton genre de film/série préféré ?": {
        "Science-Fiction": 1,
        "Drame": 2,
        "Comédie": 3,
        "Action": 4,
    },
    "Tu passes le plus de temps sur :": {
        "Instagram": 1,
        "Snapchat": 2,
        "TikTok": 3,
        "Je ne suis pas vraiment sur les réseaux": 4,
    },
}

QUESTION_TO_COLUMN = {
    "Quel est ton style de musique préféré ?": "q3",
    "Quel est pour toi le voyage idéal ?": "q4",
    "Quelle est ta destination de rêve ?": "q5",
    "Quel est ton genre de film/série préféré ?": "q6",
    "Tu passes le plus de temps sur :": "q7",
}

def parse_answer(question: str, answer: str):
    """Parse a text answer and convert it to integer (1-4)."""
    if not answer or pd.isna(answer):
        return None
    
    answer = str(answer).strip()
    
    if question not in ANSWER_MAPPINGS:
        return None
    
    mapping = ANSWER_MAPPINGS[question]
    
    # Try exact match first
    if answer in mapping:
        return mapping[answer]
    
    # Try case-insensitive match
    for key, value in mapping.items():
        if key.lower() == answer.lower():
            return value
    
    # Try partial match
    for key, value in mapping.items():
        if key.lower() in answer.lower() or answer.lower() in key.lower():
            return value
    
    return None

# Test parse_answer function
def test_parse_answer():
    print("Testing parse_answer function...")
    
    test_cases = [
        ("Quel est ton style de musique préféré ?", "Pop", 2),
        ("Quel est ton style de musique préféré ?", "Pop ", 2),
        ("Quel est ton style de musique préféré ?", "pop", 2),
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
            print(f"✓ '{answer}' → {result}")
            passed += 1
        else:
            print(f"✗ '{answer}' → {result} (expected {expected})")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed\n")
    return failed == 0

# Test with actual XLSX
def test_xlsx():
    print("Testing with input.xlsx...")
    
    try:
        df = pd.read_excel('input.xlsx', dtype=object)
        print(f"✓ Loaded {len(df)} rows\n")
        
        if len(df) == 0:
            print("✗ No data in file")
            return False
        
        row = df.iloc[0]
        print(f"First row data (ID: {row.get('ID', 'N/A')}):\n")
        
        parsed_count = 0
        for question_text, column_name in QUESTION_TO_COLUMN.items():
            # Find matching column (handle spacing)
            answer_text = None
            for col in df.columns:
                if col and question_text.replace(" ", "").lower() == col.replace(" ", "").lower():
                    answer_text = row[col]
                    break
            
            if answer_text and not pd.isna(answer_text):
                parsed = parse_answer(question_text, answer_text)
                status = "✓" if parsed else "✗"
                print(f"{status} {column_name}: '{answer_text}' → {parsed}")
                if parsed:
                    parsed_count += 1
            else:
                print(f"- {column_name}: NO ANSWER")
        
        print(f"\n✓ Parsed {parsed_count}/{len(QUESTION_TO_COLUMN)} answers")
        return parsed_count >= 3
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Answer Parsing Test")
    print("=" * 60 + "\n")
    
    success = test_parse_answer() and test_xlsx()
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!" if success else "✗ Some tests failed")
    print("=" * 60)
