# out > in | Score ΔBASE Δw Δw(season) ΔP(title) Δage | status

Counterparty: Josh (161024). Contending: 4th PF (30,100), 11.8 W, 9.4% title, year 1 (`Team Projections.md`; years 2+ read: the '27-28+ table, no trades). Win-now (Brett 9/27). Full at 38, like us: bodies he nets get cut by full Score (Capela, then Conley or Plowden, per `cut_them`). Columns: `Out | In` + Score + our five big numbers (`trades` §The big numbers).

Refresh 9/29/26: every row re-priced on the 9/29 rosters (F/C flex, full-Score cuts, 9/29 boards and pick prices). Cade is still ours, so rows lose the old `if Cade (Siakam)` / `+Fox` scenario tags. Rows where we took his net +body now send our cut (Tyus Jones, plus Post on 1-for-3s) in Out. Dropped rows (Q9): anything sending Middleton, Chaney, own '27 2nd (Chris's since the 9/28 Fox deal), Matković (Brian's) or 2.09, or taking Jon 3.02 / 3.10 (spent on Peat / Conwell). Duplicate rows merged.

Re-priced 9/29 (`--refresh`) after the sim switched ΔBASE and Δage to the `.team.md` evals. Rows moved by about ±200 Score at most, no `eval_gap`, no `cut_us`. One tier move: Cade+Butler+Tyus Jones > Murray+Porziņģis+Barrett+Josh '28 1st went from Below bar to Doesn't meet our minimums (ΔBASE −1016).

Re-priced 9/29 (7b) after his '28 picks moved from the open 1.01–1.12 range to the 01–09 band ('28 1st 1335 → 1482, 2nd 541 → 587, 3rd 217 → 242, 4th 91 → 106). The 34 rows holding a '28 pick were re-simmed; ΔBASE rose by the pick gain, win columns unchanged. Tier moves: Cade+Gordon > Mitchell+Murray+Josh '28 1st (+1300) and Cade+Collins > Mitchell+Murray+Josh '28 1st (+1400) went from Below bar to Too lopsided. Cade+Butler+Tyus Jones > Murray+Porziņģis+Barrett+Josh '28 1st went from Doesn't meet our minimums back to Below bar (ΔBASE −869).

Picks (`pick_prices.py` 9/29): his '27 2nd (2.09) 645 · Hlina '27 3rd 284 · '27 4th 129 · '28 on his `sim.py future` own-pick band 01–09 (no-trades read): 1st 1482 (band 2076–1038, so ΔBASE on '28-1st rows is about +600/−450) · 2nd 587 · 3rd 242 · 4th 106. Ours: '27 1st (1.12) 1176 · '27 4th 93.

Thread: 9/1 he took Kawhi+Turner for Bridges+Gordon+Collins ("makes sense for me trying to win now"; sorry to lose Collins). 9/25 he passed on Kyrie/Butler ("don't want to give up more depth") and offered 2 firsts + Porziņģis for Cade; Brett disliked it. He dislikes 3-for-1s. 9/27 7:20p "Hell nah, appreciate the offer though" to both 2-for-2s Brett sent (Mitchell+Towns and Murray+Towns cores). Brett: he isn't creative and has named his price (Porziņģis + two 1sts); he values the Mitchell+Towns pair highly.

Kuminga (9/28 texts): Middleton for his '27 3rd (no) → 11:13a he offered "a 2nd for Kuminga or Naz Reid" (2nd unnamed) → Brett countered Kuminga for his '28 2nd + Hlina '27 3rd, then Chaney for any 3rd → 11:20a "Nah I'm good". Every pick-for-Kuminga row now fails ΔP(title) (−0.6%) as well as sitting at the Δw gate (−0.25). His 4ths don't fix that, since picks move no bodies. Kuminga > Lillard is the body-for-body version.

Embiid (9/28 texts): Brett sent Naz Reid+Keegan Murray > Towns · Naz Reid+Suggs > Towns · Kuminga+Collins > Embiid. Josh ignored Towns and asked Naz Reid+Kuminga+Collins > Embiid. Brett countered Kuminga+Collins+Chaney > Embiid and Naz Reid+Kuminga+Collins > Embiid+Allen → "No I'm good, I wasn't even sure if I would do the trade I sent I was just feeling it out". He declined Naz Reid > Embiid and Butler > Embiid ("Nah I got to keep him for that value"). "Good value on fox. I told Chris I would have gave him more if I knew he was moving." Takeaways: he'll move Embiid at about three of our depth pieces, he won't discuss Towns, and he likes Fox.

Benchmarks:
- Cade rows: Michael's live counter, Cade > Reaves+Sabonis+Siakam (undecided), prices at +3200 +700 +3.1 +1.2 +17% +5.4 on 9/29 (we cut Tyus Jones+Post; `Bonin.shapes.md` row, re-simmed on `.team.md` BASE). Floor = within ~250 of it. No Josh Cade row gets there (best +2300), so every Cade row is Below bar or worse. His non-star pieces carry too little BASE, and without Mitchell, Towns or Murray nothing gets close.
- Depth rows (our depth, Fox or a '27 1st for Kawhi / Towns / Embiid / Murray / Lillard / Barrett): tier against holding (Score 0). He's full, so shapes that net him bodies make him cut Capela / Conley / Plowden.
- Nearly every live row costs him Δw (season). The exceptions are Collins > Barrett (+0.2 for him) and Naz Reid+Kuminga+Collins > Murray (+0.1).

Avenues ruled out: his 9/25 Porziņģis + picks offer for Cade (ΔBASE about −4600) and Kawhi / Embiid as Cade centerpieces (low BASE). Towns 1-for-1s for one depth piece (Naz Reid / Jabari Smith / Camara) are ≥ +2100 ΔBASE, so they sit in Too lopsided. Mitchell for depth fails ΔP(title), as do the Edey+Green 2-for-2s.

## Above floor

Naz Reid+Kuminga+Gordon+'27 1st > Towns+Kawhi | +3300 +1200 +1.5 +1.0 +16% +7.5
Fox+Tyus Jones > Kawhi+Barrett | +2400 +900 +1.1 +0.6 +13% +3.5
Gordon > Kawhi | +2200 +900 +0.9 +0.6 +10% +4.3
Collins > Kawhi | +2100 +1000 +0.7 +0.5 +10% +6.3
Fox > Towns | +2100 +1200 +0.7 +0.5 +7% +2.1
Naz Reid+Collins+Gordon+Kuminga+'27 1st > Towns+Kawhi | +2100 +500 +0.7 +0.7 +13% +6.5
Butler > Embiid | +2000 +900 +0.7 +0.7 +9% -4.5 | Josh rejected 9/28
Fox+Tyus Jones > Embiid+Barrett | +2000 +800 +0.8 +0.5 +11% +1.2
Edey > Towns | +2000 +1200 +0.7 +0.5 +5% +6.5
Camara+Naz Reid > Towns+Payton | +1700 +1100 +0.3 +0.3 +5% +4.1
Collins > Embiid | +1700 +900 +0.4 +0.4 +7% +3.5
Camara+Naz Reid > Towns | +1600 +1100 +0.2 +0.3 +5% +4.1
Jabari Smith+Naz Reid > Towns | +1600 +900 0.0 +0.3 +6% +5.6
Collins+'27 4th > Embiid | +1600 +800 +0.4 +0.4 +7% +4.1
Jabari Smith+Naz Reid > Towns+Plowden | +1500 +1000 0.0 +0.3 +6% +5.6
Gordon+Kuminga > Kawhi | +1500 +300 +0.7 +0.5 +10% +5.0
Collins+Kuminga > Kawhi | +1400 +300 +0.5 +0.5 +10% +6.7
Keegan Murray+Naz Reid > Towns+Small | +1400 +800 +0.1 +0.4 +6% +4.2
Camara > Embiid | +1400 +600 +0.6 +0.4 +6% +6.1
Naz Reid+Kuminga+Gordon > Towns | +1300 +600 -0.1 +0.2 +6% +2.5
Jabari Smith > Embiid | +1300 +500 +0.4 +0.4 +8% +9.1
Suggs+Kuminga+Collins > Murray | +1300 +700 0.0 +0.4 +4% +2.5
Keegan Murray+Naz Reid > Towns | +1200 +600 +0.1 +0.4 +6% +4.2
Naz Reid+Kuminga+Collins > Towns | +1200 +700 -0.2 +0.2 +5% +3.1
Collins > Barrett | +1100 +900 -0.1 -0.1 +3% -2.7
Suggs+Naz Reid > Towns | +1100 +500 +0.1 +0.4 +5% +4.6
Melton > Lillard | +1100 +300 +0.6 +0.4 +7% +7.9
Kuminga+Gordon > Embiid | +1100 +200 +0.4 +0.4 +8% +2.2
Jabari Smith+Kuminga > Kawhi | +1000 -100 +0.4 +0.6 +10% +11.8
Naz Reid+Kuminga+Collins > Murray | +1000 +800 -0.2 +0.1 +1% +1.8
Kuminga > Lillard | +1000 +100 +0.8 +0.4 +7% +12.2
Kuminga+Collins > Embiid | +1000 +200 +0.2 +0.3 +7% +3.9
Green > Kawhi | +900 +100 +0.6 +0.5 +5% +10.7
Collins+Gordon > Kawhi | +900 +200 +0.1 +0.2 +7% +5.5
Naz Reid+Kuminga+Collins > Embiid+Allen | +800 +200 +0.2 +0.4 +5% +2.8 | Josh rejected 9/28
Kyrie > Kawhi | +800 0 +0.5 +0.4 +7% +0.8
Naz Reid > Embiid | +800 +100 +0.3 +0.3 +6% +5.4 | Josh rejected 9/28
Jabari Smith > Barrett | +700 +500 -0.1 +0.1 +3% +2.9
Naz Reid+Green > Towns+Payton | +700 +500 0.0 +0.3 +1% +5.0
Edey+Collins > Towns | +600 +400 -0.1 +0.1 +2% +4.5
Camara+Gordon > Kawhi | +600 -200 +0.2 +0.2 +7% +6.7
Jabari Smith+Gordon > Kawhi | +500 -300 0.0 +0.3 +8% +8.7
Green > Embiid | +400 0 +0.3 +0.4 +3% +7.9
Naz Reid+Kuminga > Kawhi | +400 -500 +0.4 +0.4 +7% +8.4
Collins > Lillard | +400 0 +0.2 +0.1 +4% +7.2

## Floor

Kuminga+Collins+Gordon > Kawhi | +200 -500 -0.2 +0.1 +6% +5.7
Naz Reid+Kuminga > Embiid | 0 -600 0.0 +0.3 +5% +5.6
Naz Reid+Kuminga+'27 4th > Embiid | -100 -700 0.0 +0.3 +5% +6.0

## Below bar

Cade+Gordon+Melton > Mitchell+Towns+Barrett | +2300 +1000 +1.2 +0.8 +9% +3.2
Cade+Collins+Melton > Mitchell+Towns+Barrett | +2200 +1100 +1.0 +0.8 +9% +3.4
Cade+Butler > Mitchell+Towns+Josh '27 2nd+Josh '28 2nd | +2000 +1000 +1.0 +0.9 +6% +2.2 | Josh rejected 9/27
Cade+Gordon+Butler > Mitchell+Towns+Barrett | +2000 +700 +1.1 +0.9 +9% +2.4
Cade+Collins+Simons > Mitchell+Towns+Barrett | +2000 +800 +1.2 +0.8 +8% +3.6
Cade+Collins+Butler > Mitchell+Towns+Barrett | +1900 +700 +0.9 +0.8 +9% +2.6
Cade+Collins+Melton > Mitchell+Towns+Allen | +1800 +900 +1.2 +0.9 +4% +3.6
Cade+Gordon > Mitchell+Towns+Josh '27 2nd+Josh '28 2nd | +1700 +900 +0.9 +0.7 +5% +2.4
Cade+Gordon > Mitchell+Murray+Josh '27 2nd+Josh '28 2nd | +1700 +1000 +1.0 +0.7 +2% +1.9
Cade+Gordon+Collins > Mitchell+Towns+Barrett | +1700 +600 +0.9 +0.6 +8% +2.8
Cade+Tyus Jones > Mitchell+Towns | +1600 +400 +1.5 +0.9 +7% +5.5
Cade+Tyus Jones > Mitchell+Murray | +1600 +500 +1.6 +1.0 +4% +4.9
Cade+Collins > Murray+Towns+Josh '28 1st+Josh '27 2nd | +1600 +800 +0.6 +0.4 +7% +1.3 | Josh rejected 9/27
Cade+Gordon > Murray+Towns+Josh '28 1st+Josh '28 2nd | +1600 +700 +0.8 +0.5 +7% +1.1
Cade+Collins > Murray+Towns+Josh '28 1st+Josh '28 2nd | +1500 +700 +0.6 +0.4 +7% +1.3
Cade+Gordon+Collins > Mitchell+Murray+Barrett | +1500 +700 +0.9 +0.6 +5% +2.3
Cade+Gordon+Collins > Mitchell+Towns+Josh '28 1st+Josh '27 2nd | +1400 +1100 +0.1 +0.3 +1% +0.8
Cade+Gordon+Collins > Mitchell+Towns+Josh '28 1st+Josh '28 2nd | +1300 +1000 +0.1 +0.3 +1% +0.7
Cade+Butler > Murray+Towns+Josh '28 1st | +1300 +200 +0.8 +0.7 +8% +1.6
Cade+Gordon+Collins > Mitchell+Towns+Allen | +1300 +500 +1.1 +0.8 +4% +3.1
Cade+Collins+Melton > Murray+Towns+Barrett | +1200 -100 +0.9 +0.6 +11% +3.1
Cade+Melton > Mitchell+Towns | +1100 +100 +1.1 +0.8 +5% +4.9
Cade+Collins+Butler > Mitchell+Towns+Josh '28 1st | +1000 +500 +0.1 +0.6 +3% +1.2
Cade+Tyus Jones+Post > Towns+Allen+Barrett+Josh '28 1st | +1000 0 +1.1 +0.5 +7% +2.2
Cade+Gordon > Murray+Towns+Josh '28 1st | +1000 +100 +0.8 +0.5 +7% +1.8
Cade+Collins > Murray+Towns+Josh '28 1st | +900 +100 +0.6 +0.4 +7% +2.0
Cade+Tyus Jones > Mitchell+Barrett+Josh '28 1st+Josh '28 2nd | +800 +500 +0.5 +0.3 +1% +0.9
Cade+Gordon+Collins > Mitchell+Towns+Josh '28 1st | +700 +400 +0.1 +0.3 +1% +1.4
Cade+Butler > Mitchell+Murray | +700 -100 +1.0 +0.9 +3% +3.4
Cade+Gordon+Collins > Mitchell+Towns+Wiggins | +600 -200 +0.9 +0.6 +5% +3.7
Cade+Tyus Jones > Murray+Towns | +600 -700 +1.4 +0.7 +9% +5.2
Cade+Kyrie > Mitchell+Towns+Josh '28 1st | +600 +300 +0.6 +0.5 +1% +0.4
Cade+Collins > Mitchell+Murray | +300 -100 +0.8 +0.6 0% +3.7
Cade+Tyus Jones+Post > Murray+Porziņģis+Barrett+Josh '28 1st | +300 -300 +0.8 +0.2 +5% +1.9
Cade+Tyus Jones > Mitchell+Barrett+Josh '28 1st | +200 -100 +0.5 +0.3 +1% +1.6
Cade+Butler+Tyus Jones > Murray+Porziņģis+Barrett+Josh '28 1st | -400 -900 +0.3 +0.2 +4% +0.4

## Too lopsided

Camara > Towns | +3800 +2600 +1.1 +0.6 +9% +4.5
Jabari Smith > Towns | +3700 +2500 +0.9 +0.7 +10% +7.5
Fox > Mitchell | +3200 +2500 +0.9 +0.8 +3% +1.3
Naz Reid > Towns | +3200 +2100 +0.9 +0.6 +9% +3.8
Fox+Tyus Jones > Towns+Gillespie | +3200 +1900 +1.3 +0.6 +10% +1.0
Naz Reid+Collins+Gordon+Kuminga > Towns+Kawhi | +3300 +1600 +0.7 +0.7 +13% +4.3
Naz Reid+Collins+Kuminga+Gordon > Towns+Embiid | +2800 +1500 +0.4 +0.6 +11% +2.9
Suggs+Kuminga > Murray | +2600 +1500 +0.9 +0.8 +7% +4.4
Naz Reid+Kuminga > Towns | +2600 +1500 +0.6 +0.6 +9% +4.0
Naz Reid+Collins > Towns | +1900 +1400 0.0 +0.3 +5% +2.9
Cade+Collins > Mitchell+Murray+Josh '28 1st | +1800 +1400 +0.8 +0.6 0% +1.8
Fox > Murray | +2100 +1300 +0.7 +0.5 +6% +0.8
Cade+Gordon > Mitchell+Murray+Josh '28 1st | +1900 +1300 +1.0 +0.7 +2% +1.5

## Doesn't meet our minimums

Naz Reid > Josh '28 2nd | -1800 -1000 -1.0 -0.5 -7% -9.1
Naz Reid > Josh '27 2nd | -1800 -900 -1.0 -0.5 -7% -8.1 | Josh proposed 9/28
Naz Reid+Kuminga+Collins > Embiid | -1400 -1300 -0.8 -0.2 +1% +4.7 | Josh proposed 9/28
Cade+Tyus Jones > Towns+Barrett+Josh '28 1st | -900 -1300 +0.3 0.0 +5% +1.8
Cade+Tyus Jones > Mitchell+Porziņģis+Josh '28 1st | -900 -700 +0.3 +0.1 -3% +2.5
Edey+Green > Murray+Payton | -700 -300 0.0 +0.2 -6% +5.1
Naz Reid+Collins > Embiid | -700 -700 -0.6 -0.1 +1% +4.5
Naz Reid+Kuminga > Barrett | -600 -500 -0.4 -0.2 +1% -0.6
Kuminga+Collins+Gordon > Embiid | -300 -600 -0.5 -0.1 +4% +2.9
Kuminga > Josh '28 2nd | -100 -100 -0.3 -0.1 -1% -6.0 | Josh proposed 9/28
Cade+Butler > Mitchell+Barrett+Josh '28 1st+Josh '28 2nd | -100 -100 -0.1 +0.3 0% -0.6
Kuminga > Josh '27 2nd | -100 0 -0.3 -0.1 -1% -5.0 | Josh proposed 9/28
Kuminga > Josh '28 2nd+Josh '27 4th | 0 0 -0.3 -0.1 -1% -5.9
Kuminga > Josh '27 2nd+Josh '28 4th | 0 +100 -0.3 -0.1 -1% -5.1
Kuminga > Josh '28 2nd+Hlina '27 3rd | +100 +200 -0.3 -0.1 -1% -5.8 | Josh rejected 9/28
Kuminga > Josh '27 2nd+Josh '28 3rd | +200 +200 -0.3 -0.1 -1% -5.2
Edey+Green > Mitchell+Payton | +300 +800 +0.1 +0.5 -8% +5.6
Cade+Tyus Jones > Mitchell+Allen+Josh '28 1st+Josh '28 2nd | +400 +300 +0.7 +0.5 -3% +1.4
Cade+Gordon+Collins > Mitchell+Murray+Josh '28 1st | +500 +500 +0.1 +0.3 -3% +0.9
Cade+Kyrie > Mitchell+Murray+Josh '28 1st | +500 +400 +0.6 +0.6 -2% -0.1
Edey+Collins > Murray | +500 +500 -0.1 +0.1 -1% +3.1
Edey+Naz Reid > Mitchell | +600 +900 0.0 +0.3 -6% +4.4
Naz Reid+Collins+Gordon > Towns | +600 +500 -0.7 -0.1 +1% +2.1
Cade+Bridges > Mitchell+Murray+Josh '28 1st | +800 +1000 +0.5 +0.5 -6% +1.7
Poeltl > Allen | +800 +500 +0.6 +0.4 -1% -2.6
Naz Reid+Collins+Melton > Towns | +1300 +1000 -0.5 +0.1 +3% +2.8
