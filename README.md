# Constrained Integration: replication material

Replication material for the Corvinus TDK paper *Constrained Integration: Economic Participation and Policy-Practice Gaps among Myanmar Refugees in Thailand* (Csenge Ilyés, 2026).

## Contents

- `data/coded.xlsx`: the author's hand-coded sheet (857 relevant sentences). Sheet `Guide` is the codebook, `Coding` holds the codes, `Excluded_check` holds the control sample of excluded sentences.
- `data/sentences_coded.csv`: the sentence list with document IDs, source types and the official-voice marker.
- `code/analyse.py`: Python script that counts the codes by source type and view (camp, urban, migrant, official voice) and writes the tables used in Chapter 5 to `output/results_for_ch5.xlsx`.
- `output/results_for_ch5.xlsx`: the resulting tables.

## How to run

```
pip install pandas numpy openpyxl
cd code
python analyse.py
```

## Notes

- The coding was done by hand by the author. The script only counts and tabulates; it does not code any text.
- The analysis is descriptive. It does not identify causal effects.
- The English texts of Thai-language sources are unofficial AI-assisted translations; the originals are cited in the References of the paper.
- The script was written with AI assistance (see the AI-use declaration in the paper).
- The sentences are short excerpts from the 27 documents listed in Appendix A of the paper, kept for transparency and verification. The full texts are not reproduced here.
