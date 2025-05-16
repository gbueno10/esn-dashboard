import pandas as pd

# Leitura dos dados
print("Lendo os arquivos...")
students = pd.read_csv("data/students.csv")
events = pd.read_csv("data/events.csv")
purchases = pd.read_csv("data/event_purchases.csv")

# Converter colunas de data para datetime
print("\nConvertendo datas...")
students['registerDate'] = pd.to_datetime(students['registerDate'], errors='coerce')
events['startDate'] = pd.to_datetime(events['startDate'], errors='coerce')
purchases['purchaseDate'] = pd.to_datetime(purchases['purchaseDate'], errors='coerce')

# Análise de datas
print("\n=== Análise de Datas ===")

print("\n1. Estudantes (registerDate):")
print(f"Data mais antiga: {students['registerDate'].min()}")
print(f"Data mais recente: {students['registerDate'].max()}")
print(f"Total de registros: {len(students)}")

print("\n2. Eventos (startDate):")
print(f"Data mais antiga: {events['startDate'].min()}")
print(f"Data mais recente: {events['startDate'].max()}")
print(f"Total de eventos: {len(events)}")

print("\n3. Compras (purchaseDate):")
print(f"Data mais antiga: {purchases['purchaseDate'].min()}")
print(f"Data mais recente: {purchases['purchaseDate'].max()}")
print(f"Total de compras: {len(purchases)}")

# Análise de valores nulos
print("\n=== Valores Nulos em Datas ===")
print("\n1. Estudantes:")
print(students['registerDate'].isnull().sum(), "valores nulos em registerDate")

print("\n2. Eventos:")
print(events['startDate'].isnull().sum(), "valores nulos em startDate")

print("\n3. Compras:")
print(purchases['purchaseDate'].isnull().sum(), "valores nulos em purchaseDate") 