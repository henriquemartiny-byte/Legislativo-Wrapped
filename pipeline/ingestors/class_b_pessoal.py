"""
Ingestor Efêmero de Pessoal e Gastos de Gabinete (Câmara e Senado)
Padrão Vogon Cívico: Processa em memória, enriquece metadados determinísticos e auto-deleta brutos.
"""

import io
import re
import unicodedata
from typing import Dict, Any, List
import httpx
import polars as pl


def normalize_name(text: str) -> str:
    """Normaliza nomes para matching robusto sem acentos e maiúsculas."""
    if not text:
        return ""
    # Remove acentos
    nfkd = unicodedata.normalize("NFKD", text)
    clean = "".join([c for c in nfkd if not unicodedata.combining(c)])
    # Remove títulos e caracteres não alfanuméricos
    clean = re.sub(r"[^A-Za-z0-9 ]+", " ", clean)
    # Remove múltiplos espaços
    return " ".join(clean.upper().split())


# Tabela aproximada de remuneração média de Secretário Parlamentar da Câmara (SP01 a SP25 com GRG média)
# Teto mensal da verba por gabinete: R$ 165.806,07 (Ato da Mesa 243)
VALOR_MEDIO_SP = {
    "SP01": 2100.0, "SP02": 2450.0, "SP03": 2900.0, "SP04": 3400.0, "SP05": 3900.0,
    "SP06": 4500.0, "SP07": 5200.0, "SP08": 5900.0, "SP09": 6700.0, "SP10": 7600.0,
    "SP11": 8500.0, "SP12": 9500.0, "SP13": 10500.0, "SP14": 11600.0, "SP15": 12700.0,
    "SP16": 13900.0, "SP17": 15100.0, "SP18": 16400.0, "SP19": 17800.0, "SP20": 19200.0,
    "SP21": 20700.0, "SP22": 22300.0, "SP23": 23900.0, "SP24": 25600.0, "SP25": 27400.0
}
DEFAULT_SP_SALARY = 7500.0  # Média ponderada por assessor da Câmara


def fetch_camara_secretarios() -> Dict[str, List[Dict[str, Any]]]:
    """
    Baixa o arquivo oficial de funcionários da Câmara e extrai os secretários parlamentares por deputado.
    """
    url = "https://dadosabertos.camara.leg.br/arquivos/funcionarios/csv/funcionarios.csv"
    try:
        r = httpx.get(url, follow_redirects=True, timeout=30)
        if r.status_code != 200:
            print(f"Aviso: Erro ao baixar funcionarios da Camara: HTTP {r.status_code}")
            return {}
        
        df = pl.read_csv(io.BytesIO(r.content), separator=";", ignore_errors=True)
        # Filtra secretários parlamentares
        sec = df.filter(pl.col("grupo") == "Secretário Parlamentar")
        
        gabinete_map: Dict[str, List[Dict[str, Any]]] = {}
        
        for row in sec.iter_rows(named=True):
            lotacao = row.get("lotacao") or ""
            # Formato típico: "GAB. 4/528 - AFONSO MOTTA"
            parts = lotacao.split(" - ")
            if len(parts) >= 2:
                dep_name_raw = parts[-1].strip()
            else:
                dep_name_raw = lotacao
            
            norm_key = normalize_name(dep_name_raw)
            if not norm_key:
                continue
            
            cargo_code = (row.get("cargo") or "").strip().upper()[:4]
            salario_est = VALOR_MEDIO_SP.get(cargo_code, DEFAULT_SP_SALARY)
            
            assessor_info = {
                "nome": (row.get("nome") or "").strip().title(),
                "cargo": row.get("cargo") or "Secretário Parlamentar",
                "salario_est": salario_est,
                "data_nomeacao": row.get("dataNomeacao") or ""
            }
            
            if norm_key not in gabinete_map:
                gabinete_map[norm_key] = []
            gabinete_map[norm_key].append(assessor_info)
            
        print(f"Câmara: {len(sec)} secretários mapeados para {len(gabinete_map)} gabinetes.")
        return gabinete_map
    except Exception as e:
        print(f"Erro ao processar secretarios da Camara: {e}")
        return {}


def fetch_senado_comissionados() -> Dict[str, List[Dict[str, Any]]]:
    """
    Consome a API de dados administrativos do Senado e extrai servidores comissionados por senador.
    """
    url = "https://adm.senado.gov.br/adm-dadosabertos/api/v1/servidores"
    try:
        r = httpx.get(url, follow_redirects=True, timeout=30)
        if r.status_code != 200:
            print(f"Aviso: Erro ao consultar servidores do Senado: HTTP {r.status_code}")
            return {}
        
        data = r.json().get("data", [])
        gabinete_map: Dict[str, List[Dict[str, Any]]] = {}
        
        for s in data:
            hierarquia = s.get("hierarquiaCompleta", [])
            # Procura nó que identifica o gabinete do senador
            # Exemplo: 'GSRSANT - GABINETE DO SENADOR ROGÉRIO CARVALHO'
            sen_name_raw = ""
            for h in hierarquia:
                h_name = h.get("nome", "")
                m = re.search(r"GABINETE D[OA] SENADOR[A]?\s+(.*)", h_name, flags=re.IGNORECASE)
                if m:
                    sen_name_raw = m.group(1).strip()
                    break
            
            if not sen_name_raw:
                continue
                
            norm_key = normalize_name(sen_name_raw)
            assessor_info = {
                "nome": (s.get("nome") or "").strip().title(),
                "cargo": s.get("cargo") or s.get("funcao") or "Assessor Parlamentar",
                "salario_est": 11500.0,  # Média de remuneração de assessor comissionado do Senado
                "data_nomeacao": s.get("dataAdmissao") or ""
            }
            
            if norm_key not in gabinete_map:
                gabinete_map[norm_key] = []
            gabinete_map[norm_key].append(assessor_info)
            
        print(f"Senado: {sum(len(v) for v in gabinete_map.values())} servidores mapeados para {len(gabinete_map)} gabinetes.")
        return gabinete_map
    except Exception as e:
        print(f"Erro ao processar comissionados do Senado: {e}")
        return {}


def get_all_gabinete_data() -> Dict[str, Dict[str, Any]]:
    """
    Agrega dados de gabinete da Câmara e do Senado prontos para enriquecer o banco Gold.
    """
    cam_sec = fetch_camara_secretarios()
    sen_sec = fetch_senado_comissionados()
    
    # Dicionário consolidado por nome normalizado
    consolidated: Dict[str, Dict[str, Any]] = {}
    
    # Subsídio anual fixo com 13º salário (Lei nº 14.529/2023: R$ 46.366,19 * 13)
    SUBSIDIO_ANUAL = 602760.47
    
    for norm_name, staff in cam_sec.items():
        # Custo anual estimado da equipe de assessores (12 meses + 13º proporcional)
        total_folha_mensal = sum(a["salario_est"] for a in staff)
        # Limita ao teto oficial anual se passar do teto de R$ 165.806,07/mês
        folha_mensal_teto = min(total_folha_mensal, 165806.07)
        custo_equipe_ano = folha_mensal_teto * 13.33
        
        consolidated[norm_name] = {
            "casa": "Câmara dos Deputados",
            "qtd_assessores": len(staff),
            "custo_equipe_ano": round(custo_equipe_ano, 2),
            "subsidio_ano": SUBSIDIO_ANUAL,
            "auxilio_moradia_ano": 51036.00,  # Estimativa de benefício
            "assessores": staff[:30]  # Armazena a lista de assessores do gabinete
        }
        
    for norm_name, staff in sen_sec.items():
        # Senado: média de folha de comissionados por gabinete
        total_folha_mensal = sum(a["salario_est"] for a in staff)
        custo_equipe_ano = total_folha_mensal * 13.33
        
        consolidated[norm_name] = {
            "casa": "Senado Federal",
            "qtd_assessores": len(staff),
            "custo_equipe_ano": round(custo_equipe_ano, 2),
            "subsidio_ano": SUBSIDIO_ANUAL,
            "auxilio_moradia_ano": 51036.00,
            "assessores": staff[:55]
        }
        
    return consolidated


if __name__ == "__main__":
    data = get_all_gabinete_data()
    print(f"Total de parlamentares com folha de gabinete mapeada: {len(data)}")
    # Exibe amostra
    sample_key = next(iter(data.keys()))
    print(f"Amostra ({sample_key}):", data[sample_key]["qtd_assessores"], "assessores, custo equipe ano: R$", data[sample_key]["custo_equipe_ano"])
