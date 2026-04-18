import hashlib
import time
from typing import Tuple, Dict, Optional
import pandas as pd

from .clv_calculator import CLVCalculator
from .models import CLVResponse, ClientResult


class CLVService:
    def __init__(self, default_lifetime_months: int = 12, cache_size: int = 100):
        self.default_lifetime_months = default_lifetime_months
        self.cache_size = cache_size
        self._cache = {}
    
    def _get_cache_key(self, df_hash: str, lifetime_months: int) -> str:
        return f"{df_hash}_{lifetime_months}"
    
    def _hash_dataframe(self, df: pd.DataFrame) -> str:
        return hashlib.md5(pd.util.hash_pandas_object(df).values.tobytes()).hexdigest()
    
    def calculate(
        self,
        df: pd.DataFrame,
        lifetime_months: Optional[int] = None,
        use_cache: bool = True
    ) -> Tuple[pd.DataFrame, Dict]:
        start_time = time.time()
        
        lt = lifetime_months or self.default_lifetime_months
        
        if df.empty:
            raise ValueError("DataFrame is empty")
        
        if use_cache:
            df_hash = self._hash_dataframe(df)
            cache_key = self._get_cache_key(df_hash, lt)
            
            if cache_key in self._cache:
                results, stats = self._cache[cache_key]
                stats['from_cache'] = True
                stats['processing_time_ms'] = (time.time() - start_time) * 1000
                return results, stats
        
        calculator = CLVCalculator(lifetime_months=lt)
        results, stats = calculator.calculate_all_methods(df)
        
        stats['processing_time_ms'] = (time.time() - start_time) * 1000
        stats['from_cache'] = False
        
        if use_cache:
            cache_key = self._get_cache_key(self._hash_dataframe(df), lt)
            self._cache[cache_key] = (results, stats)
            
            if len(self._cache) > self.cache_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
        
        return results, stats
    
    def to_response(self, results_df: pd.DataFrame, stats: Dict) -> CLVResponse:
        clients = []
        for _, row in results_df.iterrows():
            clients.append(ClientResult(
                client_id=int(row['client_id']),
                clv=float(row['clv']),
                total_revenue=float(row['total_revenue']),
                purchase_count=int(row['purchase_count']),
                avg_check=float(row['avg_check']),
                segment=str(row['segment']),
                customer_age_months=float(row['customer_age_months']),
                frequency_per_month=float(row['frequency_per_month'])
            ))
        
        calculator = CLVCalculator()
        viz_data = calculator.prepare_visualization_data(results_df)
        
        return CLVResponse(
            success=True,
            message="CLV calculated successfully",
            total_clients=len(results_df),
            results=clients[:100],
            summary=stats,
            visualization_data=viz_data,
            processing_time_ms=stats.get('processing_time_ms', 0)
        )
    
    def clear_cache(self) -> int:
        cache_size = len(self._cache)
        self._cache.clear()
        return cache_size


clv_service = CLVService()