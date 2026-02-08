from fastapi import APIRouter

from .schemas import AICheckRequest, AICheckResult, AIContextRequest, AIContextResult
from .service import ai_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/check-sentence", response_model=AICheckResult)
async def check_sentence(request: AICheckRequest):
    return await ai_service.check_sentence(
        word=request.word,
        translation=request.translation,
        sentence=request.sentence,
    )


@router.post("/generate-contexts", response_model=AIContextResult)
async def generate_contexts(request: AIContextRequest):
    return await ai_service.generate_contexts(
        word=request.word,
        part_of_speech=request.part_of_speech,
        count=request.count,
    )
