from typing import Tuple, Dict
import pandas as pd
import numpy as np


class CLVCalculator:
    
    def __init__(self, lifetime_months: int = 12):
        self.lifetime_months = lifetime_months
    
    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        df = df[df['amount'] > 0]
        
        if df['client_id'].dtype == 'object':
            df['client_id'] = df['client_id'].str.extract('(\d+)').fillna(0)
        
        df['client_id'] = pd.to_numeric(df['client_id'], errors='coerce')
        df = df.dropna(subset=['client_id'])
        df['client_id'] = df['client_id'].astype(int)
        
        return df
    
    def calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        metrics = df.groupby('client_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'date': ['min', 'max']
        }).reset_index()
        
        metrics.columns = [
            'client_id', 'total_revenue', 'avg_check',
            'purchase_count', 'first_date', 'last_date'
        ]
        
        metrics['first_date'] = pd.to_datetime(metrics['first_date'])
        metrics['last_date'] = pd.to_datetime(metrics['last_date'])
        
        metrics['customer_age_months'] = (
            (metrics['last_date'] - metrics['first_date']).dt.days / 30.44
        ).round(1)
        
        metrics['frequency_per_month'] = np.where(
            metrics['customer_age_months'] > 0,
            metrics['purchase_count'] / metrics['customer_age_months'],
            metrics['purchase_count']
        )
        
        return metrics
    
    def calculate_clv(self, metrics: pd.DataFrame) -> pd.Series:
        clv = (
            metrics['avg_check'] *
            metrics['frequency_per_month'] *
            self.lifetime_months
        )
        return clv.round(2)
    
    def segment_clients(self, clv_values: pd.Series) -> pd.Series:
        thresholds = {
            'VIP': clv_values.quantile(0.9),
            'High': clv_values.quantile(0.7),
            'Medium': clv_values.quantile(0.4)
        }
        
        segments = []
        for clv in clv_values:
            if clv >= thresholds['VIP']:
                segments.append('VIP')
            elif clv >= thresholds['High']:
                segments.append('High')
            elif clv >= thresholds['Medium']:
                segments.append('Medium')
            else:
                segments.append('Low')
        
        return pd.Series(segments, index=clv_values.index)
    
    def calculate_all_methods(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        df_clean = self.preprocess_data(df)
        
        if df_clean.empty:
            raise ValueError("Нет корректных данных после предобработки")
        
        metrics = self.calculate_metrics(df_clean)
        metrics['clv'] = self.calculate_clv(metrics)
        metrics['segment'] = self.segment_clients(metrics['clv'])
        metrics = metrics.sort_values('clv', ascending=False).reset_index(drop=True)
        
        results = metrics[[
            'client_id', 'clv', 'total_revenue', 'purchase_count',
            'avg_check', 'segment', 'customer_age_months', 'frequency_per_month'
        ]].copy()
        
        stats = {
            'total_clients': len(results),
            'total_revenue': float(results['total_revenue'].sum()),
            'avg_clv': float(results['clv'].mean()),
            'median_clv': float(results['clv'].median()),
            'min_clv': float(results['clv'].min()),
            'max_clv': float(results['clv'].max()),
            'segment_distribution': results['segment'].value_counts().to_dict()
        }
        
        return results, stats
    
    def prepare_visualization_data(self, results_df: pd.DataFrame) -> Dict:
        top_clients = results_df.head(10)[
            ['client_id', 'clv', 'total_revenue', 'purchase_count', 'segment']
        ].copy()
        top_clients['clv'] = top_clients['clv'].round(0).astype(int)
        
        clv_distribution = results_df['clv'].tolist()
        segment_distribution = results_df['segment'].value_counts().to_dict()
        
        scatter_data = results_df[
            ['client_id', 'purchase_count', 'clv', 'segment']
        ].to_dict('records')
        
        summary_stats = {
            'total_clients': len(results_df),
            'avg_clv': round(results_df['clv'].mean(), 2),
            'median_clv': round(results_df['clv'].median(), 2),
            'total_revenue': round(results_df['total_revenue'].sum(), 2),
            'most_valuable_segment': results_df['segment'].mode()[0] if len(results_df) > 0 else 'N/A'
        }
        
        return {
            'top_clients': top_clients.to_dict('records'),
            'clv_distribution': clv_distribution,
            'segment_distribution': segment_distribution,
            'scatter_data': scatter_data,
            'summary_stats': summary_stats
        }


if __name__ == "__main__":
    test_df = pd.DataFrame({
        'client_id': [1, 1, 1, 2, 2, 3],
        'date': [
            '2023-01-01', '2023-02-01', '2023-03-01',
            '2023-01-15', '2023-04-20',
            '2023-05-10'
        ],
        'amount': [1000, 1500, 2000, 3000, 4000, 500]
    })
    
    calculator = CLVCalculator(lifetime_months=12)
    results, stats = calculator.calculate_all_methods(test_df)
    
    print(f"Всего клиентов: {stats['total_clients']}")
    print(f"Средний CLV: {stats['avg_clv']:.2f} RUB")
    print(f"Общая выручка: {stats['total_revenue']:.2f} RUB")
    print("\nРезультаты по клиентам:")
    print(results[['client_id', 'clv', 'segment', 'purchase_count']].to_string())
    print("\nCLVCalculator работает!")