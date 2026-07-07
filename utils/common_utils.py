import sys
from rich.console import Console
from rich.markdown import Markdown

console = Console()


def md_print(text):
    try:
        console.print(Markdown(text))
    except UnicodeEncodeError:
        try:
            # Fallback to standard print with replacement for unsupported characters
            encoding = sys.stdout.encoding or "utf-8"
            clean_text = text.encode(encoding, errors="replace").decode(encoding)
            print(clean_text)
        except Exception:
            print(text.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))

