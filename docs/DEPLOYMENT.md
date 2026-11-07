# Deployment and post-deployment check

**The online app does not contain this work until you merge and reboot.** On 2026-11-07, `main` and the fork's `main` were identical (`6e240a3`), both before PR #38.

## Configuration checked

| Item | State |
|---|---|
| Entry point | `causal_lab/app.py` |
| Dependencies | `causal_lab/requirements.txt`. PR #38 adds no dependency |
| Python | 3.11 (Advanced settings on Community Cloud); CI runs 3.11, with latest and minimum versions |
| Theme and options | Root `.streamlit/config.toml`, kept in step by `tests/test_streamlit_config.py` |
| Deployed from | The fork `thierryzbarhame/...`, branch `main`, so the fork must be synchronised after the merge |
| Stored study | `causal_lab/data/demo_study/results.json` is in the repository, about the same size as before |
| New files at run time | None outside the repository; `docs/` and `spike/` are not read by the app |

**Possible deployment problems.**
- The app sleeps on the free tier and takes about a minute to wake.
- A session open before the reboot can hold an old design object without the two new fields. Reload the page after rebooting.
- A project saved before this version opens with both new fields at their defaults, so its form counts as unconfirmed until an answer is changed or confirmed. That is intended.

## Steps

1. You authorise the merge of PR #38, or merge it yourself.
2. Synchronise the fork: `gh repo sync thierryzbarhame/CAUSAL-LAB-A-Virtual-Laboratory-for-Causal-Research`.
3. Open share.streamlit.io.
4. Open the application's menu.
5. Click **Reboot app**.
6. Wait about a minute, then reload the app's page.

## Checks after the reboot

Tick each one yourself; nothing here has been verified online.

**Research Question**
- [ ] "Is smoking a cause of lung cancer?": "What the question asks" says a causal effect; treatment and outcome are "stated".
- [ ] "Is smoking associated with lung cancer?": unclear; both words "to confirm"; a box "My aim is to estimate a causal effect" appears.
- [ ] "Can we predict dropout using grades?": a prediction.
- [ ] "How many students drop out each year?": a description.
- [ ] "Does Medicare eligibility at age 65 change health care use?": threshold inferred; the button "Use what the question implies in the form" appears.
- [ ] "Does a BMI over 30 raise mortality?": a question about what the value does; no threshold inferred.
- [ ] Switch to FR. "Les subventions réduisent-elles la pauvreté ?": un effet causal.

**Method Recommendation**
- [ ] Run the diagnosis with a question and an untouched form: no method, and a message about default answers.
- [ ] Press "Use what the question implies" on the Medicare question and run: Regression Discontinuity, with internal and external validity shown.
- [ ] No "/100", no score chart, no "Confidence" line.
- [ ] "Why the competing methods are less appropriate" is shown.

**Other modules: one example each**
- [ ] Guided Demo: the table loads; a re-run of 20 worlds says "identical".
- [ ] Virtual Lab: generate a world.
- [ ] Estimation: DiD, event study and staggered tabs show results.
- [ ] Break My Design: verdicts, then "What these checks say together", with no score.
- [ ] Robustness: the table appears.
- [ ] Causal Methods: run RCT and one other method; open the Break My Design tab.
- [ ] Theoretical Model: solve one catalogue model.
- [ ] Code Generator and Report: generate each; the report has no "/ 100".
- [ ] Settings: save a project and open it.

If anything fails, the previous version is still at the merge commit's parent. Note the error and do not reboot repeatedly.
