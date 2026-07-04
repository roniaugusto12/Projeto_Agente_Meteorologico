import requests
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Configurações iniciais para a API da APAC (a serem preenchidas após liberação do acesso)
APAC_API_BASE_URL = "https://api.apac.pe.gov.br/v1"  # URL base provisória
APAC_TIMEOUT = 15

def coletar_dados_apac(estacao_id: str, data_str: str, token: str = None) -> list[dict] | None:
    """
    Coleta dados meteorológicos e pluviométricos reais da APAC.
    Requer homologação e token de acesso solicitados via monitoramento@apac.pe.gov.br.
    
    Args:
        estacao_id: Código da estação na rede APAC.
        data_str: Data de referência (formato YYYY-MM-DD).
        token: Chave de API fornecida pela APAC.
        
    Returns:
        Lista de registros horários obtidos, ou None em caso de indisponibilidade/sem token.
    """
    if not token:
        logger.warning(
            f"Chamada para APAC ({estacao_id} em {data_str}) ignorada. "
            "Aguardando homologação de credenciais oficiais da API da APAC."
        )
        return None

    url = f"{APAC_API_BASE_URL}/estacoes/{estacao_id}/dados"
    params = {
        "data": data_str,
        "token": token
    }
    headers = {
        "User-Agent": "Tecomat-AgenteMeteorologico/1.0 (Recife, PE)",
        "Accept": "application/json"
    }

    try:
        logger.info(f"Enviando requisição para API APAC: {url} | Data: {data_str}")
        resposta = requests.get(url, params=params, headers=headers, timeout=APAC_TIMEOUT)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            logger.info(f"Dados obtidos com sucesso da API APAC para a estação {estacao_id}.")
            return dados
        elif resposta.status_code == 401:
            logger.error("Erro de Autenticação na API da APAC: Token inválido ou expirado.")
            return None
        else:
            logger.error(f"Erro ao consultar API APAC: Status {resposta.status_code} | Resposta: {resposta.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Falha de conexão com a API da APAC: {e}")
        return None
