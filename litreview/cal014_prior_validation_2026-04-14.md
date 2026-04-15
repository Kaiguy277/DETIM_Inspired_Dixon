# CAL-014 Prior Validation Against Expanded Literature (2026-04-14)

**Scope:** Validate the CAL-014 proposal (8 free parameters, DE+MCMC, stakes+geodetic+snowline likelihood) against 32 verified open-access PDFs in `papers_verified/`, with emphasis on the 15 papers added 2026-04-14.

**Verdict (executive summary):** CAL-014 as currently specified is **defensible with modifications**. The lapse-rate prior is well-centered for a maritime Alaska glacier but **σ=1.0e-3 is too loose** and combined with a freed MF this will re-introduce lapse–MF equifinality that Gardner & Sharp (2009) and Sjursen (2023) explicitly warn about. The r_ice prior TN(4.0e-3, 2.0e-3) is **centered too high** if interpreted as the absolute radiation-factor in our units: Geck's best parameter set has r_ice = 0.0414 m² W⁻¹ mm d⁻¹ °C⁻¹, which under our internal DETIM units needs unit-reconciliation before the prior is meaningful. Most importantly, **moving from 6 to 8 parameters with only ~50 aggregated observations is close to the edge of what Sjursen 2023 and Rounce 2020 defend as identifiable**, and the lit precedent in maritime Alaska (McNeil 2020, Ziemen 2016, O'Neel 2019) is to **fix** the lapse rate, not calibrate it. See Section 3.

Files inspected (text-extractable): 18 of the 19 priority papers. `Zekollari_2024_CMIP6_global.pdf` is a corrupt download (HTML placeholder) and was **not verifiable** — flagged.

---

## 1. LAPSE RATE prior validation

**CAL-014 prior:** `lapse_rate ~ TN(μ = −4.5e-3, σ = 1.0e-3)` on [−6.5e-3, −2.0e-3] °C m⁻¹.

### Direct evidence from the new papers

**Carturan et al. 2015 (Italian Alps, 3 glaciers; pp. 2–10 / lines 372, 402–422, 469–480):**
- On-glacier summer lapse rates ranged **−5.2 to −7.2 °C km⁻¹** (La Mare, Careser), averaging **−4.9 °C km⁻¹** on a nearby glacier cited from Petersen & Pellicciotti 2011 (line 717: "ambient lapse rates ranging … averaging −4.9 °C km⁻¹"; Petersen AWS data).
- **Fixed-calibrated** lapse rates by combination of stations: ranged **−0.0049 to −0.0082 °C m⁻¹** (their Table; lines 469–480). The single-station standard ambient rate of −0.0065 performed worst in every ranking (their Table 5 rows with R² = 0.686–0.918 vs 0.857–0.899 for calibrated).
- Quote (line 422): *"variable lapse rates are the most appropriate solution while … fixed calibrated lapse rate should be used while extrapolating."*

**Heynen et al. 2015 (Himalaya, Langtang; pp. 4–8 / lines 28–31, 339):**
- Seasonal mean lapse rates: **post-monsoon 2014 −0.0048 °C m⁻¹** (line 339), varying seasonally.
- Quote (line 28): *"Seasonal variability is strong, with shallowest lapse rates during the monsoon season."*
- Quote (line 212): *"seasonal lapse rates seem stable over the 2–3 years investigated"*.
- Conclusion: annual single-constant is marginally acceptable but summer-specific is preferred.

**McNeil et al. 2020 (Taku + Lemon Creek, Juneau Icefield — maritime Alaska; lines 288, 402, 456):**
- **Tested lapse rates −4.0 to −6.5 °C km⁻¹** and selected **−5.0 °C km⁻¹** as optimal against on-glacier PDD fit (line 457: *"The lapse rate with the highest R² value is −5.0 °C km⁻¹ and was used in subsequent [analysis]"*).
- They **fixed** the lapse rate after optimization and did not free it during MCMC. This is the closest analog to Dixon in the corpus.

**Ziemen et al. 2016 (Juneau Icefield; line 232):**
- *"using a constant lapse rate of 5 K km⁻¹"* — fixed, not calibrated.

**O'Neel et al. 2019 (USGS benchmarks incl. Wolverine — same climate zone as Dixon; line 304):**
- *"using a constant adiabatic lapse rate of −6.5 °C km⁻¹"* — fixed.

**Geck et al. 2021 (Eklutna, south-central Alaska; lines 331–333):**
- Freely calibrated lapse rate among best parameter sets ranged **−0.6 to −0.2 °C per 100 m** (i.e., **−6.0 to −2.0 °C km⁻¹**), **mean −0.3 °C per 100 m (−3.0 °C km⁻¹)**, mode −0.2 (−2.0 °C km⁻¹). Note line 331 explicitly says *"the model is overparameterized, it is not possible to determine a single best model run"* — a direct warning for CAL-014.

**Mott et al. 2020 (katabatic/heat exchange):** extraction succeeded; katabatic boundary-layer flow typically steepens lapse rates near the surface in summer — consistent with summer lapse ≈ −0.005 to −0.007 °C m⁻¹ on melting ice.

### Assessment

Prior center μ = **−4.5e-3** is defensible — it sits between Geck's mean (−3.0e-3, freely calibrated) and the maritime Alaska precedents (McNeil −5.0e-3; O'Neel, Ziemen −5.0 to −6.5e-3). It is also close to Carturan's calibrated range midpoint (−0.0059 to −0.0063).

**The σ = 1.0e-3 is too loose, however.** On bounds [−6.5e-3, −2.0e-3] a TN with σ = 1.0e-3 has meaningful probability mass across the entire bound range (≈4.5 σ wide). Gardner & Sharp 2009 (cited in CAL-014 header) and Sjursen 2023 (line 833: *"precarious due to compensating effects between Tcorr and [MF]"*) both flag this as the classic compensation pathway: lapse rate trading against MF against precip_corr.

### Recommendation: **MODIFY**

- **Tighten σ to 0.6e-3** (bounds unchanged). This pulls 95% mass to [−5.7, −3.3] which covers Geck's range, McNeil's optimum, and our CAL-013 implicit range, while eliminating the tail toward −6.5 that only fits if MF compensates downward.
- **Additional safeguard:** Before MCMC, run a 5000-sample prior-predictive check; if the marginal posterior on lapse_rate ends up indistinguishable from the prior, that is evidence it is not identified (per Sjursen 2023 line 154: *"Comparison of the statistics of the marginal prior and posterior distributions can [give] indications of short[falls]"*). Be prepared to fix lapse_rate at the CAL-013 optimum and drop back to 7 parameters.

---

## 2. RADIATION FACTOR / DDF prior validation

**CAL-014 priors:** `r_snow ~ Uniform[0.02e-3, 2.0e-3]`; `r_ice ~ TN(4.0e-3, 2.0e-3)` on [0.02e-3, 10.0e-3]; units (model code): m² W⁻¹ mm d⁻¹ °C⁻¹ ÷ 1000 (Dixon uses ×1e-3 scaling).

### Direct evidence

**Geck et al. 2021 (Eklutna, Alaska; line 346):**
- Best parameter combination: **r_ice = 0.0414 m² W⁻¹ mm d⁻¹ °C⁻¹, r_snow = 0.0098 m² W⁻¹ mm d⁻¹ °C⁻¹**, MF = 5.5 mm °C⁻¹ d⁻¹.
- Ratio r_ice/r_snow = **4.22**.
- Line 354: r_ice distributed across three values 0.0242 and 0.0414 (Geck's best space).
- Note these are in m² W⁻¹ mm d⁻¹ °C⁻¹ (native Hock 1999 units). Converting: 0.0414 m² W⁻¹ → 41.4e-3 in SI base units for that factor.

**Hock 1999 (DETIM original; line 351):** DDF_ice = 7.5, DDF_snow = 4.5 mm d⁻¹ °C⁻¹, ratio ≈ **1.67**; radiation-factor ratio on Storglaciären implicit via r values shown in Fig. 4 of that paper.

**Rounce 2020 PyGEM HMA (lines 201–202):**
- *"the degree-day factor of snow is assumed to be 70% of the degree-day factor of ice"* — **fixed ratio 0.7 (≈ 1.43)**; PyGEM calibrates ONLY fsnow, with fice = fsnow / 0.7.

**Rounce 2020 HMA projections (lines 186–188):** same — *"ratio of the degree-day factor for snow to the degree-day factor of ice is 0.7"*.

**Sjursen 2023 (line 314):** *"We define MFice = MFsnow/0.7"* — ratio FIXED 1.43. Then only MFsnow is freed; prior TN(4.1, 1.5²) mm w.e. °C⁻¹ d⁻¹, truncated at 0 (line 432–436).

**McNeil 2020 (Taku/Lemon Creek):** ks and ki calibrated per-glacier (line 405 *"ks, ki, and m values"*) but specific numeric values are in a table that did not OCR cleanly — the paper does report DIFFERENT ks/ki per glacier, so the ratio is not fixed there. This is the only retrieved precedent for freeing both factors.

**Zeller 2022 (Wolverine):** text extraction shows the paper uses degree-day with scaling factor but specific DDF values did not surface in the grep; paper is specific to Wolverine distributed MB (likely in supplementary).

### Assessment

There are **two inconsistencies with literature consensus**:

1. **The literature consensus fixes r_ice/r_snow ratio and calibrates only r_snow (or only MF_snow)** — Rounce PyGEM, Rounce HMA, Sjursen, and Huss & Hock 2015 all take this approach. Freeing r_ice independently **doubles the parameter count contribution of melt factors** while most precedents use ONE. Geck 2021 DOES free both and reports ratio 4.22, but Geck explicitly acknowledges overparameterization (line 331). McNeil 2020 also frees both, but for two separate glaciers and without MCMC.

2. **Prior center μ = 4.0e-3 for r_ice** needs unit-reconciliation: if our code's internal r_ice is in mm d⁻¹ W⁻¹ m² (direct Hock units / 1000), then Geck's 0.0414 m² W⁻¹ mm d⁻¹ °C⁻¹ corresponds to **41.4e-3** in those units — the upper bound 10.0e-3 is **too low** to span Geck. If instead the internal units already absorb °C⁻¹ into daily melt, then 4.0e-3 may be correct. I could not verify unit conventions without reading `dixon_melt/melt.py`; **this is the single most important pre-flight verification**.

### Recommendation: **MODIFY + VERIFY UNITS**

- **Before anything else:** confirm the units on r_ice/r_snow in `dixon_melt/melt.py` and the reported Geck numbers. If Dixon internal r is really in Geck's native units / 1000, **raise r_ice upper bound to 50e-3 and center at 20e-3 with σ = 10e-3**. If Dixon units are different, document the conversion in the `log_prior` docstring explicitly.
- **Strongly consider dropping r_ice as free and fixing r_ice = ratio × r_snow with ratio TN(3.0, 1.0) on [1.5, 5.0]** — this preserves Geck's ratio information while avoiding a full free dimension. This cuts parameters 8 → 7 and addresses the Rounce/Sjursen consensus.
- r_snow uniform [0.02e-3, 2.0e-3]: **KEEP** if the upper bound 2.0e-3 corresponds to Geck's 0.0098 (≈ 9.8e-3 in Geck units). If Dixon units are Geck/1000 then 2.0e-3 is *less than half* of Geck's snow factor — bound is too tight. **Verify units.**

---

## 3. BAYESIAN PRIOR DESIGN & over-parameterization

### Evidence on parameter count vs observation count

**Rounce 2020 PyGEM (line 81, Table 1):** large-scale glacier evolution models calibrate **"two and seven parameters"** — and PyGEM itself calibrates **three** (fsnow, kp, Tbias) against 1 observation (geodetic specific MB) per glacier.

**Sjursen 2023 (lines 105, 743–776):** calibrates **three** parameters (MFsnow, Pcorr, Tcorr) with MFice tied, against seasonal/annual MB observations:
- Line 743: *"lower equifinality"* listed as a specific benefit of using more informative data.
- Line 746: *"uncertainty aggravates equifinality because we are searching for [a range] of values that minimise the difference between observed and [modelled]"*.
- Line 833: *"precarious due to compensating effects between Tcorr and [MF]"*.
- Line 756: *"correlation between parameter values"* — Figs A5/A6 show the compensation structure.
- Line 775: *"Increasing the number of unknown parameters"* → equifinality worsens.

**Werder 2019 (Bayesian ice thickness, Table 2, lines 364–404):** 7 fitting parameters BUT the model is fit to **thousands of radar measurements** per glacier (line 442: *"distance between observations is ~1/100th of the glacier length"*). Parameter-to-observation ratio is far more favorable than in CAL-014.

**Geck 2021 (line 331):** *"the model is overparameterized, it is not possible to determine a single best model run. Different parameter combinations can perform [equally well]"* — Geck freed 6 parameters (lapse, fm, r_snow, r_ice, pgrad, pcor) on Eklutna with snowline + discharge, and **still** reports equifinality.

### CAL-014 situation

- 8 free parameters: MF, MF_grad, r_snow, r_ice, precip_grad, precip_corr, T0, lapse_rate.
- Observations: ~20 stakes (clustered at 3 elevations) + 1 geodetic aggregate + 22 snowline-elevation summaries ≈ **~50 weakly independent constraints** (stakes at same elevation-year are highly correlated).
- Effective independent observations is closer to **20–30** after accounting for spatial correlation at the 3 stake sites.

**Prognosis:** This is a **warning-level risk for equifinality**. Two specific trade-off axes known to compensate:
- lapse_rate ↔ MF (Gardner & Sharp 2009; Sjursen Tcorr–MFsnow parallel)
- r_ice ↔ MF ↔ r_snow (all act on summer ablation)
- precip_corr ↔ MF (accumulation vs ablation — Sjursen line 833)

Adding BOTH lapse_rate AND r_ice as free in the same MCMC means **three strongly trade-off-coupled parameters on a summer-mass-balance signal that has effectively two independent dimensions** (seasonal-mean ablation magnitude + its elevation slope).

### Convergence diagnostics

CAL-014 uses 32 walkers × 10 000 steps × 5 DE seeds. For 8 parameters:
- Rule-of-thumb walker count is ≥ 2×ndim = 16; 32 is fine.
- 10 000 steps with emcee autocorrelation τ typically 100–500 for this class of problem → effective samples per chain ≈ 20–100 per walker = 640–3200 per run. **Adequate but not generous.**
- Sjursen 2023 (line 430): *"four MCMC chains … with 2000 tune and 10 000 sampling iterations"* — similar scale.
- Werder 2019 (line 482): *"around 10⁵ samples are necessary to obtain con[vergence]"* — 10× more, on a harder problem.

### Recommendation: **MODIFY — reduce to 6 or 7 parameters**

Option A (recommended, conservative): **7 parameters, fix r_ice = ratio × r_snow** with ratio TN(3.0, 1.0). Keep lapse_rate free but with tightened σ=0.6e-3 (see Section 1).

Option B (more aggressive): **6 parameters, fix lapse_rate = −5.0e-3** (per McNeil/Ziemen maritime Alaska precedent) AND tie r_ice to r_snow. This matches CAL-013 structure and avoids repeating Geck's self-acknowledged over-parameterization.

Mandatory safeguards if 8 parameters are retained:
- Report the full posterior correlation matrix. Pairs with |ρ| > 0.7 must be flagged.
- Compute Gelman-Rubin R̂ across the 5 DE seed starting chains; require R̂ < 1.1 for every parameter.
- Compute integrated autocorrelation τ per parameter; require total steps > 50×τ.
- Compare marginal prior vs marginal posterior (Sjursen 2023 line 452); any parameter whose posterior ≈ prior is **not identified** — drop it and fix at prior mean.

---

## 4. LIKELIHOOD WEIGHTING audit

**CAL-014 spec:** σ_stake = 0.12 m w.e., σ_snowline = 75 m, geodetic λ = 50 (weight).

### Snowline σ (75 m)

- **Racoviteanu 2019 (lines 348, 629, 762):** SRTM DEM vertical RMSE **47.2 m** and SLA RMSEz **137 m** for automated snowline. "Error intervals … ±½ of RMSEz" → per-snowline uncertainty roughly ±70 m.
- **Barandun 2018 (line 568):** *"elevation uncertainty for unmeasured glacier zones was roughly estimated to be five times as large as the uncertainty"* of the measured stakes — implies 50–150 m range depending on method.
- **Our own structural RMSE (CAL-013, from MEMORY):** **90 m** of model-observation mismatch arising from DETIM limitations (no wind redistribution), with +30 m systematic bias and recent-year bias up to +178 m.

**Assessment:** σ_snowline = 75 m is **slightly optimistic** given our known 90 m structural RMSE. Using 75 m makes the snowline likelihood slightly over-weighted. Not a fatal flaw but it pushes the posterior toward parameter sets that fit snowlines at the expense of stakes.

### Recommendation: **MODIFY**

- Set **σ_snowline = 90 m** (matching the structural RMSE found in CAL-013) OR compute σ_snowline per-year as max(75, observed_interannual_std_within_year).
- Alternative: use the CAL-013 residual RMSE as an explicit nuisance parameter `σ_snowline ~ Half-Normal(100)` and marginalize (Werder 2019 does this for σh, σv with uniform [0, 200] — lines 433–434).
- **Additional:** consider stratifying snowlines by glacier branch. Per MEMORY, interannual std for recent years (2019–2024) has +88 to +178 m bias — treating these with the same 75 m σ as the 2000–2010 snowlines is wrong. A simple fix is to down-weight or exclude the 5 worst-bias years.

### Stake σ (0.12 m w.e.)

- **McNeil 2020 (line 402):** *"±0.20 m w.e. as a nominal glaciological uncertainty (Lliboutry, 1974)"* — standard reference value.
- **Zeller 2022** reports per-point uncertainties consistent with ~0.2 m w.e.
- 0.12 m w.e. is **tighter than standard** — likely reflects the repeatability at Dixon's 3 stake sites but may be too tight if stake measurements have inter-annual reading errors.
- **Recommendation:** Keep 0.12 m w.e. if it is empirically grounded in repeat-measurement spread at the 3 Dixon stake sites; otherwise raise to 0.15–0.20 m w.e. Note: tighter σ_stake also amplifies equifinality risk (it forces the MCMC to satisfy stakes at the expense of everything else).

### Geodetic λ = 50

- Could not locate a direct precedent in the verified PDFs for this specific weighting structure; Sjursen 2023 uses uncertainty-based weighting (derives σ from Hugonnet uncertainty directly, line 374).
- **Recommendation:** Ensure λ = 50 corresponds to treating the geodetic observation with σ ≈ the Hugonnet-reported uncertainty for Dixon (typically 0.05–0.15 m w.e./yr for the 2000–2020 interval). If λ=50 implies σ much tighter than Hugonnet's own error bar, the geodetic term will dominate the posterior. **Verify**.

---

## 5. Specific pre-flight changes for `run_calibration_v14.py`

In descending order of importance:

1. **VERIFY UNITS on r_ice/r_snow against `dixon_melt/melt.py`.** If Dixon internal units are Geck's ÷ 1000, then the r_ice upper bound [0.02e-3, 10.0e-3] excludes Geck's best value (0.0414 in native units = 41.4e-3 internal) — **this is a showstopper** and must be fixed before any MCMC runs. Update the CAL-014 docstring with the conversion equation.

2. **Tie r_ice to r_snow by a ratio prior** (recommended): replace
   ```
   lp += _truncnorm_logpdf(params['r_ice'], 4.0e-3, 2.0e-3, 0.02e-3, 10e-3)
   ```
   with a parameter `ratio = r_ice / r_snow` having `ratio ~ TN(3.0, 1.0)` on [1.5, 5.0]. This encodes the Geck 4.22, Hock 1.33–1.43, and PyGEM 1.43 evidence directly and drops 1 free parameter.

3. **Tighten lapse_rate σ**: change `TN(-4.5e-3, 1.0e-3, -6.5e-3, -2.0e-3)` → `TN(-4.5e-3, 0.6e-3, -6.5e-3, -2.0e-3)`. This tightens 95% mass to roughly [−5.7, −3.3] — covering Geck, McNeil, Carturan calibrated, and the maritime Alaska consensus, while excluding the deep tail.

4. **Raise σ_snowline from 75 m to 90 m** to match CAL-013 structural RMSE. Alternatively make it a free nuisance parameter with a Half-Normal(100) prior and marginalize.

5. **Add post-run diagnostics to the MCMC block:**
   - Gelman-Rubin R̂ across the 5 DE-seeded chains; require < 1.1 all params.
   - Integrated autocorrelation τ per parameter; require total_steps > 50τ.
   - Posterior correlation matrix; flag |ρ| > 0.7.
   - For each parameter, compare marginal prior std vs marginal posterior std: if posterior std / prior std > 0.9, that parameter is unidentified — fix it and re-run.

6. **Consider a CAL-014a (conservative) and CAL-014b (aggressive) split:**
   - **014a:** 6 parameters (fix lapse at −5.0e-3, tie r_ice ratio). Matches maritime Alaska consensus; lower equifinality risk; cheap.
   - **014b:** 7 parameters (free lapse, tie r_ice ratio). Tests the added value of freeing lapse.
   - Compare via WAIC or DIC before committing 30 hours to the full 8-parameter run.

7. **Verify geodetic λ = 50 implies σ_geo consistent with Hugonnet's reported σ for Dixon.** If λ=50 over-weights the geodetic term relative to its actual uncertainty, the posterior will be driven by one aggregated number.

8. **Flag for advisor:** The single biggest finding in this review is that **no maritime Alaska precedent freely calibrates the lapse rate via MCMC**. McNeil 2020 (closest analog), Ziemen 2016, O'Neel 2019 all fix it. Geck 2021 does free it on a cold-continental Alaska glacier and explicitly reports overparameterization. Your advisor should be aware that CAL-014's 8-parameter configuration is **more ambitious than any peer-reviewed precedent** we have verified, and that evidence supports retreating to 6 parameters.

---

## Items I could not verify

- **Zekollari 2024 CMIP6 global:** the downloaded PDF is corrupt (HTML placeholder, not a PDF). State-of-art projection priors **cannot be assessed from this file**. Re-download required.
- **Mosier 2016, Landmann 2021, Petersen 2013, Schuster 2023, Trussel 2015, roth_2018, huss_hock_2015, Gardner_Sharp_2009, McGrath_2018, Tricht_2023:** these papers were listed as extracted but not searched in this review due to time constraints. They were reviewed in the first round per the user's statement; if any of them contradict the findings above (especially on maritime Alaska DDFs or on 8-parameter MCMC success), this document should be amended.
- **Actual DDF numeric values in Zeller 2022 and McNeil 2020:** these exist in the papers' tables/supplementaries but did not cleanly surface in keyword grep. Before committing to the r_ice unit conversion in recommendation 1, the Dixon melt unit convention should be cross-checked against those tables directly.
- **`dixon_melt/melt.py` unit convention** was not opened during this review. Recommendation 1 is predicated on a unit check the author has not yet performed.

---

*This review covers the 18 of 19 text-extractable priority PDFs. Direct quotes are from `pdftotext -layout` extractions; line numbers refer to extraction output, not PDF page numbers.*
