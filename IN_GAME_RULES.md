# Hastings Chess

**Catastrophic Military Stupidity Simulator**  
**Also Axes**

White are the Saxons.  
Black are the Normans.

Ordinary chess rules apply except where stated below.

## Housecarls

The Saxons begin with Housecarls instead of the a2 and h2 pawns.

A Housecarl moves and captures one square in any direction, like a king.

It is not a king and may move onto attacked squares.

## The Saxon charge

Once per game, the Saxon infantry will compulsorily charge.

The charge is checked before each Saxon move from move 20 to move 30.

The odds increase with each move. By move 30, White is absolutely going to do something regrettable. This is not optional.

When the charge triggers, it replaces the Saxons' normal move.

Every surviving original Saxon pawn charges three squares forward.

Every surviving original Housecarl charges two squares forward.

Blocked charging pieces may push other pieces forward where space permits. If an enemy directly blocks the charge and cannot be pushed, the charge may capture it straight ahead.

Kings cannot be pushed or captured.

A Saxon pawn reaching the final rank during the charge becomes a Housecarl.

## The Norman counterattack

Immediately after the charge, the Normans receive:

**1 normal move + 2 bonus actions**

Each bonus action may be made by a knight or pawn.

The same piece may use both bonus actions.

Knights move normally.

During a bonus action, Norman pawns may:

- move one square forward;
- capture diagonally as normal;
- capture directly forward.

On each bonus action, a pawn may advance only one square. However, the same pawn may use both bonus actions, so it can advance one square and then another if both moves are legal. Bonus actions cannot use the normal two-square opening pawn move, en passant or promotion.

All moves must keep the Norman king safe.

In the rare case where the charge creates an apparent mate that can only be escaped using a bonus action, one bonus action may be used before the normal Norman move. It still counts as one of the two bonuses.

## Ratings

Both sides begin at **1066 Elo**.

The Norman rating changes normally.

The Saxon rating remains **1066 forever**.

This is because long-term performance modelling is difficult when your army is contractually required to abandon its formation halfway through the game.

## Computer opponent

There are **10 difficulty levels**, ranging from deliberately fallible play to maximum Hastings-aware Fairy-Stockfish search.

The computer understands the probability of the approaching charge and can prepare for it.

It does not know when the charge will actually happen.

## Replay

Engine evaluation and mate information are hidden during live play.

After the game, open Replay to see the evaluation and step through exactly where the position deteriorated.

This is often around the point when everybody runs downhill.

---

Created by **Nicholas Cooke**.

Developed with ChatGPT and powered by Fairy-Stockfish.

Hastings Chess began as a joke and subsequently received an unreasonable amount of engineering.

I am not a coder. I just had too much time on my hands and it was Wednesday.
