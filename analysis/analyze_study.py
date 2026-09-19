"""
Analysis for the Real or AI? study (app: https://aidemos.streamlit.app)

    python analyze_study.py [responses.csv] [detector_results.json]

Writes figures, tables and report_numbers.txt to report_outputs/.
"""

import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from scipy import stats

# settings
BASE = Path(__file__).resolve().parent
def _first_existing(*paths):
    for p in paths:
        if Path(p).exists():
            return str(p)
    return str(paths[0])

# use the anonymised file if it is there
CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else _first_existing(
    BASE / "data" / "responses_anonymized.csv", BASE / "responses_rows.csv")
DETECTOR_PATH = sys.argv[2] if len(sys.argv) > 2 else _first_existing(
    BASE / "data" / "detector_results.json", BASE / "detector_results.json")
OUT = BASE / "report_outputs"

# nicknames to leave out of the main analysis (empty = everyone)
EXCLUDE_NAMES = []

# median response time (s) below this = fast responder
# they stay in the main analysis, a sensitivity check without them is reported
RAPID_MEDIAN_RT = 8.0

N_BOOT = 5000
SEED = 42
rng = np.random.default_rng(SEED)

# style
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "Times", "DejaVu Serif"],
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})
C_OK, C_BAD, C_UNS = "#2E7D5B", "#C0504D", "#B8B8B8"
C_AUTH, C_AI, C_EDIT, C_PAIR = "#2E7D5B", "#8E44AD", "#E08E2B", "#3B6EA8"
CAT_COLORS = {
    "Authentic video": C_AUTH,
    "AI-generated video": C_AI,
    "Edited (non-AI) video": C_EDIT,
    "Video pair": C_PAIR,
    "Image pair": "#6FA3D6",
}

(OUT / "figures").mkdir(parents=True, exist_ok=True)
(OUT / "tables").mkdir(parents=True, exist_ok=True)
report_lines = []

def say(text=""):
    print(text)
    report_lines.append(text)

def savefig(fig, name):
    fig.savefig(OUT / "figures" / f"{name}.png")
    plt.close(fig)

# helpers
def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return (c - h, c + h)

def cluster_boot_ci(values_by_pid, stat=np.mean, n_boot=N_BOOT):
    """bootstrap CI, resampling participants"""
    arr = np.asarray(values_by_pid, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0:
        return (np.nan, np.nan)
    boots = [stat(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_boot)]
    return tuple(np.percentile(boots, [2.5, 97.5]))

def holm(pvals):
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    running = 0
    for rank, idx in enumerate(order):
        val = (m - rank) * p[idx]
        running = max(running, val)
        adj[idx] = min(1, running)
    return adj

def fmt_p(p):
    return "p < .001" if p < 0.001 else f"p = {p:.3f}"

# load and clean
raw = pd.read_csv(CSV_PATH)
say("=" * 70)
say("1. DATA CLEANING")
say("=" * 70)
say(f"Raw rows: {len(raw)}; unique participant IDs: {raw.participant_id.nunique()}")

# some rows were saved twice, keep the first per participant and item
before = len(raw)
raw = raw.sort_values(["participant_id", "timestamp"])
df = raw.drop_duplicates(subset=["participant_id", "stimulus_id"], keep="first").copy()
say(f"Duplicate participant x stimulus rows removed: {before - len(df)}")

dup_pids = raw[raw.duplicated(["participant_id", "stimulus_id"], keep=False)].participant_id.unique()
say(f"Participant IDs that had duplicated rows: {list(dup_pids)}")

df["correct"] = df["correct"].astype(str).str.lower().map({"true": True, "false": False})

quiz = df[df.stimulus_id == "post_quiz"].copy()
trials = df[df.stimulus_id != "post_quiz"].copy()

# post-quiz answers are stored as json
parsed = quiz["answer"].apply(json.loads)
quiz["skepticism"] = parsed.apply(lambda d: d["skepticism"])
quiz["trust_harder"] = parsed.apply(lambda d: d["trust_harder"])
quiz = quiz[["participant_id", "skepticism", "trust_harder"]]

def category(row):
    if row.stimulus_type == "single_video":
        return {"authentic": "Authentic video",
                "ai_generated": "AI-generated video",
                "edited_non_ai": "Edited (non-AI) video"}[row.stimulus_notes]
    return "Video pair" if row.stimulus_type == "pair_video" else "Image pair"

trials["correct"] = trials["correct"].astype(bool)
trials["category"] = trials.apply(category, axis=1)
trials["is_single"] = trials.stimulus_type == "single_video"
trials["not_sure"] = trials.answer == "Not sure"

ITEM_LABELS = {
    "video1": "Video 1 (authentic)",
    "video2": "Video 2 (AI-generated)",
    "video3": "Video 3 (authentic)",
    "video4": "Video 4 (authentic)",
    "video5": "Video 5 (AI-generated)",
    "video6": "Video 6 (edited, non-AI)",
    "pair1": "Video pair 1 (AI on left)",
    "pair2": "Video pair 2 (AI on right)",
    "delft": "Image pair (AI on right)",
}
ITEM_ORDER = list(ITEM_LABELS.keys())
trials["item_label"] = trials.stimulus_id.map(ITEM_LABELS)

# fast responders
pp_rt = trials.groupby("participant_id").response_time_seconds.median()
rapid_ids = set(pp_rt[pp_rt < RAPID_MEDIAN_RT].index)
HAS_NAMES = "participant_name" in trials.columns
names = (trials.groupby("participant_id").participant_name.first() if HAS_NAMES
         else pd.Series(trials.participant_id.unique(), index=trials.participant_id.unique()))

if EXCLUDE_NAMES:
    drop_ids = set(names[names.isin(EXCLUDE_NAMES)].index)
    say(f"Excluded from main analysis by name {EXCLUDE_NAMES}: {len(drop_ids)} participant(s)")
    trials = trials[~trials.participant_id.isin(drop_ids)]
    quiz = quiz[~quiz.participant_id.isin(drop_ids)]

N = trials.participant_id.nunique()
say(f"Participants in main analysis: {N}")
say(f"Trials in main analysis: {len(trials)} ({len(trials) / N:.0f} per participant)")
say(f"Data collection period: {raw.timestamp.min()[:10]} to {raw.timestamp.max()[:10]}")
say(f"Very fast responders (median RT < {RAPID_MEDIAN_RT:.0f} s): {len(rapid_ids)} "
    f"participant(s) -> kept in main analysis, see sensitivity analysis below")
if HAS_NAMES:
    say(f"Distinct nicknames: {names.nunique()} (nickname reused by different IDs: "
        f"{list(names[names.duplicated(keep=False)].unique())})")

# accuracy per item
say()
say("=" * 70)
say("2. ACCURACY PER ITEM")
say("=" * 70)
say("Scoring rule (same as the app): 'Not sure' counts as incorrect.")

rows = []
for sid in ITEM_ORDER:
    d = trials[trials.stimulus_id == sid]
    k, n = int(d.correct.sum()), len(d)
    lo, hi = wilson(k, n)
    p = stats.binomtest(k, n, 0.5).pvalue
    decided = d[~d.not_sure]
    rows.append({
        "item": sid, "label": ITEM_LABELS[sid], "category": d.category.iloc[0],
        "n": n, "n_correct": k, "accuracy": k / n,
        "ci_low": lo, "ci_high": hi,
        "n_not_sure": int(d.not_sure.sum()),
        "accuracy_excl_not_sure": decided.correct.mean() if len(decided) else np.nan,
        "mean_confidence": d.confidence.mean(),
        "median_rt_s": d.response_time_seconds.median(),
        "p_vs_50pct_raw": p,
    })
item_tbl = pd.DataFrame(rows)
item_tbl["p_vs_50pct_holm"] = holm(item_tbl.p_vs_50pct_raw)
item_tbl.round(3).to_csv(OUT / "tables" / "table_item_summary.csv", index=False)
say(item_tbl[["label", "n_correct", "n", "accuracy", "ci_low", "ci_high",
              "n_not_sure", "p_vs_50pct_holm"]].round(3).to_string(index=False))
say("(exact binomial test vs 50%, Holm-corrected. 50% is only a rough reference for single videos, 'Not sure' is a third option.)")

# participant scores and categories
say()
say("=" * 70)
say("3. PARTICIPANT-LEVEL ACCURACY AND CATEGORY-LEVEL RESULTS")
say("=" * 70)

pp = trials.groupby("participant_id").agg(
    total_correct=("correct", "sum"),
    accuracy=("correct", "mean"),
    mean_conf=("confidence", "mean"),
    median_rt=("response_time_seconds", "median"),
    n_not_sure=("not_sure", "sum"),
).reset_index()
pp["acc_single"] = trials[trials.is_single].groupby("participant_id").correct.mean().reindex(pp.participant_id).values
pp["acc_pair"] = trials[~trials.is_single].groupby("participant_id").correct.mean().reindex(pp.participant_id).values
pp = pp.merge(quiz, on="participant_id", how="left")
pp["rapid_responder"] = pp.participant_id.isin(rapid_ids)
pp_out = pp.copy()
pp_out["participant_id"] = ["P%02d" % (i + 1) for i in range(len(pp_out))]  # no real ids in the tables
pp_out.round(3).to_csv(OUT / "tables" / "table_participant_summary.csv", index=False)

mean_acc = pp.accuracy.mean()
lo, hi = cluster_boot_ci(pp.accuracy)
say(f"Overall accuracy (mean of participants): {mean_acc:.1%} (95% bootstrap CI {lo:.1%} to {hi:.1%}); "
    f"median score {pp.total_correct.median():.0f}/9, range {pp.total_correct.min():.0f}-{pp.total_correct.max():.0f}")
say(f"Mean score: {pp.total_correct.mean():.2f}/9 (SD {pp.total_correct.std(ddof=1):.2f})")
say(f"Participants scoring 9/9: {(pp.total_correct == 9).sum()}; "
    f">= 7/9: {(pp.total_correct >= 7).sum()}; <= 4/9: {(pp.total_correct <= 4).sum()}")

cat_rows = []
for cat in CAT_COLORS:
    d = trials[trials.category == cat]
    per_p = d.groupby("participant_id").correct.mean()
    lo, hi = cluster_boot_ci(per_p)
    cat_rows.append({
        "category": cat, "n_items": d.stimulus_id.nunique(), "n_trials": len(d),
        "accuracy": per_p.mean(), "ci_low": lo, "ci_high": hi,
        "not_sure_rate": d.not_sure.mean(),
        "mean_confidence": d.confidence.mean(),
    })
cat_tbl = pd.DataFrame(cat_rows)
cat_tbl.round(3).to_csv(OUT / "tables" / "table_category_summary.csv", index=False)
say()
say(cat_tbl.round(3).to_string(index=False))

# single vs pair
w = stats.wilcoxon(pp.acc_single, pp.acc_pair, zero_method="wilcox") if (pp.acc_single != pp.acc_pair).any() else None
say()
say(f"Single-video accuracy: mean {pp.acc_single.mean():.1%}; pair accuracy (2 video + 1 image): mean {pp.acc_pair.mean():.1%}")
if w is not None:
    say(f"Paired Wilcoxon, single vs pair accuracy: W = {w.statistic:.1f}, {fmt_p(w.pvalue)} (exploratory)")
t1 = stats.wilcoxon(pp.acc_single - 0.5)
t2 = stats.wilcoxon(pp.acc_pair - 0.5)
say(f"Single-video accuracy vs 0.50: Wilcoxon {fmt_p(t1.pvalue)}; pair accuracy vs 0.50: Wilcoxon {fmt_p(t2.pvalue)}")

# single videos: response patterns, d'
say()
say("=" * 70)
say("4. RESPONSE PATTERNS FOR SINGLE VIDEOS (AI-generated / authentic / edited non-AI)")
say("=" * 70)
sv = trials[trials.is_single].copy()
sv["resp"] = sv.answer.map({"Yes (AI-generated)": "Judged AI-generated",
                            "No": "Judged not AI",
                            "Not sure": "Not sure"})
cm = pd.crosstab(sv.category, sv.resp)
cm = cm.reindex(["Authentic video", "Edited (non-AI) video", "AI-generated video"])
cm = cm[["Judged AI-generated", "Judged not AI", "Not sure"]]
cm_pct = cm.div(cm.sum(axis=1), axis=0)
cm.to_csv(OUT / "tables" / "table_single_video_response_counts.csv")
say(cm.to_string())
say()
say((cm_pct * 100).round(1).to_string())

# d' and criterion, 'Not sure' left out
def dprime(df_):
    ai = df_[df_.stimulus_notes == "ai_generated"]
    non = df_[df_.stimulus_notes != "ai_generated"]
    H = (ai.answer == "Yes (AI-generated)").sum()
    nH = (ai.answer != "Not sure").sum()
    F = (non.answer == "Yes (AI-generated)").sum()
    nF = (non.answer != "Not sure").sum()
    h, f = (H + 0.5) / (nH + 1), (F + 0.5) / (nF + 1)   # log-linear correction
    zh, zf = stats.norm.ppf(h), stats.norm.ppf(f)
    return zh - zf, -(zh + zf) / 2, H / nH if nH else np.nan, F / nF if nF else np.nan

d_obs, c_obs, hit, fa = dprime(sv)
pids = sv.participant_id.unique()
boots = []
for _ in range(2000):
    samp = rng.choice(pids, size=len(pids), replace=True)
    b = pd.concat([sv[sv.participant_id == p] for p in samp])
    boots.append(dprime(b)[:2])
boots = np.array(boots)
d_ci = np.percentile(boots[:, 0], [2.5, 97.5])
c_ci = np.percentile(boots[:, 1], [2.5, 97.5])
say()
say(f"Hit rate (AI videos judged AI, excl. 'Not sure'): {hit:.1%}")
say(f"False-alarm rate (non-AI videos judged AI, excl. 'Not sure'): {fa:.1%}")
say(f"d' (sensitivity) = {d_obs:.2f} (95% CI {d_ci[0]:.2f} to {d_ci[1]:.2f}); "
    f"criterion c = {c_obs:.2f} (95% CI {c_ci[0]:.2f} to {c_ci[1]:.2f})")
say("Only 2 AI and 4 non-AI videos, so treat d' and c as descriptive.")

# confidence
say()
say("=" * 70)
say("5. CONFIDENCE")
say("=" * 70)
say(f"Mean confidence overall: {trials.confidence.mean():.2f} / 5 (SD {trials.confidence.std():.2f})")
by_ans = trials.groupby("answer").confidence.agg(["count", "mean"]).round(2)
say(by_ans.to_string())

# confidence on 'Not sure' is analysed separately
ex = trials[~trials.not_sure]
cc = ex.groupby(["participant_id", "correct"]).confidence.mean().unstack()
cc = cc.dropna()
wc = stats.wilcoxon(cc[True], cc[False])
say()
say(f"Definite answers only (n = {len(ex)}): mean confidence when correct {ex[ex.correct].confidence.mean():.2f}; "
    f"when incorrect {ex[~ex.correct].confidence.mean():.2f}")
say(f"Same, participant-level (n = {len(cc)} participants with both correct and incorrect definite answers): "
    f"correct {cc[True].mean():.2f} vs incorrect {cc[False].mean():.2f}; Wilcoxon {fmt_p(wc.pvalue)}")
say(f"'Not sure' answers (n = {int(trials.not_sure.sum())}): mean confidence {trials[trials.not_sure].confidence.mean():.2f}")

rho_t, p_t = stats.spearmanr(ex.confidence, ex.correct.astype(int))
say(f"Trial-level Spearman correlation confidence vs correctness (excl. 'Not sure', n = {len(ex)}): "
    f"rho = {rho_t:.2f}, {fmt_p(p_t)}. (p is approximate, trials are nested in participants)")
rho_p, p_p = stats.spearmanr(pp.mean_conf, pp.accuracy)
say(f"Participant-level Spearman correlation mean confidence vs accuracy (n = {len(pp)}): "
    f"rho = {rho_p:.2f}, {fmt_p(p_p)}")

# confident mistakes
hce = trials[(~trials.correct) & (~trials.not_sure) & (trials.confidence >= 4)]
wrong = trials[(~trials.correct) & (~trials.not_sure)]
say(f"Wrong (non-'Not sure') answers given with confidence >= 4: {len(hce)} of {len(wrong)} "
    f"({len(hce) / len(wrong):.1%})")

calib = ex.groupby("confidence").agg(n=("correct", "size"), k=("correct", "sum")).reset_index()
calib["accuracy"] = calib.k / calib.n
calib[["ci_low", "ci_high"]] = calib.apply(lambda r: pd.Series(wilson(r.k, r.n)), axis=1)
calib.round(3).to_csv(OUT / "tables" / "table_accuracy_by_confidence.csv", index=False)
say()
say(calib.round(3).to_string(index=False))

# response time
say()
say("=" * 70)
say("6. RESPONSE TIME (seconds)")
say("=" * 70)
say(f"Median RT overall: {trials.response_time_seconds.median():.1f} s "
    f"(IQR {trials.response_time_seconds.quantile(.25):.1f} - {trials.response_time_seconds.quantile(.75):.1f})")
rt_tbl = trials.groupby("category").response_time_seconds.agg(["median", "mean", "min", "max"]).round(1)
say(rt_tbl.to_string())
rt_c = trials.groupby(["participant_id", "correct"]).response_time_seconds.median().unstack().dropna()
wr = stats.wilcoxon(rt_c[True], rt_c[False])
say(f"Median RT correct vs incorrect (participant medians, n = {len(rt_c)}): "
    f"{rt_c[True].median():.1f} s vs {rt_c[False].median():.1f} s; Wilcoxon {fmt_p(wr.pvalue)}")
rho_rt, p_rt = stats.spearmanr(pp.median_rt, pp.accuracy)
say(f"Participant median RT vs accuracy: Spearman rho = {rho_rt:.2f}, {fmt_p(p_rt)}")
rt_tbl.to_csv(OUT / "tables" / "table_response_time_by_category.csv")

# pair tasks: left/right choices
say()
say("=" * 70)
say("7. PAIR TASKS: POSITION PREFERENCE")
say("=" * 70)
pr = trials[~trials.is_single]
pos = pd.crosstab(pr.stimulus_id, pr.answer).reindex(["pair1", "pair2", "delft"])
say(pos.to_string())
n_right = (pr.answer == "Right").sum()
n_left = (pr.answer == "Left").sum()
bt = stats.binomtest(n_right, n_right + n_left, 0.5)
say(f"'Right' chosen {n_right} times, 'Left' {n_left} times ('Not sure' {int(pr.not_sure.sum())}) "
    f"across the 3 pair items. Binomial test of Right vs Left = 50/50: {fmt_p(bt.pvalue)}")
say("Note: the AI item was on the right in 2 of 3 pairs, so a right-side habit and the true position can't be separated.")

# post-quiz
say()
say("=" * 70)
say("8. POST-QUIZ (1 = strongly disagree ... 5 = strongly agree)")
say("=" * 70)
Q_LABELS = {
    "skepticism": "After this quiz, I feel more skeptical\nabout content I see online.",
    "trust_harder": "Frequent exposure to AI-generated content\nmakes it harder to trust real content.",
}
for q in ["skepticism", "trust_harder"]:
    v = quiz[q]
    agree = (v >= 4).mean()
    say(f"{q}: mean {v.mean():.2f}, median {v.median():.0f}, SD {v.std(ddof=1):.2f}; "
        f"agree/strongly agree {agree:.0%}; disagree/strongly disagree {(v <= 2).mean():.0%}; "
        f"neutral {(v == 3).mean():.0%} (n = {len(v)})")
for q in ["skepticism", "trust_harder"]:
    r, p = stats.spearmanr(pp[q], pp.accuracy)
    say(f"Spearman {q} vs accuracy: rho = {r:.2f}, {fmt_p(p)} (exploratory)")
say("Note: no pre-test, so these are opinions after the task, not change.")

# sensitivity check without fast responders
say()
say("=" * 70)
say(f"9. SENSITIVITY ANALYSIS: excluding participants with median RT < {RAPID_MEDIAN_RT:.0f} s")
say("=" * 70)
keep = pp[~pp.rapid_responder]
say(f"Participants kept: {len(keep)} of {len(pp)}")
say(f"Mean accuracy: all = {pp.accuracy.mean():.1%}; without fast responders = {keep.accuracy.mean():.1%}")
say(f"Mean accuracy of the fast responders themselves: {pp[pp.rapid_responder].accuracy.mean():.1%}")
sens = trials[~trials.participant_id.isin(rapid_ids)].groupby("category").correct.mean().round(3)
say(sens.to_string())

# detector (optional)
detector = None
if Path(DETECTOR_PATH).exists():
    with open(DETECTOR_PATH) as f:
        detector = json.load(f)
    say()
    say("=" * 70)
    say("10. HUMAN vs MACHINE BASELINE (UniversalFakeDetect)")
    say("=" * 70)
    cmp_rows = []
    for sid in ITEM_ORDER:
        if sid in detector:
            det = detector[sid]
            cmp_rows.append({
                "item": sid, "label": ITEM_LABELS[sid],
                "human_accuracy": item_tbl.set_index("item").loc[sid, "accuracy"],
                "detector_correct": bool(det.get("correct", False)),
                "detector_prediction": det.get("prediction"),
            })
    cmp_tbl = pd.DataFrame(cmp_rows)
    cmp_tbl.round(3).to_csv(OUT / "tables" / "table_human_vs_detector.csv", index=False)
    say(cmp_tbl.round(3).to_string(index=False))
    say(f"Detector correct on {cmp_tbl.detector_correct.sum()} of {len(cmp_tbl)} items "
        f"({cmp_tbl.detector_correct.mean():.0%}); mean human item accuracy {cmp_tbl.human_accuracy.mean():.1%}.")
else:
    say()
    say(f"[no detector file at '{DETECTOR_PATH}', skipping the human vs detector part]")

# figures

# fig 1: outcome per item
fig, ax = plt.subplots(figsize=(8.2, 4.8))
order = ITEM_ORDER[::-1]
for i, sid in enumerate(order):
    d = trials[trials.stimulus_id == sid]
    c = d.correct.mean()
    u = d.not_sure.mean()
    w_ = 1 - c - u
    ax.barh(i, c, color=C_OK, edgecolor="white")
    ax.barh(i, w_, left=c, color=C_BAD, edgecolor="white")
    ax.barh(i, u, left=c + w_, color=C_UNS, edgecolor="white")
    ax.text(c / 2, i, f"{c:.0%}", ha="center", va="center", color="white", fontweight="bold")
    if w_ > 0.06:
        ax.text(c + w_ / 2, i, f"{w_:.0%}", ha="center", va="center", color="white")
    if u > 0.06:
        ax.text(c + w_ + u / 2, i, f"{u:.0%}", ha="center", va="center", color="#333")
ax.set_yticks(range(len(order)))
ax.set_yticklabels([ITEM_LABELS[s] for s in order])
ax.set_xlim(0, 1)
ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
ax.axvline(0.5, color="black", ls="--", lw=0.8, alpha=0.5)
ax.set_xlabel(f"Share of participants (N = {N})")
ax.set_title("Outcome of participant judgments for each media item")
ax.legend(handles=[Patch(color=C_OK, label="Correct"), Patch(color=C_BAD, label="Incorrect"),
                   Patch(color=C_UNS, label="Not sure")],
          ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.13), frameon=False)
savefig(fig, "fig1_outcome_per_item")

# fig 2: accuracy by category with participant-level points
fig, ax = plt.subplots(figsize=(8, 4.6))
cats = list(CAT_COLORS.keys())
for i, cat in enumerate(cats):
    r = cat_tbl[cat_tbl.category == cat].iloc[0]
    ax.bar(i, r.accuracy, color=CAT_COLORS[cat], alpha=0.75, width=0.6)
    ax.errorbar(i, r.accuracy, yerr=[[r.accuracy - r.ci_low], [r.ci_high - r.accuracy]],
                color="black", capsize=4, lw=1.3)
    per_p = trials[trials.category == cat].groupby("participant_id").correct.mean()
    ax.scatter(i + rng.uniform(-0.2, 0.2, len(per_p)), per_p + rng.uniform(-0.015, 0.015, len(per_p)),
               s=12, color="black", alpha=0.35, zorder=3)
    ax.text(i, 1.09, f"{r.accuracy:.0%}", ha="center", fontweight="bold")
ax.axhline(0.5, color="black", ls="--", lw=0.8, alpha=0.5)
ax.set_xticks(range(len(cats)))
ax.set_xticklabels([c.replace(" video", "\nvideo").replace(" pair", "\npair") for c in cats])
ax.set_ylim(-0.03, 1.15)
ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}" if -0.001 <= y <= 1.001 else "")
ax.set_ylabel("Accuracy (mean across participants)")
ax.set_title("Accuracy by media category\n(bars: mean and 95% bootstrap CI; dots: individual participants)")
savefig(fig, "fig2_accuracy_by_category")

# fig 3: single-video response profile
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.1, 1]})
im = ax1.imshow(cm_pct.values, cmap="Purples", vmin=0, vmax=0.8)
ax1.set_xticks(range(3))
ax1.set_xticklabels(["Judged\nAI-generated", "Judged\nnot AI", "Not sure"])
ax1.set_yticks(range(3))
ax1.set_yticklabels([f"{i}\n(n = {int(cm.loc[i].sum())})" for i in cm.index])
for i in range(3):
    for j in range(3):
        v = cm_pct.values[i, j]
        ax1.text(j, i, f"{v:.0%}\n({cm.values[i, j]})", ha="center", va="center",
                 color="white" if v > 0.45 else "black")
ax1.set_title("(a) What participants said about each true video type")
ax1.set_ylabel("True type")
ax1.spines[["left", "bottom"]].set_visible(False)
ax1.tick_params(length=0)

single_ids = ["video1", "video2", "video3", "video4", "video5", "video6"]
for i, sid in enumerate(single_ids):
    d = trials[trials.stimulus_id == sid]
    k = (d.answer == "Yes (AI-generated)").sum()
    lo_, hi_ = wilson(k, len(d))
    col = {"authentic": C_AUTH, "ai_generated": C_AI, "edited_non_ai": C_EDIT}[d.stimulus_notes.iloc[0]]
    ax2.errorbar(k / len(d), 5 - i, xerr=[[k / len(d) - lo_], [hi_ - k / len(d)]],
                 fmt="o", color=col, capsize=3, ms=8)
    ax2.text(1.03, 5 - i, f"{k}/{len(d)}", va="center", fontsize=9)
ax2.set_yticks(range(6))
ax2.set_yticklabels([ITEM_LABELS[s] for s in single_ids[::-1]])
ax2.set_xlim(0, 1.12)
ax2.axvline(0.5, color="black", ls="--", lw=0.8, alpha=0.4)
ax2.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}" if x <= 1 else "")
ax2.set_xlabel("Share answering 'AI-generated' (95% Wilson CI)")
ax2.set_title("(b) How often each video was flagged as AI")
fig.tight_layout()
savefig(fig, "fig3_single_video_response_profile")

# fig 4: confidence + confidence-accuracy
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))
conf_levels = [1, 2, 3, 4, 5]
w_ = 0.38
dfin = trials[~trials.not_sure]   # without "Not sure"
cor_dist = dfin[dfin.correct].confidence.value_counts(normalize=True).reindex(conf_levels, fill_value=0)
inc_dist = dfin[~dfin.correct].confidence.value_counts(normalize=True).reindex(conf_levels, fill_value=0)
ax1.bar(np.array(conf_levels) - w_ / 2, cor_dist, w_, color=C_OK, label=f"Correct (n = {int(dfin.correct.sum())})")
ax1.bar(np.array(conf_levels) + w_ / 2, inc_dist, w_, color=C_BAD, label=f"Incorrect (n = {int((~dfin.correct).sum())})")
ax1.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
ax1.set_xlabel("Confidence (1 = pure guess, 5 = very confident)")
ax1.set_ylabel("Share of definite answers in group")
ax1.set_title(f"(a) Confidence of definite answers\nmean: correct {dfin[dfin.correct].confidence.mean():.2f}, "
              f"incorrect {dfin[~dfin.correct].confidence.mean():.2f}")
ax1.legend(frameon=False)

ax2.errorbar(calib.confidence, calib.accuracy,
             yerr=[calib.accuracy - calib.ci_low, calib.ci_high - calib.accuracy],
             fmt="-o", color=C_AI, capsize=4, ms=7)
for _, r in calib.iterrows():
    ax2.text(r.confidence, min(r.ci_high + 0.04, 1.02), f"n={int(r.n)}", ha="center", fontsize=8.5)
ax2.axhline(0.5, color="black", ls="--", lw=0.8, alpha=0.4)
ax2.set_ylim(0, 1.1)
ax2.set_xticks(conf_levels)
ax2.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}" if y <= 1 else "")
ax2.set_xlabel("Reported confidence")
ax2.set_ylabel("Accuracy of these answers")
ax2.set_title("(b) Does higher confidence go with higher accuracy?\n('Not sure' answers excluded; 95% Wilson CI)")
fig.tight_layout()
savefig(fig, "fig4_confidence")

# fig 5: confidence gap per item
fig, ax = plt.subplots(figsize=(8.2, 4.8))
for i, sid in enumerate(ITEM_ORDER[::-1]):
    d = trials[trials.stimulus_id == sid]
    c_ok = d[d.correct].confidence
    c_bad = d[~d.correct].confidence
    if len(c_ok) and len(c_bad):
        ax.plot([c_ok.mean(), c_bad.mean()], [i, i], color="#999", lw=1.5, zorder=1)
    if len(c_ok):
        ax.scatter(c_ok.mean(), i, s=30 + 12 * len(c_ok), color=C_OK, zorder=2)
    if len(c_bad):
        ax.scatter(c_bad.mean(), i, s=30 + 12 * len(c_bad), color=C_BAD, zorder=2)
ax.set_yticks(range(9))
ax.set_yticklabels([ITEM_LABELS[s] for s in ITEM_ORDER[::-1]])
ax.set_xlim(1, 5)
ax.set_xlabel("Mean confidence (1-5)")
ax.set_title("Mean confidence for correct vs incorrect answers, per item\n(dot size proportional to number of answers)")
ax.legend(handles=[Patch(color=C_OK, label="Correct answers"), Patch(color=C_BAD, label="Incorrect answers")],
          frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)
savefig(fig, "fig5_confidence_per_item")

# fig 6: response time
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [1.3, 1]})
groups = [("Single video", trials[trials.is_single]),
          ("Video pair", trials[trials.stimulus_type == "pair_video"]),
          ("Image pair", trials[trials.stimulus_type == "pair_image"])]
pos_ = 0
ticks, tlabs = [], []
for name, d in groups:
    for j, (flag, col) in enumerate([(True, C_OK), (False, C_BAD)]):
        vals = d[d.correct == flag].response_time_seconds
        if len(vals) == 0:
            continue
        bp = ax1.boxplot(vals, positions=[pos_ + j * 0.7], widths=0.55, patch_artist=True,
                         showfliers=False, medianprops=dict(color="black"))
        bp["boxes"][0].set(facecolor=col, alpha=0.65)
        ax1.scatter(pos_ + j * 0.7 + rng.uniform(-0.15, 0.15, len(vals)), vals, s=8, color="black", alpha=0.25)
    ticks.append(pos_ + 0.35)
    tlabs.append(name)
    pos_ += 2.2
ax1.set_yscale("log")
ax1.set_yticks([3, 5, 10, 20, 40, 80, 130])
ax1.get_yaxis().set_major_formatter(plt.ScalarFormatter())
ax1.set_xticks(ticks)
ax1.set_xticklabels(tlabs)
ax1.set_ylabel("Response time (seconds, log scale)")
ax1.set_title("(a) Response time by task type and correctness")
ax1.legend(handles=[Patch(color=C_OK, alpha=.65, label="Correct"), Patch(color=C_BAD, alpha=.65, label="Incorrect")],
           frameon=False)

ax2.hist(pp.median_rt, bins=np.arange(0, pp.median_rt.max() + 4, 3), color="#6C7A89", edgecolor="white")
ax2.axvline(RAPID_MEDIAN_RT, color=C_BAD, ls="--")
ax2.text(RAPID_MEDIAN_RT + 0.4, ax2.get_ylim()[1] * 0.9,
         f"{len(rapid_ids)} participants\nbelow {RAPID_MEDIAN_RT:.0f} s", color=C_BAD, fontsize=9, va="top")
ax2.set_xlabel("Participant's median response time (s)")
ax2.set_ylabel("Number of participants")
ax2.set_title("(b) Speed differences between participants")
fig.tight_layout()
savefig(fig, "fig6_response_time")

# fig 7: participant score distribution
fig, ax = plt.subplots(figsize=(7.2, 4.2))
counts = pp.total_correct.astype(int).value_counts().reindex(range(10), fill_value=0)
ax.bar(counts.index, counts.values, color=C_AI, alpha=0.8, width=0.7)
binom = stats.binom.pmf(range(10), 9, 0.5) * N
ax.plot(range(10), binom, "o--", color="black", lw=1, ms=4, label="Reference: random guessing (p = 0.5 per item)")
ax.axvline(pp.total_correct.mean(), color=C_OK, lw=2, label=f"Observed mean = {pp.total_correct.mean():.1f}")
ax.set_xticks(range(10))
ax.set_xlabel("Number of correct answers out of 9")
ax.set_ylabel("Number of participants")
ax.set_title("Distribution of individual scores")
ax.legend(frameon=False, loc="upper left", fontsize=9)
savefig(fig, "fig7_score_distribution")

# fig 8: pair tasks - which side was chosen
fig, ax = plt.subplots(figsize=(7.6, 3.8))
for i, sid in enumerate(["pair1", "pair2", "delft"][::-1]):
    d = pr[pr.stimulus_id == sid]
    L = (d.answer == "Left").mean()
    R = (d.answer == "Right").mean()
    U = (d.answer == "Not sure").mean()
    ax.barh(i, L, color="#4C78A8", edgecolor="white")
    ax.barh(i, R, left=L, color="#F58518", edgecolor="white")
    ax.barh(i, U, left=L + R, color=C_UNS, edgecolor="white")
    for x0, w2, t in [(0, L, "Left"), (L, R, "Right"), (L + R, U, "Not sure")]:
        if w2 > 0.07:
            ax.text(x0 + w2 / 2, i, f"{t}\n{w2:.0%}", ha="center", va="center", color="white" if t != "Not sure" else "#333", fontsize=9)
    truth = d.ground_truth.iloc[0]
    xt = 0.0 if truth == "Left" else 1.0
ax.set_yticks(range(3))
ax.set_yticklabels(["Image pair\n(AI on right)", "Video pair 2\n(AI on right)", "Video pair 1\n(AI on left)"])
ax.set_xlim(0, 1)
ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
ax.set_xlabel("Share of participants choosing each side as AI-generated")
ax.set_title("Side chosen as 'the AI-generated one' in the pair tasks")
savefig(fig, "fig8_pair_position_choices")

# fig 9: post-quiz likert
fig, ax = plt.subplots(figsize=(9, 3.4))
lik_cols = {1: "#B2182B", 2: "#EF8A62", 3: "#CFCFCF", 4: "#67A9CF", 5: "#2166AC"}
lik_names = {1: "Strongly disagree", 2: "Disagree", 3: "In between", 4: "Agree", 5: "Strongly agree"}
for i, q in enumerate(["trust_harder", "skepticism"]):
    v = quiz[q].value_counts(normalize=True).reindex(range(1, 6), fill_value=0)
    left_edge = -(v[1] + v[2] + v[3] / 2)
    x = left_edge
    for lv in range(1, 6):
        ax.barh(i, v[lv], left=x, color=lik_cols[lv], edgecolor="white")
        if v[lv] > 0.06:
            ax.text(x + v[lv] / 2, i, f"{v[lv]:.0%}", ha="center", va="center",
                    color="white" if lv in (1, 5) else "black", fontsize=9)
        x += v[lv]
ax.axvline(0, color="black", lw=0.8)
ax.set_yticks([0, 1])
ax.set_yticklabels([Q_LABELS["trust_harder"], Q_LABELS["skepticism"]], fontsize=9)
ax.set_xlim(-0.6, 0.95)
ax.set_xticks([-0.5, 0, 0.5])
ax.set_xticklabels(["50%", "0", "50%"])
ax.set_xlabel("Share of participants (disagree side left, agree side right)")
ax.set_title(f"Post-quiz self-report (N = {len(quiz)})")
ax.legend(handles=[Patch(color=lik_cols[k], label=lik_names[k]) for k in range(1, 6)],
          ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.32), frameon=False, fontsize=8.5)
savefig(fig, "fig9_post_quiz")

# fig 10: individual differences
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))
sc = ax1.scatter(pp.mean_conf, pp.accuracy + rng.uniform(-0.01, 0.01, len(pp)), c=pp.median_rt,
                 cmap="viridis_r", s=60, edgecolor="black", linewidth=0.5)
cb = fig.colorbar(sc, ax=ax1)
cb.set_label("Median response time (s)")
if len(pp) > 2:
    m, b = np.polyfit(pp.mean_conf, pp.accuracy, 1)
    xs = np.linspace(pp.mean_conf.min(), pp.mean_conf.max(), 10)
    ax1.plot(xs, m * xs + b, color="black", lw=1, ls="--")
ax1.set_xlabel("Participant's mean confidence (1-5)")
ax1.set_ylabel("Participant's accuracy")
ax1.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
ax1.set_title(f"(a) Confidence vs accuracy across participants\nSpearman rho = {rho_p:.2f}, {fmt_p(p_p)}")

r_s, p_s = stats.spearmanr(pp.skepticism, pp.accuracy)
ax2.scatter(pp.skepticism + rng.uniform(-0.12, 0.12, len(pp)), pp.accuracy + rng.uniform(-0.01, 0.01, len(pp)),
            s=60, color=C_AI, edgecolor="black", linewidth=0.5, alpha=0.8)
ax2.set_xticks(range(1, 6))
ax2.set_xlabel("Post-quiz: 'I feel more skeptical about online content' (1-5)")
ax2.set_ylabel("Participant's accuracy")
ax2.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
ax2.set_title(f"(b) Accuracy vs reported skepticism\nSpearman rho = {r_s:.2f}, {fmt_p(p_s)} (exploratory)")
fig.tight_layout()
savefig(fig, "fig10_individual_differences")

# fig 11: human vs detector
if detector is not None and len(cmp_tbl) > 0:
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for i, sid in enumerate(ITEM_ORDER[::-1]):
        r = cmp_tbl[cmp_tbl.item == sid]
        if r.empty:
            continue
        r = r.iloc[0]
        ax.barh(i, r.human_accuracy, color="#7F8FA6", height=0.55)
        ax.text(r.human_accuracy + 0.02, i, f"{r.human_accuracy:.0%}", va="center", fontsize=9)
        mk = "o" if r.detector_correct else "X"
        ax.scatter(1.08, i, marker=mk, s=110, color=C_OK if r.detector_correct else C_BAD, clip_on=False)
    ax.set_yticks(range(9))
    ax.set_yticklabels([ITEM_LABELS[s] for s in ITEM_ORDER[::-1]])
    ax.set_xlim(0, 1)
    ax.axvline(0.5, color="black", ls="--", lw=0.8, alpha=0.4)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.set_xlabel("Human accuracy (share of participants correct)")
    ax.text(1.08, 9.0, "Detector", ha="center", fontsize=10, fontweight="bold")
    ax.set_title("Human accuracy vs machine baseline (UniversalFakeDetect) per item")
    ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", color=C_OK, label="Detector correct"),
                       plt.Line2D([], [], marker="X", ls="", color=C_BAD, label="Detector incorrect")],
              frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)
    savefig(fig, "fig11_human_vs_detector")

# save numbers
(OUT / "report_numbers.txt").write_text("\n".join(report_lines), encoding="utf-8")
print("\nDone. Figures in", OUT / "figures", "| tables in", OUT / "tables",
      "| numbers in", OUT / "report_numbers.txt")
