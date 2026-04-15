# Citation Audit — 2026-04-14

**Trigger:** User flagged concern about potentially hallucinated literature citations.

**Method:** Verified every DOI against CrossRef API, searched OpenAlex/Semantic Scholar for correct DOIs, downloaded open-access PDFs to verify paper content against our claims.

**Papers now verified locally** (`papers_verified/`):
- `schuster_2023.pdf` — Schuster, Rounce, Maussion (2023) Ann. Glaciol.
- `huss_hock_2015.pdf` — Huss & Hock (2015) Front. Earth Sci.
- `roth_2018_precip.pdf` — Roth, Hock, Schuler et al. (2018) Front. Earth Sci.
- Already had: Geck et al. (2021) PDF in `~/Downloads/`

---

## Summary table

| # | Citation | DOI status | Claim status |
|---|---|---|---|
| 1 | Hock (1999) DETIM | ✅ Correct | ✅ Verified — correct paper |
| 2 | Geck et al. (2021) | ✅ Correct | ✅ Direct quotes verified from PDF |
| 3 | Hugonnet et al. (2021) | ✅ Correct | ✅ Verified |
| 4 | Rounce et al. (2020) PyGEM | ✅ Correct | ✅ Verified |
| 5 | Rounce et al. (2023) Science | ✅ Correct | ✅ Verified |
| 6 | Foreman-Mackey et al. (2013) emcee | ✅ Correct | ✅ Verified |
| 7 | Rabatel et al. (2005) | ✅ Correct | ✅ Verified |
| 8 | Farinotti et al. (2019) Nature | ✅ Correct | ✅ Verified |
| 9 | **Gardner & Sharp (2009)** | ❌ **WRONG DOI** | ⚠️ Specific value unverified |
| 10 | **Roth et al. (2018)** | ⚠️ DOI valid but | ❌ **WRONG PAPER** — it's precip, not lapse rate |
| 11 | **Huss & Hock (2015)** | ❌ **WRONG DOI** | ❌ **WRONG CLAIM** — they use DDF not DETIM |
| 12 | **Schuster et al. (2023)** | ❌ **WRONG DOI** | ✅ Claim verified in PDF |
| 13 | **Cogley et al. (2011)** | ❌ **DOI 404** | ⚠️ UNESCO report, not journal |
| 14 | **Zemp et al. (2013)** | ❌ **DOI 404** | ⚠️ Cannot identify specific paper |

**Score: 8 correct, 6 problematic. Nearly half had issues.**

---

## Detailed findings

### 1. Gardner & Sharp (2009) — WRONG DOI

- **Previously cited**: `10.3189/002214309788608787`
- **CrossRef reveals**: That DOI is Aizen et al. on **Fedchenko glacier** (Pamirs) — completely different paper
- **Correct DOI options**:
  - `10.3189/172756409787769663` — Gardner & Sharp (2 authors) — "Sensitivity of net mass-balance estimates to near-surface temperature lapse rates" — Annals of Glaciology
  - `10.1175/2009jcli2845.1` — Gardner et al. (8 authors) — "Near-Surface Temperature Lapse Rates over Arctic Glaciers and Their Implications for Temperature Downscaling" — Journal of Climate
- **Our claim**: "-4.9°C/km mean for Arctic maritime glaciers"
- **Verification**: Cannot verify specific value without paper access. The **Gardner & Sharp 2009 AoG paper** is specifically about sensitivity analysis of lapse rates. The **Gardner et al. 2009 J. Climate paper** is an 8-author compilation of lapse rates from Arctic glaciers — likely the source of the "-4.9" claim.
- **Action**: Replace DOI with `10.1175/2009jcli2845.1` (8-author paper, more likely source of specific value). Note: this means changing citation from "Gardner & Sharp" to "Gardner et al."

### 2. Roth et al. (2018) — VALID DOI BUT WRONG PAPER

- **DOI**: `10.3389/feart.2018.00020` (verified)
- **Actual title**: "Modeling Winter Precipitation Over the Juneau Icefield, Alaska, Using a Linear Model of Orographic Precipitation"
- **Our claim**: "-5.0°C/km lapse rate for Juneau Icefield"
- **Problem**: This paper is about **precipitation downscaling**, not lapse rates. The paper does discuss lapse rates in passing (e.g., for extrapolating temperature to the icefield) but that's not its primary contribution.
- **Action**: **Remove this citation from the lapse rate slide**. Replace with a more appropriate Juneau Icefield lapse rate reference, or acknowledge we have no directly-verified Juneau Icefield lapse rate citation.

### 3. Huss & Hock (2015) — WRONG DOI AND WRONG CLAIM

- **Previously cited**: `10.1016/j.gloplacha.2015.01.003`
- **CrossRef reveals**: That DOI is Leng et al. on **drought impacts** (Global and Planetary Change) — completely unrelated
- **Correct DOI**: `10.3389/feart.2015.00054` — "A new model for global glacier change and sea-level rise" — Frontiers in Earth Science
- **Our claim** (in slide 11): "Uses r_ice/r_snow ratio of 2.0 globally"
- **VERIFIED WRONG**: Reading the PDF, Section 3.1.2 shows they use a simple **degree-day model** with separate `f_snow` and `f_ice` factors:
  > "Snow and ice melt is calculated using the classical degree-day model (Hock, 2003) that relates melt a_i,m... a_i,m = f_snow/ice · Σ T+_i,d where f_snow/ice (mm d⁻¹ K⁻¹) are the degree-day factors for snow or ice"
- They do **NOT** use a radiation-temperature index with a fixed r_ice/r_snow ratio. They use separate degree-day factors.
- They also use **monthly variable lapse rates** from ERA-interim pressure levels, not a fixed -5.0.
- **Action**: **Remove this citation from the r_ice/r_snow ratio support list**. The claim that they "use ratio 2.0 globally" is false.

### 4. Schuster et al. (2023) — WRONG DOI, CORRECT CLAIM

- **Previously cited**: `10.5194/tc-17-1605-2023` → 404
- **Correct DOI**: `10.1017/aog.2023.57` — Annals of Glaciology
- **Title**: "Glacier projections sensitivity to temperature-index model choices and calibration strategies"
- **Our claim**: Documents equifinality in TI models, recommends ensemble approaches
- **VERIFIED from PDF**: *"Despite the simplicity of the temperature-index model, equifinality from model parameters strongly influences the MB variability, seasonality and gradient."* (p. 298)
- **Also important context from this paper**: 
  - Their "reference" constant lapse rate is **-6.5 K/km** (OGGM default)
  - Alternative option: variable monthly lapse rates derived from ERA5 pressure levels
  - **Neither their constant nor variable approach uses -5.0°C/km as a default**
- **Action**: Fix DOI. Use direct quote in info-icon.

### 5. Cogley et al. (2011) — NOT A JOURNAL PAPER

- **Previously cited**: `10.1657/1938-4246-44.2.269` → 404
- **Reality**: This is a **UNESCO-IHP technical document** (IHP-VII Technical Documents in Hydrology No. 86, IACS Contribution No. 2), not a peer-reviewed journal article. No standard journal DOI.
- **Our claim**: Source for σ_stake = 0.12 m w.e. measurement uncertainty
- **Action**: Remove the DOI. Cite as: "Cogley JG, Hock R, Rasmussen LA, Arendt AA, et al. (2011). Glossary of Glacier Mass Balance and Related Terms. UNESCO-IHP Technical Documents in Hydrology No. 86, Paris." Available at unesdoc.unesco.org.

### 6. Zemp et al. (2013) — DOI DOES NOT EXIST

- **Previously cited**: `10.3189/2013JoG12J027` → 404
- **Problem**: Zemp has many papers in this era; cannot identify the intended paper from context alone
- **Our claim**: Source for stake uncertainty of 0.12 m w.e.
- **Action**: **Remove this citation**. The σ_stake = 0.12 m w.e. value should either:
  - Be derived from our own field measurements
  - Be cited to the WGMS manual (Huss et al. 2013 or similar)
  - Or removed from the tooltip until a verifiable source is identified

---

## Additional findings

### Geck et al. (2021) — Verified quote at odds with our approach

From `~/Downloads/modeling-the-impacts-of-climate-change...eklutna...pdf` page 913:

> "The temperature lapse rate among the best parameter sets ranged from −0.6 to −0.2°C (100 m)⁻¹ with a mean of −0.3°C (100 m)⁻¹ and a mode of −0.2°C (100 m)⁻¹."

**Translation**: Geck calibrated lapse rate to -2 to -6°C/km, with mean -3 and mode -2. Our fixed value of -5.0°C/km is at the steep end.

From Figure 6 caption (page 914):

> "Γ = −0.2°C (100 m)⁻¹, fm = 5.5 mm °C⁻¹ d⁻¹, r_ice = 0.0414 m² mm d⁻¹ °C⁻¹, r_snow = 0.0098 m² mm d⁻¹ °C⁻¹"

**Translation**: Geck's best-fit ratio r_ice/r_snow = 4.22, NOT 2.0. He calibrated them independently.

**This is critical**: We've been framing Geck's paper as "using the same approach" when in fact:
1. His calibrated lapse rate (-3°C/km mean) is shallower than our fixed -5.0
2. His calibrated r_ice/r_snow (4.22) is more than double our fixed 2.0
3. He calibrated BOTH independently, not fixing the ratio

Our fixed-parameter approach is defensible (equifinality in smaller-n datasets), but the claim that we follow Geck's methodology is incorrect. We made a **different** methodological choice that needs its own justification.

---

## Recommendations — priority order

1. **IMMEDIATE**: Fix 3 wrong DOIs in `advisor_presentation.html`:
   - Gardner & Sharp → `10.1175/2009jcli2845.1` (or `10.3189/172756409787769663`)
   - Huss & Hock → `10.3389/feart.2015.00054`
   - Schuster → `10.1017/aog.2023.57`

2. **IMMEDIATE**: Remove Roth 2018 from lapse rate slide (wrong topic).

3. **IMMEDIATE**: Remove Huss & Hock from r_ice/r_snow slide (wrong claim).

4. **IMMEDIATE**: Remove all fabricated "Section X, Table Y" references from info-icon tooltips. Replace with verified quotes where we have PDFs, or remove entirely.

5. **IMMEDIATE**: Remove Cogley and Zemp DOI links. Keep Cogley citation as UNESCO report. Remove Zemp citation.

6. **RECONSIDER**: The framing "Geck et al. 2021 uses same approach" is misleading. Acknowledge Geck calibrated independently and reached different values. Frame our fixed approach as a **different** methodology choice.

7. **ONGOING**: For the thesis, systematically verify every citation by reading the actual paper or downloading OA versions. Build a `papers_verified/` library.

---

## Future verification workflow

For every new citation:
1. Check DOI exists: `curl -s https://api.crossref.org/works/{DOI}` → should return metadata
2. Check paper matches: compare returned title/authors/year against claimed reference
3. Find open access: `curl -s https://api.openalex.org/works/https://doi.org/{DOI}` → look for `open_access.oa_url`
4. Download PDF to `papers_verified/` and read relevant sections before quoting specific values
5. Only use direct quotes from verified PDFs in info-icon tooltips

**Free APIs with no auth required:**
- CrossRef: `api.crossref.org` — DOI metadata
- OpenAlex: `api.openalex.org` — broader than CrossRef, includes open-access links
- Unpaywall: `api.unpaywall.org` — finds legal OA versions
- Semantic Scholar: `api.semanticscholar.org` — has abstracts (but rate-limited)
- arXiv: `export.arxiv.org` — for preprints
