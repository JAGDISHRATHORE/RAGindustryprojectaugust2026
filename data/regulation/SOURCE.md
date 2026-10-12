# Regulation source

`ai_act_articles.csv` and `ai_act_annex.csv` contain the English text of
Regulation (EU) 2024/1689 (the EU Artificial Intelligence Act), taken from the
Hugging Face dataset [`laredoyin/eu-ai-act`](https://huggingface.co/datasets/laredoyin/eu-ai-act)
(Apache-2.0).

The authoritative version is the one published in the Official Journal of the
European Union:
https://eur-lex.europa.eu/eli/reg/2024/1689/oj

The text was not modified. The parser in `complyrag/ingestion/regulation.py`
splits each article into numbered paragraphs and lettered points at load time.
