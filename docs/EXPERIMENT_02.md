# Experiment 0.2: retention, adaptability and approved practice

## Predeclared protocol

- Three six-symbol, deterministic, synthetic domains, trained sequentially:
  first -> second -> third -> first.
- Benchmark trains the same examples per seed for all learners, independently
  in their own databases. Validation examples have a different named RNG scope
  and are never passed into training, grading or rehearsal.
- Models: fixed budget that rejects new links; structural growth/pruning;
  growth/pruning plus replay. Capacity defaults to nine links.
- Repeat `study` for seeds 369...378, 60 observations per phase. Report mean,
  sample SD, min and max, and full per-seed metrics. Avoid changing parameters
  after seeing results without marking the change exploratory.

## Outcomes

1. **Forgetting ΔNLL:** first-world test NLL after third world minus NLL just
   after initial first-world training. Lower means better old-world retention.
2. **New-world accuracy:** mean test accuracy on second and third worlds,
   immediately after each is learned. Higher measures adaptability.
3. **Relearning ΔNLL:** first-world test NLL before and after revisiting it.
   Positive is improvement (relearning), not evidence of consolidated memory.
4. **Update attempts:** count link-update attempts through phase three,
   including rejected attempts. Replay attempts also reported separately.

These are small controlled software experiments, not evidence of biological
neurodevelopment or general reasoning. The fixed model wins on retention by
refusing to learn when full. Replay is not compute matched, so cross-model
claims about learning efficiency require an additional experiment.

## Approved human teaching

`teach-card` requires a manual provenance string; one approved answer per
world/source. `due` deliberately omits the answer. `answer` compares the
user-supplied response to the approved example, advances the simulated clock,
reinforces the approved association, and increases successful practice intervals
up to 64 steps. Incorrect responses receive bounded constructive feedback and
return for near-term practice. Its deterministic scheduling is not a biological
sleep model or validated educational outcome.

Privacy: never automatically import conversations, memory, or external
materials. The local database stores correct examples and aggregate correctness
of attempts, but **not** the raw text of wrong guesses. Avoid entering private
or sensitive data in lesson prompts. No network access is involved.

## Future falsification

Compare approaches with equal total training and replay attempts, stochastic
concept drift, novel symbol vocabularies, controlled teacher errors, adversarial
feedback, memory exhaustion, and independent held-out tasks not designed by
the same code author. Keep results even when they contradict the hypothesis.
