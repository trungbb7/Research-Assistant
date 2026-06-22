from ..models.document import PaperSummary


def serilize_paper_summary(paper_summary: PaperSummary):
    out = f"""
    Title: {paper_summary.title}

    Problem: {paper_summary.problem}

    Methodology: {", ".join([method for method in paper_summary.methodology])}

    Datasets: {", ".join([dataset for dataset in paper_summary.datasets])}

    Key contributions: {", ".join([contrib for contrib in paper_summary.key_contributions])}

    Strengths: {", ".join([strength for strength in paper_summary.strengths])}

    Weakneeses: {", ".join([weak for weak in paper_summary.weaknesses])}

    Conclution: {paper_summary.conclution}
    """
    return out
