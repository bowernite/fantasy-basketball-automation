# out > in | Score ΔBASE Δw Δw(season) ΔP(title) Δage | status

Counterparty: Michael (161016). Contending: 2nd PF (30,717), 12.8 W, 13.1% title; ours 55.5% (`Team Projections.md`, year 1; years 2+ read: `Team Projections.md` '27-28+ table (no trades)). Columns: `Out | In` + Score + our five big numbers.

What Michael has said (texts 8/8–9/28/26): he's trying to get younger, not add end-of-career guys. He won the title last year. Trade block 9/28 (Fleaflicker `isOnTradingBlock`): Sabonis, Markkanen, Nembhard, Draymond, Klay, DeRozan; no picks, no note.
- 9/28 11:56a: turned down Edey+Murray / Edey+Suggs > Sabonis+Markkanen and Kuminga+Eason > Sabonis / Markkanen ("worth more than those combos"). Called Cade > Reaves+Sabonis+Siakam "a lot but interesting since Cade's a beast".
- 4:09p: countered Cade+Giddey > Reaves+Siakam+White+2.11. We declined it.
- 4:15p: turned down the Walker / Kuminga / Sharpe adds. "Cade's amazing but that'll crush any depth I have." He wants a real rotation player back.
- 4:24p: we sent four depth-back Cade shapes (Collins / Melton as bodies). No reply as of 9/29 12:34p CT.

Target: his vets for our young pieces. A Cade deal needs Reaves+Sabonis plus a real third piece (Siakam, White or Hart), with rotation depth going back to him.

Refresh 9/29/26: every row re-priced on 9/29 rosters (both teams at 38), with the F/C flex and the full-Score cut rule.
- Rows that net us bodies now carry the sim's cuts in Out (Tyus Jones, then Post, then Emanuel Sharp), so every row is body-even for us. The statused rows were texted without these cuts.
- Michael's 2.11 became Cameron Carr (his R2.11), so Carr replaces (2.11) in every row.
- Dropped Middleton > Michael '27 3rd and Walker+Chris '27 2nd > Hart: both assets went to Chris in the Fox deal (9/28).
- No 4th-round rows: Michael hasn't asked for a small pick.
- Pick BASE: our '27 1st 1176 · '28 1st 931 ('28 band 09–12 from `sim.py future`) · Michael '27 1st 1231.
- Michael is at 38, so an N-for-1 makes him cut (usually McDermott).

Re-priced 9/29/26 (4b): ΔBASE, Δage and Score now read BASE and AGE from `Bonin.team.md` and `Ours.team.md`. Before, they came from the stale pre-draft human evals.
- Carr rows gained about +300 ΔBASE (Carr 707, was 488). That lifted 4 Cade+Carr rows from Floor to Above and 5 from Below bar to Floor. It also moved 4 Reaves+Siakam+White+Carr rows out of Doesn't meet our minimums into Below bar.
- Cade+Camara+Tyus Jones > Reaves+Sabonis+Siakam (+1869) and Williams+Kuminga > White (+792) round up to their Above cutoffs, so both move up from Floor.
- Cade+Collins+Queta+Melton > Reaves+Sabonis+Siakam now passes the ΔBASE minimum (−990, shown −1000), so it moves to Below bar.
- Cade+Tyus Jones+Post+Emanuel Sharp > Sabonis+Siakam+White+Hart drops to −1116 ΔBASE and moves to Doesn't meet our minimums.
- Bane+Gordon > Reaves rises to +1365 ΔBASE and moves to Too lopsided.
- No `eval_gap` rows. Every other row moved ≤ ±200 Score.
- 7b 9/29: our '28 1st re-priced 1335 → 931 off the `future` slot band. Kuminga+'28 1st > Siakam re-simmed: Score +1300 → +1700, ΔBASE +100 → +500; stays Above floor, re-sorted. No other row holds a '28/'29 pick.

Floors, since no live bid benchmarks them:
- Cade rows: our 4:24p shapes. Above ≥ +1900, Floor +1200…+1800.
- Non-Cade rows: Above ≥ +800, Floor ≈ +200…+700.
- Every multi-body Cade row cuts Michael's season (Δw (them) −0.3 to −3.7), so none loads a competitor.
- Garland+Reid > Clingan+Powell (Below bar) is the only live row that adds to Michael's season (+0.2 Δw (season) for him).

Names: Draymond = Draymond Green; bare Green = Jalen Green; Smith = Jabari Smith; Murray = Keegan Murray; Williams = Mark Williams; Sharp = Emanuel Sharp (not Sharpe). Sharpe > Hart and Bona > Draymond have no Δage (no weighted production on our side).

## Above floor

Cade+Tyus Jones+Post > Reaves+Sabonis+Siakam | +3200 +700 +3.1 +1.2 +17% +5.4 | Us proposed 9/28
Cade+Eason+Collins+Melton > Reaves+Sabonis+Siakam+White | +3200 +600 +2.7 +1.2 +19% +4.5 | Us proposed 9/28
Edey+Sharpe+Kuminga > Sabonis+Markkanen | +3200 +900 +2.0 +1.2 +16% +5.6
Edey+Kuminga+Walker > Sabonis+Siakam | +3100 +900 +2.2 +1.1 +14% +7.0
Edey+Murray > Sabonis+Markkanen | +3100 +1100 +2.0 +1.1 +15% +4.9 | Michael rejected 9/28
Edey+Suggs > Sabonis+Markkanen | +2900 +1000 +2.0 +1.0 +14% +5.2 | Michael rejected 9/28
Cade+Keegan Murray+Vassell+Tyus Jones > Reaves+Sabonis+Siakam+White | +2900 0 +3.2 +1.4 +20% +5.3
Cade+Jabari Smith+Collins+Melton > Reaves+Sabonis+Siakam+White | +2900 +500 +2.4 +1.1 +18% +4.9 | Us proposed 9/28
Cade+Tyus Jones+Post > Reaves+Markkanen+Siakam | +2900 +900 +2.3 +0.9 +14% +5.0
Cade+Tyus Jones+Post > Reaves+Sabonis+White | +2800 +500 +2.9 +1.0 +16% +5.2 | Us proposed 9/28
Cade+Kuminga+Tyus Jones+Post > Reaves+Sabonis+White+Carr | +2800 +500 +2.7 +1.0 +16% +5.2
Edey+Sharpe > Sabonis+White | +2700 +800 +2.1 +1.1 +13% +6.7
Sharpe+Kuminga > Sabonis | +2600 +800 +1.6 +1.0 +13% +6.4
Cade+Coby White+Camara+Tyus Jones > Reaves+Sabonis+Siakam+White | +2600 +200 +2.7 +1.1 +17% +5.0
Edey+Murray+Walker > Sabonis+Markkanen | +2600 +600 +1.7 +1.1 +13% +5.0
Edey+Eason > Sabonis+White | +2500 +700 +1.9 +1.0 +12% +6.3
Kuminga+Eason > Sabonis | +2500 +700 +1.5 +0.9 +13% +5.2 | Michael rejected 9/28
Smith+Kuminga+Walker > Siakam+Hart | +2400 +900 +1.2 +0.7 +11% +8.7
Cade+Tyus Jones+Post > Reaves+Siakam+Harden | +2300 +600 +2.3 +0.9 +9% +7.5
Sharpe+Kuminga > Markkanen | +2300 +1000 +0.8 +0.7 +10% +5.4
Cade+Vassell+Tyus Jones > Reaves+Sabonis+Harden | +2200 0 +2.7 +1.1 +14% +6.4
Murray+Walker > Markkanen+Draymond | +2200 +1200 +1.0 +0.6 +7% +5.6
Cade+Eason+Tyus Jones > Reaves+Sabonis+Siakam | +2200 -200 +2.6 +1.1 +17% +5.3
Kuminga+Walker > Siakam | +2200 +1000 +1.0 +0.6 +8% +9.1
Edey+Kuminga > Sabonis+Hart | +2100 +400 +2.1 +0.9 +12% +6.4
Kuminga+'27 1st > Markkanen | +2100 +800 +1.3 +0.7 +10% +10.0
Cade+Vassell+Tyus Jones > Reaves+Sabonis+Siakam | +2100 -300 +2.7 +1.1 +17% +5.1
Cade+Keegan Murray+Tyus Jones+Post > Reaves+Sabonis+Siakam+Carr | +2100 -200 +2.4 +1.1 +16% +5.1
Eason+Kuminga > Markkanen | +2100 +900 +0.7 +0.6 +9% +4.2 | Michael rejected 9/28
Cade+Walker+Tyus Jones+Post > Reaves+Siakam+White+Carr | +2000 +400 +1.9 +0.7 +11% +6.0 | Michael rejected 9/28
Cade+Bridges+Collins+Queta > Reaves+Sabonis+Siakam+White | +2000 +200 +2.0 +0.9 +12% +3.9
Cade+Jabari Smith+Tyus Jones+Post > Reaves+Sabonis+White+Carr | +2000 0 +2.1 +0.9 +15% +5.6
Cade+Coby White+Tyus Jones+Post > Reaves+Sabonis+Siakam+Carr | +1900 -100 +2.1 +0.9 +15% +4.8
Cade+Keegan Murray+Vassell+Collins > Reaves+Sabonis+Siakam+White | +1900 -600 +2.4 +1.2 +19% +4.6
Cade+Jabari Smith+Tyus Jones > Reaves+Sabonis+Siakam | +1900 -400 +2.4 +1.0 +16% +5.8
Cade+Camara+Tyus Jones > Reaves+Sabonis+Siakam | +1900 -200 +2.6 +1.0 +14% +5.0
Kuminga+'28 1st > Siakam | +1700 +500 +1.3 +0.6 +8% +14.0
Kuminga+Walker > White | +1600 +800 +0.8 +0.4 +5% +8.8
Edey+Tyus Jones > Sabonis+Draymond | +1600 +300 +1.7 +0.7 +8% +7.1
Smith+'27 1st > Clingan | +1600 +700 +0.6 +0.5 +8% +1.2
Murray+Walker > Markkanen | +1600 +700 +0.5 +0.5 +7% +3.8
Sharpe+Kuminga > Siakam | +1600 +400 +0.8 +0.7 +8% +8.5
Williams+Walker > Hart+Jerome | +1500 +300 +1.2 +0.6 +9% +6.6
Murray+Kuminga > Markkanen | +1500 +400 +0.5 +0.5 +8% +3.5
Eason+Kuminga > Siakam | +1400 +300 +0.7 +0.6 +8% +7.3
Simons+Walker > White | +1400 +800 +0.7 +0.3 +3% +6.6
Murray+'27 1st > Clingan | +1400 +300 +0.7 +0.6 +9% 0.0
Eason+Kuminga > Harden | +1300 +600 +0.6 +0.6 +3% +11.9
Sharpe+Walker > White | +1300 +500 +0.5 +0.5 +5% +9.1
Camara+Walker > Siakam | +1300 +600 +0.6 +0.4 +4% +6.7
Eason+Kuminga > Zubac | +1100 +400 +0.4 +0.4 +6% +4.3
Melton+Gordon > White | +1100 +600 +0.1 +0.1 +4% +2.4
Eason+Walker > White | +1100 +400 +0.4 +0.4 +5% +7.3
Edey > Sabonis | +1100 -100 +1.2 +0.6 +8% +6.0
Smith+Kuminga > Siakam | +1100 +200 +0.4 +0.4 +7% +9.1
Kuminga > Jerome | +900 +200 +0.8 +0.3 +6% +5.2
Walker > Nembhard | +900 +600 +0.3 +0.1 +2% +3.6
Williams+Sharpe > Harden | +900 +200 +0.4 +0.8 +4% +12.3
Green > Siakam | +800 +500 +0.6 +0.4 +1% +7.9
Bane > Markkanen | +800 +400 +0.3 +0.3 +4% +1.1
Williams+Kuminga > White | +800 0 +0.4 +0.5 +6% +7.7
Murray+Vassell > Markkanen | +800 0 +0.2 +0.4 +7% +3.3
Sharpe > Hart | +800 +100 +0.6 +0.4 +5% ?
Vassell+Eason > Siakam | +800 -100 +0.4 +0.4 +7% +6.8

## Floor

Cade+Tyus Jones+Post > Reaves+Sabonis+Hart | +1800 -300 +2.6 +0.9 +14% +5.0 | Us proposed 9/28
Cade+Tyus Jones+Post > Reaves+Siakam+White | +1800 +100 +2.1 +0.7 +11% +5.9 | Us proposed 9/28
Cade+Collins+Melton > Reaves+Sabonis+Harden | +1800 +100 +1.9 +0.9 +12% +5.2 | Us proposed 9/28
Cade+Kuminga+Tyus Jones+Post > Reaves+Siakam+White+Carr | +1800 +100 +1.9 +0.7 +11% +5.9 | Michael rejected 9/28
Cade+Queta+Melton > Reaves+Sabonis+Siakam | +1800 -200 +2.2 +0.9 +14% +4.5
Cade+Collins+Melton > Reaves+Sabonis+Siakam | +1800 -200 +2.0 +0.9 +15% +3.9 | Us proposed 9/28
Cade+Eason+Tyus Jones > Reaves+Sabonis+White | +1800 -400 +2.4 +1.0 +16% +5.1
Cade+Vassell+Tyus Jones > Reaves+Sabonis+White | +1700 -500 +2.5 +0.9 +16% +5.0
Cade+Jalen Green+Tyus Jones+Post > Reaves+Sabonis+Siakam+Carr | +1700 -300 +2.3 +1.0 +13% +5.5
Cade+Keegan Murray+Tyus Jones+Post > Reaves+Sabonis+White+Carr | +1700 -400 +2.2 +1.0 +15% +4.9
Cade+Keegan Murray+Tyus Jones > Reaves+Sabonis+Harden | +1700 -400 +2.4 +1.2 +13% +6.3
Cade+Tyus Jones+Post > Clingan+Sabonis+Siakam | +1600 -800 +2.9 +1.1 +16% +3.9
Cade+Keegan Murray+Tyus Jones > Reaves+Sabonis+Siakam | +1600 -700 +2.5 +1.1 +16% +5.1
Cade+Coby White+Tyus Jones > Reaves+Sabonis+Harden | +1600 -300 +2.1 +1.0 +12% +6.0
Cade+Coby White+Camara+Collins > Reaves+Sabonis+Siakam+White | +1600 -400 +2.0 +0.9 +15% +4.4
Cade+Tyus Jones > Reaves+Sabonis+Michael '27 1st | +1600 0 +1.7 +0.7 +11% +2.8
Cade+Suggs+Tyus Jones+Post > Reaves+Sabonis+White+Carr | +1500 -500 +2.2 +0.9 +14% +5.1
Cade+Coby White+Tyus Jones+Post > Reaves+Sabonis+White+Carr | +1500 -300 +1.9 +0.8 +13% +4.6
Cade+Tyus Jones+Post > Reaves+Sabonis+Nembhard | +1400 -400 +2.2 +0.8 +12% +4.2
Cade+Sharpe+Tyus Jones+Post > Reaves+Siakam+White+Carr | +1400 -200 +1.7 +0.8 +12% +5.9 | Michael rejected 9/28
Cade+Coby White+Tyus Jones > Reaves+Sabonis+Siakam | +1400 -600 +2.1 +0.9 +14% +4.8
Cade+Jabari Smith+Melton > Reaves+Sabonis+Siakam | +1400 -600 +1.9 +1.0 +15% +5.3
Cade+Naz Reid+Tyus Jones+Post > Reaves+Sabonis+White+Carr | +1400 -400 +2.0 +0.8 +12% +4.5
Cade+Camara+Melton > Reaves+Sabonis+Siakam | +1400 -500 +2.1 +0.9 +13% +4.6
Cade+Collins+Melton > Reaves+Sabonis+White | +1400 -400 +1.7 +0.7 +14% +3.8
Cade+Gordon+Queta > Reaves+Sabonis+Siakam | +1300 -600 +2.0 +0.8 +14% +3.9
Cade+Eason+Tyus Jones+Post > Reaves+Siakam+White+Carr | +1300 -300 +1.6 +0.7 +11% +5.8
Cade+Jalen Green+Tyus Jones+Post > Reaves+Sabonis+White+Carr | +1300 -500 +2.0 +0.8 +12% +5.3
Cade+Vassell+Tyus Jones+Post > Reaves+Siakam+White+Carr | +1200 -300 +1.7 +0.6 +11% +5.7
Cade+Collins+Gordon > Reaves+Sabonis+Siakam | +1200 -600 +1.8 +0.7 +14% +3.4
Cade+Collins+Queta > Reaves+Sabonis+Siakam | +1200 -600 +1.8 +0.8 +13% +4.1
Garland+Kuminga > Reaves | +700 +400 +0.1 +0.2 +3% +1.7
Smith+Walker > White | +700 +300 +0.1 +0.2 +3% +8.9
Suggs+Walker > Harden | +700 +400 +0.5 +0.5 0% +12.2
Kuminga > Nembhard | +600 +400 +0.4 +0.1 +2% +2.7
Suggs+Kuminga > Siakam | +600 -200 +0.5 +0.4 +6% +7.3
Eason > Hart | +600 0 +0.5 +0.2 +5% +6.2
Edey+Suggs > Clingan+Powell | +500 0 +0.4 +0.3 +3% +1.4
Bane+Walker > Markkanen | +200 -100 0.0 +0.2 +2% +1.7

## Below bar

Cade+Mark Williams+Tyus Jones+Post > Reaves+Siakam+White+Carr | +1100 -400 +1.6 +0.7 +11% +5.9
Cade+Coby White+Tyus Jones > Reaves+Markkanen+Siakam | +1100 -400 +1.3 +0.6 +12% +4.5
Cade+Coby White+Tyus Jones > Reaves+Sabonis+White | +1000 -800 +1.9 +0.8 +13% +4.6
Cade+Camara+Tyus Jones+Post > Reaves+Siakam+White+Carr | +1000 -300 +1.5 +0.5 +8% +5.5
Cade+Jabari Smith+Tyus Jones+Post > Reaves+Siakam+White+Carr | +1000 -400 +1.3 +0.6 +10% +6.3
Cade+Bridges+Melton > Reaves+Sabonis+Siakam | +900 -600 +1.7 +0.8 +10% +3.9
Cade+Keegan Murray+Tyus Jones+Post > Reaves+Siakam+White+Carr | +600 -700 +1.4 +0.6 +10% +5.6
Cade+Collins+Queta+Melton > Reaves+Sabonis+Siakam | +600 -1000 +1.3 +0.6 +11% +3.8
Cade+Suggs+Tyus Jones+Post > Reaves+Siakam+White+Carr | +500 -800 +1.4 +0.6 +10% +5.8
Cade+Bridges+Melton > Reaves+Sabonis+White | +500 -800 +1.4 +0.7 +9% +3.7
Cade+Coby White+Tyus Jones > Reaves+Siakam+Harden | +500 -600 +1.3 +0.7 +7% +6.9
Cade+Coby White+Tyus Jones+Post > Reaves+Siakam+White+Carr | +500 -600 +1.1 +0.5 +8% +5.3
Cade+Naz Reid+Tyus Jones+Post > Reaves+Siakam+White+Carr | +400 -700 +1.2 +0.4 +8% +5.2
Cade+Bridges+Collins > Reaves+Sabonis+Siakam | +300 -900 +1.3 +0.6 +9% +3.6
Cade+Bridges+Collins > Reaves+Sabonis+Harden | +300 -600 +1.3 +0.6 +5% +4.8
Cade+Jalen Green+Tyus Jones+Post > Reaves+Siakam+White+Carr | +200 -800 +1.2 +0.5 +7% +6.0
Smith+Walker+'27 1st > Siakam | +100 -700 +0.4 +0.4 +6% +11.0
Kuminga+Tyus Jones > Draymond+Klay | 0 -200 +0.3 +0.1 +1% +12.6
Garland > Markkanen | -500 -800 +0.1 +0.1 +3% +2.7
Garland+Reid > Clingan+Powell | -800 -900 -0.2 0.0 +1% -0.7

## Too lopsided

Our ΔBASE ≥ +1250 — reference only; do not float.

Bridges+Collins > Reaves+Powell | +4000 +3700 +0.5 +0.1 +1% +1.1
Bridges+Coby White > Reaves | +1600 +1900 -0.6 0.0 -3% +0.8
Green+'27 1st > Reaves | +2400 +1700 +0.8 +0.5 +4% +6.2
Collins > Zubac | +1900 +1400 +0.4 +0.2 +4% +0.5
Bane+Gordon > Reaves | +1600 +1400 -0.2 0.0 +2% -0.9
Bridges+Simons > Siakam+Nembhard | +1400 +1300 +0.7 +0.2 -2% +2.6

## Doesn't meet our minimums

Cade > Sabonis | -5600 -5600 +0.1 -0.1 +1% +5.4
Giddey+Edey > Clingan | -5400 -4000 -1.5 -0.7 -11% -1.6
Cade > Reaves | -4200 -3600 -0.6 -0.4 -4% +3.3
Cade+Giddey+Tyus Jones+Post > Reaves+Siakam+White+Carr | -3600 -3800 +0.3 -0.1 +1% +6.3 | Us rejected 9/28
Giddey+'27 1st > Clingan | -3000 -2700 -0.4 -0.2 -1% +0.1
Giddey > Siakam | -2900 -2500 -0.3 -0.2 -4% +8.5
Cade+Tyus Jones > Markkanen+Siakam | -2700 -3400 +0.7 +0.2 +6% +6.0
Garland+Gordon > Siakam | -2500 -2200 -0.5 -0.2 -2% +4.5
Garland+'27 1st > Siakam | -2400 -2600 +0.1 +0.1 +1% +8.5
Cade+Tyus Jones > Sabonis+Siakam | -2400 -3700 +1.5 +0.6 +9% +6.2
Cade+Tyus Jones > Sabonis+Markkanen | -1700 -3100 +1.5 +0.6 +10% +5.0
Garland > White | -1700 -1600 -0.1 0.0 -1% +5.5
Coby White+Suggs > White | -1400 -1200 -0.6 0.0 -1% +6.1
Reid+Suggs > Zubac | -1300 -1100 -0.5 0.0 -2% +3.2
Giddey+Gordon > Sabonis+Powell | -1300 -1800 +0.5 +0.1 +4% +5.3
Garland+Collins > Sabonis | -1300 -1800 +0.1 +0.2 +4% +2.8
Bane+Suggs > Clingan | -1100 -900 -0.5 0.0 -2% -4.5
Cade+Tyus Jones > Reaves+Siakam | -700 -1600 +0.9 +0.3 +6% +5.3
Garland+Suggs > Reaves | -700 -600 -0.5 0.0 -1% +2.1
Cade+Tyus Jones+Post > Sabonis+Markkanen+Nembhard | -600 -2200 +2.0 +0.7 +11% +4.6
Giddey > Reaves | -200 -100 -0.2 -0.1 -1% +4.3
Green+Simons > Siakam | -200 -200 +0.2 +0.3 -3% +7.4
Green+Smith > Markkanen | -100 -200 -0.3 +0.2 0% +5.4
Bane+Collins > Clingan | -100 0 -0.6 -0.1 +1% -6.0
Cade+Tyus Jones > Reaves+Markkanen | -100 -1000 +0.9 +0.3 +7% +3.8
Walker > Draymond | +100 +100 +0.2 +0.1 -1% +13.5
Cade+Tyus Jones+Post > Sabonis+Siakam+White | +200 -2000 +2.7 +1.0 +14% +6.5
Garland+Gordon > Reaves | +200 +200 -0.4 -0.1 +1% +0.3
Bona > Draymond | +300 +200 +0.3 0.0 -1% ?
Walker > DeRozan | +300 +200 +0.1 +0.2 0% +14.0
Cade+Tyus Jones > Reaves+Sabonis | +300 -1200 +1.7 +0.7 +11% +4.5
Cade+Giddey+Tyus Jones+Post+Emanuel Sharp > Reaves+Sabonis+Siakam+White+Carr | +500 -1600 +2.6 +0.9 +13% +6.2
Green+Bridges > Siakam+Hart | +500 +400 +0.5 +0.3 -2% +5.4
Collins+Bridges > Clingan | +900 +1100 -0.5 -0.1 -2% -6.1
Cade+Giddey+Tyus Jones+Post > Reaves+Sabonis+Siakam+Markkanen | +1000 -1200 +2.8 +1.0 +15% +5.6
Cade+Tyus Jones+Post > Sabonis+Markkanen+Siakam | +1300 -1200 +2.9 +1.1 +16% +5.7
Cade+Tyus Jones+Post+Emanuel Sharp > Sabonis+Siakam+White+Hart | +1700 -1100 +3.7 +1.2 +17% +6.5
