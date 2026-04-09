import pandas as pd
import numpy as np
import os
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class DataValidator:
    def __init__(self, transactions_path="output/transactions.csv", clv_path="output/clv_results.csv"):
        self.transactions_path = transactions_path
        self.clv_path = clv_path
        
        # Проверяем, существуют ли файлы
        if not os.path.exists(transactions_path):
            raise FileNotFoundError(f"File not found: {transactions_path}")
        if not os.path.exists(clv_path):
            raise FileNotFoundError(f"File not found: {clv_path}")
        
        self.transactions = pd.read_csv(transactions_path)
        self.clv = pd.read_csv(clv_path)
        
        print("[OK] Data loaded successfully")
        print(f"    - Transactions: {len(self.transactions)}")
        print(f"    - Customers: {len(self.clv)}")
        
    def validate_data_integrity(self):
        """Проверка целостности данных"""
        print("\n" + "="*50)
        print("DATA INTEGRITY CHECK")
        print("="*50)
        
        # Проверка пропусков
        missing_transactions = self.transactions.isnull().sum().sum()
        missing_clv = self.clv.isnull().sum().sum()
        print(f"Missing values in transactions: {missing_transactions}")
        print(f"Missing values in CLV: {missing_clv}")
        
        # Проверка отрицательных сумм
        negative_amounts = (self.transactions['amount'] < 0).sum()
        print(f"Negative amounts: {negative_amounts}")
        
        # Проверка корректности дат
        try:
            pd.to_datetime(self.transactions['date'])
            print("[OK] Dates are correct")
        except:
            print("[ERROR] Date format error")
        
        # Проверка уникальных ID
        unique_customers_transactions = self.transactions['customer_id'].nunique()
        unique_customers_clv = len(self.clv)
        print(f"Unique customers (transactions): {unique_customers_transactions}")
        print(f"Unique customers (CLV): {unique_customers_clv}")
        
        if unique_customers_transactions == unique_customers_clv:
            print("[OK] Customer counts match")
        else:
            print("[WARNING] Customer counts do not match!")
        
        print("="*50)
    
    def validate_clv_calculation(self):
        """Проверка корректности расчета CLV"""
        print("\n" + "="*50)
        print("CLV CALCULATION CHECK")
        print("="*50)
        
        # Проверка на выбросы
        z_scores = np.abs(stats.zscore(self.clv['clv_simple']))
        outliers = (z_scores > 3).sum()
        print(f"Outliers in CLV: {outliers} ({outliers/len(self.clv)*100:.1f}%)")
        
        # Логическая проверка: VIP клиенты должны иметь больше CLV
        vip_clv = self.clv[self.clv['clv_category'] == 'VIP']['clv_simple'].mean()
        high_clv = self.clv[self.clv['clv_category'] == 'High']['clv_simple'].mean()
        medium_clv = self.clv[self.clv['clv_category'] == 'Medium']['clv_simple'].mean()
        low_clv = self.clv[self.clv['clv_category'] == 'Low']['clv_simple'].mean()
        
        print(f"\nAverage CLV by category:")
        print(f"  VIP:    {vip_clv:,.2f} RUB")
        print(f"  High:   {high_clv:,.2f} RUB")
        print(f"  Medium: {medium_clv:,.2f} RUB")
        print(f"  Low:    {low_clv:,.2f} RUB")
        
        # Проверка иерархии
        if vip_clv > high_clv > medium_clv > low_clv:
            print("\n[OK] CLV hierarchy is correct (VIP > High > Medium > Low)")
        else:
            print("\n[WARNING] CLV hierarchy is incorrect!")
        
        print("="*50)
    
    def validate_segments(self):
        print("\n" + "="*50)
        print("SEGMENTATION CHECK")
        print("="*50)
        
        # Распределение по сегментам
        segment_stats = self.clv.groupby('segment').agg({
            'clv_simple': ['mean', 'median', 'count'],
            'total_revenue': 'sum'
        }).round(2)
        
        print(segment_stats)
        
        # Проверка: премиум сегмент должен иметь больший CLV
        premium_clv = self.clv[self.clv['segment'] == 'premium']['clv_simple'].mean()
        regular_clv = self.clv[self.clv['segment'] == 'regular']['clv_simple'].mean()
        occasional_clv = self.clv[self.clv['segment'] == 'occasional']['clv_simple'].mean()
        
        print(f"\nAverage CLV by segment:")
        print(f"  premium:    {premium_clv:,.2f} RUB")
        print(f"  regular:    {regular_clv:,.2f} RUB")
        print(f"  occasional: {occasional_clv:,.2f} RUB")
        
        if premium_clv > regular_clv > occasional_clv:
            print("\n[OK] Segmentation is correct (premium > regular > occasional)")
        else:
            print("\n[WARNING] Segmentation hierarchy is incorrect!")
        
        print("="*50)
    
    def validate_transaction_patterns(self):
        print("\n" + "="*50)
        print("TRANSACTION PATTERNS CHECK")
        print("="*50)
        self.transactions['date'] = pd.to_datetime(self.transactions['date'])
        
        # Проверка по месяцам
        self.transactions['month'] = self.transactions['date'].dt.to_period('M')
        monthly_sales = self.transactions.groupby('month')['amount'].sum()
        
        print(f"Data period: {self.transactions['date'].min().date()} - {self.transactions['date'].max().date()}")
        print(f"Number of months: {len(monthly_sales)}")
        
        # Проверка сезонности
        # Исправленная логика без .str
        if len(monthly_sales) >= 12:
            dec_sales_list = []
            for month in monthly_sales.index:
                if month.month == 12:
                    dec_sales_list.append(monthly_sales[month])
            
            if dec_sales_list:
                dec_sales = sum(dec_sales_list) / len(dec_sales_list)
                avg_sales = monthly_sales.mean()
                
                if dec_sales > avg_sales:
                    print(f"[OK] December sales are above average ({dec_sales:,.0f} > {avg_sales:,.0f})")
                else:
                    print(f"[WARNING] December sales are not above average ({dec_sales:,.0f} <= {avg_sales:,.0f})")
            else:
                print("[INFO] No December data available for seasonality check")
        
        # Проверка скидок
        if 'has_discount' in self.transactions.columns:
            discount_rate = self.transactions['has_discount'].mean()
            print(f"Transactions with discount: {discount_rate*100:.1f}%")
            print("  Discount effect by segment:")
            for segment in self.transactions['segment'].unique():
                seg_data = self.transactions[self.transactions['segment'] == segment]
                if len(seg_data[seg_data['has_discount'] == True]) > 0:
                    avg_with = seg_data[seg_data['has_discount'] == True]['amount'].mean()
                    avg_without = seg_data[seg_data['has_discount'] == False]['amount'].mean()
                    print(f"    {segment}: with discount {avg_with:,.0f} vs without {avg_without:,.0f} RUB")
                            
        print("="*50)
    
    def validate_customer_value_distribution(self):
        print("\n" + "="*50)
        print("PARETO PRINCIPLE CHECK (80/20)")
        print("="*50)
        
        # Сортируем клиентов по выручке
        sorted_customers = self.clv.sort_values('total_revenue', ascending=False)
        
        # Считаем накопленную выручку
        cumulative_revenue = sorted_customers['total_revenue'].cumsum()
        total_revenue = cumulative_revenue.iloc[-1]
        
        # Находим топ-20% клиентов
        top_20_percent = int(len(sorted_customers) * 0.2)
        revenue_from_top_20 = cumulative_revenue.iloc[top_20_percent - 1] if top_20_percent > 0 else 0
        percent_revenue = (revenue_from_top_20 / total_revenue) * 100
        
        print(f"Top 20% customers generate: {percent_revenue:.1f}% of revenue")
        
        if percent_revenue >= 70:
            print(f"[OK] Strong concentration (typical for CLV)")
        elif percent_revenue >= 50:
            print(f"[INFO] Moderate concentration")
        else:
            print(f"[WARNING] Low concentration - check data")
        
        print("="*50)
    
    def run_all_checks(self):
        """Запуск всех проверок"""
        print("\n" + "="*60)
        print(" STARTING DATA QUALITY CHECK")
        print("="*60)
        
        self.validate_data_integrity()
        self.validate_clv_calculation()
        self.validate_segments()
        self.validate_transaction_patterns()
        self.validate_customer_value_distribution()
        
        print("\n" + "="*60)
        print(" CHECK COMPLETED")
        print("="*60)


if __name__ == "__main__":
    try:
        validator = DataValidator(
            transactions_path="output/transactions.csv",
            clv_path="output/clv_results.csv"
        )
        
        # Запускаем все проверки
        validator.run_all_checks()
        
        print("\n[SUCCESS] All checks passed!")
        print("[INFO] Data is ready for web service")
        
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("[SOLUTION] First run generator.py to create data")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()