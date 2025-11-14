import json
import requests
import sys
import re
from collections import Counter   
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
# ALÍNEA C) - Extrair regime de trabalho de um job ID
# ============================================================================

def type_job(job_id):
    """
    Extrai o regime de trabalho (remoto/híbrido/presencial) de um job ID.
    Exemplo: python emprego.py type 506697
    """
    url = f"{BASE_URL}/job/get.json"
    
    params = {
        "api_key": API_KEY,
        "id": job_id
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
        
        
        text_to_search = ""
        if "body" in data:
            text_to_search += data["body"].lower()
        if "title" in data:
            text_to_search += " " + data["title"].lower()
        

        if re.search(r'\b(100%\s*remoto|full\s*remote|fully\s*remote|remote\s*work|trabalho\s*remoto)\b', text_to_search):
            print("remote")
        # Depois híbrido
        elif re.search(r'\b(híbrido|hibrido|hybrid|regime\s*híbrido|modelo\s*híbrido|parcialmente\s*remoto)\b', text_to_search):
            print("hybrid")
        # Depois presencial
        elif re.search(r'\b(presencial|on-?site|escritório|escritorio|no\s*local)\b', text_to_search):
            print("onsite")
        # Se não encontrar nada
        else:
            print("unknown")
        
    except requests.RequestException as e:
        print(f"Erro ao conectar à API: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erro: Resposta inválida da API (Status: {response.status_code})")
        sys.exit(1)


# ============================================================================
# ALÍNEA D) - Contar ocorrências de skills entre duas datas
# ============================================================================

def skills(data_inicial, data_final):
    """
    Conta ocorrências de skills nas descrições dos anúncios entre duas datas.
    Exemplo:
      python emprego.py skills 2024-01-01 2024-02-01
    Saída: [{ "skill1": 2, "skill2": 1, ... }]
    """

    url = f"{BASE_URL}/job/search.json"

    params = {
        "api_key": API_KEY,
        "limit": 200,               # número máximo de anúncios a analisar
        "published_after": data_inicial,
        "published_before": data_final,
    }

    # Lista de skills a analisar 
    lista_skills = [
        "python", "java", "javascript", "c#", "c++", "sql", "html",
        "css", "react", "node", "linux", "docker", "kubernetes",
        "aws", "azure", "git", "django", "flask"
    ]

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = data.get("results", [])

        contagem = Counter()

        # Percorrer anúncios e contar skills
        for job in jobs:
            texto = ""
            if "title" in job and job["title"]:
                texto += job["title"].lower() + " "
            if "body" in job and job["body"]:
                texto += job["body"].lower()

            for skill in lista_skills:
                ocorrencias = texto.count(skill.lower())
                if ocorrencias > 0:
                    contagem[skill] += ocorrencias

        # Ordenar por número de ocorrências (decrescente)
        ordenado = contagem.most_common()

        # Formato pedido: [ {"skill1":2,"skill2":1,...} ]
        resultado_dict = {skill: count for skill, count in ordenado}
        resultado = [resultado_dict]

        print(json.dumps(resultado, ensure_ascii=False, indent=2))

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
     
    # -------------------- COMANDO: type --------------------
    elif comando in ("type", "tipo", "regime"):
        if len(sys.argv) < 3:
            print("ERRO: Falta o argumento JOB_ID")
            print("Uso: python emprego.py type JOB_ID")
            sys.exit(1)
        job_id = sys.argv[2]
        type_job(job_id)

    # -------------------- COMANDO: skills --------------------
    elif comando == "skills":
        if len(sys.argv) < 4:
            print("ERRO: Faltam argumentos")
            print("Uso: python emprego.py skills dataInicial dataFinal")
            sys.exit(1)
        data_inicial = sys.argv[2]
        data_final = sys.argv[3]
        skills(data_inicial, data_final)

    
    # -------------------- COMANDO DESCONHECIDO --------------------
    else:
        print(f"Comando desconhecido: {comando}")
        print("Comandos disponíveis: top, search")
        sys.exit(1)

