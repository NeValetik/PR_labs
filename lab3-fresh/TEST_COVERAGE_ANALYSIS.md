# Test Coverage Analysis: Game Rules vs Test Cases

## Game Rules Summary

### First Card Rules
- **1-A**: If no card there (empty space), operation fails
- **1-B**: If card is face down, it turns face up and player controls it
- **1-C**: If card is already face up but not controlled by another player, it remains face up and player controls it
- **1-D**: If card is face up and controlled by another player, operation waits

### Second Card Rules
- **2-A**: If no card there, operation fails. Player relinquishes control of first card (but it remains face up)
- **2-B**: If card is face up and controlled by a player (another or themselves), operation fails (doesn't wait). Player relinquishes control of first card
- **2-C**: If card is face down, it turns face up
- **2-D**: If two cards match, player keeps control of both (remain face up)
- **2-E**: If they don't match, player relinquishes control of both (remain face up)

### After Second Card (Next Move)
- **3-A**: If previous cards matched, remove them from board and relinquish control
- **3-B**: Otherwise, for each card that is still on board, face up, and not controlled by another player, turn it face down

## Test Coverage Analysis

### ✅ Covered Rules

#### Rule 1-B: Face down card turns face up
- **Test**: `flip - should flip a card face up` (line 202-210)
- **Status**: ✅ Covered

#### Rule 1-D: Wait for card controlled by another player
- **Test**: `flip - should wait for card to become available` (line 266-280)
- **Status**: ✅ Covered (basic case)

#### Rule 2-D & 3-A: Matching pair
- **Test**: `flip - should handle matching pair correctly` (line 230-241)
- **Status**: ⚠️ Partially covered - test exists but doesn't verify removal

#### Rule 2-E & 3-B: Non-matching pair
- **Test**: `flip - should handle non-matching pair correctly` (line 243-264)
- **Status**: ⚠️ Partially covered - test exists but doesn't verify cards turn face down

#### Concurrent operations
- **Test**: `concurrent operations - should handle multiple players flipping simultaneously` (line 379-402)
- **Status**: ✅ Covered (basic concurrency)

### ❌ Missing Test Cases

#### Rule 1-A: Flipping empty space should fail
- **Current**: Test checks invalid coordinates (line 221-228) but not removed cards
- **Missing**: Test that flips a card, removes it (via match), then tries to flip that empty space
- **Impact**: HIGH - This is a critical failure case

#### Rule 1-C: Flipping face-up card not controlled by anyone
- **Current**: No test for this scenario
- **Missing**: Test where:
  1. Player1 flips card A (face up, controlled)
  2. Player1 flips card B (non-match, relinquishes control of A)
  3. Player2 flips card A (should succeed - it's face up but not controlled)
- **Impact**: MEDIUM - Important edge case

#### Rule 2-A: Second card on empty space fails and relinquishes first
- **Current**: No test for this scenario
- **Missing**: Test where:
  1. Player flips first card
  2. Another player removes that card's match
  3. Player tries to flip second card on now-empty space
  4. Should fail and relinquish control of first card
- **Impact**: HIGH - Critical failure case

#### Rule 2-B: Second card controlled by another player fails immediately
- **Current**: `preprocessWaitForCardAvailable` handles this but not fully tested
- **Missing**: Test where:
  1. Player1 flips first card
  2. Player2 flips same card (waiting)
  3. Player1 tries to flip second card on card controlled by Player2
  4. Should fail immediately (no wait) and relinquish first card
- **Impact**: HIGH - Critical deadlock prevention

#### Rule 2-B: Second card controlled by same player fails
- **Current**: No test for flipping second card on own first card
- **Missing**: Test where player tries to flip second card on their own first card
- **Impact**: MEDIUM - Edge case

#### Rule 2-C: Second card face down turns face up
- **Current**: Covered implicitly in matching/non-matching tests
- **Status**: ✅ Covered (implicitly)

#### Rule 3-A: Matching cards removed on next move
- **Current**: Test exists but doesn't verify removal happens on NEXT move
- **Missing**: Test that verifies:
  1. Player flips matching pair
  2. Cards remain face up
  3. Player flips a new first card
  4. Previous matching cards are removed
- **Impact**: HIGH - Core game mechanic

#### Rule 3-B: Non-matching cards turn face down on next move
- **Current**: Test exists but doesn't verify timing (happens on NEXT move)
- **Missing**: Test that verifies:
  1. Player flips non-matching pair
  2. Cards remain face up
  3. Player flips a new first card
  4. Previous non-matching cards turn face down (if not controlled)
- **Impact**: HIGH - Core game mechanic

#### Rule 3-B: Non-matching cards stay face up if controlled
- **Current**: No test for this scenario
- **Missing**: Test where:
  1. Player1 flips non-matching pair
  2. Player2 takes control of one of those cards
  3. Player1 flips new first card
  4. Only the uncontrolled card turns face down
- **Impact**: MEDIUM - Important edge case

#### Concurrent edge cases
- **Missing**: Test where multiple players contend for same card
- **Missing**: Test where player flips second card while another player is waiting for first card
- **Impact**: MEDIUM - Important for concurrency correctness

## Recommendations

### High Priority Tests to Add
1. **Rule 1-A**: Flip empty space after card removal
2. **Rule 2-A**: Second card on empty space fails and relinquishes first
3. **Rule 2-B**: Second card controlled by another player fails immediately
4. **Rule 3-A**: Matching cards removed on next move (not immediately)
5. **Rule 3-B**: Non-matching cards turn face down on next move (not immediately)

### Medium Priority Tests to Add
1. **Rule 1-C**: Flipping face-up card not controlled by anyone
2. **Rule 2-B**: Second card controlled by same player
3. **Rule 3-B**: Non-matching cards stay face up if controlled by another player
4. Concurrent contention scenarios

### Test Improvements Needed
1. Make existing matching pair test verify removal happens on NEXT move
2. Make existing non-matching pair test verify cards turn face down on NEXT move
3. Add more detailed assertions to verify control relinquishment

