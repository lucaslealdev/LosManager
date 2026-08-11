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
import urllib.error

from utils import config

REPOSITORIO_PADRAO = "ramonxxl/LosManager"

# Chave onde fica guardado o último repositório inválido já avisado —
# ver `ja_avisou_repositorio()`.
CHAVE_AVISO_REPO = "aviso_repo_invalido"


class RepositorioInvalido(Exception):
    """O repositório configurado não existe, está privado ou não tem
    nenhuma release publicada (a API devolve 404 nos três casos).

    Separado das falhas de rede de propósito: ficar sem internet é
    temporário e não vale incomodar o usuário, mas um repositório errado
    NUNCA vai se resolver sozinho — o programa ficaria mudo pra sempre
    achando que está atualizado. Aconteceu na loja: o campo estava com
    "ramonxx/losmanager" (faltando o "l" do usuário), a consulta dava 404
    e nenhuma atualização era oferecida, sem nenhum sinal de erro."""

    def __init__(self, repositorio):

        self.repositorio = repositorio

        super().__init__(
            f"repositório \"{repositorio}\" não encontrado no GitHub "
            "(inexistente, privado ou sem releases publicadas)"
        )


def _repositorio():
    """Repositório GitHub consultado para checar/baixar atualizações —
    configurável em Configurações (chave `repo_atualizacao`), padrão
    ramonxxl/LosManager. Permite apontar pra um fork sem editar código."""

    return config.obter("repo_atualizacao", REPOSITORIO_PADRAO).strip() or REPOSITORIO_PADRAO


def _url_release_mais_recente():

    return f"https://api.github.com/repos/{_repositorio()}/releases/latest"


def _url_pagina_releases():

    return f"https://github.com/{_repositorio()}/releases"


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


def _escolher_asset_zip(dados):
    """Procura entre os arquivos anexados ao release o .zip pronto pra
    baixar e instalar direto (é o que a Action publica — ver
    .github/workflows/build-release.yml, `Compress-Archive` +
    `softprops/action-gh-release`). Retorna None se não achar nenhum
    (ex: alguém criou uma tag/release na mão sem rodar a Action) — quem
    chamar cai de volta pro fluxo antigo de abrir o navegador."""

    for asset in dados.get("assets", []):
        if asset.get("name", "").lower().endswith(".zip"):
            return asset.get("browser_download_url")

    return None


def _consultar_release_mais_recente():
    """Chamada de rede (bloqueante) — sempre rodar numa thread separada.
    Retorna (versao_remota, url_release, url_download) ou levanta
    exceção se falhar. `url_download` é o link direto do .zip do
    release (None se o release não tiver um anexado)."""

    requisicao = urllib.request.Request(
        _url_release_mais_recente(),
        headers={"Accept": "application/vnd.github+json"}
    )

    try:
        with urllib.request.urlopen(requisicao, timeout=6) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))

    except urllib.error.HTTPError as erro:

        # 404 é o único caso que dá pra afirmar que o problema é a
        # configuração, e não a rede.
        if erro.code == 404:
            raise RepositorioInvalido(_repositorio()) from erro

        raise

    versao_remota = _parsear_versao(dados.get("tag_name", ""))
    url_release = dados.get("html_url") or _url_pagina_releases()
    url_download = _escolher_asset_zip(dados)

    return versao_remota, url_release, url_download


def ja_avisou_repositorio(repositorio):
    """Se o usuário já foi avisado de que ESTE repositório não responde.
    Guardar o nome (e não um simples "já avisei") faz o aviso voltar
    sozinho se alguém trocar o campo por outro valor também errado."""

    return config.obter(CHAVE_AVISO_REPO, "") == repositorio


def marcar_aviso_repositorio(repositorio):
    """Chamar da thread principal (é uma escrita no banco), depois de
    mostrar o aviso, pra ele não se repetir a cada abertura."""

    config.definir(CHAVE_AVISO_REPO, repositorio)


def verificar_silenciosamente(ao_encontrar_atualizacao, ao_repositorio_invalido=None):
    """Uso automático (chamado uma vez ao abrir o app): roda em thread
    separada e só chama `ao_encontrar_atualizacao(versao_atual,
    versao_nova, url_release, url_download)` se realmente houver uma
    versão mais nova. Erro de rede é ignorado silenciosamente — não é pra
    incomodar o usuário toda vez que abrir o programa sem internet — e
    rodando direto do código-fonte não faz a checagem.

    A exceção é o repositório inválido (404): esse chama
    `ao_repositorio_invalido(repositorio)`, uma única vez por valor
    configurado, porque é problema de configuração e não passa sozinho."""

    if not getattr(sys, "frozen", False):
        return

    versao_atual = obter_versao_atual()

    if versao_atual is None:
        return

    def tarefa():

        try:
            versao_remota, url_release, url_download = _consultar_release_mais_recente()

        except RepositorioInvalido as erro:

            if ao_repositorio_invalido and not ja_avisou_repositorio(erro.repositorio):
                ao_repositorio_invalido(erro.repositorio)

            return

        except Exception:
            return

        if versao_remota > versao_atual:
            ao_encontrar_atualizacao(versao_atual, versao_remota, url_release, url_download)

    threading.Thread(target=tarefa, daemon=True).start()


def verificar_manualmente(ao_concluir, ao_falhar):
    """Uso do botão "Verificar Atualização" em Configurações: roda em
    thread separada e sempre chama um dos dois callbacks — o usuário
    pediu essa checagem explicitamente, então merece uma resposta
    visível mesmo quando já está tudo atualizado ou a checagem falha."""

    versao_atual = obter_versao_atual()

    def tarefa():

        try:
            versao_remota, url_release, url_download = _consultar_release_mais_recente()
        except Exception as erro:
            ao_falhar(erro)
            return

        ao_concluir(versao_atual, versao_remota, url_release, url_download)

    threading.Thread(target=tarefa, daemon=True).start()
