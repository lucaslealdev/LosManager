"""
Teste da tabela responsiva da tela de Produtos (ver CLAUDE.md, seção
"Responsive screens" e `utils/responsivo.py`): a lista de produtos não
tem uma altura fixa de linhas — ela é recalculada a partir do espaço
realmente disponível sempre que a janela principal é redimensionada,
via `responsivo.tornar_dinamica`.

É um teste de GUI de verdade (cria a tela real e redimensiona a
janela raiz de verdade), então segue o mesmo padrão de
`test_tela_produtos_largura.py`: usa `ambiente_grafico()` pra garantir
um display utilizável (Windows / Linux com monitor / Xvfb automático),
e só importa customtkinter/screens depois que esse ambiente já está
pronto.

As alturas usadas não são fixas nem os 1366x768 do PC da loja — são
calculadas em cima do tamanho real da tela (`winfo_screenheight()`) na
hora do teste, por dois motivos vistos na prática:

1. Numa primeira versão com 768/500/900 fixos: passava em todo lugar
   testado localmente, mas falhou na Action (windows-latest) — lá a
   mesma tela consome bem mais altura antes de chegar na tabela (a
   fonte "Arial" de verdade rende mais alta que a substituta do
   Linux/Xvfb), então 768px já batia no piso mínimo de linhas e a
   diferença entre os tamanhos desaparecia.
2. Tentando compensar com uma altura BEM maior que a tela (pra
   garantir folga): alguns window managers tratam um geometry() maior
   que a tela como um pedido de maximizar, e depois de "maximizado"
   passam a ignorar geometry() menores — reproduzido numa sessão
   gráfica real aqui. Por isso o estado "grande" usa quase a tela
   inteira, nunca mais que ela.
"""

import time
import unittest

from testes.gui_ambiente import ambiente_grafico, fechar_janela
from utils.responsivo import ATRASO_DEBOUNCE_MS, MINIMO_LINHAS_PADRAO

# Bem mais folgado que o ATRASO_DEBOUNCE_MS do próprio
# utils/responsivo.py, pra não dar falso negativo numa máquina lenta
# ou momentaneamente carregada (a Action, por exemplo, é bem mais
# lenta que uma máquina de desenvolvedor pra isso).
ESPERA_DEBOUNCE_SEGUNDOS = (ATRASO_DEBOUNCE_MS + 1000) / 1000

ALTURA_JANELA_PEQUENA = 300

# Margem de segurança subtraída da altura real da tela, pra sobrar
# espaço pra decoração da janela/barra de tarefas e o pedido não virar
# um "maximizar" por acidente — testado na prática: com só 80px de
# margem (screen 1080 -> pedido de 1000), o window manager local
# "grudou" a janela em 998px e passou a ignorar geometry() menores;
# com 200px de margem (pedido de 880) o mesmo redimensionamento
# funcionou normalmente pra frente e pra trás.
MARGEM_TELA_PX = 200

# Diferença mínima de altura real (px) entre as duas janelas pra
# considerar que o ambiente gráfico atual realmente deixou redimensionar
# o suficiente pra testar — abaixo disso, pula o teste em vez de
# arriscar um falso negativo por causa do ambiente, não do código.
DIFERENCA_MINIMA_PX = 100


class TesteResponsividadeTelaProdutos(unittest.TestCase):
    """Tabela de produtos responsiva ao redimensionar a janela"""

    @classmethod
    def setUpClass(cls):
        cls._ambiente = ambiente_grafico()
        cls._ambiente.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._ambiente.__exit__(None, None, None)

    def _redimensionar_e_esperar(self, root, geometria):
        """Aplica uma nova geometria na janela raiz e dá tempo pro
        `<Configure>` disparar e pro debounce de utils/responsivo.py
        (recalcula só depois de ATRASO_DEBOUNCE_MS parado) terminar,
        antes de ler a altura resultante da tabela."""

        root.geometry(geometria)
        root.update()

        time.sleep(ESPERA_DEBOUNCE_SEGUNDOS)
        root.update()

    def test_altura_da_tabela_muda_ao_redimensionar_a_janela(self):
        """A altura da tabela acompanha o redimensionamento da janela"""

        # Importados só agora (depois que o ambiente_grafico já
        # garantiu um display) — customtkinter/screens.produtos criam
        # widgets reais na hora de montar a tela.
        import customtkinter as ctk
        from screens.produtos import Produtos

        root = ctk.CTk()

        # Quase a tela inteira, nunca mais que ela (ver docstring do
        # módulo) — calculado agora porque depende do ambiente atual
        # (monitor real, ou o -screen do Xvfb).
        altura_grande = max(root.winfo_screenheight() - MARGEM_TELA_PX, 500)
        geometria_grande = f"1366x{altura_grande}"

        root.geometry(geometria_grande)

        try:
            tela = Produtos(root)
            root.update()

            altura_janela_grande = root.winfo_height()
            linhas_janela_grande = int(tela.tabela.cget("height"))

            self._redimensionar_e_esperar(root, f"1366x{ALTURA_JANELA_PEQUENA}")
            altura_janela_pequena = root.winfo_height()
            linhas_janela_pequena = int(tela.tabela.cget("height"))

            self._redimensionar_e_esperar(root, geometria_grande)
            linhas_apos_crescer_de_novo = int(tela.tabela.cget("height"))
        finally:
            fechar_janela(root)

        diferenca_real = altura_janela_grande - altura_janela_pequena

        if diferenca_real < DIFERENCA_MINIMA_PX:
            self.skipTest(
                "Este ambiente gráfico não deixou a janela variar de "
                f"altura o suficiente pra testar (pedido: "
                f"{geometria_grande} vs 1366x{ALTURA_JANELA_PEQUENA}; "
                f"altura real obtida: {altura_janela_grande}px vs "
                f"{altura_janela_pequena}px, diferença de só "
                f"{diferenca_real}px)."
            )

        if linhas_janela_grande <= MINIMO_LINHAS_PADRAO:
            self.skipTest(
                "Mesmo usando quase a tela inteira "
                f"({altura_janela_grande}px), a tabela não passou do "
                f"piso mínimo de {MINIMO_LINHAS_PADRAO} linhas nesse "
                "ambiente — os outros widgets da tela (título, filtro, "
                "formulário, dica) consomem espaço demais aqui pra dar "
                "pra provar a diferença sem arriscar o bug do "
                "'maximizar' de novo."
            )

        self.assertLess(
            linhas_janela_pequena, linhas_janela_grande,
            "A tabela deveria ter MENOS linhas na janela pequena do que "
            f"na grande (grande: {linhas_janela_grande} linhas em "
            f"{altura_janela_grande}px; pequena: {linhas_janela_pequena} "
            f"linhas em {altura_janela_pequena}px)."
        )
        self.assertGreater(
            linhas_apos_crescer_de_novo, linhas_janela_pequena,
            "A tabela deveria voltar a ter MAIS linhas depois que a "
            f"janela cresceu de novo (tinha {linhas_janela_pequena}, "
            f"ficou {linhas_apos_crescer_de_novo})."
        )


if __name__ == "__main__":
    unittest.main()
