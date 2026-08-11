"""
=================================================================
SINCRONIZA O AGENTS.md A PARTIR DO CLAUDE.md
=================================================================
Os dois arquivos são o MESMO documento de orientação do projeto —
muda só o cabeçalho, que diz a qual ferramenta ele se dirige (Claude
Code / Codex). Manter os dois na mão já deu errado uma vez: o
AGENTS.md ficou várias features atrás do CLAUDE.md (faltavam o
calendário, o "Ver Pedido", as observações por item...).

Então a regra passa a ser: editar SEMPRE o CLAUDE.md e rodar

    python sincronizar_agents.py

que reescreve o AGENTS.md a partir dele.

    python sincronizar_agents.py --verificar

não escreve nada e só devolve código de saída 1 se os dois estiverem
fora de sincronia (útil pra conferir antes de commitar).
=================================================================
"""

import os
import sys

# Trocas aplicadas no CLAUDE.md para gerar o AGENTS.md. Só o cabeçalho
# difere; o resto do documento é idêntico de propósito.
SUBSTITUICOES = [
    (
        "# CLAUDE.md",
        "# AGENTS.md"
    ),
    (
        "This file provides guidance to Claude Code (claude.ai/code) "
        "when working with code in this repository.",
        "This file provides guidance to Codex (Codex.ai/code) "
        "when working with code in this repository."
    ),
]

PASTA = os.path.dirname(os.path.abspath(__file__))
ORIGEM = os.path.join(PASTA, "CLAUDE.md")
DESTINO = os.path.join(PASTA, "AGENTS.md")


# ======================================================


def gerar_conteudo():
    """Lê o CLAUDE.md e devolve o texto que o AGENTS.md deve ter."""

    with open(ORIGEM, encoding="utf-8") as arquivo:
        texto = arquivo.read()

    for procurar, trocar in SUBSTITUICOES:

        if procurar not in texto:
            raise SystemExit(
                f"[ERRO] Não encontrei no CLAUDE.md o trecho esperado do "
                f"cabeçalho:\n\n    {procurar}\n\n"
                "Se o cabeçalho mudou, ajuste SUBSTITUICOES neste script."
            )

        # Só a primeira ocorrência: o cabeçalho aparece uma vez, e trocar
        # o resto do texto mudaria menções legítimas ao CLAUDE.md.
        texto = texto.replace(procurar, trocar, 1)

    return texto


# ======================================================


def ler_destino():

    if not os.path.exists(DESTINO):
        return None

    with open(DESTINO, encoding="utf-8") as arquivo:
        return arquivo.read()


# ======================================================


def main():

    verificar = "--verificar" in sys.argv

    esperado = gerar_conteudo()
    atual = ler_destino()

    if atual == esperado:
        print("AGENTS.md já está sincronizado com o CLAUDE.md.")
        return 0

    if verificar:
        print(
            "AGENTS.md está DESATUALIZADO em relação ao CLAUDE.md.\n"
            "Rode: python sincronizar_agents.py"
        )
        return 1

    # newline="\n" pra não gerar CRLF no Windows e o arquivo não aparecer
    # inteiro modificado no diff do git.
    with open(DESTINO, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(esperado)

    print("AGENTS.md atualizado a partir do CLAUDE.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
