import json
import requests
import sys
import re

# ============================================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================================

API_KEY = "4638754010a3f9ccfa253f46b376a643"
BASE_URL = "https://api.itjobs.pt"


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7',
}


# ============================================================================
# ALÍNEA A) - Listar N trabalhos mais recentes
# ============================================================================

def top(n):
    """
    Lista os N trabalhos mais recentes publicados pela itjobs.pt.
    Exemplo: python emprego.py top 30
    """
    url = f"{BASE_URL}/job/list.json"
    params = {"api_key": API_KEY, "limit": n}
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        
        if response.status_code == 403:
            print("ERRO: API bloqueada pelo Cloudflare. A tentar alternativa...")
            response = requests.get(url, params=params, timeout=10)
        
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            print(f"Erro da API: {data['error']}")
            sys.exit(1)
        
        jobs = data.get("results", [])
        print(json.dumps(jobs, ensure_ascii=False, indent=2))
        
    except requests.RequestException as e:
        print(f"Erro ao conectar à API: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erro: Resposta inválida da API (Status: {response.status_code})")
        sys.exit(1)


# ============================================================================
# ALÍNEA B) - Listar trabalhos part-time por empresa e localidade
# ============================================================================

def search(localidade, empresa, n):
    """
    Lista trabalhos part-time de uma empresa numa localidade.
    Exemplo: python emprego.py search Porto "KCS IT" 3
    """
    url = f"{BASE_URL}/job/search.json"
    
    
    params = {
        "api_key": API_KEY,
        "q": empresa,
        "limit": 100
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        
        if response.status_code == 403:
            print("ERRO: API bloqueada pelo Cloudflare. A tentar alternativa...")
            response = requests.get(url, params=params, timeout=10)
        
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            print(f"Erro da API: {data['error']}")
            sys.exit(1)
        
        jobs = data.get("results", [])
        
        # Filtra por localidade e part-time
        filtered_jobs = []
        for job in jobs:
            # Localidade
            location_match = False
            if "locations" in job and job["locations"]:
                for loc in job["locations"]:
                    if localidade.lower() in loc.get("name", "").lower():
                        location_match = True
                        break
            
            # Se é part time
            is_part_time = False
            if "types" in job and job["types"]:
                for job_type in job["types"]:
                    type_name = job_type.get("name", "").lower()
                    if "part" in type_name or "parcial" in type_name:
                        is_part_time = True
                        break
            
           
            if location_match and is_part_time:
                filtered_jobs.append(job)
                if len(filtered_jobs) >= n:
                    break
        
# resultados
        if not filtered_jobs:
            print("Nenhum trabalho part-time.")
        else:
            print(json.dumps(filtered_jobs[:n], ensure_ascii=False, indent=2))
        
    except requests.RequestException as e:
        print(f"Erro ao conectar à API: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erro: Resposta inválida da API (Status: {response.status_code})")
        sys.exit(1)


# ============================================================================
# MAIN - Processamento dos argumentos da linha de comando
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python emprego.py top N")
        print("  python emprego.py search LOCALIDADE EMPRESA N")
        print("  python emprego.py type JOB_ID")

        sys.exit(1)
    
    comando = sys.argv[1]
    
    # -------------------- COMANDO: top --------------------
    if comando == "top":
        if len(sys.argv) < 3:
            print("ERRO: Falta o argumento N")
            print("Uso: python emprego.py top N")
            sys.exit(1)
        try:
            n = int(sys.argv[2])
            top(n)
        except ValueError:
            print(f"ERRO: '{sys.argv[2]}' não é um número válido")
            sys.exit(1)
    
    # -------------------- COMANDO: search --------------------
    elif comando == "search":
        if len(sys.argv) < 5:
            print("ERRO: Faltam argumentos")
            print("Uso: python emprego.py search LOCALIDADE EMPRESA N")
            print("Exemplo: python emprego.py search Porto 'KCS IT' 3")
            sys.exit(1)
        try:
            localidade = sys.argv[2]
            empresa = sys.argv[3]
            n = int(sys.argv[4])
            search(localidade, empresa, n)
        except ValueError:
            print(f"ERRO: '{sys.argv[4]}' não é um número válido")
            sys.exit(1)
     

    
    # -------------------- COMANDO DESCONHECIDO --------------------
    else:
        print(f"Comando desconhecido: {comando}")
        print("Comandos disponíveis: top, search")
        sys.exit(1)

