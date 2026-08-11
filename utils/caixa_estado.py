"""Estado do caixa (aberto/fechado).

Fica aqui, e não em `screens/caixa.py`, porque quem precisa saber se o
caixa está aberto não é só a tela de Caixa: o menu do `main.py` bloqueia
a navegação e a tela de Pedidos bloqueia a gravação enquanto não houver
um caixa aberto. Importar a tela só para fazer essa consulta criaria
dependência circular (main -> screens -> main)."""

from database.conexao import banco


# ======================================================


def buscar_caixa_aberto():
    """Retorna a linha do caixa aberto, ou None se não houver nenhum."""

    return banco.buscar_um(
        "SELECT * FROM caixa WHERE status='Aberto' ORDER BY id DESC LIMIT 1"
    )


# ======================================================


def esta_aberto():

    return buscar_caixa_aberto() is not None
