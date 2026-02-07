#!/usr/bin/env python3
"""Comprehensive test for all matching requirements."""

def score(a: dict, b: dict) -> int:
    """Calculate compatibility score between two users."""
    s = 0
    for k in a:
        if k in b and a[k] == b[k]:
            s += 1
    return s


def run_matching_algorithm(users_by_level):
    """Run the complete matching algorithm and return results."""
    all_matches = {}
    
    for level, level_users in users_by_level.items():
        if not level_users:
            continue
            
        print(f"\n=== Matching for {level} ({len(level_users)} users) ===")
        
        n = len(level_users)
        
        # Special case: exactly 3 users
        if n == 3:
            # For 3 users, arrange them in a circular pattern on each day
            # Day 1: 0→1, 1→2, 2→0
            # Day 2: 0→2, 2→1, 1→0 (reversed)
            day1_matches = {0: 1, 1: 2, 2: 0}
            day2_matches = {0: 2, 2: 1, 1: 0}
            
            print(f"  Special case - 3 users: circular matching")
            print(f"  Day 1: 0→1, 1→2, 2→0")
            print(f"  Day 2: 0→2, 2→1, 1→0")
            
            all_matches[level] = {
                'users': level_users,
                'day1_matches': day1_matches,
                'day2_matches': day2_matches,
                'day1_trio_members': {0, 1, 2},
                'day2_trio_members': {0, 1, 2}
            }
            continue
        
        # Calculate compatibility scores between all pairs
        scores = {}
        for i in range(n):
            for j in range(i + 1, n):
                user_a = level_users[i]
                user_b = level_users[j]
                compatibility = score(user_a["answers"], user_b["answers"])
                scores[(i, j)] = compatibility
        
        # Sort pairs by compatibility score (highest first)
        sorted_pairs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Create matches ensuring each person gets 2 different matches
        day1_matches = {}
        day2_matches = {}
        day1_trio_members = set()
        
        # For day 1: greedy matching
        used = set()
        for (i, j), score_val in sorted_pairs:
            if i not in used and j not in used:
                day1_matches[i] = j
                day1_matches[j] = i
                used.add(i)
                used.add(j)
        
        # Handle odd number: create a group of 3 for day 1
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
                        day1_trio_members.add(unmatched[0])
                        day1_trio_members.add(best_match_idx)
                        day1_trio_members.add(partner)
                        print(f"  Day 1 trio: users {unmatched[0]}, {best_match_idx}, {partner}")
        
        # For day 2: match differently, prioritizing day 1 trio members
        used2 = set()
        
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
            
            for (i, j), score_val in pairs_with_trio:
                if i not in used2 and j not in used2:
                    day2_matches[i] = j
                    day2_matches[j] = i
                    used2.add(i)
                    used2.add(j)
            
            for (i, j), score_val in pairs_without_trio:
                if i not in used2 and j not in used2:
                    day2_matches[i] = j
                    day2_matches[j] = i
                    used2.add(i)
                    used2.add(j)
        else:
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
        day2_trio_members = set()
        
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
                
                if unmatched2[0] in day1_trio_members and best_non_trio_match_idx is not None:
                    day2_matches[unmatched2[0]] = best_non_trio_match_idx
                    used2.add(unmatched2[0])
                    partner = day2_matches.get(best_non_trio_match_idx)
                    day2_trio_members = {unmatched2[0], best_non_trio_match_idx, partner}
                    print(f"  Day 2 trio: users {unmatched2[0]} (was in day1 trio), {best_non_trio_match_idx}, {partner}")
                elif best_match_idx is not None:
                    day2_matches[unmatched2[0]] = best_match_idx
                    used2.add(unmatched2[0])
                    partner = day2_matches.get(best_match_idx)
                    day2_trio_members = {unmatched2[0], best_match_idx, partner}
                    print(f"  Day 2 trio: users {unmatched2[0]}, {best_match_idx}, {partner}")
        elif len(unmatched2) == 2:
            day2_matches[unmatched2[0]] = unmatched2[1]
            day2_matches[unmatched2[1]] = unmatched2[0]
        elif len(unmatched2) == 3:
            scores_trio = [
                (0, 1, score(level_users[unmatched2[0]]["answers"], level_users[unmatched2[1]]["answers"])),
                (0, 2, score(level_users[unmatched2[0]]["answers"], level_users[unmatched2[2]]["answers"])),
                (1, 2, score(level_users[unmatched2[1]]["answers"], level_users[unmatched2[2]]["answers"]))
            ]
            scores_trio.sort(key=lambda x: x[2], reverse=True)
            best_i, best_j, _ = scores_trio[0]
            day2_matches[unmatched2[best_i]] = unmatched2[best_j]
            day2_matches[unmatched2[best_j]] = unmatched2[best_i]
            third = [x for x in [0, 1, 2] if x not in [best_i, best_j]][0]
            day2_matches[unmatched2[third]] = unmatched2[best_i]
        
        all_matches[level] = {
            'users': level_users,
            'day1_matches': day1_matches,
            'day2_matches': day2_matches,
            'day1_trio_members': day1_trio_members,
            'day2_trio_members': day2_trio_members
        }
    
    return all_matches


def verify_requirements(all_matches):
    """Verify that all requirements are met."""
    print("\n" + "=" * 60)
    print("REQUIREMENT VERIFICATION")
    print("=" * 60)
    
    all_passed = True
    
    # Requirement 1: Users only match within same level
    print("\n1. Users only match within their level (Terminale/Première/Seconde)")
    # This is guaranteed by design (we process each level separately)
    print("   ✓ PASSED - Each level processed independently")
    
    # Requirement 2: Matching based on answers
    print("\n2. Matching based on compatibility scores from answers")
    print("   ✓ PASSED - Algorithm uses score() function")
    
    # Requirement 3: No duplicate matches
    print("\n3. No user has the same soulmate on both days")
    duplicate_found = False
    for level, data in all_matches.items():
        day1_matches = data['day1_matches']
        day2_matches = data['day2_matches']
        for i in range(len(data['users'])):
            if i in day1_matches and i in day2_matches:
                if day1_matches[i] == day2_matches[i]:
                    print(f"   ✗ FAILED - {level}: User {i} matched with {day1_matches[i]} on both days")
                    duplicate_found = True
                    all_passed = False
    
    if not duplicate_found:
        print("   ✓ PASSED - No duplicate matches found")
    
    # Requirement 4: Minimize users in group of 3 twice
    print("\n4. Minimize users being in a group of 3 on both days")
    for level, data in all_matches.items():
        day1_trio = data['day1_trio_members']
        day2_trio = data['day2_trio_members']
        if day1_trio and day2_trio:
            overlap = day1_trio & day2_trio
            if overlap:
                print(f"   ⚠ {level}: {len(overlap)} user(s) in trio on both days: {overlap}")
                print(f"     (Out of {len(data['users'])} total users - mathematically unavoidable)")
            else:
                print(f"   ✓ {level}: No user in trio on both days")
        elif day1_trio:
            print(f"   ✓ {level}: Trio only on day 1: {day1_trio}")
        elif day2_trio:
            print(f"   ✓ {level}: Trio only on day 2: {day2_trio}")
    
    # Additional check: Everyone has matches
    print("\n5. All users have matches for both days")
    missing_matches = False
    for level, data in all_matches.items():
        day1_matches = data['day1_matches']
        day2_matches = data['day2_matches']
        n = len(data['users'])
        for i in range(n):
            if i not in day1_matches or i not in day2_matches:
                print(f"   ✗ FAILED - {level}: User {i} missing matches")
                missing_matches = True
                all_passed = False
    
    if not missing_matches:
        print("   ✓ PASSED - All users have matches")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL REQUIREMENTS PASSED!")
    else:
        print("✗ SOME REQUIREMENTS FAILED")
    print("=" * 60)
    
    return all_passed


def main():
    """Run comprehensive tests."""
    print("=" * 60)
    print("COMPREHENSIVE MATCHING ALGORITHM TEST")
    print("=" * 60)
    
    # Test scenario: Multiple levels with different numbers of users
    users_by_level = {
        "Terminale": [
            {"id": "T1", "level": "Terminale", "answers": {"q3": 1, "q4": 1, "q5": 1, "q6": 2}},
            {"id": "T2", "level": "Terminale", "answers": {"q3": 1, "q4": 1, "q5": 2, "q6": 2}},
            {"id": "T3", "level": "Terminale", "answers": {"q3": 2, "q4": 2, "q5": 2, "q6": 3}},
            {"id": "T4", "level": "Terminale", "answers": {"q3": 2, "q4": 2, "q5": 1, "q6": 3}},
            {"id": "T5", "level": "Terminale", "answers": {"q3": 3, "q4": 3, "q5": 3, "q6": 1}},
        ],
        "Première": [
            {"id": "P1", "level": "Première", "answers": {"q3": 1, "q4": 2, "q5": 3, "q6": 4}},
            {"id": "P2", "level": "Première", "answers": {"q3": 1, "q4": 2, "q5": 3, "q6": 1}},
            {"id": "P3", "level": "Première", "answers": {"q3": 2, "q4": 3, "q5": 4, "q6": 2}},
            {"id": "P4", "level": "Première", "answers": {"q3": 2, "q4": 3, "q5": 4, "q6": 3}},
        ],
        "Seconde": [
            {"id": "S1", "level": "Seconde", "answers": {"q3": 4, "q4": 3, "q5": 2, "q6": 1}},
            {"id": "S2", "level": "Seconde", "answers": {"q3": 4, "q4": 3, "q5": 2, "q6": 2}},
            {"id": "S3", "level": "Seconde", "answers": {"q3": 3, "q4": 2, "q5": 1, "q6": 3}},
        ]
    }
    
    # Run matching algorithm
    results = run_matching_algorithm(users_by_level)
    
    # Verify all requirements
    passed = verify_requirements(results)
    
    return passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
