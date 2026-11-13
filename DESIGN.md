---
name: Causal Lab
description: Data portraits for a careful causal-methods tool; flat labelled fields on a white board, one ink field for the main result.
colors:
  ink: "#1B2333"
  ink-soft: "#3A4357"
  board: "#FFFFFF"
  du-bois-blue: "#3451B2"
  unclear-gold: "#F2B705"
  to-confirm-pink: "#F6C8D2"
  failure-crimson: "#D7263D"
  truth-green: "#2E9E83"
  threshold-magenta: "#C2416B"
  on-ink-muted: "#D7DCE6"
  on-ink-link: "#B9C6FF"
  hairline: "#C9CFDA"
  ink-pressed: "#0E131D"
typography:
  display:
    fontFamily: "Big Shoulders Display, Source Sans 3, sans-serif"
    fontSize: "clamp(2.4rem, 5.6vw, 6rem)"
    fontWeight: 800
    lineHeight: 0.95
    letterSpacing: "0.01em"
  headline:
    fontFamily: "Big Shoulders Display, Source Sans 3, sans-serif"
    fontSize: "clamp(2.2rem, 5.2vw, 4.4rem)"
    fontWeight: 800
    lineHeight: 0.95
    letterSpacing: "0.01em"
  title:
    fontFamily: "Big Shoulders Display, Source Sans 3, sans-serif"
    fontSize: "clamp(1.6rem, 2.6vw, 2.6rem)"
    fontWeight: 800
    lineHeight: 0.95
    letterSpacing: "0.01em"
  statement:
    fontFamily: "Big Shoulders Display, Source Sans 3, sans-serif"
    fontSize: "clamp(1.6rem, 2.8vw, 2.4rem)"
    fontWeight: 800
    lineHeight: 1.12
  label:
    fontFamily: "Big Shoulders Display, Source Sans 3, sans-serif"
    fontSize: "clamp(0.85rem, 1.25vw, 1.05rem)"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0.08em"
  body:
    fontFamily: "Source Sans 3, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "tnum"
  lede:
    fontFamily: "Source Sans 3, sans-serif"
    fontSize: "1.2rem"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "tnum"
  caption:
    fontFamily: "Source Sans 3, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "tnum"
rounded:
  none: "0px"
  node: "50%"
spacing:
  rule: "3px"
  rule-thin: "2px"
  gutter: "clamp(1.25rem, 4vw, 4rem)"
  line-x: "clamp(0.9rem, 2.2vw, 2.4rem)"
  beat-block: "clamp(3rem, 8vh, 5.5rem)"
  pair-gap: "3rem"
  stack: "2rem"
components:
  button-primary:
    backgroundColor: "{colors.du-bois-blue}"
    textColor: "{colors.board}"
    rounded: "{rounded.none}"
    padding: "0.85rem 1.6rem 0.75rem"
  button-primary-hover:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.board}"
  button-primary-active:
    backgroundColor: "{colors.ink-pressed}"
    textColor: "{colors.board}"
  field-to-confirm:
    backgroundColor: "{colors.to-confirm-pink}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "0.06em 0.14em 0.02em"
  field-unclear:
    backgroundColor: "{colors.unclear-gold}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "0.06em 0.14em 0.02em"
  route-bar-confirmed:
    backgroundColor: "{colors.du-bois-blue}"
    textColor: "{colors.board}"
    rounded: "{rounded.none}"
    padding: "0.55rem 0.75rem 0.45rem"
  route-bar-threshold:
    backgroundColor: "{colors.threshold-magenta}"
    textColor: "{colors.board}"
    rounded: "{rounded.none}"
    padding: "0.55rem 0.75rem 0.45rem"
  route-bar-method:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.board}"
    rounded: "{rounded.none}"
    padding: "0.55rem 0.75rem 0.45rem"
  chart-bar-truth:
    backgroundColor: "{colors.truth-green}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    height: "2.6rem"
    padding: "0 0.7rem"
  chart-bar-failure:
    backgroundColor: "{colors.failure-crimson}"
    textColor: "{colors.board}"
    rounded: "{rounded.none}"
    height: "2.6rem"
    padding: "0 0.7rem"
  chart-bar-neutral:
    backgroundColor: "{colors.board}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    height: "2.6rem"
    padding: "0 0.7rem"
  ink-field:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.board}"
    rounded: "{rounded.none}"
  screenshot-frame:
    backgroundColor: "{colors.board}"
    rounded: "{rounded.none}"
  beat-node:
    backgroundColor: "{colors.ink}"
    rounded: "{rounded.node}"
    size: "1.2rem"
---

> **Superseded for the page on 2026-11-13** (PROCESS.md, row 15): `docs/index.html` now uses the app's research style (navy, blue, Source Sans 3; tokens at the top of its stylesheet, taken from `.streamlit/config.toml` and `causal_lab/ui/style.py`). This file still describes the Du Bois look kept by the film (`video/`) and the slides (`docs/slides/`).


# Design System: Causal Lab

Scope: this visual system governs the promo page and the future slides published from `docs/` (GitHub Pages). The Streamlit app keeps its own theme in `causal_lab/.streamlit/config.toml` and `causal_lab/ui/style.py`. The page shares the app's semantic colours (#3451B2 primary, #2E9E83 true effect, #C2416B thresholds) and nothing else here is imposed on the app.

## Overview

**Creative North Star: "The Data Portrait"**

Every surface is a plate in the manner of W. E. B. Du Bois's data portraits for the 1900 Paris Exposition: flat fields of gouache colour on a white board, each field carrying a lettered caps label, read before any number is. A research question, a method choice and a failing estimator are each drawn once, as shapes a stranger can read without the prose. Du Bois is credited on every surface that uses the language.

Density is low and monumental. Type is condensed, heavy and uppercase for everything that names something; running text is a plain humanist sans with tabular figures, because numbers are the evidence. Depth does not exist: colour, the 3px ink rule and one inverted ink field do all the structural work. Motion is a single, once-only settling of words onto their fields; with reduced motion the plate is simply static.

The palette is semantic, not decorative. A colour field means one thing everywhere, and a key on the surface says what. Failure has its own colour and nothing else may borrow it.

**Key Characteristics:**
- White board, ink type, one ink field per surface for the main result.
- Flat, square-cornered colour fields, each with one meaning and a lettered label.
- Condensed lettered caps (Big Shoulders Display 800) for every heading, label and value on a field; Source Sans 3 for prose.
- One vertical 3px ink line runs through the narrative beats, with a round node at each beat.
- Bars are drawn to scale; screenshots sit in 3px ink frames with captions naming their source.
- No shadows, no gradients, no rounded rectangles.

## Colors

A Du Bois gouache set on white: saturated, flat, and every hue bound to one meaning.

### Primary
- **Du Bois Blue** (#3451B2): the action and what is confirmed. The Try-it plate, links, the focus ring, confirmed steps on a route. Shared with the app as its primary.

### Secondary
- **Truth Green** (#2E9E83): the true effect and intervals that cover it. Carries ink text, never white. Shared with the app.
- **Threshold Magenta** (#C2416B): cutoffs, thresholds and dates. Carries white text. Shared with the app.

### Tertiary
- **Failure Crimson** (#D7263D): what fails, and nothing else: a biased estimate, intervals that miss, a failing metric in a table.
- **Unclear Gold** (#F2B705): a reading the tool is not sure of. Also the text-selection colour.
- **To-Confirm Pink** (#F6C8D2): a term the user must confirm.

### Neutral
- **Ink** (#1B2333): all type on the board, every rule and frame, the method bar, and the one inverted ink field.
- **Soft Ink** (#3A4357): secondary text on the board: author line, captions, route annotations.
- **Board** (#FFFFFF): the ground; also type and rules inside the ink field.
- **Pressed Ink** (#0E131D): the primary plate's active state only.
- **Muted On-Ink** (#D7DCE6): captions, chart titles and notes inside the ink field.
- **On-Ink Link** (#B9C6FF): links inside the ink field, where Du Bois Blue would fail contrast.
- **Hairline** (#C9CFDA): 1px row separators in data tables.

### Named Rules
**The One Meaning Rule.** Each field colour means one thing on every surface: blue confirmed or act, gold unclear, pink to confirm, magenta a cutoff, green the truth, crimson failure. Crimson is never decoration, never a call to action, never a brand accent.

**The Keyed Palette Rule.** A surface that uses the field colours shows a key (a row of swatches, each with its lettered meaning) before the reader needs it.

**The Shared-Semantics Rule.** Blue, green and magenta are the app's own; keep their values and meanings identical to the app's so a screenshot and the plate around it agree.

## Typography

**Display Font:** Big Shoulders Display (with Source Sans 3, sans-serif), self-hosted woff2, SIL OFL
**Body Font:** Source Sans 3 (with sans-serif), roman and italic, self-hosted woff2, SIL OFL

**Character:** Condensed poster caps against a plain, legible text face: the lettering names and labels, the sans explains and counts. All text sets tabular figures.

### Hierarchy
- **Display** (800, clamp(2.4rem, 5.6vw, 6rem), 0.95, uppercase): the one portrait per surface, words sitting on their colour fields.
- **Headline** (800, clamp(2.2rem, 5.2vw, 4.4rem), 0.95, uppercase, max 18ch): beat headings.
- **Title** (800, clamp(1.6rem, 2.6vw, 2.6rem), 0.95, uppercase, max 52ch): the one-sentence promise and the verdict line.
- **Statement** (800, clamp(1.6rem, 2.8vw, 2.4rem), 1.12, sentence case, max 30ch): a single plain-spoken claim in the display face, for limits and disclaimers.
- **Body** (400, 1.125rem, 1.55): prose, 62 to 70ch.
- **Lede** (400, 1.2rem, 1.55, max 62ch): the opening paragraph of a beat; quoted questions in italic.
- **Label** (800, clamp(0.85rem, 1.25vw, 1.05rem), 0.08em, uppercase): tags under fields, key entries; larger label sizes (1.05 to 1.6rem, 0.02 to 0.06em) for chart titles, row keys, bar text and the Try-it plate.
- **Caption** (400, 0.95rem, Soft Ink or Muted On-Ink): figure captions, route annotations, chart notes.

### Named Rules
**The Lettered Caps Rule.** Every heading, label, field value and control is set in Big Shoulders Display 800 uppercase with balanced wrapping; prose is never set in it, and labels are never set in the body face.

**The Counted Figures Rule.** Numbers are set with tabular figures everywhere, and every number shown links to, or names, its source.

## Layout

Full-bleed bands with a fluid side gutter (clamp(1.25rem, 4vw, 4rem)). A thin top line (name, author, links) sits over a 3px ink rule. The first viewport holds the promise, the portrait and the primary plate together. A full-width key band, ruled 2px above and below, follows the portrait.

Narrative beats run down a single column. A 3px ink line sits at clamp(0.9rem, 2.2vw, 2.4rem) from the left edge, through every beat; beat content is indented past it by one gutter, and each beat opens with a round node on the line. Beats have clamp(3rem, 8vh, 5.5rem) of vertical padding. Text and its screenshot pair in one column below 64rem and in a 5:7 grid with a 3rem gap above it. Evidence lists switch to a 16rem label column at 56rem; chart rows stack their key over the bar below 40rem. Tables scroll horizontally inside their own wrapper rather than reflowing.

### Named Rules
**The One Ruled Line Rule.** One vertical ink line runs through all the beats of a surface; inside the ink field it turns white, and nothing else draws a competing vertical.

**The To-Scale Rule.** Bar lengths are proportional to the values they show, with the value lettered on the bar, and a note says so.

## Elevation & Depth

None. The system is flat: no shadows, no gradients, no blur. Hierarchy comes from scale, from 3px and 2px ink rules, and from inversion: the main result sits on a full-width ink field where type, rules, frames and the line turn white.

### Named Rules
**The Flat Gouache Rule.** Surfaces never lift. If something needs emphasis, give it a field colour with its meaning, a heavier rule, or the ink field, not a shadow.

**The Single Ink Field Rule.** One ink field per surface, reserved for the main result.

## Shapes

Square corners everywhere (0px): plates, fields, bars, frames, swatches. The single round form is the beat node, a 1.2rem disc on the ruled line with a 3px ring in the ground colour. Borders are solid ink at 3px (frames, the top line, the ruled line, the footer) or 2px (key band, tag top rules, list dividers, caption separators, table heads), with 1px Hairline only between table rows.

## Components

### Buttons
Character: one poster plate, the only filled control on a surface.
- **Shape:** square (0px).
- **Primary (Try it):** Du Bois Blue plate, white lettered caps at 1.6rem, 0.04em tracking, padding 0.85rem 1.6rem 0.75rem, no underline.
- **Hover / Focus:** background turns Ink over 160ms cubic-bezier(0.16, 1, 0.3, 1); active turns Pressed Ink. Focus is the global 3px Du Bois Blue outline at 3px offset.
- **Secondary:** none. Every other action is a text link.

### Links
- Du Bois Blue with a 2px underline at 0.2em offset; hover turns Ink. Inside the ink field: On-Ink Link, hover white.

### Navigation
- The top line: the name in lettered caps (1.6rem) at left, the author line in Soft Ink, two or three links in 600-weight body text at right, wrapping on narrow screens. Rule below at 3px.

### Portrait fields (signature)
- Words in Display type, each term laid on a flat colour field (pink to confirm, gold unclear) with tight padding (0.06em 0.14em 0.02em).
- Every field carries a lettered tag below it, over a 2px ink rule spanning the word.
- Motion: fields wipe in from the left (900ms) and tags settle (700ms, from 0.4rem above and 35% opacity), staggered 180ms, cubic-bezier(0.16, 1, 0.3, 1), once on load; static under reduced motion.
- A visually hidden sentence gives the full reading for assistive tech; the drawn portrait is hidden from it.

### Key
- A band of swatches (1.6rem by 1rem flat rectangles), each followed by its meaning in body text, headed by a lettered "Key" label. Ruled 2px top and bottom.

### Route bars
- A stepped list of lettered bars that lengthen toward the conclusion (55%, 70%, 85%, 100%), coloured by meaning (blue confirmed, magenta cutoff, ink for the method reached), each with a Soft Ink annotation below quoting its source.

### Charts
- Horizontal bars 2.6rem tall on the ink field, a lettered row key at left (9 to 15rem column), value lettered on the bar. Truth in green with ink text, failure in crimson with white text, neutral counts in white with ink text; a split bar shows covers/misses. A lettered chart title in Muted On-Ink above and a caption-size note below naming the source.

### Screenshot frames
- A 3px ink frame (white on the ink field), the image linked to its full size, and a caption below a 2px rule naming where the screenshot comes from.

### Evidence list and tables
- Items divided by 2px ink rules; a lettered 1.5rem label column beside the body. Tables: left-aligned, no wrap, 2px ink rule under the head, 1px Hairline between rows; failing values in bold Failure Crimson with the word "fails" beside them, so colour is never the only signal.

## Do's and Don'ts

### Do:
- **Do** give every coloured field a lettered label and keep its one meaning (The One Meaning Rule).
- **Do** show a key whenever field colours appear.
- **Do** keep the Try-it plate in Du Bois Blue (#3451B2) as the only filled control.
- **Do** draw bars to scale and letter the value on the bar.
- **Do** set every heading and label in Big Shoulders Display 800 uppercase, prose in Source Sans 3 with tabular figures.
- **Do** put the main result on the single ink field, with white rules, frames and line.
- **Do** caption every screenshot with its source and link every number to its source.
- **Do** credit W. E. B. Du Bois on any surface that uses this visual language.
- **Do** keep AA contrast: ink text on gold, pink and green; white text on blue, magenta, crimson and ink; On-Ink Link for links on ink.

### Don't:
- **Don't** use Failure Crimson (#D7263D) for anything but failure, including buttons, highlights or brand accents.
- **Don't** add shadows, gradients, blur or rounded rectangles; the beat node is the only circle.
- **Don't** add a second filled button style.
- **Don't** introduce colours outside this palette, or reuse the app's shared colours with a different meaning.
- **Don't** let colour be the only signal of failure; pair it with a word.
- **Don't** animate more than the once-only portrait settle, and never without a reduced-motion static state.
