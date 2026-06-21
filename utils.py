from rich.console import Console
from rich.markdown import Markdown

console = Console()


def md_print(text):
    console.print(Markdown(text))
