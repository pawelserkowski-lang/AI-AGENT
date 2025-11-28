from rich.console import Console
import logging

console = Console()
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger("GeminiAgent")
