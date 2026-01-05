import pandas as pd

# 1. Зареждане
csv_path = "dataset.csv"  # Увери се, че пътят е верен
df = pd.read_csv(csv_path)

# 2. Преброяване
# value_counts() прави всичко автоматично
counts = df['class_id'].value_counts().sort_index()
total = len(df)

print(f"📊 Общ брой точки в dataset-a: {total}\n")
print(f"{'ID на Клас':<15} | {'Брой точки':<15} | {'Процент':<10}")
print("-" * 45)

# 3. Принтиране с проценти
for class_id, count in counts.items():
    percentage = (count / total) * 100
    print(f"{class_id:<15} | {count:<15} | {percentage:.2f}%")

print("-" * 45)

# 4. Бърза проверка за баланс
min_class = counts.min()
max_class = counts.max()
ratio = max_class / min_class

if ratio > 3:
    print(f"\n⚠️ ВНИМАНИЕ: Имаш сериозен дисбаланс!")
    print(f"Най-големият клас е {ratio:.1f} пъти по-голям от най-малкия.")
    print("Съвет: Добави още точки за най-малкия клас или използвай class_weight='balanced'.")
else:
    print("\n✅ Данните изглеждат сравнително балансирани.")