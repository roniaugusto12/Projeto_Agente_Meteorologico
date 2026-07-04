import zipfile

zip_path = "2026.zip"
csv_name = "INMET_NE_PE_A301_RECIFE_01-01-2026_A_30-06-2026.CSV"

try:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        with zip_ref.open(csv_name) as f:
            for i in range(15):
                line = f.readline().decode('iso-8859-1')
                print(f"{i+1}: {line.strip()}")
except Exception as e:
    print(f"Erro: {e}")
