from models.document import PaperSummary, ResearchReport


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


def serialize_research_report(report: ResearchReport) -> str:
    references_str = "\n".join([f"- {ref}" for ref in report.references])
    out = f"""# {report.title}

## Overview
{report.overview}

## Key Findings
{report.key_findings}

## Comparison
{report.comparision}

## Trends
{report.trends}

## Conclusion
{report.conclustion}

## References
{references_str}
"""
    return out
