from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ClientResult(BaseModel):
    client_id: int = Field(..., description="ID клиента")
    clv: float = Field(..., description="Прогнозируемая ценность клиента (RUB)")
    total_revenue: float = Field(..., description="Общая выручка от клиента (RUB)")
    purchase_count: int = Field(..., description="Количество покупок")
    avg_check: float = Field(..., description="Средний чек (RUB)")
    segment: str = Field(..., description="Сегмент клиента")
    customer_age_months: float = Field(..., description="Возраст клиента (месяцы)")
    frequency_per_month: float = Field(..., description="Частота покупок в месяц")


class CLVResponse(BaseModel):
    success: bool = Field(True, description="Успешность операции")
    message: str = Field("", description="Сообщение")
    total_clients: int = Field(..., description="Всего клиентов")
    results: List[ClientResult] = Field(..., description="Результаты по клиентам")
    summary: Dict[str, Any] = Field(..., description="Агрегированная статистика")
    visualization_data: Dict[str, Any] = Field(..., description="Данные для графиков")
    processing_time_ms: Optional[float] = Field(None, description="Время обработки (мс)")


class ErrorResponse(BaseModel):
    success: bool = Field(False)
    error: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Детали ошибки")
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    status: str = Field(..., description="Статус сервиса")
    version: str = Field("1.0.0", description="Версия API")
    timestamp: datetime = Field(default_factory=datetime.now)