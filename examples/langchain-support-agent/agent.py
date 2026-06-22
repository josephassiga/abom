"""A small LangChain customer-support agent (illustrative — for `abom scan`)."""
from pathlib import Path

from langchain.tools import tool
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

llm = ChatOpenAI(model="gpt-4o", temperature=0)
fallback_llm = ChatOpenAI(model="gpt-4o-mini")

retriever = Chroma(
    collection_name="support-kb",
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
).as_retriever()

SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system.txt").read_text()


@tool
def search_orders(customer_id: str) -> str:
    """Look up a customer's recent orders by id."""
    return f"orders for {customer_id}"


@tool
def issue_refund(order_id: str, amount: float) -> str:
    """Issue a refund for an order. Consequential — requires approval."""
    return f"refunded {amount} on {order_id}"


TOOLS = [search_orders, issue_refund]
