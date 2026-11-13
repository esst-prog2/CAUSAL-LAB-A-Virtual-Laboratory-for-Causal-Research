# Review of the 30-second film

Rendered 2026-11-13 with HyperFrames 0.9.41: `docs/video/causal-lab-30s.mp4`, 1920x1080, 30 fps, 30.0 s, H.264, no sound, 2.1 MB.

## Creative calls

- **One film, three beats.** The three beats are the three clauses of the page's headline (Session 8, slide 15: "three beats, one for each part of your sentence"). A title card opens the film and an end card with the address closes it.
- **The page's research style (version 3).** Navy title, beat 3 and end card; white and soft-grey beats; Source Sans 3 only. The question appears as the page's annotated input panel ("To confirm" and "Unclear" tags, a "No method yet" pill). The route to the method is four numbered steps, and the main result reuses the page's Figure 1 bars. This replaces the Du Bois look of versions 1 and 2 (PROCESS.md, row 16).
- **Proof from the live app.** The screens in beats 1 and 2 were captured from the live app on 13 November 2026, at 1.8x zoom, and cropped to the part that proves the line. Beat 3 rebuilds the stored study's numbers as bars drawn to scale (−0.50, −0.264, 858 of 1,000, 31.6% / 68.4%).
- **Storylines not built:** a cursor-driven walkthrough of the app, and a film that opens on the DiD failure.

## Measured and looked at

- **Measured.** `hyperframes check`: 0 errors. Contrast: 43 of 43 text checks pass WCAG AA. Layout: 0 issues. ffprobe: duration and codec.
- **Looked at.** The review sheets (`snapshot --review`: beats, seams and the phone sheet), and the poster frame at 9 s.
- **Not checked by anyone:** how the film plays on a phone in a real browser.

## Fixed in this pass

- `t=3.5–7 s` · panel labels · "You type" and the tags were 26 and 27 px, under the 28 px floor → 28 px.
- `t=22–24.5 s` · source line · on screen too briefly for its 10 words → shortened to "Source: docs/DEMO_DETAILS.md".

## Warnings kept on purpose

- `film_silent`: slide 15 says no sound is needed, and the film is made to play muted on the page.
- `dead_stretch` (7.6–10.9 s and 14.6–18.4 s): time to read the live-app screenshots, marked `data-hold`.
- `line_unread` on the end card: the address is long but it is the real one, and it also stays on the page under the film.
- Structure warnings (one file, no sub-compositions): the film is short and kept in one file so it is easier to read.

## Weakest shot

The opening frames of beats 1 and 2 show only the headline for about half a second before anything moves. With more time, the panel would build in with the headline.
