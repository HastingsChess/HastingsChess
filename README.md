# Hastings Chess

**Catastrophic Military Stupidity Simulator**

**Also Axes**

A deliberately asymmetric chess variant about the Battle of Hastings, battlefield discipline, and the consequences of everybody suddenly making a very bad decision at once.

Hastings Chess begins much like ordinary chess. The Saxons have a small early advantage in the form of two Housecarls. The Normans have a conventional army.

Then, sometime between Saxon moves 20 and 30, the Saxon infantry will become tremendously overconfident and charge down the board.

At that point the game becomes considerably less conventional.

The charge throws the Saxon position forward, breaks up the existing structure and is immediately followed by a special Norman counterattack. The result is a chess variant built around the central tactical idea of Hastings: the Saxons are dangerous while organised, considerably less comfortable once they stop being organised, and the Normans are very interested in the moment when that happens.

It is intentionally asymmetric.

It is also, despite appearances, an actual game.

---

## The basic idea

White plays the Saxons.

Black plays the Normans.

Most ordinary chess rules remain unchanged. Pieces move normally, check and checkmate work normally, castling remains castling, and a king is still sufficiently important that you are discouraged from allowing somebody to kill it.

Hastings Chess adds three major ideas:

1. Housecarls give the Saxons unusual close-range strength.
2. A compulsory Saxon infantry charge occurs once during the middle game.
3. The Normans receive an immediate counterattack consisting of a normal move followed by two special bonus actions.

The entire game is built around preparing for, surviving, exploiting or regretting that sequence.

---

## 1. Starting position

The board begins from the normal chess starting position with one change.

The Saxon pawns on a2 and h2 are replaced by Housecarls.

Everything else begins normally.

The Saxons move first.

---

## 2. Housecarls

A Housecarl is represented by a slightly rubbish picture of an axe. It is notated as an H.

Housecarls move and capture one square in any direction, exactly like a king.

They are not kings.

This distinction is important.

A Housecarl may therefore move onto a square attacked by an enemy piece. Losing a Housecarl is unfortunate but constitutionally acceptable.

Housecarls cannot castle, are not royal pieces and do not create any special check condition.

In practical terms they are compact, flexible close-combat pieces which are particularly unpleasant around crowded positions.

They also participate in the Saxon charge.

---

## 3. The Saxon charge

The charge happens once per game.

Beginning before the Saxons' 20th move, the game checks whether the charge occurs.

The probability rises as follows:

| Saxon move | Chance of charge |
|---:|---:|
| 20 | 1% |
| 21 | 3% |
| 22 | 5% |
| 23 | 7% |
| 24 | 9% |
| 25 | 10% |
| 26 | 15% |
| 27 | 25% |
| 28 | 40% |
| 29 | 60% |
| 30 | 100% |

If the charge does not occur, the Saxons play their normal move.

If it does occur, normal plans are temporarily suspended in favour of history.

### What charges?

Every surviving original Saxon pawn charges three squares directly forward.

Every surviving original Housecarl charges two squares directly forward.

The charge replaces the Saxons' ordinary move for that turn.

It is compulsory.

There is no button marked Perhaps this is strategically unwise.

---

### Congestion during the charge

Armies are less considerate about occupying one another's squares than chess pieces usually are.

The charge therefore has its own collision rules.

Where possible, a charging unit meeting another piece can push that piece one square forward if the destination is available.

This may involve friendly or enemy pieces.

If a blocking enemy cannot be pushed and is directly in the path of the charge, the charge rules allow it to be captured straight ahead.

The game resolves the charge automatically in the correct order.

Kings cannot be pushed or captured by the charge.

The purpose of these rules is not to reproduce a traffic-management system. It is to make the entire Saxon line move forward whether the position was sensibly arranged for this event or not.

---

### Promotion during the charge

An original Saxon pawn which reaches the eighth rank as part of the compulsory charge becomes a Housecarl.

Outside the compulsory charge, ordinary pawn promotion applies and the usual choices of queen, rook, bishop or knight are available.

---

## 4. The Norman counterattack

Immediately after the compulsory Saxon charge, the Normans receive a special counterattack.

The Norman turn consists of:

one ordinary chess move

followed by:

two bonus actions

The ordinary move works exactly as a normal legal chess move.

The two bonus actions are restricted.

Each bonus action may be made by either:

- a Norman knight, or
- a Norman pawn.

The same eligible piece may make both bonus actions.

Yes, this means the same knight can potentially move three times.

This is intentional.

---

### Norman knight bonus actions

A knight used during a bonus action moves and captures exactly as a knight normally does.

It must remain legal with respect to Norman king safety.

---

### Norman pawn bonus actions

During a bonus action, a Norman pawn may:

- move one square forward into an empty square;
- capture normally on a forward diagonal;
- capture an enemy piece directly in front of it.

That final possibility is special to the Norman counterattack.

Bonus-action pawns may not:

- make an initial two-square advance;
- capture en passant;
- promote;
- enter the first rank.

All normal king-safety requirements still apply.

The bonus system is designed to represent exploitation of the disorder created by the Saxon charge rather than to provide Black with three completely unrestricted chess moves.

An earlier experimental version allowed every Norman piece to use bonus actions. That feature has been removed from the release rules because some ideas deserve to remain ideas.

---

## 5. Bonus-first rescue

There is one unusual edge case.

The compulsory charge can occasionally create a position in which the Norman king appears to have been checkmated before the Normans have had a conventional opportunity to respond.

Because the position was created by a compulsory multi-piece event rather than an ordinary chess move, Hastings Chess also checks whether one of the permitted Norman bonus actions can rescue the king.

If so, the Normans may use one bonus action before the ordinary move.

That action consumes one of the two available bonus actions.

The Norman sequence then becomes:

rescue bonus action → ordinary move → remaining bonus action

This is not an additional action.

It is simply a different ordering of the same three available actions when required to keep the position legally playable.

This rule exists because an actual test game found the problem before I did.

---

## 6. Everything else

Unless Hastings Chess explicitly changes a rule, ordinary chess rules apply.

That includes:

- check;
- checkmate;
- stalemate;
- castling;
- ordinary pawn movement and captures;
- ordinary promotion;
- en passant outside Norman bonus actions;
- king safety.

If you already know how to play chess, you therefore only need to learn the Housecarls, the charge and the Norman counterattack.

Unfortunately, those are quite important.

---

## 7. Ratings

Hastings Chess has a deliberately asymmetric local Elo system.

Both sides begin at:

1066

The Norman rating then changes normally after completed rated games.

The Saxon rating does not.

Ever.

A Saxon player may win repeatedly, play excellent chess and thoroughly outclass the opposition.

Their rating remains:

1066

The logic is straightforward: any rating system attempting to evaluate Saxon strategic competence must eventually account for the fact that the entire army is going to charge whether this is a good idea or not.

The Norman rating is therefore a rating.

The Saxon rating is really more of a doctrine.

---

## 8. Computer opponent

Hastings Chess uses a custom hybrid built around Fairy-Stockfish.

Fairy-Stockfish understands the ordinary chess position and the custom Housecarl piece. Hastings-specific Python logic handles the parts that ordinary chess engines were, perhaps understandably, never designed to encounter.

These include:

- the compulsory charge;
- collision and push logic;
- charge-specific captures;
- Norman bonus actions;
- compound Norman turns;
- bonus-first rescue;
- Hastings-specific legality.

The two systems are then combined for move selection and analysis.

Most importantly, the computer opponent knows the probability of an approaching Saxon charge.

Once the charge becomes possible, it can evaluate moves partly according to how well the resulting position is likely to survive or exploit the possibility that the Saxons will shortly do something incredibly unwise.

It does not know in advance whether the random charge check will succeed.

It simply knows the same probability the player does and plans accordingly.

This turned out to matter quite a lot.

---

## 9. Difficulty

The computer opponent has ten difficulty levels.

The release difficulty ladder is intended to range from deliberately fallible beginner play through to the strongest Hastings search available.

All ten levels understand the rules correctly.

Lower difficulty does not mean that the engine forgets what a Housecarl is, makes illegal bonus moves or fails to notice the compulsory charge. Instead, weaker levels receive weaker move selection and reduced tactical precision.

At the top end, the engine searches substantially more deeply through both conventional chess positions and Hastings-specific compound counterattacks.

There is also an internal benchmark configuration retained for development and balance testing so that future versions can be compared consistently with the existing test data. It is highly unlikely that I will make future versions, because this one works and I can’t be bothered. If, however, you would like to do so, then that is totally fine. Please credit me though, it’s just a nice thing to do isn’t it.

---

## 10. Replay analysis

Engine evaluations are not shown during live games.

You are expected to make your own mistakes.

After a game has finished, Replay mode can show a conventional White/Black evaluation bar and mate information.

This becomes particularly useful around the compulsory charge.

You can step through:

position before charge → charge → Norman ordinary response → bonus action one → bonus action two

and watch the evaluation explain precisely when everything went wrong. That tends to happen between turns 20 and 30.

Because some intermediate Hastings positions cannot exist in ordinary chess, replay analysis uses the same hybrid system as the computer opponent rather than blindly feeding impossible positions to Fairy-Stockfish.

---

## 11. Difficulty balance

Hastings Chess is deliberately asymmetric.

The Normans are intended to have an advantage, particularly when both sides play strongly. The Saxons begin with useful advantages of their own. First move, two Housecarls and considerable early attacking potential, but eventually have to contend with a compulsory breakdown in positional discipline.

At difficulty level 1 the win split is about 50/50. As you increase difficulty, the Normans become increasingly able to exploit the structural damage created by the compulsory charge.

This is not currently regarded as a defect.

William did, after all, win.

Unless you are Magnus, level 10 is better than you and you will die. If you are Magnus, then you should probably have better things to do.

---

## 12. Historical accuracy

Hastings Chess is inspired by the tactical shape and popular historical understanding of the Battle of Hastings.

It is not a battlefield simulator. It is still basically chess, and therefore abstract.

No claim is being made that Anglo-Saxon infantry historically moved exactly three squares, that Norman cavalry received two action points after a failed shield wall, or that Bishop Odo had a FIDE rating.

The central idea is simpler.

The Saxons begin in a strong position.

At some point they lose formation by advancing.

The Normans get an opportunity to exploit the resulting disorder.

The game is built around that relationship.

Everything else is chess, RNGs, and questionable judgement.

---

## 13. Installation

Release builds are intended to be portable.

### Windows

Extract the Windows release and run:

HastingsChess.exe

No separate Python or Fairy-Stockfish installation is required.

The portable Windows build has been run successfully on a normal Windows system.

### macOS

The macOS release is supplied as:

Hastings Chess.app

The Apple Silicon build contains its own required runtime and native Fairy-Stockfish engine.

At the time of writing, the macOS package has passed native automated build/launch checks but has not yet had the same personal-machine testing as the Windows release.

Unsigned or non-notarised development releases may require the usual macOS Gatekeeper approval.

---

## 14. Why does this exist?

Hastings Chess began as a joke.

Unfortunately, the joke continued to work.

The original idea was that a chess game based on Hastings should contain a point at which the Saxon position is forcibly ruined by an ill-advised infantry advance.

That led to the charge.

The charge required a Norman response.

The Norman response required special actions.

The special actions required a proper rules engine.

The rules engine required an opponent that understood the resulting game.

The opponent eventually became a Hastings-aware Fairy-Stockfish hybrid capable of changing its strategy according to the probability of imminent Saxon indiscipline.

At this point stopping would have been arbitrary.

---

## 15. Creator and development

Concept and game design: Nicholas Cooke

Development: Nicholas Cooke with ChatGPT

Chess engine: Fairy-Stockfish v14

Hastings Chess uses its own Python rules/controller layer around Fairy-Stockfish so that the engine can operate inside a game containing Housecarls, probabilistic compulsory charges and compound Norman counterattacks without requiring Fairy-Stockfish itself to become personally responsible for any of those decisions.

The project includes the relevant Fairy-Stockfish licence and source materials required for distribution.

Hastings Chess is intended to be free, open, playable and much more carefully engineered than the original idea deserved.

The original idea was conceived on the toilet. From there, things got a bit out of hand.

Please note that I am not a coder. I just had too much time on my hands and it was Wednesday. I am, however, other things, and if you’re really interested you can find those things at the link below, although please be aware that I am sometimes contractually obliged to take things seriously.

[Nicholas Cooke — writer and researcher](https://sites.google.com/view/nicholascookewriter)

Edit: also Thursday. I genuinely just looked at the cat and analysed whether she could take me like a knight. This was involuntary.
