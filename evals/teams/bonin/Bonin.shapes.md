# out > in | Score ΔBASE Δw Δw(season) ΔP(title) Δage | status

Counterparty: Bonin (161016). Contending — 3rd PF, 10.4% title (`Team Projections.md`). Columns: `Out | In` + Score + our five big numbers.

Texts 8/8/26: Brett opened — asked if he's looking to deal and what he wants. No reply until 9/28.

Texts 9/28/26: Brett offered Middleton for his '27 3rd. Michael: "Not bad, I'll think on it. But in general I'm trying to get younger instead of adding guys towards end of career." Won the title last year; has vets on his Fleaflicker trade block (Brett 9/28). Trade block 9/28 (Fleaflicker `isOnTradingBlock`): Sabonis, Markkanen, Nembhard, Draymond, Klay, DeRozan; no picks, no note. Target: his vets for our young pieces and picks.

Screening (9/10/26): 40 shapes simmed. Sims use our 35-body roster (same as eval). Net bodies ≤ +1. Do not float Too lopsided. Bonin is a short-term competitor — prefer shapes that don't load his year-1 much (`Δw (them)`). Every row re-priced 9/25/26 (Score, Δage). Bane+Gordon > Reaves held at Floor despite its Score: it adds to Bonin's season (+0.1 Δw (season) for him) and sits just under Too lopsided.

Screening (9/28/26): 56 young-for-vet shapes simmed on the no-Jon roster (Cade kept; Hlina overlay in). Michael's roster unchanged since 9/2 (checked on the wire 9/28). Every 9/28 row cuts his season, so none loads a competitor. Floor for non-Cade rows ≈ +400 Score. Cade rows are tiered against Jon's deal, Cade+2.09+'27 1st > SGA+Wells+McBride+Champagnie+Jaylin (+1800 +1100 +1.5 +0.6 +5% +4.1, `Jon.shapes.md`). Jon backed out 9/28, so the floor is a reference, not a live bid. Out-side picks: '28 1st 1425, Chris '27 2nd 900. In-side picks: Michael '27 3rd 357, Michael '27 1st 1524. Sharpe rows have no Δage (0 projected GP), nor Bona > Draymond. Draymond = Draymond Green; bare Green = Jalen Green. Smith, Green and Camara come from the Hlina deal after the auction, so their rows can't execute before it lands. Middleton > Michael '27 3rd fails on paper (Δw −0.26, ΔP −0.5) because the sim keeps Middleton over a pad body; in practice he is cut after the auction, so the deal is +357 BASE for free.

Texts 9/28/26 (Cade): Brett offered Cade > Reaves+Sabonis+Siakam. Michael: "Last one is a lot but interesting since Cade's a beast. Lemme think a bit" and "I'm trying to get younger". Expect a smaller counter. Counter screen (9/28, same roster): every Cade 2-for-1 fails ΔBASE except Reaves+Markkanen (ΔBASE −955, Below bar). A Cade deal needs Reaves+Sabonis plus a real third piece (Siakam, White or Hart) to clear the floor.

Fox re-price 9/28/26: the four Cade menu rows (Reaves+Sabonis+Siakam / +White, Reaves+Siakam+White, Reaves+Sabonis+Hart) priced with Chris's Middleton+Chris '27 2nd+own '27 2nd > Fox also applied on the Cade-kept roster (`$TMPDIR/ff-F`, 35 bodies). Middleton goes to Chris in that deal, so Middleton > Michael '27 3rd can't execute.

Fox deal executed 9/28 (Fleaflicker 485835). Middleton, Chris '27 2nd and own '27 2nd are Chris's now, so rows that send any of them can't be offered.

Texts 9/28/26 3:32p: Brett sent the three step-down rows (Status). Michael 4:09p countered Cade+Giddey > Reaves+Siakam+White+(2.11); fails ΔBASE (−3500). Counter screen on `$TMPDIR/ff-F` (config `$TMPDIR/ff-sim-bonin-counter-F.json`): his shape with a young cheap add in place of Giddey clears; 2.11 = Allen Graves, VALUE 634.

Texts 9/28/26 4:15p: Michael rejected the Walker/Kuminga/Sharpe counters: "Cade's amazing but that'll crush any depth I have. Don't love any of Walker, kuminga, sharpe". Wants a real rotation player back. Depth-back screen (same config): on his Reaves+Siakam+White core only Eason/Vassell clear (+1400–1500); keeping Siakam or White in play with Sabonis clears easily. No-2.11 and Harden (37, fits his get-younger aim) variants priced too (Brett: not tied to his 2.11). Body-even screen (Brett: keep his depth whole): 3-for-3 and 4-for-4 with Collins/Melton/Queta as cheap bodies clear; 4-for-4 Reaves+Sabonis+Siakam+White is best (+3000–3300). Giving him extra bodies (4-for-3) fails ΔBASE.

## Above floor

Cade > Reaves+Markkanen+Siakam | +3500 +1200 +2.6 +1.3 +17% +5.0
Cade > Reaves+Sabonis+Siakam | +3400 +1000 +3.1 +1.3 +16% +5.3 | Us proposed 9/28
Edey+Kuminga+Walker > Sabonis+Siakam | +3300 +1000 +2.0 +1.4 +15% +7.1
Edey+Sharpe+Kuminga > Sabonis+Markkanen | +3300 +1000 +1.6 +1.5 +17% +5.5
Cade+Eason+Collins+Melton > Reaves+Sabonis+Siakam+White | +3300 +600 +2.7 +1.4 +20% +4.4
Edey+Murray > Sabonis+Markkanen | +3200 +1100 +1.7 +1.3 +16% +4.8
Cade+Kuminga > Reaves+Sabonis+White+(2.11) | +3100 +700 +3.0 +1.2 +16% +4.6
Cade+Keegan Murray+Vassell > Reaves+Sabonis+Siakam+White | +3100 +200 +3.3 +1.6 +20% +5.3
Cade+Jabari Smith+Collins+Melton > Reaves+Sabonis+Siakam+White | +3000 +400 +2.4 +1.3 +19% +4.9
Edey+Suggs > Sabonis+Markkanen | +3000 +1000 +1.8 +1.2 +15% +5.2
Cade > Reaves+Sabonis+White | +2900 +800 +2.9 +1.2 +15% +5.2 | Us proposed 9/28 3:32p
Cade+Coby White+Camara > Reaves+Sabonis+Siakam+White | +2800 +400 +2.9 +1.4 +17% +5.0
Edey+Sharpe > Sabonis+White | +2800 +900 +1.7 +1.3 +14% +6.7
Sharpe+Kuminga > Sabonis | +2700 +800 +1.2 +1.2 +14% +6.4
Cade > Reaves+Siakam+Harden | +2600 +1000 +2.6 +1.1 +10% +7.4
Edey+Eason > Sabonis+White | +2600 +800 +1.7 +1.1 +13% +6.4
Smith+Kuminga+Walker > Siakam+Hart | +2600 +900 +1.2 +1.0 +12% +8.7
Edey+Murray+Walker > Sabonis+Markkanen | +2600 +700 +1.4 +1.2 +14% +5.0
Sharpe+Kuminga > Markkanen | +2500 +1000 +0.7 +1.0 +12% +5.3
Cade+Vassell > Reaves+Sabonis+Harden | +2400 +200 +2.8 +1.3 +14% +6.3
Cade+Keegan Murray > Reaves+Sabonis+Siakam+(2.11) | +2400 0 +2.7 +1.3 +17% +4.5
Cade > Sabonis+Siakam+White+Hart | +2400 -300 +3.8 +1.7 +19% +6.5
Kuminga+Walker > Siakam | +2400 +1000 +1.0 +0.8 +9% +9.1
Kuminga+Eason > Sabonis | +2400 +700 +1.2 +1.0 +13% +5.2
Murray+Walker > Markkanen+Draymond | +2400 +1200 +1.0 +0.8 +9% +5.5
Cade+Vassell > Reaves+Sabonis+Siakam | +2300 -200 +2.8 +1.3 +17% +5.1
Cade+Eason > Reaves+Sabonis+Siakam | +2300 -100 +2.8 +1.4 +17% +5.3
Cade+Coby White > Reaves+Sabonis+Siakam+(2.11) | +2300 +200 +2.3 +1.2 +15% +4.2
Cade+Walker > Reaves+Siakam+White+(2.11) | +2300 +600 +2.1 +0.9 +11% +5.2 | Us proposed 9/28 4:13p, rejected 4:15p
Cade+Jabari Smith > Reaves+Sabonis+White+(2.11) | +2300 +200 +2.3 +1.1 +15% +5.0
Eason+Kuminga > Markkanen | +2300 +900 +0.7 +0.8 +11% +4.1
Edey+Kuminga > Sabonis+Hart | +2200 +400 +1.8 +1.1 +12% +6.4
Cade > Clingan+Sabonis+Siakam | +2200 -300 +3.0 +1.5 +18% +3.6
Kuminga+'27 1st > Markkanen | +2200 +600 +1.3 +0.9 +12% +9.8
Cade+Kuminga > Reaves+Siakam+White+(2.11) | +2100 +300 +2.2 +0.9 +12% +5.2 | Us proposed 9/28 4:13p, rejected 4:15p
Cade > Reaves+Siakam+White | +2100 +400 +2.4 +1.0 +12% +5.9 | Us proposed 9/28 3:32p
Cade+Camara > Reaves+Sabonis+Siakam | +2000 -100 +2.7 +1.2 +14% +5.0
Cade+Jabari Smith > Reaves+Sabonis+Siakam | +2000 -300 +2.5 +1.3 +16% +5.8
Cade+Keegan Murray > Reaves+Sabonis+White+(2.11) | +2000 -200 +2.4 +1.2 +16% +4.2
Cade+Jalen Green > Reaves+Sabonis+Siakam+(2.11) | +2000 0 +2.5 +1.2 +13% +4.8
Cade > Reaves+Sabonis+Hart | +1900 0 +2.7 +1.1 +14% +4.9 | Us proposed 9/28 3:32p
Cade+Collins+Melton > Reaves+Sabonis+Harden | +1900 +100 +1.9 +1.0 +12% +5.1
Cade+Keegan Murray+Vassell+Collins > Reaves+Sabonis+Siakam+White | +1900 -600 +2.4 +1.3 +18% +4.6
Cade+Bridges+Collins+Queta > Reaves+Sabonis+Siakam+White | +1900 +200 +2.0 +1.0 +12% +3.9
Cade+Eason > Reaves+Sabonis+White | +1900 -400 +2.5 +1.2 +16% +5.1
Cade+Coby White > Reaves+Sabonis+White+(2.11) | +1900 0 +2.1 +1.0 +14% +4.0
Kuminga+Walker > White | +1800 +800 +0.7 +0.6 +7% +8.8
Sharpe+Kuminga > Siakam | +1800 +400 +0.7 +0.9 +10% +8.5
Edey > Sabonis+Draymond | +1700 +500 +1.5 +0.8 +8% +7.2
Murray+Walker > Markkanen | +1700 +700 +0.4 +0.7 +8% +3.7
Smith+'27 1st > Clingan | +1700 +400 +0.7 +0.8 +11% +1.2
Williams+Walker > Hart+Jerome | +1600 +200 +1.1 +0.9 +10% +6.5
Simons+Walker > White | +1600 +800 +0.7 +0.4 +6% +6.6
Murray+Kuminga > Markkanen | +1600 +400 +0.5 +0.7 +9% +3.4
Eason+Kuminga > Siakam | +1500 +300 +0.7 +0.8 +9% +7.3
Eason+Kuminga > Harden | +1500 +700 +0.6 +0.8 +5% +11.9
Sharpe+Walker > White | +1500 +500 +0.4 +0.7 +8% +9.1
Kuminga+'28 1st > Siakam | +1400 0 +1.3 +0.9 +10% +13.9
Murray+'27 1st > Clingan | +1400 0 +0.9 +0.9 +11% -0.1
Camara+Walker > Siakam | +1300 +600 +0.5 +0.4 +4% +6.7
Eason+Walker > White | +1200 +400 +0.4 +0.5 +6% +7.3
Melton+Gordon > White | +1100 +600 +0.1 +0.2 +4% +2.3
Smith+Kuminga > Siakam | +1100 +200 +0.4 +0.6 +7% +9.1
Eason+Kuminga > Zubac | +1100 +400 +0.4 +0.5 +5% +4.3
Kuminga > Jerome | +1000 +200 +0.8 +0.5 +6% +5.2
Edey > Sabonis | +1000 0 +1.0 +0.6 +7% +6.0
Green > Siakam | +1000 +500 +0.6 +0.6 +2% +7.8
Bane > Markkanen | +1000 +400 +0.3 +0.4 +5% +1.0
Williams+Sharpe > Harden | +900 +100 +0.1 +1.0 +5% +12.3
Sharpe > Hart | +900 +100 +0.5 +0.6 +6% ?
Walker > Nembhard | +900 +700 +0.3 +0.2 +2% +3.6
Williams+Kuminga > White | +900 -100 +0.3 +0.7 +8% +7.7
Suggs+Walker > Harden | +900 +400 +0.4 +0.6 +2% +12.2
Edey+Suggs > Clingan+Powell | +800 0 +0.5 +0.5 +5% +1.1
Smith+Walker > White | +800 +200 +0.1 +0.3 +4% +8.8
Murray+Vassell > Markkanen | +700 0 +0.2 +0.4 +7% +3.2
Vassell+Eason > Siakam | +700 -100 +0.4 +0.5 +7% +6.8

## Floor

Cade+Vassell > Reaves+Sabonis+White | +1800 -400 +2.6 +1.1 +16% +5.0
Cade+Coby White > Reaves+Sabonis+Harden | +1800 -100 +2.2 +1.2 +12% +6.0
Cade+Keegan Murray > Reaves+Sabonis+Harden | +1800 -300 +2.5 +1.3 +14% +6.3
Cade+Collins+Melton > Reaves+Sabonis+Siakam | +1800 -200 +2.0 +1.0 +15% +3.9
Cade+Queta+Melton > Reaves+Sabonis+Siakam | +1800 -200 +2.2 +1.1 +14% +4.4
Cade > Reaves+Sabonis+Michael '27 1st | +1800 +400 +1.5 +0.8 +11% +2.6
Cade > Sabonis+Markkanen+Siakam | +1800 -700 +2.9 +1.4 +18% +5.7
Cade+Suggs > Reaves+Sabonis+White+(2.11) | +1800 -300 +2.5 +1.1 +15% +4.5
Cade+Keegan Murray > Reaves+Sabonis+Siakam | +1700 -600 +2.6 +1.3 +16% +5.1
Cade+Coby White > Reaves+Sabonis+Siakam | +1700 -400 +2.2 +1.2 +15% +4.8
Cade > Reaves+Sabonis+Nembhard | +1700 -100 +2.2 +1.0 +13% +4.1
Cade+Naz Reid > Reaves+Sabonis+White+(2.11) | +1700 -200 +2.2 +1.0 +13% +3.9
Cade+Sharpe > Reaves+Siakam+White+(2.11) | +1700 0 +2.0 +1.0 +12% +5.1 | Us proposed 9/28 4:13p, rejected 4:15p
Cade+Giddey > Reaves+Sabonis+Siakam+Markkanen | +1600 -800 +3.1 +1.3 +17% +5.6
Cade+Coby White+Camara+Collins > Reaves+Sabonis+Siakam+White | +1600 -400 +2.0 +1.1 +15% +4.5
Cade+Jalen Green > Reaves+Sabonis+White+(2.11) | +1600 -300 +2.3 +1.1 +12% +4.6
Cade+Jabari Smith+Melton > Reaves+Sabonis+Siakam | +1500 -700 +1.9 +1.2 +16% +5.3
Bane+Gordon > Reaves | +1500 +1200 -0.2 +0.2 +3% -1.0
Cade+Eason > Reaves+Siakam+White+(2.11) | +1500 -100 +1.8 +0.9 +12% +5.0
Cade+Vassell > Reaves+Siakam+White+(2.11) | +1400 -100 +1.9 +0.8 +11% +4.9
Cade+Collins+Melton > Reaves+Sabonis+White | +1400 -400 +1.7 +0.8 +14% +3.8
Suggs+Kuminga > Siakam | +700 -200 +0.5 +0.6 +6% +7.3
Garland+Kuminga > Reaves | +700 +200 0.0 +0.3 +4% +1.7
Eason > Hart | +700 0 +0.5 +0.4 +5% +6.1
Kuminga > Nembhard | +700 +400 +0.4 +0.2 +2% +2.7
Walker+Chris '27 2nd > Hart | +600 -200 +0.8 +0.4 +5% +11.1
Bane+Walker > Markkanen | +400 -100 0.0 +0.3 +4% +1.6

## Below bar

Cade+Camara+Melton > Reaves+Sabonis+Siakam | +1400 -600 +2.1 +1.1 +13% +4.6
Cade+Gordon+Queta > Reaves+Sabonis+Siakam | +1300 -700 +2.0 +1.0 +14% +3.8
Cade+Collins+Gordon > Reaves+Sabonis+Siakam | +1300 -600 +1.8 +0.9 +15% +3.4
Cade+Coby White > Reaves+Markkanen+Siakam | +1300 -200 +1.4 +0.8 +12% +4.5
Cade+Collins+Queta > Reaves+Sabonis+Siakam | +1200 -600 +1.8 +0.9 +12% +4.0
Cade+Coby White > Reaves+Sabonis+White | +1200 -600 +2.0 +1.0 +14% +4.7
Cade+Mark Williams > Reaves+Siakam+White+(2.11) | +1300 -300 +1.8 +1.0 +12% +5.1
Cade+Jabari Smith > Reaves+Siakam+White+(2.11) | +1200 -200 +1.5 +0.8 +11% +5.6
Cade+Giddey > Reaves+Sabonis+Siakam+White+(2.11) | +1200 -900 +2.9 +1.2 +14% +5.7
Cade+Camara > Reaves+Siakam+White+(2.11) | +1100 -100 +1.7 +0.7 +8% +4.8
Cade+Bridges+Melton > Reaves+Sabonis+Siakam | +1000 -600 +1.7 +1.0 +10% +3.9
Cade+Keegan Murray > Reaves+Siakam+White+(2.11) | +900 -600 +1.6 +0.8 +10% +4.8
Cade+Coby White > Reaves+Siakam+White+(2.11) | +800 -400 +1.3 +0.7 +9% +4.6
Cade+Suggs > Reaves+Siakam+White+(2.11) | +700 -700 +1.7 +0.8 +10% +5.1
Cade+Coby White > Reaves+Siakam+Harden | +600 -400 +1.4 +0.9 +7% +6.8
Cade+Naz Reid > Reaves+Siakam+White+(2.11) | +600 -600 +1.4 +0.6 +8% +4.5
Cade+Jalen Green > Reaves+Siakam+White+(2.11) | +400 -700 +1.5 +0.7 +7% +5.2
Cade+Bridges+Melton > Reaves+Sabonis+White | +500 -800 +1.4 +0.8 +9% +3.7
Walker > DeRozan | +400 +300 +0.1 +0.2 0% +14.0
Cade+Bridges+Collins > Reaves+Sabonis+Siakam | +300 -1000 +1.3 +0.8 +8% +3.6
Cade+Bridges+Collins > Reaves+Sabonis+Harden | +300 -600 +1.3 +0.8 +4% +4.8
Kuminga > Draymond+Klay | +200 -100 +0.6 +0.2 +2% +12.5
Walker > Draymond | +200 +100 +0.2 +0.1 0% +13.4
Cade > Reaves+Markkanen | +100 -1000 +1.0 +0.6 +9% +3.8
Smith+Walker+'27 1st > Siakam | -100 -1000 +0.3 +0.6 +7% +10.9
Garland > Markkanen | -400 -800 +0.1 +0.2 +4% +2.6
Garland+Reid > Clingan+Powell | -700 -900 0.0 +0.2 +2% -1.0


## Too lopsided

Our ΔBASE ≥ +1250 — reference only; do not float.

Bridges+Collins > Reaves+Powell | +3900 +3600 +0.5 +0.2 +1% +1.1
Bridges+Coby White > Reaves | +1500 +1800 -0.6 +0.1 -3% +0.7
Collins > Zubac | +1700 +1400 +0.4 +0.2 +2% +0.5
Bridges+Simons > Siakam+Nembhard | +1500 +1400 +0.7 +0.4 -2% +2.5
Green+'27 1st > Reaves | +2200 +1300 +0.8 +0.8 +7% +6.1

## Doesn't meet our minimums

Cade > Sabonis | -6000 -5600 -0.2 -0.4 -4% +5.4
Giddey+Edey > Clingan | -5400 -4000 -1.4 -0.7 -12% -1.6
Cade > Reaves | -4400 -3700 -0.6 -0.5 -6% +3.3
Cade+Giddey > Reaves+Siakam+White+(2.11) | -3300 -3500 +0.5 +0.1 +1% +5.6 | Michael proposed 9/28 4:09p, we declined 4:13p
Giddey+'27 1st > Clingan | -3000 -2800 -0.2 -0.1 -1% +0.1
Giddey > Siakam | -2900 -2300 -0.3 -0.3 -5% +8.5
Garland+Gordon > Siakam | -2700 -2200 -0.6 -0.2 -4% +4.4
Garland+'27 1st > Siakam | -2600 -2800 +0.1 +0.1 +1% +8.5
Cade > Markkanen+Siakam | -2500 -3200 +0.8 +0.3 +6% +5.9
Cade > Sabonis+Siakam | -2400 -3400 +1.4 +0.6 +7% +6.3
Garland+Collins > Sabonis | -1700 -1800 -0.3 0.0 +1% +2.8
Garland > White | -1600 -1600 -0.1 0.0 0% +5.5
Cade > Sabonis+Markkanen | -1500 -2800 +1.3 +0.6 +10% +4.9
Reid+Suggs > Zubac | -1500 -1100 -0.5 0.0 -4% +3.1
Giddey+Gordon > Sabonis+Powell | -1400 -1600 +0.3 0.0 +1% +5.3
Coby White+Suggs > White | -1300 -1200 -0.6 +0.1 -1% +6.1
Bane+Suggs > Clingan | -900 -1000 -0.4 +0.2 0% -4.6
Garland+Suggs > Reaves | -900 -800 -0.5 +0.1 -1% +2.1
Cade > Reaves+Siakam | -700 -1500 +1.0 +0.5 +6% +5.3
Giddey > Reaves | -200 -100 -0.2 -0.1 -1% +4.3
Cade > Sabonis+Markkanen+Nembhard | -100 -1800 +2.0 +0.8 +12% +4.5
Green+Simons > Siakam | -100 -200 +0.2 +0.4 -1% +7.3
Green+Smith > Markkanen | -100 -200 -0.4 +0.3 +1% +5.2
Garland+Gordon > Reaves | 0 0 -0.4 -0.1 0% +0.2
Bane+Collins > Clingan | 0 -100 -0.5 +0.1 +1% -6.0
Middleton > Michael '27 3rd | +200 +200 -0.3 -0.1 -1% -16.1 | Us proposed 9/28
Bona > Draymond | +300 +200 +0.3 +0.1 -1% ?
Cade > Reaves+Sabonis | +300 -1200 +1.5 +0.8 +11% +4.4
Cade+Collins+Queta+Melton > Reaves+Sabonis+Siakam | +600 -1000 +1.3 +0.8 +12% +3.8
Green+Bridges > Siakam+Hart | +600 +400 +0.5 +0.6 -2% +5.2
Cade > Sabonis+Siakam+White | +700 -1500 +2.7 +1.3 +15% +6.6
Collins+Bridges > Clingan | +1000 +1100 -0.4 +0.1 -2% -6.2
