# Review of the 30-second film

Rendered 2026-11-13 with HyperFrames 0.9.41: `docs/video/causal-lab-30s.mp4`, 1920x1080, 30 fps, 30.0 s, H.264, no sound.

## Creative calls

- **One film, three beats.** The three beats are the three clauses of the page's headline (Session 8, slide 15: "three beats, one for each part of your sentence"). The film opens on a title card and ends on a card with the address. The page's visual world is kept: flat coloured fields with a lettered label on each, and the ink field for the main result.
- **Proof from the live app.** The screens in beats 1 and 2 were captured from the live app on 13 November 2026, at 1.8x zoom, and cropped to the part that proves the line. Beat 3 rebuilds the stored study's numbers as bars drawn to scale (−0.50, −0.264, 858 of 1,000, 31.6% / 68.4%).
- **Storylines not built:** a cursor-driven walkthrough of the app; and a film that opens on the DiD failure.

## Measured and looked at

- **Measured.** `hyperframes check`: 0 errors. Contrast: every text check passes WCAG AA. ffprobe: duration and codec.
- **Looked at.** The review sheets (`snapshot --review`: beats, seams, the phone sheet), and frames at 9 s and 16.5 s after the fix.
- **Not checked by anyone:** how the film plays on a phone in a real browser.

## Fixed in this pass

- `t=7–10 s` and `t=15–18 s` · screenshots · they floated small and their text was about 8 px → the live app, recaptured at 1.8x zoom and cropped. Text is now about 28 px, the screenshot sits beside the portrait, and in beat 2 it enters with the bars at 12.7 s, not 15 s.

## Warnings kept on purpose

- `film_silent`: slide 15 says no sound is needed, and the film is made to play muted on the page.
- `line_unread` on the last card: the address is long but is the real one. It also stays on the page under the film.
- Structure warnings (one file, no sub-compositions): the film is short and was kept in one file so it is easier to read.

## Weakest shot

The title card (0–3.5 s) only names the product. With more time, it would show the question being typed into the real app.
