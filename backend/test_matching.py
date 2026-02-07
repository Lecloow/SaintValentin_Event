#!/usr/bin/env python3
"""Test the matching algorithm logic without database."""

def score(a: dict, b: dict) -> int:
    """Calculate compatibility score between two users."""
    s = 0
    for k in a:
        if k in b and a[k] == b[k]:
            s += 1
    return s


def test_matching_odd_numbers():
    """Test matching with odd number of users per level."""
    print("Testing matching algorithm with odd numbers...")
    
    # Simulate 5 users (odd number) in Terminale
    level_users = [
        {"id": "1", "level": "Terminale", "answers": {"q3": 1, "q4": 1, "q5": 1}},
        {"id": "2", "level": "Terminale", "answers": {"q3": 1, "q4": 1, "q5": 2}},
        {"id": "3", "level": "Terminale", "answers": {"q3": 2, "q4": 2, "q5": 2}},
        {"id": "4", "level": "Terminale", "answers": {"q3": 2, "q4": 2, "q5": 1}},
        {"id": "5", "level": "Terminale", "answers": {"q3": 3, "q4": 3, "q5": 3}},
    ]
    
    n = len(level_users)
    
    # Calculate compatibility scores
    scores_dict = {}
    for i in range(n):
        for j in range(i + 1, n):
            user_a = level_users[i]
            user_b = level_users[j]
            compatibility = score(user_a["answers"], user_b["answers"])
            scores_dict[(i, j)] = compatibility
    
    sorted_pairs = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)
    
    # Day 1 matching
    day1_matches = {}
    day1_trio_members = set()
    used = set()
    
    for (i, j), score_val in sorted_pairs:
        if i not in used and j not in used:
            day1_matches[i] = j
            day1_matches[j] = i
            used.add(i)
            used.add(j)
    
    # Handle odd number for day 1
    if len(used) < n:
        unmatched = [idx for idx in range(n) if idx not in used]
        if len(unmatched) == 1:
            if day1_matches:
                best_match_idx = None
                best_score = -1
                for idx in range(n):
                    if idx in used:
                        compatibility = score(level_users[unmatched[0]]["answers"], level_users[idx]["answers"])
                        if compatibility > best_score:
                            best_score = compatibility
                            best_match_idx = idx
                
                if best_match_idx is not None:
                    day1_matches[unmatched[0]] = best_match_idx
                    used.add(unmatched[0])
                    partner = day1_matches.get(best_match_idx)
                    # Mark trio members
                    day1_trio_members.add(unmatched[0])
                    day1_trio_members.add(best_match_idx)
                    day1_trio_members.add(partner)
                    print(f"✓ Day 1 trio formed: users {unmatched[0]}, {best_match_idx}, {partner}")
    
    # Day 2 matching - prioritize matching day 1 trio members first
    day2_matches = {}
    used2 = set()
    
    # If there was a day 1 trio and we expect a day 2 trio (odd number)
    # prioritize matching day 1 trio members first to avoid them being unmatched again
    if day1_trio_members and n % 2 == 1:
        pairs_with_trio = []
        pairs_without_trio = []
        for (i, j), score_val in sorted_pairs:
            if day1_matches.get(i) == j or day1_matches.get(j) == i:
                continue
            if i in day1_trio_members or j in day1_trio_members:
                pairs_with_trio.append(((i, j), score_val))
            else:
                pairs_without_trio.append(((i, j), score_val))
        
        # Process trio members first
        for (i, j), score_val in pairs_with_trio:
            if i not in used2 and j not in used2:
                day2_matches[i] = j
                day2_matches[j] = i
                used2.add(i)
                used2.add(j)
        
        # Then process others
        for (i, j), score_val in pairs_without_trio:
            if i not in used2 and j not in used2:
                day2_matches[i] = j
                day2_matches[j] = i
                used2.add(i)
                used2.add(j)
    else:
        # Normal matching for day 2
        for (i, j), score_val in sorted_pairs:
            if day1_matches.get(i) == j or day1_matches.get(j) == i:
                continue
            if i not in used2 and j not in used2:
                day2_matches[i] = j
                day2_matches[j] = i
                used2.add(i)
                used2.add(j)
    
    # Handle remaining unmatched for day 2
    unmatched2 = [idx for idx in range(n) if idx not in used2]
    if len(unmatched2) == 1:
        if day2_matches:
            best_match_idx = None
            best_score = -1
            best_non_trio_match_idx = None
            best_non_trio_score = -1
            
            for idx in range(n):
                if idx in used2:
                    compatibility = score(level_users[unmatched2[0]]["answers"], level_users[idx]["answers"])
                    if compatibility > best_score:
                        best_score = compatibility
                        best_match_idx = idx
                    if idx not in day1_trio_members and compatibility > best_non_trio_score:
                        best_non_trio_score = compatibility
                        best_non_trio_match_idx = idx
            
            # Prefer non-trio member if unmatched person was in day 1 trio
            if unmatched2[0] in day1_trio_members and best_non_trio_match_idx is not None:
                day2_matches[unmatched2[0]] = best_non_trio_match_idx
                used2.add(unmatched2[0])
                partner = day2_matches.get(best_non_trio_match_idx)
                print(f"✓ Day 2 trio formed: user {unmatched2[0]} (was in day1 trio) with {best_non_trio_match_idx} (NOT in day1 trio) and {partner}")
            elif best_match_idx is not None:
                day2_matches[unmatched2[0]] = best_match_idx
                used2.add(unmatched2[0])
                partner = day2_matches.get(best_match_idx)
                print(f"✓ Day 2 trio formed: users {unmatched2[0]}, {best_match_idx}, {partner}")
    
    # Verify requirements
    print("\n=== Verification ===")
    
    # Check that everyone has a match for both days
    all_matched = True
    for i in range(n):
        if i not in day1_matches or i not in day2_matches:
            print(f"✗ User {i} missing a match")
            all_matched = False
    
    if all_matched:
        print("✓ All users have matches for both days")
    
    # Check no duplicate matches
    duplicate_found = False
    for i in range(n):
        if day1_matches.get(i) == day2_matches.get(i):
            print(f"✗ User {i} has same match on both days: {day1_matches.get(i)}")
            duplicate_found = True
    
    if not duplicate_found:
        print("✓ No user has the same match on both days")
    
    # Check trio constraint
    day2_trio_members = set()
    if len(unmatched2) == 1 and unmatched2[0] in day2_matches:
        matched_idx = day2_matches[unmatched2[0]]
        partner_idx = day2_matches.get(matched_idx)
        day2_trio_members.add(unmatched2[0])
        day2_trio_members.add(matched_idx)
        if partner_idx is not None:
            day2_trio_members.add(partner_idx)
    
    # Check if anyone is in a trio on both days
    both_days_trio = day1_trio_members & day2_trio_members
    if both_days_trio:
        print(f"⚠ Users in trio on BOTH days: {both_days_trio}")
        print(f"  (This is allowed, but we try to avoid it)")
    else:
        print("✓ No user is in a trio on both days")
    
    print(f"\nDay 1 trio members: {day1_trio_members}")
    print(f"Day 2 trio members: {day2_trio_members}")
    
    return all_matched and not duplicate_found


def test_matching_even_numbers():
    """Test matching with even number of users per level."""
    print("\nTesting matching algorithm with even numbers...")
    
    # Simulate 4 users (even number) in Première
    level_users = [
        {"id": "1", "level": "Première", "answers": {"q3": 1, "q4": 1, "q5": 1}},
        {"id": "2", "level": "Première", "answers": {"q3": 1, "q4": 1, "q5": 2}},
        {"id": "3", "level": "Première", "answers": {"q3": 2, "q4": 2, "q5": 2}},
        {"id": "4", "level": "Première", "answers": {"q3": 2, "q4": 2, "q5": 1}},
    ]
    
    n = len(level_users)
    
    # Calculate compatibility scores
    scores_dict = {}
    for i in range(n):
        for j in range(i + 1, n):
            user_a = level_users[i]
            user_b = level_users[j]
            compatibility = score(user_a["answers"], user_b["answers"])
            scores_dict[(i, j)] = compatibility
    
    sorted_pairs = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)
    
    # Day 1 matching
    day1_matches = {}
    used = set()
    
    for (i, j), score_val in sorted_pairs:
        if i not in used and j not in used:
            day1_matches[i] = j
            day1_matches[j] = i
            used.add(i)
            used.add(j)
    
    # Day 2 matching
    day2_matches = {}
    used2 = set()
    
    for (i, j), score_val in sorted_pairs:
        if day1_matches.get(i) == j or day1_matches.get(j) == i:
            continue
        if i not in used2 and j not in used2:
            day2_matches[i] = j
            day2_matches[j] = i
            used2.add(i)
            used2.add(j)
    
    # Handle remaining (should be 0 or 2 for even numbers)
    unmatched2 = [idx for idx in range(n) if idx not in used2]
    if len(unmatched2) == 2:
        day2_matches[unmatched2[0]] = unmatched2[1]
        day2_matches[unmatched2[1]] = unmatched2[0]
    
    # Verify requirements
    print("=== Verification ===")
    
    all_matched = True
    for i in range(n):
        if i not in day1_matches or i not in day2_matches:
            print(f"✗ User {i} missing a match")
            all_matched = False
    
    if all_matched:
        print("✓ All users have matches for both days")
    
    duplicate_found = False
    for i in range(n):
        if day1_matches.get(i) == day2_matches.get(i):
            print(f"✗ User {i} has same match on both days")
            duplicate_found = True
    
    if not duplicate_found:
        print("✓ No user has the same match on both days")
    
    return all_matched and not duplicate_found


if __name__ == "__main__":
    print("=" * 60)
    print("Soulmate Matching Algorithm Tests")
    print("=" * 60)
    
    test1_passed = test_matching_odd_numbers()
    test2_passed = test_matching_even_numbers()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
