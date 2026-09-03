from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from Scripts.RetrieveQuestionsFromPlabable import getRandom_p_questions
from Scripts.RetrieveQuestionsFromUni import getRandom_u_questions

DB_PATH = "Data/db/merged.db"
EXTRACT_SCRIPT = "Scripts/extract_plabable.py"


app = FastAPI(
    title="Plabable Exam Backend API",
    description="API for retrieving medical exam questions.",
)

@app.get("/plabable", summary="Get random questions for plabable", response_model=List[dict])
def get_plabable_questions(n: int = Query(10, gt=0, le=100), topic: Optional[str] = None):
    """
    Retrieve random questions for plabable, optionally filtered by topic.
    - **n**: Number of questions to retrieve (max 100)
    - **topic**: Topic to filter questions by (optional)
    """
    try:
        if topic:
            questions = getRandom_p_questions(n=n, topic=topic.upper(), db_path=DB_PATH)
        else:
            questions = getRandom_p_questions(n=n, db_path=DB_PATH)
        return questions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/uni", summary="Get random questions for uni", response_model=List[dict])
def get_uni_questions(n: int = Query(10, gt=0, le=100), topic: Optional[str] = None, level: Optional[int] = None):
    """
    Retrieve random questions for uni, optionally filtered by topic and level.
    - **n**: Number of questions to retrieve (max 100)
    - **topic**: Topic to filter questions by (optional)
    - **level**: Level to filter questions by (optional)
    """
    try:
        questions = getRandom_u_questions(n=n, topic=topic, level=level, db_path=DB_PATH)
        return questions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
