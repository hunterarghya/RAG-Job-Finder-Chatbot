from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.deps import get_current_user
from chat import rag_answer

router = APIRouter(prefix="/api", tags=["chat"])


# ------------------- Request Schema -------------------
class QueryRequest(BaseModel):
    query: str


# ------------------ Chat Endpoint --------------------
@router.post("/query")
def query_bot(
    req: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat endpoint for authenticated users.
    Accepts: { "query": "..." }
    Returns: { "answer": "..." }
    """
    question = req.query.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    
    answer = rag_answer(question)

    return {"answer": answer}
