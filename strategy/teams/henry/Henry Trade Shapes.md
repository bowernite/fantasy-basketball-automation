# Henry Trade Shapes

Counterparty: Henry (161019). Tanking, fringe boundary: 9th PF (26,806), 6.2 W, 0.0% P(title) (`Team Projections.md` year 1, 9/29; years 2+ read: `Team Projections.md` '27-28+ table (no trades)). 37 bodies, so he takes one extra body without a cut. 9/28 text: "Giannis is available, send offers." Likes simple deals; understands body constraints. Likely wants youth, BASE, picks (guess, not stated).

Rules for this target: we receive ≤ bodies we send (Brett 9/28). Simpler shapes preferred. Our picks are ~15% cheaper to us than listed VALUE while contending (Brett 9/28, size assumed); ΔBASE here is raw.

Sims: 9/29/26 on 9/29 rosters (Fox in, Cade kept, us at 38), F/C flex; ΔBASE and Δage read from the `.team.md` evals (re-priced 9/29). Out-side picks (`Ours.team.md`): '27 1st 1176, '28 1st 931, Mitch '27 2nd 694, '28 2nd 417, Henry '28 3rd 232, '27 4th 93. Rows with a '28 pick re-simmed 9/29 on the `sim.py future` own-pick bands (Brett '28 09–12, Henry '28 02–09); the rest keep their 9/29 re-price. Baseline P(title) 55.5%. Giannis alone: Δw (season) ours +2.36, ΔP(title) ours 13.3% (`Henry.team.md`). Sharpe (0 GP) and Williams (10 GP) cost near-zero season value, so shapes built on them keep ΔP(title) +9%; Giddey-centered shapes cap near +6%. Rows sending 3 for 1 put Henry at 39; the sim cuts McGowens (BASE 0).

Cade rows sit in Below bar: they're floored against Michael's open counter Cade > Reaves+Sabonis+Siakam (+3200, ΔP +17%, re-simmed 9/29, `Bonin.shapes.md`), still undecided. Cade 1-for-2 rows carry Tyus Jones (and Post on the 1-for-3) in Out to stay body-even.

Refresh 9/29: dropped rows priced on the Jon deal (Jon passed) or Michael's Cade scenarios, and rows sending Middleton, Chris '27 2nd, own '27 2nd (all Chris's since the 9/28 Fox deal), 2.09 (used) or Wells/McBride (never arrived). Added Mitch '27 2nd, '28 2nd and '27 4th sweetener variants and one Fox variant.

Ruled out 9/28: Kyrie/VanVleet/Butler (age, Henry is climbing); Giddey+Garland 2-for-1 (ΔBASE about −1000).

## Above floor

| Out | In | Score | ΔBASE | Δw | Δw (season) | ΔP(title) | Δage |
|---|---|---|---|---|---|---|---|
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Bane**</li><li>**Sharpe**</li><li>**Williams**</li><li>**['27 1st]**</li><li>**['27 4th]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2500** | **+1200** | **+0.4** | **+1.0** | **+9%** | +7.2 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Sharpe**</li><li>**Williams**</li><li>**['27 4th]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2400** | **+1200** | **+0.2** | **+0.9** | **+9%** | +5.5 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Edey**</li><li>**Sharpe**</li><li>**Williams**</li><li>**['27 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2300** | **+1100** | **+0.6** | **+1.0** | **+8%** | +9.5 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Sharpe**</li><li>**Williams**</li><li>**[Henry '28 3rd]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2300** | **+1100** | **+0.2** | **+0.9** | **+9%** | +5.8 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Sharpe**</li><li>**Williams**</li><li>**['28 2nd]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2100** | **+900** | **+0.2** | **+0.9** | **+9%** | +6.8 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giddey**</li><li>**Williams**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+1900** | **+1200** | **+0.3** | **+0.6** | **+5%** | +7.8 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giddey**</li><li>**Williams**</li><li>**['27 4th]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+1800** | **+1100** | **+0.3** | **+0.6** | **+5%** | +7.9 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Sharpe**</li><li>**Williams**</li><li>**[Mitch '27 2nd]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+1800** | **+600** | **+0.2** | **+0.9** | **+9%** | +6.6 |

## Floor

| Out | In | Score | ΔBASE | Δw | Δw (season) | ΔP(title) | Δage |
|---|---|---|---|---|---|---|---|
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Bane**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+1600** | **+1200** | **+0.1** | **+0.5** | **+2%** | +4.4 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Edey**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+1600** | **+1000** | **+0.3** | **+0.5** | **+3%** | +6.1 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Edey**</li><li>**Green**</li><li>**Sharpe**</li><li>**['28 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+1600** | **+900** | **+0.2** | **+0.8** | **+3%** | +9.1 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Green**</li><li>**Sharpe**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+1500** | **+900** | -0.1 | **+0.7** | **+3%** | +5.9 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Edey**</li><li>**Green**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li><li>**Rollins**</li></ul> | **+1400** | **+900** | **+0.6** | **+0.7** | **+2%** | +4.0 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Sharpe**</li><li>**Eason**</li><li>**['27 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+1400** | **+300** | **+0.3** | **+0.8** | **+9%** | +7.5 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Sharpe**</li><li>**Williams**</li><li>**['27 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+1300** | **+100** | **+0.2** | **+0.9** | **+9%** | +7.8 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giddey**</li><li>**Sharpe**</li><li>**['28 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+1300** | **+500** | **+0.4** | **+0.6** | **+6%** | +9.6 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giddey**</li><li>**Garland**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li><li>**Rollins**</li></ul> | **+1100** | **+400** | **+0.8** | **+0.5** | **+4%** | +4.2 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giddey**</li><li>**Sharpe**</li><li>**['27 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+1100** | **+200** | **+0.4** | **+0.6** | **+6%** | +9.3 |

## Below bar

| Out | In | Score | ΔBASE | Δw | Δw (season) | ΔP(title) | Δage |
|---|---|---|---|---|---|---|---|
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Cade**</li><li>**Jones**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li><li>**Okongwu**</li></ul> | **+2700** | **+1200** | **+1.8** | **+0.9** | **+10%** | +4.8 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Cade**</li><li>**Sharpe**</li><li>**Williams**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li><li>**Okongwu**</li><li>**Rollins**</li></ul> | **+2500** | **+600** | **+2.1** | **+1.3** | **+12%** | +3.5 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Cade**</li><li>**Jones**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li><li>**Rollins**</li></ul> | **+1500** | **+300** | **+1.7** | **+0.7** | **+7%** | +4.4 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Cade**</li><li>**Jones**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li><li>**McDaniels**</li></ul> | **+1400** | **+500** | **+1.3** | **+0.5** | **+5%** | +5.4 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Cade**</li><li>**Jones**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li><li>**Hartenstein**</li></ul> | **+1300** | **+400** | **+1.2** | **+0.5** | **+6%** | +6.0 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giddey**</li><li>**Sharpe**</li><li>**Williams**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+900** | **+200** | -0.2 | **+0.6** | **+5%** | +7.8 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Edey**</li><li>**['28 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+700** | **+100** | **+0.3** | **+0.5** | **+3%** | +7.9 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Edey**</li><li>**Sharpe**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+500** | 0 | -0.2 | **+0.5** | **+3%** | +6.1 |

## Too lopsided

| Out | In | Score | ΔBASE | Δw | Δw (season) | ΔP(title) | Δage |
|---|---|---|---|---|---|---|---|
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Cade**</li><li>**Jones**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li><li>**Knueppel**</li></ul> | **+4600** | **+3300** | **+1.6** | **+0.7** | **+8%** | +3.6 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Bane**</li><li>**Sharpe**</li><li>**Williams**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+3800** | **+2500** | **+0.4** | **+1.0** | **+9%** | +3.8 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Cade**</li><li>**Jones**</li><li>**Post**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li><li>**Okongwu**</li><li>**Rollins**</li></ul> | **+4700** | **+2500** | **+2.9** | **+1.2** | **+13%** | +3.4 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**['27 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+3700** | **+2400** | **+1.3** | **+0.9** | **+9%** | +7.8 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Bane**</li><li>**Sharpe**</li><li>**Williams**</li><li>**[Mitch '27 2nd]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+3100** | **+1800** | **+0.4** | **+1.0** | **+9%** | +5.6 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giddey**</li><li>**[Mitch '27 2nd]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2600** | **+1700** | **+0.9** | **+0.6** | **+6%** | +8.6 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Bane**</li><li>**Sharpe**</li><li>**Williams**</li><li>**['28 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2800** | **+1500** | **+0.4** | **+1.0** | **+9%** | +7.5 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giddey**</li><li>**['28 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2400** | **+1500** | **+0.9** | **+0.6** | **+6%** | +9.6 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Fox**</li><li>**Sharpe**</li><li>**Williams**</li><li>**['28 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2800** | **+1400** | **+0.5** | **+1.0** | **+10%** | +7.3 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Edey**</li><li>**Sharpe**</li><li>**Williams**</li><li>**['28 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2500** | **+1400** | **+0.6** | **+1.0** | **+8%** | +9.9 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Sharpe**</li><li>**Williams**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2500** | **+1300** | **+0.2** | **+0.9** | **+9%** | +5.2 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Bane**</li><li>**Sharpe**</li><li>**Williams**</li><li>**['27 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2600** | **+1300** | **+0.4** | **+1.0** | **+9%** | +7.1 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giddey**</li><li>**['27 1st]**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+2100** | **+1300** | **+0.9** | **+0.6** | **+6%** | +9.3 |

## Doesn't meet our minimums

| Out | In | Score | ΔBASE | Δw | Δw (season) | ΔP(title) | Δage |
|---|---|---|---|---|---|---|---|
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Edey**</li><li>**Green**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | -900 | -600 | -0.7 | **+0.2** | -4% | +6.4 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Cade**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | -600 | -1100 | **+0.5** | **+0.4** | **+3%** | +6.8 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giddey**</li><li>**Edey**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | -100 | -100 | -0.2 | **+0.1** | -1% | +7.7 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Garland**</li><li>**Bane**</li><li>**Sharpe**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+600** | **+200** | -0.4 | **+0.5** | **+2%** | +4.4 |
| <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giddey**</li><li>**Green**</li></ul> | <ul style="list-style-type:disc;margin:0;padding-left:1.25em"><li>**Giannis**</li></ul> | **+900** | **+800** | -0.1 | **+0.3** | -1% | +7.6 |
