import sqlite3
import sys
import os


def _caminho_base():
    """Descobre a pasta correta tanto rodando como .py quanto
    já compilado como .exe (PyInstaller)."""

    if getattr(sys, "frozen", False):
        # Rodando como .exe: usa a pasta onde o .exe está
        return os.path.dirname(sys.executable)

    # Rodando como .py: usa a pasta raiz do projeto (uma acima de database/)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CAMINHO_BANCO = os.path.join(_caminho_base(), "losmanager.db")


class Banco:

    def __init__(self):

        self.conexao = sqlite3.connect(
            CAMINHO_BANCO,
            check_same_thread=False
        )

        self.cursor = self.conexao.cursor()

        self.criar_tabelas()

    # =========================================================

    def criar_tabelas(self):

        # =====================================================
        # CATEGORIAS
        # =====================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT UNIQUE NOT NULL

        )
        """)

        categorias_padrao = [
            "Pastéis",
            "Caldinhos",
            "Bebidas",
            "Refrigerantes",
            "Sucos",
            "Combos",
            "Sobremesas"
        ]

        for categoria in categorias_padrao:

            self.cursor.execute(
                """
                INSERT OR IGNORE INTO categorias(nome)
                VALUES(?)
                """,
                (categoria,)
            )

        # =====================================================
        # PRODUTOS
        # =====================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            codigo TEXT,

            nome TEXT NOT NULL,

            categoria TEXT,

            custo REAL DEFAULT 0,

            preco REAL NOT NULL,

            estoque INTEGER DEFAULT 0,

            ativo INTEGER DEFAULT 1,

            foto TEXT

        )
        """)

        # =====================================================
        # CLIENTES
        # =====================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT NOT NULL,

            telefone TEXT,

            celular TEXT,

            endereco TEXT,

            numero TEXT,

            bairro TEXT,

            cidade TEXT,

            cep TEXT,

            observacao TEXT

        )
        """)

        # =====================================================
        # PEDIDOS
        # =====================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            numero INTEGER,

            cliente_id INTEGER,

            data TEXT,

            hora TEXT,

            subtotal REAL,

            desconto REAL,

            acrescimo REAL,

            total REAL,

            pagamento TEXT,

            status TEXT,

            observacao TEXT,

            FOREIGN KEY(cliente_id)
            REFERENCES clientes(id)

        )
        """)

        # =====================================================
        # ITENS PEDIDO
        # =====================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            pedido_id INTEGER,

            produto_id INTEGER,

            quantidade INTEGER,

            valor_unitario REAL,

            subtotal REAL,

            FOREIGN KEY(pedido_id)
            REFERENCES pedidos(id),

            FOREIGN KEY(produto_id)
            REFERENCES produtos(id)

        )
        """)

        # =====================================================
        # CAIXA
        # =====================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS caixa(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            data_abertura TEXT,
            hora_abertura TEXT,
            valor_abertura REAL,

            data_fechamento TEXT,
            hora_fechamento TEXT,
            valor_fechamento REAL,
            valor_esperado REAL,
            diferenca REAL,

            status TEXT DEFAULT 'Aberto'

        )
        """)

        # =====================================================
        # MOVIMENTOS DE CAIXA (sangria / suprimento)
        # =====================================================

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentos_caixa(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            caixa_id INTEGER,

            tipo TEXT,
            valor REAL,
            descricao TEXT,
            data TEXT,
            hora TEXT,

            FOREIGN KEY(caixa_id)
            REFERENCES caixa(id)

        )
        """)

        # =====================================================
        # ENDEREÇOS DO CLIENTE (um cliente pode ter vários)
        # =====================================================
        # As colunas endereco/numero/bairro/cidade/cep continuam
        # existindo em `clientes` (acima) só para não quebrar bancos
        # antigos — o app não lê/grava mais nelas depois da migração.

        self._criar_tabela_enderecos_cliente()

        self.conexao.commit()

    # =========================================================

    def _criar_tabela_enderecos_cliente(self):
        """Cria a tabela de múltiplos endereços por cliente. Se ela
        ainda não existia (banco de uma versão anterior do sistema),
        migra automaticamente o endereço único que já estava salvo
        direto em `clientes`, virando o endereço "Principal" de cada
        cliente. Roda toda vez que o app abre, mas a migração em si só
        acontece uma vez (na primeira execução com essa tabela nova)."""

        tabela_ja_existia = self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='enderecos_cliente'"
        ).fetchone() is not None

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS enderecos_cliente(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            cliente_id INTEGER NOT NULL,

            apelido TEXT,
            endereco TEXT,
            numero TEXT,
            bairro TEXT,
            cidade TEXT,
            cep TEXT,

            principal INTEGER DEFAULT 0,

            FOREIGN KEY(cliente_id)
            REFERENCES clientes(id)

        )
        """)

        if not tabela_ja_existia:
            self._migrar_enderecos_antigos()

    # =========================================================

    def _migrar_enderecos_antigos(self):
        """Copia o endereço único que já existia em `clientes` (versões
        anteriores do sistema) para a tabela nova, como endereço
        "Principal" de cada cliente. Clientes sem nenhum dado de
        endereço preenchido são ignorados."""

        clientes_antigos = self.cursor.execute(
            "SELECT id, endereco, numero, bairro, cidade, cep FROM clientes"
        ).fetchall()

        for cliente_id, endereco, numero, bairro, cidade, cep in clientes_antigos:

            if not any([endereco, numero, bairro, cidade, cep]):
                continue

            self.cursor.execute(
                """
                INSERT INTO enderecos_cliente
                    (cliente_id, apelido, endereco, numero, bairro, cidade, cep, principal)
                VALUES (?, 'Principal', ?, ?, ?, ?, ?, 1)
                """,
                (cliente_id, endereco, numero, bairro, cidade, cep)
            )

    # =========================================================

    def executar(self, sql, parametros=()):

        self.cursor.execute(sql, parametros)
        self.conexao.commit()

    # =========================================================
    # TRANSAÇÃO MANUAL (várias escritas que precisam ser tudo-ou-nada)
    # =========================================================

    def executar_sem_commit(self, sql, parametros=()):
        """Igual `executar`, mas sem dar commit — usado quando várias
        escritas precisam virar uma transação só (ver `commit`/`rollback`
        abaixo), pra não deixar dado pela metade se algo falhar no meio."""

        self.cursor.execute(sql, parametros)

    def commit(self):

        self.conexao.commit()

    def rollback(self):

        self.conexao.rollback()

    # =========================================================

    def buscar(self, sql, parametros=()):

        self.cursor.execute(sql, parametros)
        return self.cursor.fetchall()

    # =========================================================

    def buscar_um(self, sql, parametros=()):

        self.cursor.execute(sql, parametros)
        return self.cursor.fetchone()

    # =========================================================

    def ultimo_id(self):

        return self.cursor.lastrowid


banco = Banco()
