# User test: two people, their own questions

Purpose: see how the question analysis behaves on questions the developer did not write, and whether people understand its answers.

## For the person running the test

1. Find two people who do empirical research or study statistics. They should not have seen the app's patterns or `docs/evaluation/`.
2. Give each of them the link and the instructions below. Nothing else: no example question, no explanation of what the app expects.
3. Watch without helping. If they ask what to type, say: "A research question you actually care about." If they ask whether an answer is right, say: "What do you think?"
4. Keep every question and every form, even the ones that look bad.
5. Before they start, confirm that the online app has been rebooted and shows "What the question asks" under the research question.

**About the evaluation sets.** Their questions are new material. They must not be added to the frozen `question_set.json`. Keep them for a later, separate evaluation set, and do not change the analyser because of them until you have decided whether they will be used as such. A question that was used to fix the analyser can no longer test it.

## Instructions for the tester (about 20 minutes)

Open https://causal-lab-a-virtual-laboratory-for-causal-research-busavtyebb.streamlit.app (it may take a minute to wake up).

1. Open **Research Question**.
2. Write a research question of your own, as you would in a proposal.
3. Read the analysis that appears under it.
4. Fill in the rest of the form as your study would, and run the diagnosis.
5. Open **Recommendation** and read it.
6. Fill in one copy of the form below.
7. Repeat with two more questions, of different kinds if you can.

## Feedback form (one per question)

| Item | Your answer |
|---|---|
| Research question (copy it exactly) | |
| What the app says the question asks (causal, prediction, description, unclear) | |
| Treatment and outcome it found, with their labels | |
| Recommended method, or "none, it asked" | |
| Was the interpretation reasonable? (yes / partly / no, and why) | |
| Was the method recommendation appropriate? (yes / partly / no / no recommendation, and why) | |
| Did it ask for clarification when it should have? (yes / no / asked too much) | |
| What was confusing? | |
| Suggestions for improvement | |

Tester (initials or anonymous), field of study, date:
