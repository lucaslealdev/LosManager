"""
=================================================================
VERIFICAÇÃO DE ATUALIZAÇÃO (consulta releases novas no GitHub)
=================================================================
O número da build fica embutido em assets/versao.txt, escrito pela
GitHub Action (`.github/workflows/build-release.yml`) logo antes de
compilar — não existe no código-fonte nem em builds feitas na mão
fora do GitHub Actions, então `obter_build_atual()` retorna None
nesses casos (não tem com o que comparar).
=================================================================
"""

import sys
import json
import threading
import urllib.request

from utils import config

URL_RELEASE_MAIS_RECENTE = "https://api.github.com/repos/ramonxxl/LosManager/releases/latest"
URL_PAGINA_RELEASES = "https://github.com/ramonxxl/LosManager/releases"


def obter_build_atual():

    try:
        with open(config.caminho_asset("versao.txt"), "r", encoding="utf-8") as arquivo:
            return int(arquivo.read().strip())
    except (OSError, ValueError):
        return None


def texto_versao():
    """Texto amigável pro rodapé de Configurações, cobrindo os 3
    cenários possíveis: build oficial saída do GitHub Actions, build
    local via build.bat (sem o número embutido) ou rodando direto do
    código-fonte (`python main.py`)."""

    build_atual = obter_build_atual()

    if build_atual is not None:
        return f"Los Manager — build #{build_atual}"

    if getattr(sys, "frozen", False):
        return "Los Manager — build local (compilada fora do GitHub Actions)"

    return "Los Manager — código-fonte (modo desenvolvimento)"


def _consultar_release_mais_recente():
    """Chamada de rede (bloqueante) — sempre rodar numa thread separada.
    Retorna (build_remota, url_release) ou levanta exceção se falhar."""

    requisicao = urllib.request.Request(
        URL_RELEASE_MAIS_RECENTE,
        headers={"Accept": "application/vnd.github+json"}
    )

    with urllib.request.urlopen(requisicao, timeout=6) as resposta:
        dados = json.loads(resposta.read().decode("utf-8"))

    build_remota = int(dados.get("tag_name", "").strip().lstrip("vV"))
    url_release = dados.get("html_url") or URL_PAGINA_RELEASES

    return build_remota, url_release


def verificar_silenciosamente(ao_encontrar_atualizacao):
    """Uso automático (chamado uma vez ao abrir o app): roda em thread
    separada e só chama `ao_encontrar_atualizacao(build_atual,
    build_nova, url_release)` se realmente houver uma build mais nova.
    Qualquer erro de rede é ignorado silenciosamente — não é pra
    incomodar o usuário toda vez que abrir o programa sem internet —
    e roda direto do código-fonte não faz a checagem."""

    if not getattr(sys, "frozen", False):
        return

    build_atual = obter_build_atual()

    if build_atual is None:
        return

    def tarefa():

        try:
            build_remota, url_release = _consultar_release_mais_recente()
        except Exception:
            return

        if build_remota > build_atual:
            ao_encontrar_atualizacao(build_atual, build_remota, url_release)

    threading.Thread(target=tarefa, daemon=True).start()


def verificar_manualmente(ao_concluir, ao_falhar):
    """Uso do botão "Verificar Atualização" em Configurações: roda em
    thread separada e sempre chama um dos dois callbacks — o usuário
    pediu essa checagem explicitamente, então merece uma resposta
    visível mesmo quando já está tudo atualizado ou a checagem falha."""

    build_atual = obter_build_atual()

    def tarefa():

        try:
            build_remota, url_release = _consultar_release_mais_recente()
        except Exception as erro:
            ao_falhar(erro)
            return

        ao_concluir(build_atual, build_remota, url_release)

    threading.Thread(target=tarefa, daemon=True).start()
