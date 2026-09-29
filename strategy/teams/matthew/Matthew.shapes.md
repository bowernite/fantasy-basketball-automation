# out > in | Score ΔBASE Δw Δw(season) ΔP(title) Δage | status

Counterparty: Matthew Pook, Pharaoh Mattankhamun-Ra (160941). Not Hlina (Matthew the Apostle). Tanking: year 1 11th PF (26,187), 5.2 W, 0% title (Team Projections, 9/29). Years 2+ read: `Team Projections.md` '27-28+ table (no trades). His roster is young, so send him young players and picks; older or short-window players only go as small add-ons. He has 37 bodies and 1 open slot.

Rules:
- 9/25: no In-side Amen shapes. He won't trade Amen, whom we just sent him.
- 9/25: Wemby is untouchable (Brett). Wemby rows are reference only.
- 9/25: after two Johnson hypotheticals he asked "Any hypotheticals without Johnson?"
- 9/28: no In-side Ausar shapes. At 3:34p he turned down both Ausar rows: "I just can't imagine your pick being higher than 8 or 9 in a not so strong draft" and "how could I split up the brothers right after getting them". He discounts our '27 1st. Ausar rows are reference only.

Negotiation: 9/25 he rejected Cade + picks > Barnes+Harper+Ausar+Black, and we floated Cade+Kuminga+picks > Wemby+Ausar+Black. Those rows used spent picks and are deleted. 9/25 he said "It'd probably be something around Scottie and a 1st for Cade", so his Barnes ≈ Cade less a 1st. 9/28 3:39p Brett sent the three Barnes rows marked proposed. 4:11p Matthew: "I like edey but am scared by the injuries but may need a little more depth looking at my team."

Cade benchmark: the Cade sweepstakes is over. Todd withdrew 9/27 and Jon passed 9/28. Cade is still ours, and Michael's Cade thread is undecided. Cade rows tier against Michael's Cade+Tyus Jones+Post > Reaves+Sabonis+Siakam, re-priced body-even 9/29 on his roster: +3200 +700 +3.1 +1.2 +17% +5.3. Within ~250 = Floor, clearly below = Below bar. No live Cade row is within 250: the two closest (+3100) are now Too lopsided. Non-Cade rows tier by judgment: Floor ≈ +700 to +1500 Score.

Refresh 9/29/26 (`sim_run.py --refresh`, 9/29 rosters and projections, F/C flex, full-Score cut rule):
- Deleted rows whose assets moved: every '26 pick (our 2.09; his 1.06 is Burries, his 2.05 is Stirtz at Joe), Chris '27 2nd and our own '27 2nd (to Chris for Fox), Matthew '28 1st (to Mitch), Chaney Johnson (dropped), Matković (to Brian). Don '27 2nd is now Mitch '27 2nd.
- Our picks, off the 9/29 canonical table: '27 1st 1176 · '28 1st 1335 · '28 2nd 541 · Mitch '27 2nd 694 · '27 3rd 206.
- Body-even: rows where the sim cut our bodies now carry the cut in Out (Tyus Jones, then Post). The two rejected Ausar rows keep their floated body.
- Harper = Dylan Harper. Jabari = Jabari Smith. Green = Jalen Green.
- 4ths: no rows priced. Our '27 4th (93) is a cheap sweetener if he wants a small add.
- Re-priced 9/29 (`--refresh`) after the sim switched ΔBASE and Δage to the `.team.md` evals. Rows moved by at most ±200 Score. Two Cade > Johnson+Barnes rows went from Floor to Too lopsided (ΔBASE +1283 and +1406, against the +1250 cutoff).

## Above floor

Edey+Jabari+'27 1st+Mitch '27 2nd > Barnes | +1700 +1200 -0.1 +0.1 +5% +3.0 | Us proposed 9/28

## Floor

Giddey+'27 1st > Barnes | +1300 +1000 0.0 0.0 +3% +2.7 | Us proposed 9/28
Edey+Suggs+'27 1st+Mitch '27 2nd+'27 3rd > Barnes | +1100 +500 0.0 +0.2 +5% +2.7 | Us proposed 9/28
Giddey+'27 1st+Mitch '27 2nd > Johnson | +1000 +400 +0.6 +0.4 +4% +2.7
'27 1st > Ausar | +700 +200 +0.9 +0.3 +3% +4.7 | Matthew rejected 9/28

## Below bar

Cade+Sharpe+Mark+'27 1st+'28 1st > Johnson+Barnes | +2500 +700 +0.9 +1.0 +14% +2.5
Cade+Sharpe+Mark+Kuminga+Walker+'27 1st+'28 1st > Barnes+Harper+Ausar+Black | +2000 +1000 +0.6 +0.5 +6% +1.0
Cade+Sharpe+Mark+Tyus Jones+'27 1st+'28 1st > Barnes+Harper+Ausar+Clowney | +1900 +1000 +0.7 +0.5 +6% +1.1
Cade+Tyus Jones+Post+'28 2nd > Johnson+Ausar+Black | +1800 +800 +1.6 +0.6 +5% +0.1
Cade+Kuminga+Tyus Jones > Johnson+Ausar+Black | +1800 +800 +1.5 +0.6 +5% -0.8
Cade+Sharpe+'27 1st > Wemby+Black | +1800 +1100 +0.6 +0.6 +5% -0.8
Cade+Sharpe+Kuminga+'27 1st+'28 1st > Barnes+Harper+Black | +1800 +1200 +0.6 +0.3 +5% +1.0
Cade+Sharpe+Kuminga+'27 1st+'28 1st > Wemby+Ausar+Black | +1800 +600 +1.3 +0.8 +7% +0.5
Cade+Sharpe+Kuminga+'27 1st > Barnes+Harper | +1500 +1100 -0.1 +0.2 +4% +0.1
Cade+Sharpe+Mark+'27 1st+'28 1st > Barnes+Harper+Ausar | +1500 +700 +0.5 +0.5 +6% +1.2
Cade+Sharpe+Kuminga+'27 1st > Wemby+Ausar | +1500 +600 +0.6 +0.7 +6% -0.5
Cade+Sharpe+Tyus Jones > Johnson+Ausar+Black | +1500 +500 +1.3 +0.7 +6% -0.8
Cade+Kuminga+Tyus Jones > Barnes+Ausar+Black | +1400 +700 +0.9 +0.2 +4% -0.7
Cade+Kuminga+Tyus Jones > Johnson+Black+Maluach | +1400 +400 +1.3 +0.3 +6% -1.4
Cade+Tyus Jones+Post > Johnson+Ausar+Jakučionis | +1300 +500 +1.1 +0.5 +4% -0.5
Cade+Sharpe+Tyus Jones+Post > Barnes+Ausar+Black+Clowney | +1300 +700 +0.8 +0.3 +5% -0.7
Cade+Sharpe+Mark+'27 1st > Johnson+Harper | +1300 +600 +0.1 +0.6 +5% 0.0
Cade+Kuminga+Tyus Jones+'28 2nd > Johnson+Ausar+Black | +1300 +300 +1.5 +0.6 +5% +0.1
Cade+Eason+Tyus Jones > Johnson+Ausar+Black | +1300 +400 +1.2 +0.5 +5% -0.9
Cade+'27 1st > Wemby | +1300 +700 +0.3 +0.4 +4% -0.8
Cade+Kuminga+'27 1st+'28 1st > Barnes+Harper | +1200 +800 +0.4 +0.1 +4% +1.2
Cade+Kuminga+'27 1st+'28 1st > Wemby+Ausar | +1200 +200 +1.1 +0.7 +6% +0.6
Cade+Tyus Jones+Post > Johnson+Ausar+Clowney | +1200 +300 +1.2 +0.5 +5% -0.6
Cade+Mark+Tyus Jones > Johnson+Ausar+Black | +1200 +300 +1.1 +0.6 +5% -0.8
Cade+Sharpe+Tyus Jones > Barnes+Ausar+Black | +1100 +400 +0.7 +0.3 +5% -0.7
Cade+Sharpe+Kuminga+Tyus Jones > Barnes+Ausar+Black+Jakučionis | +1000 +300 +0.6 +0.2 +4% -0.7
Cade+Tyus Jones > Johnson+Ausar | +900 +100 +1.1 +0.5 +4% -0.5
Cade+Sharpe+'27 1st+'28 1st > Barnes+Harper | +900 +500 +0.1 +0.2 +4% +1.2
Cade+Sharpe+Kuminga > Johnson+Ausar+Black | +900 -100 +1.1 +0.6 +6% -0.8
Cade+Tyus Jones+Post > Johnson+Black+Clowney | +900 +200 +0.9 +0.3 +4% -0.7
Cade+Sharpe+Kuminga+Tyus Jones > Barnes+Ausar+Black+Clowney | +800 +200 +0.7 +0.2 +4% -0.7
Cade+Mark+Tyus Jones > Barnes+Ausar+Black | +800 +200 +0.6 +0.2 +4% -0.7
Cade+Walker+Kuminga+'27 1st+'28 1st > Barnes+Harper | +700 +400 +0.1 0.0 +3% +1.1
Cade+Eason+'27 1st+'28 1st > Barnes+Harper | +700 +400 0.0 +0.1 +4% +0.8
Cade+Eason+Kuminga > Johnson+Ausar+Black | +700 -200 +1.0 +0.5 +5% -0.9
Cade+Mark+'27 1st+'28 1st > Barnes+Harper | +600 +300 0.0 +0.2 +4% +1.1
Cade+Tyus Jones > Johnson+Black | +600 0 +0.8 +0.3 +3% -0.7
Giddey+'27 1st+Mitch '27 2nd > Barnes | +600 +300 0.0 0.0 +3% +3.1
Cade+Kuminga+'27 1st > Wemby | +600 +100 +0.1 +0.3 +4% -0.8
Cade+Tyus Jones > Barnes+Ausar | +500 0 +0.5 +0.1 +4% -0.3
Suggs+'27 1st > Ausar+Black | +500 -100 +0.8 +0.3 +2% +1.1 | Matthew rejected 9/28
Jabari > Ausar | +400 +300 +0.1 +0.1 +1% +0.3
Walker+Mitch '27 2nd > Black | +400 +300 +0.4 +0.1 0% +2.4
Walker+'27 1st > Ausar | +400 -100 +0.7 +0.2 +2% +4.0
Cade+Sharpe+Mark+Tyus Jones > Barnes+Ausar+Black+Jakučionis | +300 -200 +0.3 +0.3 +4% -0.7
Cade+Sharpe+'27 1st > Wemby | +200 -300 -0.1 +0.5 +4% -0.8
Cade+Sharpe+Mark+Kuminga+Tyus Jones > Barnes+Ausar+Black+Clowney+Jakučionis | 0 -400 +0.2 +0.3 +4% -0.7
Cade+'27 1st+'28 1st > Wemby | -100 -600 +0.3 +0.4 +4% +0.3

## Too lopsided

Green+Walker+'27 1st > Barnes | +4500 +3500 +0.6 +0.6 +7% +3.0
Edey+Jabari+'27 1st > Barnes | +2300 +1900 -0.1 +0.1 +5% +2.6
Cade+Sharpe+Mark+Kuminga+'27 1st+'28 1st > Barnes+Harper+Ausar+Black | +2400 +1500 +0.9 +0.6 +7% +1.0
Cade+Sharpe+Mark+Kuminga+'27 1st > Johnson+Barnes | +3100 +1400 +0.7 +1.0 +14% +1.4
Cade+Tyus Jones+'27 1st+'28 1st > Barnes+Harper | +1900 +1300 +0.6 +0.1 +4% +1.2
Cade+Sharpe+Kuminga+'27 1st+'28 1st > Johnson+Barnes | +3100 +1300 +1.3 +1.0 +14% +2.6
Jabari+Walker > Ausar+Black | +1600 +1300 +0.5 +0.1 +2% -0.1

## Doesn't meet our minimums

Cade+Tyus Jones+Post > Harper+Ausar+Black | -700 -200 +0.2 -0.4 -6% -2.8
Giddey+Edey+'27 1st > Barnes+Black | -500 -100 -0.4 -0.4 -2% +1.5
Cade+Mark+'27 1st > Wemby | -100 -500 -0.3 +0.4 +3% -0.8
Edey+Tyus Jones > Ausar+Black | +200 +300 +0.5 -0.1 -3% -1.1
Giddey+Edey > Barnes+Black | +700 +1100 -0.4 -0.4 -2% +0.4
Giddey+Walker+'27 1st > Barnes | +800 +600 -0.3 -0.1 +2% +2.6
Camara+Tyus Jones+'27 1st > Ausar+Black | +800 +500 +0.9 +0.1 0% +0.8
Cade+Sharpe+Mark+'27 1st > Barnes+Harper | +900 +600 -0.5 +0.2 +3% 0.0
Edey+Jabari+Bona+'27 1st+Mitch '27 2nd > Barnes | +1400 +900 -0.3 0.0 +5% +3.0
