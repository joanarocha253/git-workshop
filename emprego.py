import json
import requests
import sys
import re
import csv
from collections import Counter
from bs4 import BeautifulSoup


# CONFIGURAÇÕES GLOBAIS

API_KEY = "4638754010a3f9ccfa253f46b376a643"
BASE_URL = "https://api.itjobs.pt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7',
}


TEAMLYZER_BASE = "https://pt.teamlyzer.com"
TEAMLYZER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TeamlyzerScraper/1.0)"
}

# ALÍNEA A) - Listar N trabalhos mais recentes

def top(n, csv_path=None):
    """
    Lista os N trabalhos mais recentes publicados pela itjobs.pt.
    Exemplo: 
      python emprego.py top 30
      python emprego.py top 30 resultado.csv
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

        # Exportar para CSV se o nome do ficheiro foi indicado
        if csv_path:
            export_jobs_to_csv(jobs, csv_path)
        
    except requests.RequestException as e:
        print(f"Erro ao conectar Ã  API: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erro: Resposta invÃ¡lida da API (Status: {response.status_code})")
        sys.exit(1)

# ALÍNEA B) - Listar trabalhos part-time por empresa e localidade

def search(localidade, empresa, n, csv_path=None):
    """
    Lista trabalhos part-time de uma empresa numa localidade.
    Exemplo: 
      python emprego.py search Porto "KCS IT" 3
      python emprego.py search Porto "KCS IT" 3 resultados.csv
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
            
            # Se Ã© part time
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

        # Exportar para CSV se o nome do ficheiro foi indicado
        if csv_path and filtered_jobs:
            export_jobs_to_csv(filtered_jobs[:n], csv_path)
        
    except requests.RequestException as e:
        print(f"Erro ao conectar Ã  API: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erro: Resposta invÃ¡lida da API (Status: {response.status_code})")
        sys.exit(1)

# ALÍNEA C) - Extrair regime de trabalho de um job ID

def type_job(job_id):
    """
    Extrai o regime de trabalho (remoto/hÃ­brido/presencial) de um job ID.
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
        # remoto
        if re.search(r'\b(100%\s*remoto|full\s*remote|fully\s*remote|remote\s*work|trabalho\s*remoto)\b', text_to_search):
            print("remote")
        # híbrido
        elif re.search(r'\b(híbrido|hibrido|hybrid|regime\s*híbrido|modelo\s*híbrido|parcialmente\s*remoto)\b', text_to_search):
            print("hybrid")
        # presencial
        elif re.search(r'\b(presencial|on-?site|escritório|escritorio|no\s*local)\b', text_to_search):
            print("onsite")
        # se não encontrar nada
        else:
            print("unknown")
        
    except requests.RequestException as e:
        print(f"Erro ao conectar Ã  API: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erro: Resposta invÃ¡lida da API (Status: {response.status_code})")
        sys.exit(1)

# ALÍNEA D) - Contar ocorrências de skills entre duas datas

def skills(data_inicial, data_final):
    """
    Conta ocorrÃªncias de skills nas descriÃ§Ãµes dos anÃºncios entre duas datas.
    Exemplo:
      python emprego.py skills 2024-01-01 2024-02-01
    SaÃ­da: [{ "skill1": 2, "skill2": 1, ... }]
    """
    url = f"{BASE_URL}/job/search.json"

    params = {
        "api_key": API_KEY,
        "limit": 200,               # nÃºmero mÃ¡ximo de anÃºncios a analisar
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

        # Percorrer anÃºncios e contar skills
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

        # Ordenar por nÃºmero de ocorrÃªncias (decrescente)
        ordenado = contagem.most_common()

        # Formato pedido: [ {"skill1":2,"skill2":1,...} ]
        resultado_dict = {skill: count for skill, count in ordenado}
        resultado = [resultado_dict]

        print(json.dumps(resultado, ensure_ascii=False, indent=2))

    except requests.RequestException as e:
        print(f"Erro ao conectar Ã  API: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erro: Resposta invÃ¡lida da API (Status: {response.status_code})")
        sys.exit(1)

# Alinea E): exportar lista de jobs para CSV

def clean_html(raw_html):
    """
    Remove tags HTML de um texto.
    """
    clean = re.compile('<.*?>')
    return re.sub(clean, '', raw_html).strip()

def export_jobs_to_csv(jobs, csv_path):
    """
    Exporta uma lista de anúncios para CSV com os campos:
    titulo; empresa; descricao; data_publicacao; salario; localizacao
    """
    fieldnames = [
        "titulo",
        "empresa",
        "descricao",
        "data_publicacao",
        "salario",
        "localizacao",
    ]

    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for job in jobs:
                titulo = job.get("title", "") or "Sem título"
                empresa = job.get("company", {}).get("name", "") or "Não especificado"
                descricao_raw = job.get("body", "") or ""
                descricao = clean_html(descricao_raw) or "Sem descrição"
                data_pub = job.get("publishedAt", "") or "Desconhecida"
                salario = job.get("wage", "") or "Não especificado"

                locs = job.get("locations", []) or []
                localizacao = ", ".join(loc.get("name", "") for loc in locs) or "Não especificado"

                writer.writerow({
                    "titulo": titulo,
                    "empresa": empresa,
                    "descricao": descricao,
                    "data_publicacao": data_pub,
                    "salario": salario,
                    "localizacao": localizacao,
                })

        print(f"CSV criado com sucesso: {csv_path}")

    except OSError as e:
        print(f"Erro ao escrever o ficheiro CSV '{csv_path}': {e}")




# ============================================================
#                   TRABALHO PRÁTICO 2 
# ============================================================


# ALÍNEA A) - Informações acerca da empresa que publicita o trabalho

def find_teamlyzer_company_url(company_name):
    """
    Procura a empresa no ranking do Teamlyzer e devolve o URL da página dela.
    """
    ranking_url = TEAMLYZER_BASE + "/companies/ranking"

    try:
        response = requests.get(ranking_url, headers=TEAMLYZER_HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Erro ao aceder ao Teamlyzer: {e}")
        return None

    soup = BeautifulSoup(response.text, "lxml")
    
    # Normalizar nome da empresa
    company_clean = re.sub(r'[^\w\s]', '', company_name.lower().strip())

    for link in soup.find_all("a", href=True):
        if "/companies/" in link["href"] and link["href"] != "/companies/ranking":
            texto = re.sub(r'[^\w\s]', '', link.get_text(strip=True).lower())
            
            
            if company_clean in texto or texto in company_clean:
                return TEAMLYZER_BASE + link["href"]

    return None


def scrape_teamlyzer_info(url):
    """
    Extrai rating, descrição, benefícios e salário médio da página da empresa.
    NOTA: Os seletores são genéricos - deve adaptar ao HTML real do site!
    """
    try:
        response = requests.get(url, headers=TEAMLYZER_HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Erro ao fazer scraping: {e}")
        return {
            "teamlyzer_rating": None,
            "teamlyzer_description": None,
            "teamlyzer_benefits": None,
            "teamlyzer_salary": None
        }

    soup = BeautifulSoup(response.text, "lxml")

    # RATING 
    rating = None
    for tag in soup.find_all(text=re.compile(r'\d+[.,]\d+')):
        match = re.search(r'(\d+)[.,](\d+)', tag)
        if match:
            try:
                rating = float(f"{match.group(1)}.{match.group(2)}")
                if 0 <= rating <= 5:
                    break
            except:
                continue

    # DESCRIÇÃO 
    desc = None
    meta_desc = soup.find("meta", {"name": "description"})
    if meta_desc and meta_desc.get("content"):
        desc = meta_desc["content"]
    else:
        first_p = soup.find("p")
        if first_p:
            desc = first_p.get_text(" ", strip=True)

    # BENEFÍCIOS 
    benefits = None
    for ul in soup.find_all("ul"):
        items = [li.get_text(" ", strip=True) for li in ul.find_all("li")]
        if items and len(items) > 2:  
            benefits = "; ".join(items[:5])  # Primeiros 5
            break

    # SALÁRIO 
    salary = None
    for tag in soup.find_all(text=re.compile(r'(salário|salary|€|\$)', re.IGNORECASE)):
        text = tag.strip()
        if len(text) < 200:  
            salary = text
            break

    return {
        "teamlyzer_rating": rating,
        "teamlyzer_description": desc,
        "teamlyzer_benefits": benefits,
        "teamlyzer_salary": salary
    }


def get_job(job_id, csv_path=None):
    """
    Alínea (a) – Junta dados do itjobs + scraping Teamlyzer.
    Exemplo: python emprego.py get 506697
             python emprego.py get 506697 output.csv
    """
    url = f"{BASE_URL}/job/get.json"
    params = {"api_key": API_KEY, "id": job_id}

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        job = response.json()
        
        if "error" in job:
            print(f"Erro da API: {job['error']}")
            return
            
    except requests.RequestException as e:
        print(f"Erro ao obter job da API: {e}")
        return
    except json.JSONDecodeError:
        print("Erro: Resposta inválida da API")
        return

    # Nome da empresa
    company = job.get("company", {}).get("name")
    if not company:
        print("O job não tem empresa associada.")
        print(json.dumps(job, indent=2, ensure_ascii=False))
        return

    # URL da empresa no Teamlyzer
    url_empresa = find_teamlyzer_company_url(company)

    if not url_empresa:
        print(f"Empresa '{company}' não encontrada no Teamlyzer.")
        job.update({
            "teamlyzer_rating": None,
            "teamlyzer_description": None,
            "teamlyzer_benefits": None,
            "teamlyzer_salary": None
        })
    else:
        # Extrair informação da empresa
        extra = scrape_teamlyzer_info(url_empresa)
        job.update(extra)

    # Imprimir JSON 
    print(json.dumps(job, indent=2, ensure_ascii=False))
    
# ALÍNEA B) - contagem de vagas por tipo/nome da posição e por região.

def statistics_zone(csv_path="statistics_zone.csv"):
   
    url = f"{BASE_URL}/job/list.json"
    params = {
        "api_key": API_KEY,
        "limit": 200   
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

        if not jobs:
            print("Não foram encontrados trabalhos para gerar estatísticas.")
            return

        # (Zona, Tipo de Trabalho) -> Nº de vagas
        contagens = Counter()

        for job in jobs:
            titulo = job.get("title", "") or "Sem título"
            locations = job.get("locations") or []

            # Se o anúncio não tiver localizações, conto numa zona "Desconhecida"
            if not locations:
                zona = "Desconhecida"
                contagens[(zona, titulo)] += 1
            else:
                # Cada localização conta como uma vaga nessa zona
                for loc in locations:
                    zona = loc.get("name", "") or "Desconhecida"
                    contagens[(zona, titulo)] += 1

        # --- Escrita do CSV ---
        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Zona", "Tipo de Trabalho", "Nº de vagas"])

                for (zona, tipo), n_vagas in sorted(contagens.items()):
                    writer.writerow([zona, tipo, n_vagas])

            print("Ficheiro de exportação criado com sucesso.")

        except OSError as e:
            print(f"Erro ao escrever o ficheiro CSV '{csv_path}': {e}")

    except requests.RequestException as e:
        print(f"Erro ao conectar à API: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erro: Resposta inválida da API (Status: {response.status_code})")
        sys.exit(1)

# ALÍNEA C) - Listar principais skills para um trabalho a partir do Teamlyzer

def list_skills(job_title, count=1000):
    """
    Alínea (c) – Lista as principais (top 10) skills para um determinado trabalho.
    Acede ao Teamlyzer para obter as skills mais relevantes.
    Exemplo: python emprego.py list skills "data scientist"
             python emprego.py list skills "python" --count 1000
    """
    # Normalizar o título do trabalho para criar a URL
    job_title_normalized = job_title.lower().strip().replace(" ", "")
    
    # Construir URL do Teamlyzer para esse job
    teamlyzer_url = f"{TEAMLYZER_BASE}/companies/jobs?tags={job_title_normalized}order=most_relevant"
    
    try:
        response = requests.get(teamlyzer_url, headers=TEAMLYZER_HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Erro ao aceder ao Teamlyzer: {e}")
        print(json.dumps([{"skill": job_title, "count": 0}], indent=2, ensure_ascii=False))
        return
    
    soup = BeautifulSoup(response.text, "lxml")
    
    # Lista de skills técnicas válidas
    valid_skills = {
        # Linguagens de programação
        "python", "java", "javascript", "typescript", "c++", "c#", "php", "ruby", 
        "go", "golang", "rust", "swift", "kotlin", "scala", "r", "matlab",
        
        # Frameworks e bibliotecas
        "react", "angular", "vue", "svelte", "django", "flask", "fastapi", 
        "spring", "hibernate", "express", "node", "nodejs", "laravel", ".net",
        "jquery", "bootstrap", "tailwind",
        
        # Bases de dados
        "sql", "postgresql", "mysql", "mongodb", "redis", "cassandra", 
        "elasticsearch", "oracle", "sqlite", "mariadb", "dynamodb",
        
        # DevOps e Cloud
        "docker", "kubernetes", "aws", "azure", "gcp", "jenkins", "gitlab",
        "terraform", "ansible", "ci/cd", "linux", "unix", "bash",
        
        # Controlo de versões
        "git", "github", "bitbucket", "svn",
        
        # Web
        "html", "css", "sass", "less", "webpack", "rest", "api", "graphql",
        "soap", "microservices",
        
        # Data Science e AI
        "machine learning", "ml", "deep learning", "ai", "tensorflow", 
        "pytorch", "scikit-learn", "pandas", "numpy", "keras", "data science",
        
        # Metodologias
        "agile", "scrum", "kanban", "devops",
        
        # Outras tecnologias
        "spark", "hadoop", "kafka", "rabbitmq", "nginx", "apache"
    }
    
    # Contador de skills encontradas
    skills_counter = Counter()
    
    # Obter todo o texto da página
    page_text = soup.get_text().lower()
    
    # Procurar apenas pelas skills válidas
    for skill in valid_skills:
        # Usar regex para encontrar a skill como palavra completa
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        occurrences = len(re.findall(pattern, page_text))
        if occurrences > 0:
            skills_counter[skill] += occurrences
    
    # Obter top 10 skills
    top_skills = skills_counter.most_common(10)
    
    # Se não encontramos skills, retornar mensagem
    if not top_skills:
        result = [{"skill": job_title, "count": count}]
    else:
        # Formatar resultado: [{"skill": "python", "count": 1000}, ...]
        result = [{"skill": skill, "count": cnt} for skill, cnt in top_skills]
    
    # Imprimir resultado em formato JSON
    print(json.dumps(result, indent=2, ensure_ascii=False))

# MAIN

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python emprego.py top N [FICHEIRO_CSV]")
        print("  python emprego.py search LOCALIDADE EMPRESA N [FICHEIRO_CSV]")
        print("  python emprego.py type JOB_ID")
        print("  python emprego.py skills dataInicial dataFinal")
        print("  python emprego.py get JOB_ID")
        sys.exit(1)

    comando = sys.argv[1]

    
    # -------------------- COMANDO: top --------------------
    if comando == "top":
        if len(sys.argv) < 3:
            print("ERRO: Falta o argumento N")
            print("Uso: python emprego.py top N [FICHEIRO_CSV]")
            sys.exit(1)
        try:
            n = int(sys.argv[2])
            csv_path = sys.argv[3] if len(sys.argv) >= 4 else None
            top(n, csv_path)
        except ValueError:
            print(f"ERRO: '{sys.argv[2]}' nÃ£o Ã© um nÃºmero vÃ¡lido")
            sys.exit(1)
    
    # -------------------- COMANDO: search --------------------
    elif comando == "search":
        if len(sys.argv) < 5:
            print("ERRO: Faltam argumentos")
            print("Uso: python emprego.py search LOCALIDADE EMPRESA N [FICHEIRO_CSV]")
            print("Exemplo: python emprego.py search Porto 'KCS IT' 3 resultados.csv")
            sys.exit(1)
        try:
            localidade = sys.argv[2]
            empresa = sys.argv[3]
            n = int(sys.argv[4])
            csv_path = sys.argv[5] if len(sys.argv) >= 6 else None
            search(localidade, empresa, n, csv_path)
        except ValueError:
            print(f"ERRO: '{sys.argv[4]}' nÃ£o Ã© um nÃºmero vÃ¡lido")
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
    
        # -------------------- TP2: comando get --------------------
    elif comando == "get":
        if len(sys.argv) < 3:
            print("Uso: python emprego.py get JOB_ID")
            sys.exit(1)
        job_id = sys.argv[2]
        get_job(job_id)

        # -------------------- TP2: comando statistics --------------------
    elif comando == "statistics":
        if len(sys.argv) < 3:
            print("ERRO: Falta o argumento 'zone'")
            print("Uso: python emprego.py statistics zone")
            sys.exit(1)

        subcomando = sys.argv[2].lower()

        if subcomando == "zone":
            
            csv_path = sys.argv[3] if len(sys.argv) >= 4 else "statistics_zone.csv"
            statistics_zone(csv_path)
        else:
            print(f"Subcomando desconhecido para 'statistics': {subcomando}")
            print("Uso: python emprego.py statistics zone")
            sys.exit(1)

        # -------------------- TP2: comando list skills --------------------
    elif comando == "list":
        if len(sys.argv) < 3:
            print("ERRO: Falta o subcomando")
            print("Uso: python emprego.py list skills JOB_TITLE [--count N]")
            sys.exit(1)
        
        subcomando = sys.argv[2].lower()
        
        if subcomando == "skills":
            if len(sys.argv) < 4:
                print("ERRO: Falta o argumento JOB_TITLE")
                print("Uso: python emprego.py list skills JOB_TITLE [--count N]")
                sys.exit(1)
            
            job_title = sys.argv[3]
            count = 1000  # Valor padrão
            
            # Verificar se foi fornecido o parâmetro --count
            if len(sys.argv) >= 5 and sys.argv[4] == "--count":
                if len(sys.argv) >= 6:
                    try:
                        count = int(sys.argv[5])
                    except ValueError:
                        print(f"ERRO: '{sys.argv[5]}' não é um número válido")
                        sys.exit(1)
            
            list_skills(job_title, count)
        else:
            print(f"Subcomando desconhecido para 'list': {subcomando}")
            print("Uso: python emprego.py list skills JOB_TITLE")
            sys.exit(1)
    
    # -------------------- COMANDO DESCONHECIDO --------------------
    else:
        print(f"Comando desconhecido: {comando}")
        print("Comandos disponíveis: top, search, type, skills, get, statistics, list")
        sys.exit(1)