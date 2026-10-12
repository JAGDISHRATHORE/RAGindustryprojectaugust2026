from conftest import ROOT

from complyrag.ingestion.documents import chunk_document
from complyrag.ingestion.regulation import load_articles, paragraph_text, split_paragraphs

ARTICLES = load_articles(ROOT / "data/regulation/ai_act_articles.csv")


def test_all_articles_loaded():
    assert len(ARTICLES) >= 110
    assert ARTICLES[14].title == "Human oversight"


def test_paragraph_counts_match_the_official_text():
    expected = {9: 10, 10: 6, 11: 3, 12: 3, 13: 3, 14: 5, 15: 5}
    for article, n in expected.items():
        assert len(split_paragraphs(ARTICLES[article].text)) == n, article


def test_inline_article_references_do_not_start_a_paragraph():
    # Art. 9(2)(c) ends with "referred to in Article 72;" which must stay inside paragraph 2.
    p2 = paragraph_text(ARTICLES, 9, 2)
    assert "Article 72" in p2
    assert p2.startswith("The risk management system shall be understood")


def test_points_stay_with_their_paragraph():
    p4 = paragraph_text(ARTICLES, 14, 4)
    assert "(e) to intervene in the operation" in p4
    assert "automation bias" in p4


def test_company_document_is_chunked_by_section():
    chunks = chunk_document(ROOT / "data/company/human_oversight_procedure.md")
    ids = [c.id for c in chunks]
    assert ids == [f"NWK-HOP-003#s{i}" for i in range(1, 7)]
    assert all(c.system == "creditlens" for c in chunks)
    assert chunks[5].section == "6. Overriding the model"
    assert chunks[5].text.startswith("Overriding the model")
    assert chunks[0].metadata["version"] == "1.2"
