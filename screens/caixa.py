import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from database.conexao import banco


class Caixa(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.pack(fill="both", expand=True, padx=20, pady=20)

        self.caixa_atual = self.buscar_caixa_aberto()

        self.montar_tela()

    # ======================================================

    def limpar(self):

        for widget in self.winfo_children():
            widget.destroy()

    # ======================================================

    def montar_tela(self):

        self.limpar()

        # Frame com rolagem: em telas menores (notebooks antigos) o
        # conteúdo não cabia inteiro na altura da janela e não tinha
        # como rolar até os botões/movimentações de baixo. Recriado
        # aqui porque `limpar()` destrói tudo dentro de `self` a cada
        # atualização da tela (abrir/fechar caixa, sangria...).
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        titulo = ctk.CTkLabel(
            self.scroll,
            text="Caixa",
            font=("Arial", 30, "bold")
        )
        titulo.pack(pady=(5, 20))

        if self.caixa_atual is None:
            self.tela_caixa_fechado()
        else:
            self.tela_caixa_aberto()

    # ======================================================
    # BANCO
    # ======================================================

    def buscar_caixa_aberto(self):

        return banco.buscar_um(
            "SELECT * FROM caixa WHERE status='Aberto' ORDER BY id DESC LIMIT 1"
        )

    # ======================================================
    # TELA: SEM CAIXA ABERTO
    # ======================================================

    def tela_caixa_fechado(self):

        bloco = ctk.CTkFrame(self.scroll)
        bloco.pack(pady=40)

        ctk.CTkLabel(
            bloco,
            text="🔒",
            font=("Arial", 50)
        ).pack(pady=(25, 5))

        ctk.CTkLabel(
            bloco,
            text="Nenhum caixa aberto no momento",
            font=("Arial", 20, "bold")
        ).pack(pady=(0, 20))

        ctk.CTkLabel(
            bloco,
            text="Valor inicial (troco)"
        ).pack()

        self.entrada_valor_inicial = ctk.CTkEntry(bloco, width=200)
        self.entrada_valor_inicial.insert(0, "0,00")
        self.entrada_valor_inicial.pack(pady=10)

        ctk.CTkButton(
            bloco,
            text="🔓 Abrir Caixa",
            width=200,
            height=42,
            fg_color="#2a7",
            hover_color="#186",
            command=self.abrir_caixa
        ).pack(pady=(10, 25))

    # ======================================================

    def abrir_caixa(self):

        texto_valor = self.entrada_valor_inicial.get().strip().replace(",", ".")

        try:
            valor_inicial = float(texto_valor) if texto_valor else 0.0
        except ValueError:
            messagebox.showwarning("Caixa", "Valor inicial inválido.")
            return

        agora = datetime.now()

        banco.executar(
            """
            INSERT INTO caixa
                (data_abertura, hora_abertura, valor_abertura, status)
            VALUES (?, ?, ?, 'Aberto')
            """,
            (
                agora.strftime("%d/%m/%Y"),
                agora.strftime("%H:%M"),
                valor_inicial
            )
        )

        messagebox.showinfo("Caixa", "Caixa aberto com sucesso!")

        self.caixa_atual = self.buscar_caixa_aberto()
        self.montar_tela()

    # ======================================================
    # TELA: CAIXA ABERTO
    # ======================================================

    def tela_caixa_aberto(self):

        caixa_id = self.caixa_atual[0]
        data_abertura = self.caixa_atual[1]
        hora_abertura = self.caixa_atual[2]
        valor_abertura = self.caixa_atual[3]

        # ---------------- Cabeçalho ----------------

        info = ctk.CTkFrame(self.scroll)
        info.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            info,
            text=f"🟢 Caixa aberto em {data_abertura} às {hora_abertura}  —  "
                 f"Valor inicial: R$ {valor_abertura:.2f}",
            font=("Arial", 15, "bold")
        ).pack(side="left", padx=15, pady=15)

        # ---------------- Resumo do dia ----------------

        hoje = datetime.now().strftime("%d/%m/%Y")

        pedidos_hoje_todos = banco.buscar(
            """
            SELECT p.numero, p.hora, COALESCE(c.nome, 'Cliente Balcão'),
                   p.total, p.pagamento, p.subtotal, p.desconto, p.acrescimo, p.status
            FROM pedidos p
            LEFT JOIN clientes c ON c.id = p.cliente_id
            WHERE p.data = ?
            ORDER BY p.id DESC
            """,
            (hoje,)
        )

        # Pedido cancelado devolve estoque e dinheiro pro cliente, então não
        # deve contar em venda, taxa de motoboy nem no dinheiro esperado do
        # caixa — mesmo raciocínio já aplicado nos cards de Relatórios.
        pedidos_hoje = [p for p in pedidos_hoje_todos if p[8] != "Cancelado"]

        total_geral = sum(p[3] for p in pedidos_hoje)

        # Venda = valor dos produtos (subtotal - desconto); Motoboy = taxa
        # de entrega (acrescimo). Separados porque a taxa de entrega não é
        # faturamento da pastelaria, só repassa pro motoboy.
        total_vendas = sum((p[5] or 0.0) - (p[6] or 0.0) for p in pedidos_hoje)
        total_motoboy = sum(p[7] or 0.0 for p in pedidos_hoje)

        totais_pagamento = {}
        totais_pagamento_venda = {}
        totais_pagamento_motoboy = {}
        for pedido in pedidos_hoje:
            forma = pedido[4]
            venda = (pedido[5] or 0.0) - (pedido[6] or 0.0)
            motoboy = pedido[7] or 0.0
            totais_pagamento[forma] = totais_pagamento.get(forma, 0) + pedido[3]
            totais_pagamento_venda[forma] = totais_pagamento_venda.get(forma, 0) + venda
            totais_pagamento_motoboy[forma] = totais_pagamento_motoboy.get(forma, 0) + motoboy

        total_dinheiro = totais_pagamento.get("Dinheiro", 0.0)

        # ---------------- Movimentos (sangria/suprimento) ----------------

        movimentos = banco.buscar(
            """
            SELECT tipo, valor, descricao, hora
            FROM movimentos_caixa
            WHERE caixa_id = ?
            ORDER BY id DESC
            """,
            (caixa_id,)
        )

        total_sangrias = sum(m[1] for m in movimentos if m[0] == "Sangria")
        total_suprimentos = sum(m[1] for m in movimentos if m[0] == "Suprimento")

        dinheiro_esperado = (
            valor_abertura + total_dinheiro + total_suprimentos - total_sangrias
        )

        # ---------------- Cards de resumo ----------------

        cards = ctk.CTkFrame(self.scroll, fg_color="transparent")
        cards.pack(fill="x", pady=10)

        self.card(cards, "Pedidos Hoje", str(len(pedidos_hoje)), 0)
        self.card(cards, "Vendas Hoje", f"R$ {total_vendas:.2f}", 1)
        self.card(cards, "Taxa Motoboy Hoje", f"R$ {total_motoboy:.2f}", 2)
        self.card(cards, "Dinheiro Esperado", f"R$ {dinheiro_esperado:.2f}", 3)

        # ---------------- Totais por forma de pagamento ----------------

        bloco_formas = ctk.CTkFrame(self.scroll)
        bloco_formas.pack(fill="x", pady=15)

        ctk.CTkLabel(
            bloco_formas,
            text="Totais por forma de pagamento",
            font=("Arial", 15, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        if totais_pagamento:
            for forma, valor in totais_pagamento.items():

                venda = totais_pagamento_venda.get(forma, 0.0)
                motoboy = totais_pagamento_motoboy.get(forma, 0.0)

                texto = f"{forma}: R$ {valor:.2f}  (Vendas: R$ {venda:.2f}"
                if motoboy:
                    texto += f"  +  Motoboy: R$ {motoboy:.2f}"
                texto += ")"

                ctk.CTkLabel(
                    bloco_formas,
                    text=texto
                ).pack(anchor="w", padx=25, pady=2)
        else:
            ctk.CTkLabel(
                bloco_formas,
                text="Nenhuma venda registrada ainda hoje."
            ).pack(anchor="w", padx=25, pady=2)

        ctk.CTkLabel(bloco_formas, text="").pack(pady=5)

        # ---------------- Botões de ação ----------------

        acoes = ctk.CTkFrame(self.scroll, fg_color="transparent")
        acoes.pack(fill="x", pady=10)

        ctk.CTkButton(
            acoes,
            text="➖ Sangria (retirar dinheiro)",
            width=220,
            fg_color="#a33",
            hover_color="#822",
            command=lambda: self.registrar_movimento("Sangria")
        ).pack(side="left", padx=(5, 10))

        ctk.CTkButton(
            acoes,
            text="➕ Suprimento (adicionar dinheiro)",
            width=240,
            command=lambda: self.registrar_movimento("Suprimento")
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            acoes,
            text="🔒 Fechar Caixa",
            width=200,
            fg_color="#c80",
            hover_color="#960",
            command=lambda: self.fechar_caixa(dinheiro_esperado)
        ).pack(side="left", padx=10)

        # ---------------- Lista de movimentos ----------------

        if movimentos:

            bloco_mov = ctk.CTkFrame(self.scroll)
            bloco_mov.pack(fill="both", expand=True, pady=15)

            ctk.CTkLabel(
                bloco_mov,
                text="Movimentações do caixa (sangrias / suprimentos)",
                font=("Arial", 14, "bold")
            ).pack(anchor="w", padx=15, pady=(15, 5))

            for tipo, valor, descricao, hora in movimentos:

                sinal = "-" if tipo == "Sangria" else "+"

                ctk.CTkLabel(
                    bloco_mov,
                    text=f"{hora}  |  {tipo}  |  {sinal}R$ {valor:.2f}  |  {descricao}"
                ).pack(anchor="w", padx=25, pady=2)

    # ======================================================

    def card(self, master, titulo, valor, coluna):

        c = ctk.CTkFrame(master)
        c.grid(row=0, column=coluna, padx=10, sticky="nsew")
        master.grid_columnconfigure(coluna, weight=1)

        ctk.CTkLabel(
            c, text=titulo, font=("Arial", 14)
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            c, text=valor, font=("Arial", 22, "bold")
        ).pack(pady=(0, 15))

    # ======================================================

    def registrar_movimento(self, tipo):

        janela = ctk.CTkInputDialog(
            text=f"Valor da {tipo.lower()} (R$):",
            title=tipo
        )
        texto_valor = janela.get_input()

        if texto_valor is None:
            return

        try:
            valor = float(texto_valor.strip().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Caixa", "Valor inválido.")
            return

        if valor <= 0:
            messagebox.showwarning("Caixa", "Informe um valor maior que zero.")
            return

        janela2 = ctk.CTkInputDialog(
            text="Motivo / descrição:",
            title=tipo
        )
        descricao = janela2.get_input()

        if descricao is None:
            descricao = ""

        agora = datetime.now()

        banco.executar(
            """
            INSERT INTO movimentos_caixa
                (caixa_id, tipo, valor, descricao, data, hora)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                self.caixa_atual[0], tipo, valor, descricao,
                agora.strftime("%d/%m/%Y"), agora.strftime("%H:%M")
            )
        )

        self.montar_tela()

    # ======================================================

    def fechar_caixa(self, valor_esperado):

        janela = ctk.CTkInputDialog(
            text=f"Dinheiro esperado em caixa: R$ {valor_esperado:.2f}\n\n"
                 "Digite o valor contado fisicamente:",
            title="Fechar Caixa"
        )
        texto_valor = janela.get_input()

        if texto_valor is None:
            return

        try:
            valor_contado = float(texto_valor.strip().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Caixa", "Valor inválido.")
            return

        diferenca = valor_contado - valor_esperado
        agora = datetime.now()

        banco.executar(
            """
            UPDATE caixa
            SET data_fechamento=?, hora_fechamento=?, valor_fechamento=?,
                valor_esperado=?, diferenca=?, status='Fechado'
            WHERE id=?
            """,
            (
                agora.strftime("%d/%m/%Y"), agora.strftime("%H:%M"),
                valor_contado, valor_esperado, diferenca,
                self.caixa_atual[0]
            )
        )

        if abs(diferenca) < 0.01:
            resumo = "Caixa fechado certinho, sem diferença! 🎉"
        elif diferenca > 0:
            resumo = f"Caixa fechado com SOBRA de R$ {diferenca:.2f}."
        else:
            resumo = f"Caixa fechado com FALTA de R$ {abs(diferenca):.2f}."

        messagebox.showinfo("Caixa Fechado", resumo)

        self.caixa_atual = None
        self.montar_tela()
