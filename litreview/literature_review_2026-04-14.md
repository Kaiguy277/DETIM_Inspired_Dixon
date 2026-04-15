# Literature Review — Dixon Glacier DETIM Calibration Strategy
**Date:** 2026-04-14
**Author:** K. Myers (with AI synthesis support)
**Purpose:** Evaluate whether the current DETIM calibration design (CAL-013, D-028) is defensible against the published literature, with particular attention to advisor (Dr. Geck) concerns about (a) fixed lapse rate, (b) fixed r_ice/r_snow ratio, (c) snowline likelihood vs branch-segmented validation, and (d) ice-thickness dataset choice.

---

## 1. Executive Summary

**Bottom line:** The current calibration design (multi-objective Bayesian DE+MCMC over 6 parameters with stakes + geodetic + snowlines, post-hoc area filter) is methodologically modern and defensible in its overall *framework*, but it is mis-specified in three places where the literature is unambiguous:

1. **Lapse rate is the single most-sensitive forcing parameter** in distributed temperature-index models. Fixing it at -5.0 °C km⁻¹ is at the steep end of measured on-glacier values and biases melt high. Geck (2021) calibrated lapse rate over Eklutna and obtained mode -3.0 °C km⁻¹ (range -2 to -6). Gardner & Sharp (2009) showed using the moist adiabatic lapse rate (-6.5) instead of a measured/variable rate gives mass balance ~4× more negative for the same DDFs. Schuster (2023) explicitly identifies lapse rate choice as one of the largest sources of *projection* spread among 18 TI-model variants. **Recommendation:** Free the lapse rate as a calibrated parameter with a Gaussian prior centered on -4.5 °C km⁻¹, σ = 1.0, bounded [-2.0, -6.5].

2. **r_ice / r_snow should be calibrated independently, not fixed at 2.0.** Geck (2021) calibrated r_ice and r_snow as independent parameters and found best performers at r_ice = 0.0144 m² mm W⁻¹ °C⁻¹ d⁻¹ and r_snow = 0.0042; the implied ratio is ~3.4, well above our 2.0. Pellicciotti-style ETI literature consistently shows r_ice / r_snow ≈ 3–4 because of the albedo contrast (snow ≈ 0.7, bare ice ≈ 0.3–0.35). Schuster (2023) found that "no surface-type distinction" gives systematically more negative MB and worse calibration than treating snow and ice separately. **Recommendation:** Calibrate r_ice and r_snow as two independent parameters with priors centered on Geck's Eklutna best-fits.

3. **Multi-objective Bayesian framework with snowlines in likelihood is best practice** (Sjursen 2023, Geck 2021), but our σ_snowline = 75 m may be too tight given the 90 m structural RMSE we already measured (D-028). Sjursen (2023) uses σ_obs derived from independent reanalysis uncertainty (their Table 2: σ_Bw 0.06–0.19, σ_Bs 0.15–0.34, σ_Ba 0.10–0.34 m w.e.) — i.e., uncertainties scale with the actual observation type and its known error budget rather than being assumed. Our σ_stake = 0.12 m w.e. is broadly consistent with their summer balance σ ≈ 0.15–0.34 (we have less spatial sampling per year so the lower σ may be optimistic). **Recommendation:** Inflate σ_snowline to ≥ 90 m (the residual RMSE floor we cannot reduce) and consider the 3-section branch-stratified likelihood Geck verbally suggested.

**Priority of changes (highest to lowest):**
- P1 (must fix): Free lapse rate (single most-supported recommendation in the literature).
- P1 (must fix): Calibrate r_ice and r_snow independently (Geck's specific request, well-supported).
- P2 (should do): Inflate σ_snowline to honest residual; add per-branch snowline term.
- P3 (nice to have): Compare IceBoost vs Farinotti ice thickness for the dynamics module (already in progress per `compare_iceboost_farinotti.py`).
- P4 (defer): Variable monthly lapse rate is supported by Gardner & Sharp and Petersen but requires data we don't have on Dixon; a calibrated *constant* rate is the practical compromise.

---

## 2. Paper-by-Paper Synthesis

### 2.1 Geck et al. (2021) — Eklutna Glacier, Alaska
**Citation:** Geck, J., Hock, R., Loso, M.G., Ostman, J., Dial, R. (2021). *Modeling the impacts of climate change on mass balance and discharge of Eklutna Glacier, Alaska, 1985–2019.* Journal of Glaciology 67(265), 909–920.

**Model:** DETIM ("Distributed Enhanced Temperature Index Model"), Hock 1999 Method 2. Same model family as Dixon work — directly comparable.

**Lapse rate (γ):** *Calibrated*, not fixed. p. 913 Fig. 4 caption: "The temperature lapse rate γ ranged from -0.6 to -0.27 °C (100 m)⁻¹ with a mean of -0.3 °C (100 m)⁻¹ and a mode of -0.2 °C (100 m)⁻¹." That is -2 to -6 °C km⁻¹, mean -3, mode -2. **This is the empirical evidence for the advisor's concern.** Our fixed -5.0 °C km⁻¹ is at the steep end of this distribution.

**r_ice / r_snow:** *Both calibrated independently.* p. 913 Fig. 4: "All melt factors ranged from 3.75 to 6.00 mm d⁻¹ °C⁻¹ with the most frequent values being 5.75 and 6.00 mm d⁻¹ °C⁻¹. The radiation factor for ice was distributed across three values between 0.0242 and 0.414 m² W⁻¹ mm °C⁻¹ d⁻¹"; for snow the best-performing value was 0.0042 m² W⁻¹ mm d⁻¹ °C⁻¹ (p. 914 Fig. 6 caption: "r_snow = 0.0042 m² W⁻¹ mm °C⁻¹ d⁻¹, r_ice = 0.0144"). **Implied ratio r_ice/r_snow = 0.0144 / 0.0042 = 3.43**, not 2.0. Our fixed 2.0 ratio is biased low.

**Calibration strategy:** Random search over 25,062 parameter combinations; selected the top 250 by jointly minimizing z-score of stake RMSE *and* z-score of snowline RMSE (eqn 4, p. 913). Cross-validated against discharge (R² = 0.77 averaged over 8 years). Six parameters varied: γ, f_m (melt factor), r_snow, r_ice, p_grad, p_cor (p. 913 Fig. 4 — exactly Geck's six free parameters).

**Observations:** 14 stake locations (1985–2010 winter + summer point balances), 50 snowlines from satellite imagery, geodetic mass balance from Sass et al. (2017a), discharge from West Fork Eklutna River. Multi-objective.

**Key relevance:** "Calibrating the model to the combined dataset of summer and winter point balances to capture the effects that melt parameters have on winter balance, for example, due to winter melt events, and precipitation parameters on summer balance, for example, due to summer snowfall events" (p. 912). p. 916: "Results from model calibration indicate the value of using multi-criteria validation that includes the use of a geodetic mass-balance constraint, point balances and snowline positions. Even after a geodetic constraint, the point balances alone were not well-constrained, as the comparison between modeled and observed point balances found 95% of individual parameter set model runs had an r² > 0.90 (n = 25 062). This suggests that selecting the best model parameters based solely on point balances is not sufficient."

**Equifinality discussion (p. 913):** "Different parameter combinations can perform equally well in reproducing the observations. For example, overestimation of melt can be compensated by an overestimated degree-day factor (DDF) which can be compensated by an underestimated precipitation correction factor."

### 2.2 Sjursen et al. (2023) — Bayesian calibration on 7 Norwegian glaciers
**Citation:** Sjursen, K.H., Dunse, T., Tambue, A., Schuler, T.V., Andreassen, L.M. (2023). *Bayesian parameter estimation in glacier mass-balance modelling using observations with distinct temporal resolutions and uncertainties.* Journal of Glaciology 69(278), 1804–1820.

**Model:** Distributed temperature-index model with snow/ice DDF separation. Three free parameters in MCMC: P_corr, T_corr, MF_snow (p. 1807). They fix r_ice/r_snow ratio (their MF_ice / MF_snow is fixed at 2 — same as our setup).

**Lapse rate:** Held constant per glacier (taken from seNorge2018 reanalysis). They do *not* calibrate it because the seNorge product already supplies a defensible value. This is a different design choice than Dixon — they have a high-quality regional reanalysis to lean on; we have one SNOTEL.

**r_ice/r_snow:** Fixed at 2 (their footnote on parameter table, p. 1806: "f_ice = 2 · MF_snow"). Same as our current setup. This shows fixing the ratio is a common simplification *but* Sjursen has the luxury of seasonal balance observations that help pin both melt and accumulation; Geck's preference for free r_ice and r_snow reflects a more data-rich calibration.

**Calibration strategy:** Markov Chain Monte Carlo (emcee) with weakly informative Gaussian priors. Three experiments: B_w/s (winter+summer balances), B_a (annual only), B_10yr (decadal geodetic only). Likelihood is Gaussian with σ derived from independent reanalysis of glaciological observations:

Table 2, p. 1807: σ_Bw = 0.06–0.19, σ_Bs = 0.15–0.34, σ_Ba = 0.10–0.34 m w.e. (per glacier, derived from Andreassen et al. 2016); σ_B10yr = 0.26–0.31 m w.e. (Hugonnet uncertainty propagation).

**Key findings:**
- p. 1808: "the higher temporal resolution of B_w/s gives the best constraint on θ" — winter+summer balances constrain parameters far better than annual or decadal data.
- p. 1810: "PDFs of posterior predictive samples do not encompass the PDF of observations" — even with MCMC, posterior predictive intervals can fail to cover real interannual spread (a humility check for our work).
- p. 1812: "B_a appears to systematically favour mass-balance scenarios characterised by low ablation and low accumulation" — *equifinality* warning when only annual data are used.

**Relevance to Dixon:** Their σ_stake values (0.06–0.34 m w.e.) bracket our σ = 0.12 — defensible but on the lower (more confident) end. Their decadal geodetic σ of 0.26–0.31 is similar to what we should adopt for the Hugonnet constraint (we should check that our likelihood formulation matches).

### 2.3 Schuster, Rounce & Maussion (2023) — TI model choices in projections
**Citation:** Schuster, L., Rounce, D.R., Maussion, F. (2023). *Glacier projections sensitivity to temperature-index model choices and calibration strategies.* Annals of Glaciology 64(92), 293–308.

**Model:** OGGM framework, 18 TI-model variants × 5 calibration strategies × 88 reference glaciers globally.

**Lapse rate:** Two choices compared (Table 1, p. 296): "constant -6.5 K km⁻¹" vs "variable, derived from ERA5 (spatially & seasonally variable, but constant over years)". Found (p. 297): "the calibrated degree-day factor is smaller for the variable lapse rate choice than the constant choice... the variable lapse rate is, in our case, mostly less negative than the constant choice (median of -5.6 K km⁻¹ versus -6.5 K km⁻¹)... The temperature-index model performed best on MB profile mean absolute error since neither the variable lapse rate nor the temperature bias is given more flexibility (Table 1)." **The variable lapse rate variant systematically reduces calibrated DDF, in line with Gardner & Sharp.**

**r_ice / r_snow surface-type distinction:** Three choices (Table 1): (i) no distinction, (ii) negative exponential decay with cumulative T_max, (iii) linear from f_snow at T < -0.5 °C to f_ice at T > 0 °C, with f_ice = 2 · f_snow. They do *not* calibrate the ratio independently but explicitly note (p. 296): "for any further degree-day factor increase from snow to ice, two new parameters are introduced: f_snow and the rate at which f_snow increases with cumulative T_max."

p. 298: "Without surface-type distinction, melt increases linearly with CPDD, which is a further enhanced with surface-type distinction (Figs. 2a,c). Consequently, the specific MB also strongly decreases, which is further reduced when winter or summer precipitation anomalies correlate in our experiment with melt and precipitation, and the resulting snow on the ablation area." Surface-type distinction matters for projection spread.

**Calibration:** Five strategies (C1–C5, Table 2, p. 296). Most-informed C1 uses geodetic + average winter MB + interannual MB variability + MB profile (calibrating p_f, t_b, df). Reference for OGGM is C5 (geodetic only).

**Key findings on projection sensitivity:**
- p. 301 Fig. 6b: "temperature lapse rate choice" produces volume-ratio (variable/constant) range of ~0.67–1.5 by 2100 → **±50% projected glacier volume difference attributable to lapse rate choice alone.** This is comparable to the spread from GCM choice.
- p. 302: "The temperature lapse rate choice has the most systematic influence... using the variable lapse rate (in 19% (4–38% percentile range) in 2100 under SSP1-2.6 in Fig. S15b). As the glaciers retreat to higher elevations, the calibrated degree-day factors (Fig. 1) do not counteract the increase impact of the less negative lapse rate using the variable choice in more complex MB models."

**Bottom line for Dixon:** Lapse rate choice is a *projection-sensitive* parameter. Fixing it at -5.0 means our projections inherit a structural bias.

### 2.4 Petersen et al. (2013) — Suitability of constant lapse rate
**Citation:** Petersen, L., Pellicciotti, F., Juszak, I., Carenzo, M., Brock, B. (2013). *Suitability of a constant air temperature lapse rate over an Alpine glacier: testing the Greuell and Böhm model as an alternative.* Annals of Glaciology 54(63), 120–130.

**Site:** Haut Glacier d'Arolla, Switzerland; 5 AWS + 9 T-loggers along flowline.

**Findings:**
- p. 122 Fig. 2: Constant calibrated linear lapse rate (CLRcal) = -0.0032 °C m⁻¹ (= -3.2 °C km⁻¹). Much shallower than ELR. RMSE = 1.26 °C with CLRcal vs 1.39 with ELR.
- p. 123: "Below 2900 m a.s.l. on the glacier tongue, LRs are highly variable but frequently strongly negative, particularly when katabatic winds develop."
- p. 128 Conclusion: "Use of a constant LR is inappropriate at most locations and in most conditions, whereas GBvarH better captures the shape of the temperature profile along the flowline... The model does not, however, work well for cloudy, cold conditions, when the fit between modeled and observed average temperatures is poorer at TL8."

**Relevance:** Even a "constant calibrated" lapse rate is a major improvement over a free-air or moist-adiabatic value. The calibrated value Petersen finds (-3.2 °C km⁻¹) is essentially identical to Geck's mode for Eklutna (-3 °C km⁻¹). Two independent on-glacier studies in different climates converge on a value about 60% of our current fixed value.

### 2.5 Gardner & Sharp (2009) — DDM sensitivity to lapse rate
**Citation:** Gardner, A.S., Sharp, M. (2009). *Sensitivity of net mass-balance estimates to near-surface temperature lapse rates when employing the degree-day method to estimate glacier melt.* Annals of Glaciology 50(50), 80–86.

**Site:** Devon Ice Cap, Canadian Arctic. 26-year DDM simulation.

**Lapse rate experiments:** Three runs:
- VLR (variable daily, derived from 750 mbar T): mean MB = -333 ± 120 mm w.e./yr
- MMLR (mean measured summer = -4.9 °C km⁻¹): MB = -510 mm w.e./yr (~50% more negative)
- MALR (moist adiabatic = -6.5 °C km⁻¹): MB = -1300 mm w.e./yr (~4× more negative)

**Direct quote (p. 86):** "DDMs are highly sensitive to the choice of lapse rate when models are forced with downscaled temperature fields. For the DDM used in this study, use of a variable daily lapse rate estimated from lower-tropospheric (750 mbar) temperatures to downscale surface air temperatures gives significantly better mass-balance estimates than a constant lapse rate equal to either the summer mean or the moist adiabatic lapse rate."

**On compensation by tuning DDFs (p. 85):** "Model root-mean-square errors similar to those achieved when the DDM is forced with a variable lapse rate could be achieved by adjusting the degree-day factor for ice to 4.5–6.5 and 2–3.5 mm w.e. d⁻¹ when employing the mean measured summer lapse rate and the moist adiabatic lapse rate, respectively. When comparing against previously published values (Hock, 2003), a degree-day factor < 5.0 mm w.e. d⁻¹ for ice is unrealistic. Therefore, the model can only be tuned with a realistic degree-day factor for ice to produce comparable results to those achieved using the untuned variable lapse rate when the mean measured summer lapse rate is employed."

**Implication for Dixon:** Our calibrated MF = 7.30 mm w.e. d⁻¹ °C⁻¹ is at the high end of plausible — exactly what you'd expect if MF is compensating for a too-steep lapse rate. **This is direct empirical evidence that our high MF is partially an artifact of the fixed -5.0 °C km⁻¹ lapse rate.**

### 2.6 Landmann et al. (2021) — Particle filter ensemble assimilation
**Citation:** Landmann, J.M., Künsch, H.R., Huss, M., Ogier, C., Kalisch, M., Farinotti, D. (2021). *Assimilating near-real-time mass balance stake readings into a model ensemble using a particle filter.* The Cryosphere 15, 5017–5040.

**Approach:** Ensemble of *four* different TI/SEB models (BraithwaiteModel, HockModel, PellicciottiModel, OerlemansModel) running 10,000 particles each. Particle filter assimilates camera-derived stake readings.

**Lapse rate:** Bayesian prior derived from t-distribution fit (Eq. 3, p. 5021), with samples drawn at *each* gridcell. Lapse rate is treated as uncertain and updated with observations — *not* a fixed scalar.

**r_ice/r_snow:** Each model has its own DDFs. For HockModel (Eq. 8): MF + a_snow_ice · I_pot, with separate snow/ice radiation parameters. From Table 2 (p. 5027): MF = 1.77–2.85 mm w.e. K⁻¹ d⁻¹, a_ice = 0.009–0.030. **The four-model ensemble approach explicitly acknowledges that no single TI structure is correct.**

**Relevance:** Ensemble-of-structures is more rigorous than any single-model calibration. Reasonable inspiration for our future work but heavier than what we need for thesis. Their σ approach for stakes (~5 cm = 0.05 m snow depth → 0.05 × ρ_snow ≈ 0.02 m w.e.) is *much* tighter than ours because they have direct physical observations.

### 2.7 Mosier et al. (2016) — How much complexity is right?
**Citation:** Mosier, T.M., Hill, D.F., Sharp, K.V. (2016). *How much cryosphere model complexity is just right? Exploration using the Conceptual Cryosphere Hydrology Framework.* The Cryosphere 10, 2147–2171.

**Sites:** Gulkana and Wolverine glaciers (Alaska).

**Models compared:** SDI (degree-index), ETI(H) (Hock 1999 enhanced), ETI(P) (Pellicciotti 2005), LST (longwave-shortwave-temperature). Calibrated against MODIS snow-covered area, ICESat elevation, and USGS streamflow.

**Key finding:** "the best performing models are those that are more physically consistent and representative, but no single model performs best for all of our model evaluation criteria" (Abstract). For Wolverine specifically, ETI(H) (= our model family) and ETI(P) outperform SDI (degree-day-only). At Gulkana, results are mixed because of less reliable albedo.

**Relevance:** Validates the *choice* of DETIM (= ETI(H)) for an Alaska glacier — Wolverine is climatologically the closest USGS benchmark to Dixon (maritime Kenai). But the work also confirms that no calibration is perfect and equifinality is intrinsic.

### 2.8 Trüssel et al. (2015) — Yakutat Alaska DETIM
**Citation:** Trüssel, B.L., Truffer, M., Hock, R., Motyka, R.J., Huss, M., Zhang, J. (2015). *Runaway thinning of the low-elevation Yakutat Glacier, Alaska, and its sensitivity to climate change.* Journal of Glaciology 61(225), 65–75.

**Model:** DETIM (same model family). Fixed lapse rate -0.0064 °C m⁻¹ (= -6.4 °C km⁻¹), free-air rate. Calibrated MF, p_corr, p_grad, a_snow, a_ice (radiation factors; same Hock 1999 structure as Geck and us).

**Calibration approach:** "We perform a grid search for these parameters, with each varied within wide but physically plausible ranges" (p. 70 col 2). "First we determined a sub-set of 15 best-performing parameter sets... then chose those that produced the right area-averaged value of 0.1 m w.e. a⁻¹." Uses point balances + geodetic difference. **No Bayesian framework; pure grid search with multi-criteria filter.** Our DE+MCMC is more rigorous.

**Lapse rate:** Fixed at -6.4 °C km⁻¹ (free-air), explicitly noted as a simplification: "DETIM is fed with daily climate data, and calculates surface mass balance for each gridcell of a DEM. Temperature data at YG station are extrapolated to the grid using surface elevation and a lapse rate. This part is independent of calibration." This is the exact design choice Geck moved away from in his 2021 paper.

**r_ice/r_snow:** Both calibrated as separate radiation factors a_snow and a_ice (Fig. 7, p. 71), best values a_snow ≈ 0.0144, a_ice ≈ 0.0264 → ratio 1.83 (close to our 2.0 but obtained as a free fit, not fixed by assumption).

### 2.9 Tricht & Huybrechts (2023) — Tien Shan with 3D ice flow
**Citation:** Van Tricht, L., Huybrechts, P. (2023). *Modelling the historical and future evolution of six ice masses in the Tien Shan, Central Asia, using a 3D ice-flow model.* The Cryosphere 17, 4463–4485.

**Mass balance:** Simplified energy balance (not pure DETIM); calibrates MF, c_0, c_1 against mass-balance stakes. Less directly comparable to our DETIM but shows the trend in modern Alaska/Asia work to couple SMB with explicit dynamics. Lapse rate handling is glossed in the methods.

**Relevance:** Demonstrates that for projections, *coupling SMB to a dynamical glacier evolution* is the publication-grade move. Our `glacier_dynamics.py` module + projection pipeline already does this in simplified form (Δh-parameterization, Huss et al. 2010).

### 2.10 Huss & Hock (2015) — GloGEM global model
**Citation:** Huss, M., Hock, R. (2015). *A new model for global glacier change and sea-level rise.* Frontiers in Earth Science 3, 54.

**Model:** GloGEM, simple temperature-index (degree-day on monthly time series). Globally applies *constant* monthly lapse rates (12 values, p. 5: "Air temperature is extrapolated to all glacier elevation bands using a set of twelve constant monthly temperature lapse rates (Section 2.3)"). Uses ERA-Interim 2 m air T from 1000/500 hPa pressure-level T differences (p. 4 §2.3.1).

**Calibration:** Three-step sequential (p. 8, Fig. 2A): (1) tune c_prec to match average winter MB, (2) tune f_snow to match annual MB (with f_ice = 2 · f_snow held fixed), (3) tune ΔT_air to match regional mean. Single-glacier point matching is *not* MCMC; sequential point-tuning. Less rigorous than our setup but operates at 200,000-glacier scale.

**Relevance:** Justifies the "f_ice = 2 · f_snow" simplification *at global scale* where Geck-style independent calibration is infeasible. At a single-glacier thesis study, however, the simplification is unjustified.

### 2.11 O'Neel et al. (2019) — USGS Benchmark reanalysis
**Citation:** O'Neel, S., et al. (2019). *Reanalysis of the US Geological Survey Benchmark Glaciers: long-term insight into climate forcing of glacier mass balance.* Journal of Glaciology 65(253), 850–866.

**Sites:** Gulkana, Wolverine, Lemon Creek, South Cascade, Sperry. Wolverine is the most climatologically relevant analogue for Dixon (maritime Kenai).

**Method:** Reanalysis combining glaciological stake measurements with geodetic calibration via piecewise-linear balance profile fitting (p. 854 Fig. 3). Not a TI model — this is a reanalysis. They use a "regional mean adiabatic degree-day rate of -6.5 °C km⁻¹" (p. 854 §4.2) as a default lapse rate where they need to fill — confirming that field practitioners default to MALR when not calibrating.

**Wolverine cumulative MB** (Fig. 4b, p. 857): -0.37 ± 0.23 m w.e./yr 1966–2018, -0.77 m w.e./yr post-1990. Useful as a regional reality-check for our Dixon projections.

**Lapse rate sensitivity (p. 856):** "adjusting the lapse rate by 1 °C only impacted solutions by 10⁻² m a⁻¹, whereas the differences between geodetic calibrations are 10⁻¹ to 10⁰ m a⁻¹." For *reanalysis* (where geodetic dominates), lapse rate is relatively unimportant. For *forward modeling* (our case), Schuster and Gardner & Sharp show it dominates.

### 2.12 McGrath et al. (2018) — Snow accumulation variability
**Citation:** McGrath, D., Sass, L., O'Neel, S., McNeil, C., Candela, S.G., Baker, E.H., Marshall, H.-P. (2018). *Interannual snow accumulation variability on glaciers derived from repeat, spatially extensive ground-penetrating radar surveys.* The Cryosphere 12, 3617–3633.

**Sites:** Gulkana, Wolverine. 5 years of GPR.

**Key findings on accumulation gradients:**
- Wolverine SWE elevation gradient: 440 mm/100 m (p. 3625; Fig. 4); Gulkana 115 mm/100 m. **Our calibrated p_grad ≈ 0.05–0.07 (5–7% per 100 m) ≈ on the order of 100 mm/100 m at our Dixon precip range — consistent with Wolverine being much steeper.** For maritime Kenai we should expect Wolverine-like gradients.
- p. 3625 §4.5: "Wolverine exhibited better agreement (4% average difference) among the approaches, with most approaches agreeing within 5% of the six-approach mean (Fig. 13b)... At both glaciers, the estimates using elevation as the only predictor yielded B_w estimates on average within 3% of the six-method mean."
- "Both glaciers exhibited a high degree of temporal stability, with ~85% of the glacier area experiencing less than 25% normalized absolute variability over this 5-year interval" (p. 3617). **Inter-annual snow distribution patterns are stable; this supports using a constant p_grad in calibration.**

**Relevance:** Supports our choice to calibrate a single p_grad rather than year-varying. Validates the single-stake-per-elevation Dixon design as broadly capturing the glacier-wide pattern (within ~7%). Supports our use of snowlines because they reflect this stable accumulation pattern.

### 2.13 Roth et al. (2018) — Juneau Icefield precipitation
**Citation:** Roth, A., Hock, R., Schuler, T.V., Bieniek, P.A., Pelto, M., Aschwanden, A. (2018). *Modeling Winter Precipitation Over the Juneau Icefield, Alaska, Using a Linear Model of Orographic Precipitation.* Frontiers in Earth Science 6, 20.

**Approach:** LT (linear orographic) precipitation model downscaled from WRF. 1 km resolution. Calibrated against 25 snow-pit measurements over 10 years.

**Relevance:** Demonstrates that a simple precip_corr × precip_grad × elevation parameterization (our approach) is a *first-order* model. The LT model captures spatial structure (e.g., NE/SW asymmetry across icefield divides). For Dixon's relatively small footprint, our linear gradient is probably adequate, but if Geck pushes for it, an LT downscale is the upgrade path.

p. 8: "The LT model is based on two simple advection equations that describe cloud water (q_c) and hydrometeor (q_h) formation in a horizontal domain..." Calibration against snow pits. **No DETIM coupling; just precipitation field.**

---

## 3. Comparison Table

| Paper | Model | Lapse rate | r_ice / r_snow | Calibration | Observations |
|---|---|---|---|---|---|
| **Geck 2021** | DETIM (Hock '99 M2) | **Calibrated**, mean -3.0, range -2 to -6 °C km⁻¹ | **Both calibrated independently**; ratio ≈ 3.4 | Random search (25k); top 250 by joint stake+snowline z-score | Stakes, snowlines (50), geodetic, discharge |
| **Sjursen 2023** | Distributed TI | Fixed (seNorge reanalysis) | Fixed (f_ice = 2 · f_snow) | MCMC (emcee), 3 params (P_corr, T_corr, MF_snow), Gaussian likelihood | Winter+summer balances, decadal geodetic |
| **Schuster 2023** | OGGM TI | Both tested: constant -6.5 vs variable ERA5 | Tested with/without surface-type distinction | 5 strategies (C1–C5), reference is geodetic-only | Geodetic + winter MB + interannual + MB profile |
| **Petersen 2013** | Greuell-Böhm + CLR | Calibrated CLR = -3.2 °C km⁻¹; ELR = -6.5 | n/a (T model only) | RMSE minimization | T-loggers along flowline |
| **Gardner & Sharp 2009** | DDM | Three: VLR (variable), MMLR (-4.9), MALR (-6.5) | Fixed (DDF_s = 3.3, DDF_i = 8.2 from Braithwaite '95) | Forward only, not tuned | 23 yr stake transect |
| **Landmann 2021** | Ensemble: 4 TI/SEB | Bayesian, t-distribution prior per gridcell | Model-dependent (each of 4 has own DDFs) | Particle filter (10,000 particles × 4 models) | Camera-stake daily, sub-daily |
| **Mosier 2016** | CCHF: SDI/ETI(H)/ETI(P)/LST | n/a (model intercomparison framing) | varies by model | KGE on streamflow, MODIS SCA, ICESat | Streamflow, MODIS SCA, ICESat |
| **Trüssel 2015** | DETIM | **Fixed** -6.4 °C km⁻¹ (free-air) | **Both calibrated**; ratio ≈ 1.83 | Grid search + multi-filter | Stakes (15), geodetic, terminus |
| **Tricht 2023** | SEB + 3D HO ice flow | Glossed (uses station + lapse) | n/a (SEB) | Hand-tuned MF/c_0/c_1 vs stakes + dh/dt | Stakes, geodetic, dynamics |
| **Huss & Hock 2015** | GloGEM (DDM) | 12 monthly constants from ERA-I pressure-level T | Fixed f_ice = 2 · f_snow | 3-step sequential point match | Regional consensus geodetic |
| **O'Neel 2019** | Reanalysis (not TI) | -6.5 default | n/a | Piecewise-linear profile + geodetic calibration | Stakes, geodetic |
| **McGrath 2018** | Statistical (MVR + tree) | n/a | n/a | OLS regression on terrain | GPR (5 yr), snow pits |
| **Roth 2018** | LT orographic | n/a | n/a | Manual LT params + snow pits | 25 snow pits over 10 yr |
| **Dixon (current, CAL-013)** | DETIM (Hock '99 M2) | **FIXED -5.0 °C km⁻¹** | **FIXED ratio = 2.0** | DE+MCMC, 6 params (MF, MF_grad, r_snow, p_grad, p_corr, T0) | Stakes (25), geodetic (1), snowlines (22 yr), area filter (6) |

---

## 4. Answers to the 5 Specific Questions

### Q1: Should we calibrate the lapse rate?
**Yes, with strong evidence.**

- **Direct evidence:** Geck (2021), Petersen (2013), Schuster (2023) all calibrate or critically test lapse rate; the converged answer for on-glacier alpine/maritime conditions is **-3 to -4 °C km⁻¹**, much shallower than our -5.0.
- **Sensitivity evidence:** Gardner & Sharp (2009) demonstrate ~4× MB sensitivity between MALR and VLR; Schuster (2023) shows ±50% projected volume sensitivity.
- **Compensation evidence:** Our CAL-013 posterior MF = 7.30 (7.06–7.58) is at the upper end of the 5.75–6.00 mode Geck found at Eklutna. This is consistent with Gardner & Sharp's finding that *MF will silently absorb lapse-rate bias*. Our high MF likely contains lapse-rate compensation.

**Defending -5.0:** The only literature support for ≈-5 is the moist-adiabatic-rate-adjacent values used in some global studies (Huss & Hock seasonal lapse) or Trüssel's free-air -6.4 (which Geck himself moved away from). No on-glacier calibration in the recent literature converges on -5.0.

**Recommendation:** Free γ as a 7th calibrated parameter. Prior: N(-4.5, 1.0) °C km⁻¹, hard bounds [-2.0, -6.5]. The center reflects the multi-study mean; the wide σ lets the data speak.

**Should it be monthly variable?** *Ideal but not feasible.* Gardner & Sharp's variable rate requires sub-daily 750 mbar T data; Petersen's requires multi-AWS network. We have one Dixon AWS (summer only) at the ELA. A single calibrated annual constant is the practical compromise the literature supports for our data sparsity. We could test seasonal (DJF vs JJA) lapse if the model can be modified cleanly.

### Q2: Should r_ice / r_snow be calibrated independently?
**Yes — Geck's specific advice is well-supported.**

- **Geck (2021):** explicitly calibrated both, found ratio ≈ 3.4.
- **Trüssel (2015):** explicitly calibrated both, found ratio ≈ 1.8 (close to our 2.0 but obtained as a *free fit*, not assumed).
- **Schuster (2023):** retains the f_ice = 2 · f_snow ratio for tractability across 88 glaciers but explicitly flags that the surface-type distinction *and* its parameterization affect both calibration and projections.
- **Sjursen (2023):** retains f_ice = 2 · f_snow because they have rich seasonal stake data; not a justification for our case where we have only 25 stake-years.

The albedo physics argues for ratio > 2: snow albedo ≈ 0.7, bare ice albedo ≈ 0.3–0.4 → roughly factor 2 difference in absorbed shortwave; combined with the temperature-correlated longwave emission you'd expect closer to 3. **Geck's empirical 3.4 is consistent with the albedo physics; our 2.0 is on the low end.**

**Recommendation:** Add r_ice as a separate calibrated parameter. Prior: N(0.014, 0.005) m² mm W⁻¹ °C⁻¹ d⁻¹ (Geck's mode). Keep r_snow with its own prior centered on 0.0042. **This adds 1 free parameter** (the constraint between them is dropped). Behavior in the calibration: expect MF to drop and r_ice to rise — a re-balancing of how much melt is "T-driven" vs "I-driven".

### Q3: Is our multi-objective Bayesian approach well-supported?
**Yes — our framework is at the modern best-practice level, but we have specific implementation gaps.**

**Where we're aligned with best practice:**
- **DE + MCMC** is more rigorous than Geck's 250-best random search. Sjursen (2023) uses MCMC (emcee) — same as us. Landmann (2021) uses particle filter. We are in the same methodological tier.
- **Multi-objective likelihood** (stakes + geodetic + snowlines) directly mirrors Geck (2021) §6.1: "Results from model calibration indicate the value of using multi-criteria validation."
- **Post-hoc area filter** is methodologically defensible as an independent validation; matches what Trüssel (2015) does (filter the top-15 by area-averaged MB after grid search).

**Where we have implementation gaps:**
1. **σ specifications are critical** and not yet defended in our methods doc against the literature. Sjursen (2023) Table 2 derives σ from independent reanalysis error budgets (σ_Bs = 0.15–0.34 m w.e.). Our σ_stake = 0.12 is *tighter* than Sjursen for summer balance — this overweights stakes. Our σ_snowline = 75 m is *less than* the residual structural RMSE we already measured (90 m). Both should be revisited.
2. **Snowline likelihood resolution.** Geck used 50 snowlines as one of the joint z-scores. We use 22 years and put them in the likelihood with a single σ. Geck's normalization-by-z-score inherently handles the fact that the snowline error scale is in meters not m w.e.; our likelihood needs a defensible σ_snowline.
3. **Branch-stratified snowlines** (Geck's verbal advice): our 90 m structural error reflects spatial averaging across all branches. If the north branch (steeper, smaller catchment, different aspect) systematically biases the average snowline elevation, separating into 3 likelihood terms (`run_snowline_north_branch.py` already exists in the workbench) would let the model fit each branch's accumulation regime separately. This is **not** in any published paper but is a defensible thesis-grade refinement.

### Q4: Is our observation weighting appropriate?
**Partly. σ_stake is on the optimistic side; σ_snowline is too tight relative to model's structural floor.**

| Obs type | Our σ | Literature comparable | Verdict |
|---|---|---|---|
| Stakes | 0.12 m w.e. | Sjursen σ_Bs 0.15–0.34, σ_Ba 0.10–0.34; Landmann ~0.02 (camera-stake) | **Slightly tight.** Defensible if you argue our 3-site network is well-measured, but on the "confident" end. Consider 0.20 m w.e. or per-site σ. |
| Geodetic (Hugonnet) | not specified clearly in this review | Sjursen σ_B10yr 0.26–0.31 m w.e./yr | Should match published Hugonnet uncertainty propagation: ~0.28 m w.e./yr for 20-yr decadal. |
| Snowline | 75 m | n/a — Geck used z-score normalization, not absolute m. Our own measured residual: 90 m | **Too tight.** σ should not be smaller than the structural RMSE of the *best* model run. Use σ ≥ 90 m (our D-028 finding: "Snowline RMSE: 90m — structural limitation"). With σ = 75 m, the likelihood penalizes runs for spread the model physically cannot remove, biasing the posterior toward parameter sets that suppress snowline variability — which is the +30 m bias and 2× too-low spatial std we already observed. |
| Area (filter) | 1.0 km² | n/a | Filter rather than likelihood — defensible, retains all 1000 samples per D-028. |

**Recommendation:** σ_stake → 0.15–0.20 m w.e.; σ_snowline → 90–110 m (= measured residual + small slack); σ_geodetic → match published Hugonnet σ for the 2000–2020 epoch.

### Q5: Specific recommendations for redesigning calibration
Concrete, in priority order:

**P1 (must-do, supported by Geck + multiple corroborating papers):**
1. **Add γ (lapse rate) as 7th free parameter.** Prior N(-4.5, 1.0), bounds [-2.0, -6.5].
2. **Decouple r_ice from r_snow.** Add r_ice as 8th parameter with prior N(0.014, 0.005); change r_snow prior to N(0.0042, 0.002). Drop the fixed-ratio assumption.

**P2 (should-do, supported by multiple papers):**
3. **Inflate σ_snowline** to ≥ 90 m (the measured structural floor); document in methods that we do *not* claim sub-90m discriminating power.
4. **Inflate σ_stake** to 0.15–0.20 m w.e. unless we can defend 0.12 from the actual stake measurement campaign uncertainty.
5. **Stratify snowline likelihood by branch** (north / middle / south). This honors Geck's specific suggestion and tests whether the structural snowline bias is a single-glacier-average artifact or per-branch.

**P3 (good-to-do, methodologically routine):**
6. **Confirm σ_geodetic** matches published Hugonnet propagation (~0.28 m w.e./yr).
7. **Validation metrics:** explicitly report posterior predictive coverage of stake observations (per-year) and snowline elevations (per-year), following Sjursen (2023) Fig. 6 style. This is the honest test of whether the posterior actually captures the data.
8. **Independent comparison to USGS Wolverine** (closest analogue per O'Neel 2019). Plot Dixon vs Wolverine annual mass balance series — useful sanity check.

**P4 (defer or scope-limit):**
9. **IceBoost vs Farinotti comparison** (already in progress per `compare_iceboost_farinotti.py`) — keep as an appendix sensitivity test for the *projection* module, not the SMB calibration.
10. **Variable lapse rate** — defer; not feasible with current data, and Schuster (2023) shows the constant-calibrated case is acceptable for projection-grade work.
11. **LT orographic precip** (Roth 2018) — major upgrade, not scope-feasible for the thesis.

**Final recommended likelihood:**
$$
\log L = -\tfrac{1}{2} \sum_{i=1}^{N_\text{stake}} \frac{(b_i^\text{obs} - b_i^\text{mod})^2}{\sigma_\text{stake}^2} - \tfrac{1}{2} \frac{(B_\text{geod}^\text{obs} - B_\text{geod}^\text{mod})^2}{\sigma_\text{geod}^2} - \tfrac{1}{2} \sum_{j,b} \frac{(z_{j,b}^\text{obs} - z_{j,b}^\text{mod})^2}{\sigma_\text{snowline}^2}
$$
where j indexes year, b indexes branch (3 branches if implementing stratification), σ_stake = 0.15, σ_geod = 0.28, σ_snowline = 100 m.

**Final recommended free parameters (8):**
| Param | Prior | Bounds |
|---|---|---|
| MF (mm w.e. d⁻¹ °C⁻¹) | N(5.5, 1.5) | [3.0, 9.0] |
| MF_grad | N(0, 0.001) | bounds as before |
| r_snow (m² mm W⁻¹ °C⁻¹ d⁻¹) | N(0.0042, 0.002) | [0.001, 0.01] |
| **r_ice** (NEW) | N(0.014, 0.005) | [0.005, 0.030] |
| **γ (°C km⁻¹)** (NEW) | N(-4.5, 1.0) | [-6.5, -2.0] |
| precip_grad | as current | as current |
| precip_corr | as current | as current |
| T0 | as current | as current |

---

## 5. Recommended Changes to Current Approach (Ranked)

**Tier 1 — Required for thesis defense:**
- Free lapse rate (γ) [P1, supported by Geck, Petersen, Gardner & Sharp, Schuster]
- Decouple r_ice and r_snow [P1, supported by Geck, Trüssel; Geck's specific request]

**Tier 2 — Strongly recommended:**
- Inflate σ_snowline to ≥ 90 m [P2, our own D-028 evidence + first-principles]
- Per-branch snowline likelihood [P2, Geck's verbal advice; novel for thesis]
- Inflate σ_stake to ~0.15 [P2, Sjursen comparison]

**Tier 3 — Good practice:**
- Document σ_geodetic against Hugonnet propagation [P3]
- Posterior predictive plots in Sjursen Fig. 6 style [P3, transparent reporting]
- Wolverine cross-check [P3, regional context]

**Tier 4 — Defer / scope:**
- IceBoost vs Farinotti (appendix only, projection-side)
- LT orographic precip (out of thesis scope; flag for future work)
- Variable monthly lapse rate (data-limited; flag for future work)

---

## 6. Papers We Still Need (Paywalled or Critical Gaps)

The papers in `papers_verified/` cover the core methods space well. Gaps that would strengthen the thesis if accessible:

1. **Hock (1999)** *J. Glaciol. 45* — original DETIM paper. Not in `papers_verified/`. We cite it; should have full PDF for the methods chapter.
2. **Hock (2003)** *J. Hydrol. 282* — review of TI methods; widely cited. Open access.
3. **Pellicciotti et al. (2005)** *J. Glaciol. 51* — ETI(P) original. Should have. Often paywalled but accessible via author webpage.
4. **Sass et al. (2017a)** — the Eklutna companion paper Geck cites for stakes/geodetic; useful for cross-Alaska context.
5. **Hugonnet et al. (2021)** *Nature 592* — geodetic mass balance pipeline. Open access. Critical for defending our σ_geod.
6. **Pritchard et al. (2024) IceBoost paper** — needed to defend the IceBoost vs Farinotti choice. Not in verified set.
7. **Beamer et al. (2017) on Gulf of Alaska precipitation partitioning** — Mosier cites this as best for partitioning thresholds in Alaska; relevant for our T0 prior.
8. **Anderson & Mackintosh (2012)** — non-linear T-melt response; Schuster cites this for the linearity assumption in TI models.

The verified set is sufficient for the *recommendations* above. The above gaps are for completeness in the eventual methods chapter narrative.

---

## 7. Honest Limitations of This Review

- I read pages 1–10 (or 1–12) of each PDF; deeper appendices may contain results that nuance the findings above. The methods and results sections were the priority.
- Quote pages cited refer to the *journal paginations as printed* (matching the PDF page numbers shown in the rendered images), not to PDF-file page numbers.
- I have not independently verified Geck's r_ice/r_snow ratio of ~3.4 — that is computed from the values in his Fig. 6 caption; if the figure caption uses different units than I read, the ratio could differ. Worth double-checking with Geck directly before changing the model.
- The recommendation to free γ assumes the calibration can identify 8 parameters from 25 stakes + 1 geodetic + 22 snowlines + 6 area constraints. Our existing CAL-013 had 6 free parameters and 1,656 posterior samples — we should run a parameter identifiability analysis (e.g., correlation matrix of posterior, or trace plots) to confirm that 8 parameters remain identifiable. If γ and MF end up perfectly correlated in the posterior (the Gardner & Sharp compensation problem in MCMC form), we'd need to either add more constraints or fix one.
- The σ recommendations are calibrated reasonable values, not derived from a formal analysis of our specific datasets. The actual stake measurement uncertainty for the Dixon ABL/ELA/ACC sites should be quantified from the field protocol (e.g., snow-pit density measurement repeatability) before locking in σ_stake.

---

*End of literature review — 2026-04-14.*
