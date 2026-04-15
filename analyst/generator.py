import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
import os
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class CLVDataGenerator:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Устанавливаем seed для воспроизводимости
        random.seed(self.config['seed'])
        np.random.seed(self.config['seed'])
        
        # Результаты генерации
        self.customers_df = None
        self.transactions_df = None
        self.clv_df = None
        
        print(f"[OK] Generator initialized (seed={self.config['seed']})")
    
    def _generate_customers(self) -> pd.DataFrame:
        """Генерация базы клиентов с сегментацией"""
        num_customers = random.randint(
            self.config['customers']['min'],
            self.config['customers']['max']
        )
        
        customers = []
        segments_config = self.config['customers']['segments']
        
        for i in range(1, num_customers + 1):
            # Выбор сегмента с учетом долей
            segment = random.choices(
                population=list(segments_config.keys()),
                weights=[segments_config[s]['share'] for s in segments_config],
                k=1
            )[0]
            
            seg_cfg = segments_config[segment]
            
            # Дата первой покупки (рандомизация в пределах датасета)
            start_date = datetime.strptime(
                self.config['transactions']['date_range']['start'], 
                "%Y-%m-%d"
            )
            end_date = datetime.strptime(
                self.config['transactions']['date_range']['end'], 
                "%Y-%m-%d"
            )
            
            first_purchase = start_date + timedelta(
                days=random.randint(0, (end_date - start_date).days)
            )
            
            # Lifetime клиента
            # Спросить по поводу точной жизни клиента
            lifetime_days = seg_cfg['lifetime_months'] * 30
            churn_date = first_purchase + timedelta(
                days=random.randint(int(lifetime_days * 0.7), lifetime_days)
            )
            
            customers.append({
                'customer_id': f"CUST_{i:05d}",
                'segment': segment,
                'first_purchase_date': first_purchase.strftime("%Y-%m-%d"),
                'churn_date': min(churn_date, end_date).strftime("%Y-%m-%d"),
                'avg_check': seg_cfg['avg_check'],
                'frequency_weeks': seg_cfg['frequency_weeks'],
                'churn_rate': seg_cfg['churn_rate']
            })
        
        self.customers_df = pd.DataFrame(customers)
        print(f"[OK] Generated {len(self.customers_df)} customers")
        return self.customers_df
    
    def _apply_seasonality(self, date: datetime, amount: float) -> float:
        """Применение сезонных коэффициентов"""
        seasonality = self.config['transactions']['seasonality']
        
        # Декабрьский бум
        if date.month == 12:
            amount *= seasonality['december_multiplier']
        
        # Черная пятница
        elif date.month == 11 and date.day >= 20:
            amount *= seasonality['black_friday_multiplier']
        
        # Летнее затишье
        elif date.month in [7, 8]:
            amount *= seasonality['summer_slowdown']
        
        return amount
    
    def _apply_promotion(self, amount: float) -> Tuple[float, bool, float]:
        """Применение скидок и акций"""
        promo_config = self.config['transactions']['promotions']
        
        if not promo_config['enabled']:
            return amount, False, 0.0
        
        has_discount = random.random() < promo_config['discount_probability']
        
        if has_discount:
            discount = np.random.uniform(0.05, promo_config['avg_discount'] * 2)
            amount *= (1 - discount)
            return amount, True, discount
        
        return amount, False, 0.0
    
    def _generate_transactions_for_customer(self, customer: Dict) -> List[Dict]:
        """Генерация всех транзакций для одного клиента"""
        transactions = []
        
        start_date = datetime.strptime(customer['first_purchase_date'], "%Y-%m-%d")
        churn_date = datetime.strptime(customer['churn_date'], "%Y-%m-%d")
        
        # Средняя частота покупок (дней между покупками)
        avg_days_between = customer['frequency_weeks'] * 7
        
        # Генерируем покупки до оттока
        current_date = start_date
        transaction_num = 0
        max_transactions = 100  # защита от бесконечного цикла   Надо будет поиграться с числами, попробовать 200 и тп
        
        while current_date <= churn_date and transaction_num < max_transactions:
            # Вероятность пропуска покупки (шумы)
            if random.random() < self.config['transactions']['noise']['skip_probability']:
                current_date += timedelta(days=avg_days_between * 0.5)
                continue
            
            # Сумма покупки (нормальное распределение)
            amount = np.random.normal(
                customer['avg_check'],
                customer['avg_check'] * 0.3
            )
            amount = max(10, amount)  # минимальная сумма
            
            # Применяем сезонность
            amount = self._apply_seasonality(current_date, amount)
            
            # Применяем скидки
            amount, has_discount, discount = self._apply_promotion(amount) # НЕТ ПРОВЕРКИ НА ОТРИЦАТЕЛЬНЫЕ СУММЫ!
            
            # Добавляем шум
            noise = self.config['transactions']['noise']['amount_noise']
            amount *= np.random.uniform(1 - noise, 1 + noise)
            
            transactions.append({
                'transaction_id': f"TXN_{customer['customer_id']}_{transaction_num:04d}",
                'customer_id': customer['customer_id'],
                'segment': customer['segment'],
                'date': current_date.strftime("%Y-%m-%d"),
                'amount': round(amount, 2),
                'has_discount': has_discount,
                'discount_percent': round(discount * 100, 1) if has_discount else 0
            })
            
            # Следующая покупка (экспоненциальное распределение)
            days_to_next = int(np.random.exponential(avg_days_between))
            current_date += timedelta(days=max(1, days_to_next))
            transaction_num += 1
        
        return transactions
    
    def generate_transactions(self) -> pd.DataFrame:
        """Генерация всех транзакций"""
        if self.customers_df is None:
            self._generate_customers()
        
        all_transactions = []
        
        for _, customer in self.customers_df.iterrows():
            customer_dict = customer.to_dict()
            transactions = self._generate_transactions_for_customer(customer_dict)
            all_transactions.extend(transactions)
        
        self.transactions_df = pd.DataFrame(all_transactions)
        
        # Сортируем по дате
        self.transactions_df['date_obj'] = pd.to_datetime(self.transactions_df['date'])
        self.transactions_df.sort_values('date_obj', inplace=True)
        self.transactions_df.drop('date_obj', axis=1, inplace=True)
        self.transactions_df.reset_index(drop=True, inplace=True)
        
        print(f"[OK] Generated {len(self.transactions_df)} transactions")
        return self.transactions_df
    
    def calculate_clv(self) -> pd.DataFrame:
        """Расчет CLV для каждого клиента"""
        if self.transactions_df is None:
            self.generate_transactions()
        
        # Агрегация по клиентам
        clv_stats = self.transactions_df.groupby('customer_id').agg({
            'amount': ['sum', 'mean', 'count', 'std'],
            'segment': 'first',
            'date': ['min', 'max']
        }).round(2)
        
        # Упрощаем мультииндекс
        clv_stats.columns = ['total_revenue', 'avg_check', 'frequency', 'std_check', 
                            'segment', 'first_date', 'last_date']
        clv_stats.reset_index(inplace=True)
        
        # Рассчитываем время жизни (в месяцах)
        clv_stats['first_date'] = pd.to_datetime(clv_stats['first_date'])
        clv_stats['last_date'] = pd.to_datetime(clv_stats['last_date'])
        clv_stats['lifetime_months'] = (
            (clv_stats['last_date'] - clv_stats['first_date']).dt.days / 30.44
        ).round(1)
        
        # Расчет CLV по простой формуле
        # CLV = Средний чек × Частота покупок × Время жизни (в месяцах)
        clv_stats['clv_simple'] = (clv_stats['avg_check'] * (clv_stats['frequency'] / clv_stats['lifetime_months'].clip(lower=0.1)) * 12).round(2) # ПРОВЕРИТЬ ЕЩЕ РАЗ ФОРМУЛУ, но вроде я исправила
        
        # Альтернативная формула (с учетом тренда)
        monthly_spend = clv_stats['total_revenue'] / clv_stats['lifetime_months'].clip(lower=0.1)
        clv_stats['clv_with_trend'] = (monthly_spend * 12 * 1.1).round(2)  # прогноз на год +10%
        
        # Нормализация для сравнения
        clv_min = clv_stats['clv_simple'].min()
        clv_max = clv_stats['clv_simple'].max()
        if clv_max > clv_min:
            clv_stats['clv_normalized'] = (
                (clv_stats['clv_simple'] - clv_min) / 
                (clv_max - clv_min) * 100
            ).round(2)
        else:
            clv_stats['clv_normalized'] = 50.0
        
        # Категории CLV
        def categorize_clv(value):
            if value >= clv_stats['clv_simple'].quantile(0.9):
                return 'VIP'
            elif value >= clv_stats['clv_simple'].quantile(0.7):
                return 'High'
            elif value >= clv_stats['clv_simple'].quantile(0.4):
                return 'Medium'
            else:
                return 'Low'
        
        clv_stats['clv_category'] = clv_stats['clv_simple'].apply(categorize_clv)
        
        # Сортируем по CLV
        clv_stats.sort_values('clv_simple', ascending=False, inplace=True)
        clv_stats.reset_index(drop=True, inplace=True)
        
        self.clv_df = clv_stats
        print(f"[OK] CLV calculated for {len(self.clv_df)} customers")
        return self.clv_df
    
    def export_data(self, output_dir: str = "output"):
        """Экспорт всех данных в файлы"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Сохраняем транзакции
        if self.transactions_df is not None:
            transactions_path = os.path.join(output_dir, "transactions.csv")
            self.transactions_df.to_csv(transactions_path, index=False, encoding='utf-8-sig')
            print(f"[FILE] Transactions saved: {transactions_path}")
        
        # Сохраняем CLV результаты
        if self.clv_df is not None:
            clv_path = os.path.join(output_dir, "clv_results.csv")
            self.clv_df.to_csv(clv_path, index=False, encoding='utf-8-sig')
            print(f"[FILE] CLV results saved: {clv_path}")
        
        # Сохраняем метаданные
        if self.config['export_metadata']:
            metadata = {
                "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "config": self.config,
                "statistics": self.get_statistics()
            }
            metadata_path = os.path.join(output_dir, "metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"[FILE] Metadata saved: {metadata_path}")
    
    def get_statistics(self) -> Dict:
        """Получение статистики по сгенерированным данным"""
        if self.clv_df is None:
            self.calculate_clv()
        
        stats = {
            "total_customers": len(self.clv_df),
            "total_transactions": len(self.transactions_df),
            "total_revenue": float(self.transactions_df['amount'].sum()),
            "avg_transaction": float(self.transactions_df['amount'].mean()),
            "clv_stats": {
                "mean": float(self.clv_df['clv_simple'].mean()),
                "median": float(self.clv_df['clv_simple'].median()),
                "std": float(self.clv_df['clv_simple'].std()),
                "min": float(self.clv_df['clv_simple'].min()),
                "max": float(self.clv_df['clv_simple'].max())
            },
            "segment_distribution": self.clv_df['segment'].value_counts().to_dict(),
            "clv_category_distribution": self.clv_df['clv_category'].value_counts().to_dict()
        }
        
        return stats
    
    def print_summary(self):
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("DATA SUMMARY")
        print("="*60)
        print(f"Customers: {stats['total_customers']}")
        print(f"Transactions: {stats['total_transactions']}")
        print(f"Total Revenue: {stats['total_revenue']:,.2f} RUB")
        print(f"Avg Transaction: {stats['avg_transaction']:,.2f} RUB")
        print("\nCLV Statistics:")
        print(f"  Mean: {stats['clv_stats']['mean']:,.2f} RUB")
        print(f"  Median: {stats['clv_stats']['median']:,.2f} RUB")
        print(f"  Range: from {stats['clv_stats']['min']:,.2f} to {stats['clv_stats']['max']:,.2f} RUB")
        print("\nSegment Distribution:")
        for seg, count in stats['segment_distribution'].items():
            print(f"  {seg}: {count} customers ({count/stats['total_customers']*100:.1f}%)")
        print("\nCLV Categories:")
        for cat, count in stats['clv_category_distribution'].items():
            print(f"  {cat}: {count} customers ({count/stats['total_customers']*100:.1f}%)")
        print("="*60)


if __name__ == "__main__":
    # Создаем генератор
    generator = CLVDataGenerator("config.json")
    
    # Генерируем данные
    generator.generate_transactions()
    generator.calculate_clv()
    
    # Выводим статистику
    generator.print_summary()
    
    # Экспортируем результаты
    generator.export_data("output")
    
    print("\n[OK] Data generation completed successfully!")
    print("[FOLDER] Results saved in 'output' folder")