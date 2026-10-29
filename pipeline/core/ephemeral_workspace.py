"""
Gerenciador Efêmero e Roteador de Classes de Dados do Vogon Cívico.

Garante que:
- Classe A (Gigantes: Receita QSA, SICONFI, IBGE) sejam consultados remotamente via BigQuery (pushdown).
- Classe B (APIs Diárias: PNCP, CGU) sejam baixados num diretório temporário autodestrutivo,
  tenham seu hash SHA-256 auditado, sejam agregados via Polars/DuckDB e DELETADOS imediatamente do disco.
- Classe C (Gold Layer / Dashboards) salve apenas cubos analíticos leves (poucos MBs) prontos para visualização.
"""

from contextlib import contextmanager
import hashlib
from pathlib import Path
import tempfile
from typing import Iterator, Dict, Any


@contextmanager
def ephemeral_ingestion_zone(source_name: str) -> Iterator[Path]:
    """
    Cria uma zona temporária para baixar dados brutos (Classe B).
    Assim que o bloco `with` termina (mesmo se houver erro), 100% dos arquivos
    brutos são automaticamente excluídos do disco.
    """
    with tempfile.TemporaryDirectory(prefix=f"vogon_ephemeral_{source_name}_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        try:
            yield tmp_path
        finally:
            # O TemporaryDirectory do Python já remove toda a árvore ao sair do contexto.
            pass


def compute_audit_provenance(payload_bytes: bytes, source_url: str) -> Dict[str, Any]:
    """
    Calcula o carimbo de proveniência criptográfica (SHA-256) antes de descartar o arquivo bruto.
    """
    sha256_hash = hashlib.sha256(payload_bytes).hexdigest()
    return {
        "source_url": source_url,
        "sha256": sha256_hash,
        "size_bytes": len(payload_bytes),
    }

