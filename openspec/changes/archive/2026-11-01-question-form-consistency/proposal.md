## Why

On 2026-11-01 the user asked for the Method Recommendation to be "credible and correct for every type of question". Two weaknesses remained:
- The cutoff fix covered one contradiction between the question and the form. The others went undetected: a lottery, an instrument, a nationwide change, a predictive question, a staggered rollout. In each case the engine still answered from the form alone.
- Nothing showed that the engine gives the published design for well-known studies.

## What Changes

- **Question signals.** The diagnosis reads the design features the question describes, in English and in French: cutoff, randomisation or lottery, instrument, staggered rollout, a single unit or a nationwide change, border, prediction or association, heterogeneity, mechanism, dose, effects over time. The patterns are narrow on purpose:
  - "eligibility" alone is not a cutoff;
  - "natural experiment" is not a randomisation;
  - "National" in a programme's name is not a nationwide change.
- **The question checked against the form.** When the question contradicts the form, no method is recommended. The method the question points to is listed as needing information, with the exact question to answer.

  | The question… | The form says… | The method concerned asks… | Other methods |
  |---|---|---|---|
  | names a cutoff | no cutoff | RDD: does the cutoff decide treatment? | held back |
  | names a lottery or a randomisation | not random, and no instrument declared | RCT: was treatment assigned at random? | held back; IV still possible |
  | names an instrument | no instrument | IV: declare the instrument | not held back |
  | names a single unit or a nationwide change | many treated units | — | all held back |
  | asks for a prediction or an association, with no causal wording | — | — | all held back; the researcher is asked to name a treatment and an outcome |
- **Geographic RDD.** A geographic assignment whose question names a border supports a regression discontinuity in the distance to the border (Keele & Titiunik 2015; Dell 2010).
- **Caveats from the wording.** These are added to the rationale without blocking the recommendation:
  - a staggered rollout described in the question while the timing is set to a single date;
  - effects over time, which point to the event study;
  - a dose of treatment while the treatment is binary;
  - heterogeneity (conditional effects, causal forests; Wager & Athey 2018);
  - mechanisms (mediation needs sequential ignorability; Imai, Keele & Tingley 2010).
- **Recommendation page.** It shows the answers the recommendation rests on, and warns when every design answer is still at its default.
- **Benchmark of 23 cases.** Each published study must get the design its authors used. The cases also cover French wording, plus five questions where the engine must ask instead of answering. The studies are:
  - LaLonde; Miguel & Kremer; the Oregon lottery;
  - Thistlethwaite & Campbell; Lee; Angrist & Lavy; Dell;
  - Card & Krueger; Duflo; Miller, Johnson & Wherry;
  - Abadie, Diamond & Hainmueller; Abadie & Gardeazabal;
  - Barone-Adesi et al.;
  - Angrist & Krueger; Angrist; Card;
  - Dehejia & Wahba.

## Capabilities

### Modified Capabilities
- `method-recommendation`: question signals; question-versus-form rules; geographic RDD; caveats; the answers the recommendation rests on.

## Impact

- **Code:** `causal_engine/diagnosis.py`, `causal_engine/recommendation.py`, `app.py`, and the EN and FR texts.
- **Tests:** `tests/test_recommendation_benchmark.py` (new) and an app test for a question that contradicts the form.
