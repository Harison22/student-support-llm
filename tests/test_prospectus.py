from backend.prospectus import ProspectusRetriever


def test_prospectus_retriever_ranks_matching_pages():
    retriever = ProspectusRetriever("missing.pdf", max_pages=1)
    retriever._pages = [
        (1, "The University of Dar es Salaam offers undergraduate programmes."),
        (2, "Admission requirements include principal passes for eligible applicants."),
    ]

    matches = retriever.search("What are the admission requirements?")

    assert len(matches) == 1
    assert matches[0].page == 2
    assert "Admission requirements" in matches[0].text


def test_prospectus_retriever_uses_opening_pages_for_generic_udsm_questions():
    retriever = ProspectusRetriever("missing.pdf")
    retriever._pages = [(1, "University of Dar es Salaam undergraduate prospectus")]

    matches = retriever.search("Tell me about University of Dar es Salaam")

    assert len(matches) == 1
    assert matches[0].page == 1
