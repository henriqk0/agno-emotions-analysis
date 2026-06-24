---
name: irony-and-sarcasm
description: >
  Helps detect sarcasm, irony, and satirical tone in YouTube comments, since
  these are often misclassified by sentiment/emotion analysis models.
---

# Irony & Sarcasm Detection

## Overview

YouTube comments frequently use sarcasm and irony, which invert the literal
meaning of words. A comment like "great job, YouTube" can be genuine praise
or heavy sarcasm depending on context.

## Detection Heuristics

### Lexical markers

- **Punctuation exaggeration**: repeated `!` or `?` — e.g. "wow amazing !!!!"
- **All-caps on mundane words**: "BEST video EVER" about a low-effort clip
- **Qualifier + compliment**: "honestly this is the best thing I've ever seen"
  when the video is clearly low-quality
- **Canned phrases**: "thanks, I hate it", "well this is fine", "what a
  surprise", "shocked pikachu face"

### Contextual signals

- **Contrast with video quality**: if the video has many dislikes or negative
  replies but a comment is effusively positive, likely sarcastic
- **Reply threading**: a comment replying to another with opposite intent is
  often ironic
- **Absurdity/hyperbole**: "this cured my blindness" about a normal video

### Tone analysis

- **Deadpan delivery**: short, matter-of-fact statements praising something
  obviously bad — e.g. "this is fine" during a chaotic moment
- **Mock agreement**: "yes, absolutely, 100% correct" when replying to a
  clearly wrong take

## Emotion Re-mapping

When sarcasm or irony is detected, re-map the surface emotion:
| Surface emotion | Likely intended emotion |
|-----------------|------------------------|
| happiness | frustration / annoyance |
| praise | criticism / mockery |
| excitement | disbelief / shock |
| agreement | disagreement / ridicule |

## Examples

```
Comment: "Another masterpiece from this channel, as always."
Context:  video about a failed DIY project
Signal:   contrast between praise and obvious failure
Analysis: sarcastic — intended emotion is mockery
```

```
Comment: "wow so informative 🙄"
Context:  video title "Top 10 Facts You Already Know"
Signal:   eye-roll emoji + "so informative" about obvious info
Analysis: ironic — intended emotion is annoyance
```

```
Comment: "this is exactly what I needed to see today"
Context:  video about a depressing news event
Signal:   positive framing of negative content
Analysis: dark irony — intended emotion is resignation/sadness
```

## Usage

Apply these heuristics after fetching comments but before passing them to
sentiment/emotion analysis. Flag sarcastic/ironic comments and provide both
the surface and the corrected intended emotion in the analysis output.
