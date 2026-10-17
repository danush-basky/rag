from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_PLAIN_0_0_4, generate_latest

router = APIRouter(tags=["Metrics"])


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_PLAIN_0_0_4)
