"""
=================================================================
VERIFICAÇÃO DE ATUALIZAÇÃO (consulta releases novas no GitHub)
=================================================================
A versão (semver: MAJOR.MINOR.PATCH) fica embutida em
assets/versao.txt, escrito pela GitHub Action
(`.github/workflows/build-release.yml`) logo antes de compilar —
MAJOR.MINOR vêm do arquivo `VERSION` na raiz do repositório (ajustado
à mão quando a mudança merece), e PATCH é o número sequencial da
própria Action. Esse arquivo não existe no código-fonte nem em builds
feitas na mão fora do GitHub Actions, então `obter_versao_atual()`
retorna None nesses casos (não tem com o que comparar).
=================================================================
"""

import sys
import json
import threading
import urllib.request

from utils import config

URL_RELEASE_MAIS_RECENTE = "https://api.github.com/repos/ramonxxl/LosManager/releases/latest"
URL_PAGINA_RELEASES = "https://github.com/ramonxxl/LosManager/releases"


def _parsear_versao(texto):
    """'v1.0.47' ou '1.0.47' -> (1, 0, 47). Levanta ValueError se não
    for um formato major.minor.patch válido — comparar por tupla (não
    por string) evita o erro clássico de "1.0.9" > "1.0.10"."""

    partes = texto.strip().lstrip("vV").split(".")

    if len(partes) != 3:
        raise ValueError(f"versão em formato inesperado: {texto!r}")

    return tuple(int(parte) for parte in partes)


def formatar_versao(versao):

    return "v" + ".".join(str(parte) for parte in versao)


def obter_versao_atual():

    try:
        with open(config.caminho_asset("versao.txt"), "r", encoding="utf-8") as arquivo:
            return _parsear_versao(arquivo.read())
    except (OSError, ValueError):
        return None


def texto_versao():
    """Texto amigável pro rodapé de Configurações, cobrindo os 3
    cenários possíveis: build oficial saída do GitHub Actions, build
    local via build.bat (sem a versão embutida) ou rodando direto do
    código-fonte (`python main.py`)."""

    versao_atual = obter_versao_atual()

    if versao_atual is not None:
        return f"Los Manager — {formatar_versao(versao_atual)}"

    if getattr(sys, "frozen", False):
        return "Los Manager — build local (compilada fora do GitHub Actions)"

    return "Los Manager — código-fonte (modo desenvolvimento)"


def _consultar_release_mais_recente():
    """Chamada de rede (bloqueante) — sempre rodar numa thread separada.
    Retorna (versao_remota, url_release) ou levanta exceção se falhar."""

    requisicao = urllib.request.Request(
        URL_RELEASE_MAIS_RECENTE,
        headers={"Accept": "application/vnd.github+json"}
    )

    with urllib.request.urlopen(requisicao, timeout=6) as resposta:
        dados = json.loads(resposta.read().decode("utf-8"))

    versao_remota = _parsear_versao(dados.get("tag_name", ""))
    url_release = dados.get("html_url") or URL_PAGINA_RELEASES

    return versao_remota, url_release


def verificar_silenciosamente(ao_encontrar_atualizacao):
    """Uso automático (chamado uma vez ao abrir o app): roda em thread
    separada e só chama `ao_encontrar_atualizacao(versao_atual,
    versao_nova, url_release)` se realmente houver uma versão mais
    nova. Qualquer erro de rede é ignorado silenciosamente — não é pra
    incomodar o usuário toda vez que abrir o programa sem internet —
    e rodando direto do código-fonte não faz a checagem."""

    if not getattr(sys, "frozen", False):
        return

    versao_atual = obter_versao_atual()

    if versao_atual is None:
        return

    def tarefa():

        try:
            versao_remota, url_release = _consultar_release_mais_recente()
        except Exception:
            return

        if versao_remota > versao_atual:
            ao_encontrar_atualizacao(versao_atual, versao_remota, url_release)

    threading.Thread(target=tarefa, daemon=True).start()


def verificar_manualmente(ao_concluir, ao_falhar):
    """Uso do botão "Verificar Atualização" em Configurações: roda em
    thread separada e sempre chama um dos dois callbacks — o usuário
    pediu essa checagem explicitamente, então merece uma resposta
    visível mesmo quando já está tudo atualizado ou a checagem falha."""

    versao_atual = obter_versao_atual()

    def tarefa():

        try:
            versao_remota, url_release = _consultar_release_mais_recente()
        except Exception as erro:
            ao_falhar(erro)
            return

        ao_concluir(versao_atual, versao_remota, url_release)

    threading.Thread(target=tarefa, daemon=True).start()
