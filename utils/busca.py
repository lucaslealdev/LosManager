"""
=================================================================
BUSCA CASE E ACENTO-INSENSITIVE (compartilhada entre as telas)
=================================================================
O SQLite só ignora maiúscula/minúscula em letras simples (a-z) e NÃO
em letras acentuadas (á, é, ç, ã...) — comum no cardápio e nos nomes
de clientes. Por isso as telas buscam TUDO e filtram aqui em Python.

Além de ignorar maiúscula/minúscula, também ignoramos acento: buscar
"cesar" encontra "César", buscar "café" encontra "cafe", etc.
=================================================================
"""

import unicodedata


def _normalizar(texto):
    """Deixa minúsculo e remove os acentos (á->a, ç->c, ã->a...),
    pra comparar sem diferenciar maiúscula/minúscula nem acentuação."""

    texto = unicodedata.normalize("NFKD", texto or "")
    sem_acento = "".join(c for c in texto if not unicodedata.combining(c))

    return sem_acento.lower()


def contem(termo, texto):
    """Retorna True se `termo` aparece em `texto`, ignorando
    maiúsculas/minúsculas e acentuação. Trata `termo` vazio (considera
    que bate com tudo) e `texto` None (trata como string vazia)."""

    if not termo:
        return True

    return _normalizar(termo) in _normalizar(texto)


def comeca_com(termo, texto):
    """Retorna True se `texto` começa com `termo`, ignorando
    maiúsculas/minúsculas e acentuação. Usado pra ordenar resultados
    (ex: quem começa com o termo buscado aparece primeiro)."""

    if not termo:
        return True

    return _normalizar(texto).startswith(_normalizar(termo))
