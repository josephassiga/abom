"""A tiny sample agent for abom scan tests."""
from langchain.tools import tool

PRIMARY_MODEL = "gpt-4o-mini"
FALLBACK_MODEL = "claude-3-5-sonnet-20241022"


@tool
def lookup_customer(customer_id: str) -> str:
    """Look up a customer record by id."""
    return f"customer:{customer_id}"


def run(prompt: str) -> str:
    # would call PRIMARY_MODEL, fall back to FALLBACK_MODEL
    return prompt
