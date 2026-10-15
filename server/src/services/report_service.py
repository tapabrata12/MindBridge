from fastapi import HTTPException, status
from typing import Any
import logging
from pymongo.errors import PyMongoError
from langchain_core.runnables import  RunnableSerializable
from pydantic import BaseModel
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, List, Any
from src.core.config import settings
from src.schemas.assessment import PHQ9ReportResult, PHQ9AssessmentResult
from src.rag.retriever import retrieve_context
from src.db import mongodb
from src.models.report import create_phq9_report_document

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # Print to console
        logging.FileHandler("mongo_app.log")  # Save to a file
    ]
)
logger = logging.getLogger(__name__)

SEVERITY_SEARCH_QUERIES: dict[str, str] = {
    "minimal": "minimal depression symptoms self-care and monitoring",
    "mild": "mild depression symptoms coping strategies",
    "moderate": "moderate depression symptoms diagnostic criteria and treatment",
    "moderately_severe": "moderately severe depression symptoms professional treatment options",
    "severe": "severe depression symptoms clinical intervention and support",
}

def _format_context(chunks: list[dict]) -> str:
    formatted_string = ""
    for chunk in chunks:
        source: str = chunk['source_document']
        text: str = chunk['text']
        formatted_string += f"Source document: {source}\n Important Text: \"{text}\"\n\n"
    return formatted_string

def _get_report_llm() -> RunnableSerializable[dict[str, Any], dict | BaseModel]:
    llm = ChatNVIDIA(
        model=settings.NVIDIA_CHAT_MODEL,
        api_key= settings.NVIDIA_API_KEY,
        temperature=0.3,
        top_p=0.95,
        max_tokens=16384,
        # extra_body={"chat_template_kwargs": {"thinking": True, "reasoning_effort": "high"}},
    )
    structured_llm = llm.with_structured_output(PHQ9ReportResult)

    report_prompt_template = ChatPromptTemplate.from_messages([
    ("system", (
    "You are a supportive mental health report writer for a wellness app, not a clinician. "
    "Base your writing ONLY on the provided source context below — do not invent clinical claims "
    "or add information not grounded in that context. "
    "Write a plain-language explanation of what the person's results may suggest, using warm, "
    "non-alarming language.\n\n"
    "You MUST also provide a 'remedies' list containing exactly 3 to 5 short, practical coping tips "
    "(for example: breathing exercises, sleep hygiene, gentle self-care, grounding techniques). "
    "Only include a remedy if it is genuinely grounded in the provided source context — do not invent "
    "tips that aren't supported by the material. If the source context contains no explicit coping "
    "techniques, return an empty remedies list rather than inventing one.\n\n"
    "For the 'sources' field, list ONLY the document filenames you drew from (e.g. "
    "'feeling-good-the-new-mood-therapy.pdf'), nothing else — no explanations, no quotes, "
    "just the plain filenames, with no duplicates.\n\n"
    "Never state a definitive diagnosis — always frame things as possibilities, and encourage "
    "professional consultation when appropriate."
    )),

    ("human","PHQ-9 Severity: {severity}\nPHQ-9 Total Score: {total_score}\n\nRelevant source material:\n{context}")
    ])

    return report_prompt_template | structured_llm


async def generate_phq9_report(result: PHQ9AssessmentResult):
    query = SEVERITY_SEARCH_QUERIES[result.severity]
    chunks = await retrieve_context(query, limit=10)
    # Call the string context builder and other important credentials

    llm_chain = _get_report_llm()
    severity = result.severity
    total_score = result.total_score
    formatted_string = _format_context(chunks)

    llm_result = await llm_chain.ainvoke({"severity": severity, "total_score": total_score, "context": formatted_string})
    return llm_result

"""
This is the Save function for the document to be saved into the DB.

Parameter: user_id, assessment_id. Report
Return: Saved MongoDB Model
"""

async def save_report_to_db(user_id: str, assessment_id: str, report: PHQ9ReportResult)-> Dict[str,Any]:
    # Step 1: check if mongoDB client is responding or not
    if mongodb.db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database is not working for internal server problem")
    # Step 2: Create model for saving
    report_model = create_phq9_report_document(user_id=user_id, assessment_id=assessment_id, report= report)
    # Step 3: Extract Saved model from the DB
    saved_model = await mongodb.db[settings.REPORT_COLLECTION_NAME].insert_one(report_model)
    # Step 4: Convert the DB created _id
    report_model["_id"] = str(saved_model.inserted_id)
    # Return it as JSON
    return saved_model

"""
This is the Save function for the document to be saved into the DB.

Parameter: user_id
Return: All Saved MongoDB Reports
"""

async def get_all_saved_reports(user_id: str, assessment_id: str)-> List[Dict[str, str]]:
    # Step 1: check if mongoDB client is responding or not
    if mongodb.db is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Database is not working for internal server problem")

    # Step 2: Get the collection

    try:
        collection = await mongodb.db[settings.REPORT_COLLECTION_NAME]

        if collection is None:
            return []

        # Step 3:
        cursor = collection.find({"user_id": user_id, "assessment_id": assessment_id}).sort("created_at", -1)  # -1 means newest first

        all_reports = await cursor.to_list(length=50)  # take at most 50 cards

        all_reports_list = []

        for report in all_reports:
            report["_id"] = str(report["_id"])
            all_reports_list.append(report)

        return all_reports_list

    except PyMongoError as e:
        # Log database errors safely
        logger.error(HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database is not working for internal server problem"), exc_info=True)


    except Exception as e:
        logger.error(e, exc_info=True)