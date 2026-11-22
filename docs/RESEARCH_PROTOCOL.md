# Research protocol

**Question:** Does structural growth/pruning with bounded rehearsal outperform
fixed connectivity on sequential task learning under equal connection budgets?

**Null hypothesis:** Extra plasticity gives no reliable retention benefit after
normalizing for updates, capacity and replay overhead.

### Experiment 0.1

Synthetic domains: three mappings over six symbols. Sequential curriculum:
first → second → third → first. All models see identical training events;
held-out streams are generated under different seed scopes and are never
passed to update paths. Fixed model refuses new links when full; plastic model
replaces low-value unprotected links; replay model additionally rehearses.

Primary outcome: held-out negative log likelihood (NLL) on the first domain
after phases two and three. Secondary: top-1 accuracy, link count, number
of pruned/rejected links, replay updates, and recovery after revisit.

**Cautions:** This is a deliberately narrow associative learner: no neurons,
no new conceptual representations, no generalization beyond fixed labels.
Replay uses extra updates and a stored buffer; it must not be described as a
fair compute-matched victory. Protected links enable teacher choices but could
freeze capacity; test that tradeoff explicitly.

### Follow-ups

Use 10+ independent seeds; publish mean and variance with paired comparisons.
Add harder stochastic and unknown-state domains, online concept drift,
compute-matched baselines, delayed supervision, and uncertainty calibration.
Pre-register improvements before tuning against held-out worlds. Keep
PhiEmergence and Coherence Lab physical claims separate from learning claims.
