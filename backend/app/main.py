from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import time
from typing import Optional

from .models import CLVResponse, ErrorResponse, HealthResponse
from .clv_service import clv_service

app = FastAPI(
    title="CLV Calculator API",
    description="API для расчёта Customer Lifetime Value (CLV)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Info"])
async def root():
    return {
        "service": "CLV Calculator API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(status="healthy", version="1.0.0")


@app.post(
    "/calculate",
    response_model=CLVResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    tags=["CLV"]
)
async def calculate_clv(
    file: UploadFile = File(..., description="CSV файл с транзакциями"),
    lifetime_months: Optional[int] = Query(12, ge=1, le=60, description="Срок жизни клиента (месяцы)")
):
    start_time = time.time()
    
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(415, detail={"error": "UnsupportedFormat", "message": "Only CSV files are supported"})
        
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(400, detail={"error": "EmptyFile", "message": "File is empty"})
        
        try:
            df = pd.read_csv(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(400, detail={"error": "ParseError", "message": f"Failed to parse CSV: {str(e)}"})
        
        required_columns = {'client_id', 'date', 'amount'}
        missing_columns = required_columns - set(df.columns)
        
        if missing_columns:
            raise HTTPException(400, detail={
                "error": "MissingColumns",
                "message": f"Missing required columns: {missing_columns}"
            })
        
        results_df, stats = clv_service.calculate(df, lifetime_months=lifetime_months)
        
        response = clv_service.to_response(results_df, stats)
        response.processing_time_ms = (time.time() - start_time) * 1000
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail={"error": "InternalError", "message": str(e)})


@app.post("/cache/clear", tags=["Admin"])
async def clear_cache():
    cleared = clv_service.clear_cache()
    return {"success": True, "message": f"Cache cleared, {cleared} items removed"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)