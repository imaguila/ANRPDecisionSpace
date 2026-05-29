from problem import run_pipeline

# 👇 eliges dataset
problema = "BAGNALL"

# 👇 eliges indicadores
indicadores = [
    "throughput",
    "productivity",
    "squandering"
]

df = run_pipeline(problema, indicadores)

print(df.head())

# guardar
df.to_csv(f"data/{problema}/{problema.lower()}_output.csv", index=False)
