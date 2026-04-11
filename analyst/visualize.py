import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Настройка для работы без дисплея
if 'DISPLAY' not in os.environ:
    import matplotlib
    matplotlib.use('Agg')  # Неинтерактивный бэкенд

# Настройка русских шрифтов для Windows
#plt.rcParams['font.family'] = 'Segoe UI'
#plt.rcParams['axes.unicode_minus'] = False
# сделала для стандартных! потом могу исправить

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']

# Загрузка данных
print("Loading data...")
clv = pd.read_csv("output/clv_results.csv")
transactions = pd.read_csv("output/transactions.csv")
transactions['date'] = pd.to_datetime(transactions['date'])

print(f"Data loaded: {len(clv)} customers, {len(transactions)} transactions")

fig = plt.figure(figsize=(18, 12))
fig.suptitle('CLV Analysis Dashboard', fontsize=20, fontweight='bold', y=0.98)

# Цветовая схема
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']

# ============================================
# Graph 1: CLV Distribution
# ============================================
ax1 = fig.add_subplot(2, 3, 1)
ax1.hist(clv['clv_simple'], bins=30, edgecolor='black', alpha=0.7, color='#3498db')
ax1.axvline(clv['clv_simple'].mean(), color='red', linestyle='--', 
            linewidth=2, label=f'Mean: {clv["clv_simple"].mean():,.0f} RUB')
ax1.axvline(clv['clv_simple'].median(), color='green', linestyle='--', 
            linewidth=2, label=f'Median: {clv["clv_simple"].median():,.0f} RUB')
ax1.set_title('CLV Distribution', fontsize=12, fontweight='bold', pad=10)
ax1.set_xlabel('CLV (RUB)')
ax1.set_ylabel('Number of Customers')
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)

# ============================================
# Graph 2: Average CLV by Segment
# ============================================
ax2 = fig.add_subplot(2, 3, 2)
segment_clv = clv.groupby('segment')['clv_simple'].mean().sort_values(ascending=False)
bars = ax2.bar(segment_clv.index, segment_clv.values, 
               color=['#FFD700', '#C0C0C0', '#CD7F32'])
ax2.set_title('Average CLV by Segment', fontsize=12, fontweight='bold', pad=10)
ax2.set_xlabel('Segment')
ax2.set_ylabel('Average CLV (RUB)')
ax2.tick_params(axis='x', rotation=45)

for bar, value in zip(bars, segment_clv.values):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'{value:,.0f}', ha='center', va='bottom', fontsize=9)

# ============================================
# Graph 3: CLV Categories
# ============================================
ax3 = fig.add_subplot(2, 3, 3)
category_dist = clv['clv_category'].value_counts()
order = ['VIP', 'High', 'Medium', 'Low']
category_dist = category_dist.reindex(order)
wedges, texts, autotexts = ax3.pie(category_dist.values, 
                                    labels=category_dist.index,
                                    autopct='%1.1f%%',
                                    colors=colors,
                                    startangle=90)
ax3.set_title('CLV Categories Distribution', fontsize=12, fontweight='bold', pad=10)

# ============================================
# Graph 4: Top-10 Customers
# ============================================
ax4 = fig.add_subplot(2, 3, 4)
top10 = clv.nlargest(10, 'clv_simple')
colors_top = plt.cm.RdYlGn_r(np.linspace(0, 1, len(top10)))
bars = ax4.barh(range(len(top10)), top10['clv_simple'], color=colors_top)
ax4.set_yticks(range(len(top10)))
ax4.set_yticklabels(top10['customer_id'])
ax4.set_title('Top 10 Customers by CLV', fontsize=12, fontweight='bold', pad=10)
ax4.set_xlabel('CLV (RUB)')
ax4.invert_yaxis()

for i, (bar, value) in enumerate(zip(bars, top10['clv_simple'])):
    ax4.text(value, bar.get_y() + bar.get_height()/2,
             f' {value:,.0f}', ha='left', va='center', fontsize=8)

# ============================================
# Graph 5: Monthly Revenue Trend
# ============================================
ax5 = fig.add_subplot(2, 3, 5)
monthly_sales = transactions.set_index('date').resample('ME')['amount'].sum()
ax5.plot(monthly_sales.index, monthly_sales.values, 
         marker='o', linewidth=2, markersize=6, color='#2ecc71')
ax5.fill_between(monthly_sales.index, monthly_sales.values, alpha=0.3)
ax5.set_title('Monthly Revenue Trend', fontsize=12, fontweight='bold', pad=10)
ax5.set_xlabel('Date')
ax5.set_ylabel('Revenue (RUB)')
ax5.grid(True, alpha=0.3)
ax5.tick_params(axis='x', rotation=45)

# ============================================
# Graph 6: Frequency vs Average Check
# ============================================
ax6 = fig.add_subplot(2, 3, 6)
scatter = ax6.scatter(clv['frequency'], clv['avg_check'], 
                      c=clv['clv_simple'], cmap='viridis', 
                      s=np.clip(clv['frequency']*20, 15, 200), alpha=0.6)
ax6.set_xlabel('Purchase Frequency')
ax6.set_ylabel('Average Check (RUB)')
ax6.set_title('Frequency vs Average Check', fontsize=12, fontweight='bold', pad=10)
ax6.grid(True, alpha=0.3)

cbar = plt.colorbar(scatter, ax=ax6)
cbar.set_label('CLV (RUB)', rotation=270, labelpad=15)

# Настройка отступов
plt.tight_layout()
plt.subplots_adjust(top=0.93, hspace=0.3, wspace=0.3)

# Сохраняем изображение
plt.savefig("output/clv_dashboard.png", dpi=150, bbox_inches='tight', facecolor='white')
print("[OK] Dashboard saved: output/clv_dashboard.png")

print("\n" + "="*60)
print("STATISTICS FOR PRESENTATION")
print("="*60)

print(f"\n[1] GENERAL STATISTICS:")
print(f"    Total customers: {len(clv)}")
print(f"    Total transactions: {len(transactions)}")
print(f"    Total revenue: {transactions['amount'].sum():,.2f} RUB")
print(f"    Average transaction: {transactions['amount'].mean():,.2f} RUB")

print(f"\n[2] CLV STATISTICS:")
print(f"    Mean CLV: {clv['clv_simple'].mean():,.2f} RUB")
print(f"    Median CLV: {clv['clv_simple'].median():,.2f} RUB")
print(f"    Max CLV: {clv['clv_simple'].max():,.2f} RUB")
print(f"    Min CLV: {clv['clv_simple'].min():,.2f} RUB")

print(f"\n[3] SEGMENT DISTRIBUTION:")
for segment in clv['segment'].unique():
    count = len(clv[clv['segment'] == segment])
    percent = count/len(clv)*100
    avg_clv = clv[clv['segment'] == segment]['clv_simple'].mean()
    print(f"    {segment}: {count} customers ({percent:.1f}%), avg CLV: {avg_clv:,.0f} RUB")

print(f"\n[4] CLV CATEGORIES:")
for category in ['VIP', 'High', 'Medium', 'Low']:
    count = len(clv[clv['clv_category'] == category])
    percent = count/len(clv)*100
    if count > 0:
        avg_clv = clv[clv['clv_category'] == category]['clv_simple'].mean()
        print(f"    {category}: {count} customers ({percent:.1f}%), avg CLV: {avg_clv:,.0f} RUB")

print(f"\n[5] TOP 10 CUSTOMERS BY CLV:")
print(f"    {'Rank':<4} {'Customer ID':<15} {'Segment':<12} {'CLV (RUB)':<15}")
print(f"    {'-'*4} {'-'*15} {'-'*12} {'-'*15}")
for idx, (i, row) in enumerate(top10.iterrows(), 1):
    print(f"    {idx:<4} {row['customer_id']:<15} {row['segment']:<12} {row['clv_simple']:>15,.0f}")

print(f"\n[6] PARETO PRINCIPLE (80/20):")
sorted_customers = clv.sort_values('total_revenue', ascending=False)
cumulative_revenue = sorted_customers['total_revenue'].cumsum()
total_revenue = cumulative_revenue.iloc[-1]
top_20_percent = int(len(sorted_customers) * 0.2)
revenue_from_top_20 = cumulative_revenue.iloc[top_20_percent - 1] if top_20_percent > 0 else 0
percent_revenue = (revenue_from_top_20 / total_revenue) * 100
print(f"    Top 20% customers generate: {percent_revenue:.1f}% of revenue")

print("\n" + "="*60)
print("Displaying charts...")

if 'DISPLAY' in os.environ:
    print("Close the plot window to continue")
    print("="*60)
    plt.show(block=True)
else:
    print("[INFO] No display available. Skipping plot window.")
    print("="*60)
    plt.close()

print("\nPlot window closed. Continuing...")