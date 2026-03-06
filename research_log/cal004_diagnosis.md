# CAL-004 Diagnosis: 30,000-Foot View

**Date:** 2026-03-06

## The Core Contradiction

The model faces an impossible trade-off in winter months:

**October-April uses standard lapse (alpha=1.0, beta=+2.77)** because we have
no winter overlap data. This makes winter temperatures at 804m **warmer** than
Nuka by +2.77°C. But this is almost certainly wrong — if katabatic cooling
operates in summer (when the glacier surface is at 0°C), it likely operates
in winter too (glacier surface is well below 0°C, even if reduced).

### What the warm winter bias causes

With standard lapse in October:
- Nuka Oct mean: +2.8°C → Transfer to 804m: **+5.6°C**
- At +5.6°C, almost all October precipitation falls as **rain**, not snow
- But October is the START of the accumulation season!

November is similar: Nuka -1.5°C → 804m: **+1.3°C** → still above T0=0.5°C → rain.

**The model can't accumulate winter snowpack** at low elevations because
Oct-Nov-Apr temperatures are artificially warm. It compensates by:
- Setting precip_corr=0.5 (reduce total precip to reduce rain)
- Setting T0=0.5°C (anything >-0.5°C becomes snow — desperately)
- Maximizing internal_lapse (-8°C/km) to make upper glacier colder

### The numbers tell the story

**WY2023 at ELA (1078m) with precip_corr=0.5:**
- Model accumulates 515 mm snow over the full year
- Observed winter balance: **2,360 mm w.e.**
- The model produces 22% of observed accumulation!

**WY2024 at ACC (1293m) with precip_corr=0.5:**
- Model accumulates 670 mm snow
- Observed winter balance: **3,010 mm w.e.**
- The model produces 22% of observed accumulation!

The model has far too little snow. It then under-melts to compensate
(low MF_grad keeps melt low at high elevations), and the cost function
balances these errors.

### Why precip_corr=0.5?

This seems paradoxical — SNOTEL gauges typically undercatch, so you'd expect
precip_corr > 1. But with the warm October-November bias:
- Higher precip_corr = more precipitation falling as rain (not snow)
- More rain = more runoff = more negative mass balance
- The optimizer reduces precip_corr to limit rain damage

**precip_corr=0.5 is not a physical result — it's compensating for wrong
winter temperatures.**

## The Winter Temperature Problem

The Nuka→Dixon transfer coefficients for Oct-Apr use standard lapse
(alpha=1.0, beta=+2.77). This assumes "no katabatic effect in winter."

**This assumption is almost certainly wrong:**
1. Glacier surface is below 0°C year-round → temperature inversion persists
2. Katabatic winds operate whenever surface is colder than ambient air
3. Even snow-covered glaciers have katabatic drainage
4. The glacier is at lower elevation than Nuka — but the surface boundary
   layer keeps it cold

**Evidence:** With winter transfer = standard lapse, the model can only
produce 22% of observed winter accumulation. The actual winter temperature
on-glacier must be colder than the standard lapse predicts.

## What Needs to Change

### Architecture issue: Winter temperature transfer

The model needs a physically reasonable winter temperature transfer.
Options (ranked by preference):

**Option 1: Apply a reduced katabatic correction year-round**
- Use alpha=0.8, beta=0 for Oct-Apr (between standard lapse and summer values)
- Simple, testable, captures the key insight that glacier is always colder
- Rationale: katabatic effect exists but is weaker in winter (smaller
  ambient-surface T difference)

**Option 2: Infer winter transfer from mass balance closure**
- Back-calculate what winter temperatures MUST be to produce observed
  winter accumulation at each stake
- Use this to derive winter α, β coefficients
- More constrained but circular (using calibration targets to set forcing)

**Option 3: Deploy year-round temperature sensors (field work)**
- Definitive answer but requires another field season
- Should be recommended in thesis as critical future work

### Architecture issue: Precipitation phase matters enormously

The current rain/snow partition uses a single T0 with ±1°C linear transition.
When temperatures hover near T0 (which they do for months in shoulder seasons),
small temperature errors cause huge accumulation errors.

The model is extremely sensitive to:
1. Temperature at T0 transition → snow vs rain
2. Whether October/November precip accumulates as snow or runs off as rain
3. The timing of spring melt onset

### What does NOT need to change

- DETIM core equation is fine (MF=4.1 is reasonable)
- Statistical temperature transfer for summer is validated and working
- Elevation-dependent MF concept is correct (gradient just needs room)
- Geodetic fit is already reasonable (-0.88 vs -0.94 over 20 years)
- Glacier dynamics, routing, projection frameworks are ready

## Recommended Next Step

**Implement Option 1: reduced katabatic correction for winter.**

Propose: alpha=0.85, beta=+1.0 for Oct-Apr (instead of 1.0, +2.77).
This says: "In winter, the glacier is about 1.8°C colder than standard
lapse would predict" (vs 5.1°C colder in summer).

This single change should:
- Allow more October-November precipitation to fall as snow
- Reduce the need for extreme T0 and precip_corr
- Let precip_corr find a physically reasonable value (1.5-3.0)
- Dramatically improve winter accumulation and stake fits

Then re-calibrate (CAL-005) and assess.
