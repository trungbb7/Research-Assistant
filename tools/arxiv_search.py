import arxiv
from ..models.paper import Paper
from langchain_core.tools import tool

arxiv_client = arxiv.Client()


@tool
def arxiv_search(query: str, max_results: int = 5, id_list: list[str] = None):
    """Search papers from arxiv.org"""
    try:
        search = arxiv.Search(
            query=query,
            id_list=id_list,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        results = []

        for paper in arxiv_client.results(search):
            results.append(
                Paper(
                    title=paper.title,
                    authors=[author.name for author in paper.authors],
                    summary=paper.summary,
                    published=paper.published.strftime("%Y-%m-%d"),
                    pdf_url=paper.pdf_url,
                    entry_id=paper.entry_id,
                    categories=paper.categories,
                )
            )

        return "\n".join([paper.model_dump_json() for paper in results])
    except Exception as e:
        return f"Error while searching papers from arXiv: {str(e)}. Please wait a moment before trying again."
