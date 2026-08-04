import customtkinter as ctk
from datetime import datetime

from database.conexao import banco


class Dashboard(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.pack(fill="both", expand=True, padx=30, pady=30)

        self.montar_cabecalho()
        self.montar_cards()

    # ======================================================
    # CABEÇALHO
    # ======================================================

    def montar_cabecalho(self):

        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", pady=(10, 30))

        ctk.CTkLabel(
            cabecalho,
            text="LOS MANAGER",
            font=("Arial", 34, "bold"),
            text_color=("#2b1d14", "#f5a623")
        ).pack()

        ctk.CTkLabel(
            cabecalho,
            text="Sistema de Gestão  •  Los Pastelles",
            font=("Arial", 16),
            text_color="gray"
        ).pack(pady=(4, 0))

        # Linha decorativa fininha, cor da marca
        linha = ctk.CTkFrame(cabecalho, height=3, fg_color="#f5a623")
        linha.pack(fill="x", padx=120, pady=(14, 0))

    # ======================================================
    # CARDS
    # ======================================================

    def montar_cards(self):

        dados = self.buscar_dados()

        grade = ctk.CTkFrame(self, fg_color="transparent")
        grade.pack(expand=True)

        # Define os 4 cards: (ícone, cor, título, valor)
        cartoes = [
            ("🧾", "#3b82f6", "Pedidos Hoje", str(dados["pedidos_hoje"])),
            ("👥", "#8b5cf6", "Clientes", str(dados["clientes"])),
            ("🥟", "#f5a623", "Produtos", str(dados["produtos"])),
            ("💰", "#22a559", "Faturamento Hoje", f"R$ {dados['faturamento']:.2f}"),
        ]

        # 2 colunas x 2 linhas, todas do mesmo tamanho
        for coluna in range(2):
            grade.grid_columnconfigure(coluna, weight=1, uniform="cards")

        for indice, (icone, cor, titulo, valor) in enumerate(cartoes):

            linha = indice // 2
            coluna = indice % 2

            self.criar_card(grade, icone, cor, titulo, valor, linha, coluna)

    # ======================================================

    def criar_card(self, pai, icone, cor, titulo, valor, linha, coluna):

        card = ctk.CTkFrame(
            pai,
            width=280,
            height=150,
            corner_radius=16,
            fg_color=("white", "#242424"),
            border_width=1,
            border_color=("#e5e5e5", "#333333")
        )

        card.grid(
            row=linha,
            column=coluna,
            padx=14,
            pady=14,
            sticky="nsew"
        )

        card.grid_propagate(False)

        conteudo = ctk.CTkFrame(card, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=20, pady=18)

        # ---------------- Ícone dentro de um círculo colorido ----------------

        selo = ctk.CTkFrame(
            conteudo,
            width=46,
            height=46,
            corner_radius=23,
            fg_color=cor
        )
        selo.pack(anchor="w")
        selo.pack_propagate(False)

        ctk.CTkLabel(
            selo,
            text=icone,
            font=("Arial", 20),
            text_color="white"
        ).place(relx=0.5, rely=0.5, anchor="center")

        # ---------------- Título ----------------

        ctk.CTkLabel(
            conteudo,
            text=titulo,
            font=("Arial", 14),
            text_color="gray",
            anchor="w"
        ).pack(fill="x", pady=(14, 2))

        # ---------------- Valor ----------------

        ctk.CTkLabel(
            conteudo,
            text=valor,
            font=("Arial", 26, "bold"),
            anchor="w"
        ).pack(fill="x")

    # ======================================================
    # BANCO: números reais do sistema
    # ======================================================

    def buscar_dados(self):

        hoje = datetime.now().strftime("%d/%m/%Y")

        pedidos_hoje = banco.buscar_um(
            "SELECT COUNT(*) FROM pedidos WHERE data=?", (hoje,)
        )

        clientes = banco.buscar_um(
            "SELECT COUNT(*) FROM clientes"
        )

        produtos = banco.buscar_um(
            "SELECT COUNT(*) FROM produtos WHERE ativo=1"
        )

        faturamento = banco.buscar_um(
            "SELECT COALESCE(SUM(total), 0) FROM pedidos WHERE data=?", (hoje,)
        )

        return {
            "pedidos_hoje": pedidos_hoje[0] if pedidos_hoje else 0,
            "clientes": clientes[0] if clientes else 0,
            "produtos": produtos[0] if produtos else 0,
            "faturamento": faturamento[0] if faturamento else 0.0,
        }
