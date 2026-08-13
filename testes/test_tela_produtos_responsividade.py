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
"""

import time
import unittest

from testes.gui_ambiente import ambiente_grafico, fechar_janela
from utils.responsivo import ATRASO_DEBOUNCE_MS

# Tempo de sobra além do debounce do próprio utils/responsivo.py, pra
# não dar falso negativo numa máquina momentaneamente carregada.
ESPERA_DEBOUNCE_SEGUNDOS = (ATRASO_DEBOUNCE_MS + 150) / 1000


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
        root.geometry("1366x768")

        try:
            tela = Produtos(root)
            root.update()

            altura_inicial = int(tela.tabela.cget("height"))

            self._redimensionar_e_esperar(root, "1366x500")
            altura_apos_encolher = int(tela.tabela.cget("height"))

            self._redimensionar_e_esperar(root, "1366x900")
            altura_apos_crescer = int(tela.tabela.cget("height"))
        finally:
            fechar_janela(root)

        self.assertLess(
            altura_apos_encolher, altura_inicial,
            "A tabela deveria ter MENOS linhas depois que a janela "
            f"diminuiu de altura (tinha {altura_inicial}, ficou "
            f"{altura_apos_encolher})."
        )
        self.assertGreater(
            altura_apos_crescer, altura_apos_encolher,
            "A tabela deveria ter MAIS linhas depois que a janela "
            f"voltou a crescer (tinha {altura_apos_encolher}, ficou "
            f"{altura_apos_crescer})."
        )


if __name__ == "__main__":
    unittest.main()
