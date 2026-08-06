import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

from database.conexao import banco
from utils import config
from utils import busca
from utils import tema
from utils import responsivo


class Relatorios(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.pack(fill="both", expand=True, padx=20, pady=20)

        self.todos_pedidos = []

        self.criar_interface()
        self.carregar_pedidos()
        self.aplicar_filtro()

    # ======================================================

    def criar_interface(self):

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        titulo = ctk.CTkLabel(
            self.scroll,
            text="Relatórios e Histórico de Pedidos",
            font=("Arial", 28, "bold")
        )
        titulo.pack(pady=(5, 15))

        topo = ctk.CTkFrame(self.scroll)
        topo.pack(fill="x")

        ctk.CTkLabel(topo, text="Período").grid(row=0, column=0, padx=10, pady=15)

        self.periodo = ctk.CTkSegmentedButton(
            topo,
            values=["Hoje", "7 dias", "Este mês", "Tudo"],
            command=lambda valor: self.aplicar_filtro()
        )
        self.periodo.set("Hoje")
        self.periodo.grid(row=0, column=1, padx=10)

        ctk.CTkLabel(
            topo, text="🔍 Buscar (cliente ou nº do pedido)"
        ).grid(row=0, column=2, padx=(30, 10))

        self.busca = ctk.CTkEntry(
            topo, width=280, placeholder_text="Ex: João  ou  7"
        )
        self.busca.grid(row=0, column=3, padx=10)
        self.busca.bind("<KeyRelease>", lambda evento: self.aplicar_filtro())

        # ---------------- Cards de resumo ----------------

        self.cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.cards_frame.pack(fill="x", pady=15)

        # Popula com valores zerados só pra existir de verdade (com sua
        # altura real) antes da tabela ser dimensionada logo abaixo —
        # os valores certos vêm de aplicar_filtro() ao final do __init__.
        self.atualizar_cards([])

        # ---------------- Ações sobre o pedido selecionado ----------------
        # Criado (e empacotado) antes da tabela só para medir a altura
        # real que ele ocupa; a tabela é inserida visualmente ANTES
        # dele via pack(before=...) logo abaixo.

        acoes_pedido = ctk.CTkFrame(self.scroll, fg_color="transparent")
        acoes_pedido.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            acoes_pedido,
            text="🚫 Cancelar Pedido Selecionado",
            fg_color=tema.COR_VERMELHO,
            hover_color="#B93601",
            width=240,
            command=self.cancelar_pedido
        ).pack(side="left")

        ctk.CTkLabel(
            acoes_pedido,
            text="Cancelar devolve automaticamente ao estoque os produtos e "
                 "ingredientes usados no pedido. O pedido continua no "
                 "histórico, só marcado como \"Cancelado\".",
            font=("Arial", 12),
            text_color="gray"
        ).pack(side="left", padx=15)

        # ---------------- Zona de perigo: zerar relatórios ----------------

        zona_perigo = ctk.CTkFrame(self.scroll, border_width=1, border_color="#a33")
        zona_perigo.pack(fill="x", pady=(15, 15))

        ctk.CTkLabel(
            zona_perigo,
            text="⚠️ Zona de Perigo",
            font=("Arial", 14, "bold"),
            text_color="#a33"
        ).pack(anchor="w", padx=15, pady=(12, 2))

        ctk.CTkLabel(
            zona_perigo,
            text="Apaga pedidos de verdade do banco de dados. Pede a senha "
                 "cadastrada em Configurações e uma confirmação extra.",
            font=("Arial", 12),
            text_color="gray"
        ).pack(anchor="w", padx=15, pady=(0, 10))

        botoes_perigo = ctk.CTkFrame(zona_perigo, fg_color="transparent")
        botoes_perigo.pack(anchor="w", padx=15, pady=(0, 15))

        ctk.CTkButton(
            botoes_perigo,
            text="🗑 Zerar Pedidos de Hoje",
            fg_color="#c80",
            hover_color="#960",
            width=200,
            command=lambda: self.zerar_pedidos(apenas_hoje=True)
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            botoes_perigo,
            text="🗑 Zerar TODO o Histórico",
            fg_color="#a33",
            hover_color="#822",
            width=200,
            command=lambda: self.zerar_pedidos(apenas_hoje=False)
        ).pack(side="left")

        # ---------------- Tabela ----------------
        # Vem por último na construção (pra já poder medir a altura de
        # tudo que ficou acima E abaixo dela), mas é inserida
        # visualmente antes de "acoes_pedido" via pack(before=...).

        linhas = responsivo.linhas_para_tabela(self, self.scroll, pady_tabela=10)

        self.tabela = ttk.Treeview(
            self.scroll,
            columns=("id", "numero", "data", "hora", "cliente", "total", "pagamento", "status"),
            show="headings",
            height=linhas
        )

        colunas = [
            ("numero", "Nº", 70, "center"),
            ("data", "Data", 90, "center"),
            ("hora", "Hora", 70, "center"),
            ("cliente", "Cliente", 260, "w"),
            ("total", "Total", 100, "e"),
            ("pagamento", "Pagamento", 110, "center"),
            ("status", "Status", 100, "center"),
        ]

        for chave, texto, largura, ancora in colunas:
            self.tabela.heading(chave, text=texto)
            self.tabela.column(chave, width=largura, anchor=ancora)

        # Coluna "id" fica fora de displaycolumns: guarda o id do pedido
        # sem mostrar na tela (é só pra saber o que cancelar depois).
        self.tabela["displaycolumns"] = [chave for chave, *_ in colunas]

        self.tabela.tag_configure("cancelado", foreground="gray")

        self.tabela.pack(fill="x", pady=10, before=acoes_pedido)

        responsivo.tornar_dinamica(self, self.scroll, lambda: self.tabela, pady_tabela=10)

    # ======================================================
    # ZERAR RELATÓRIOS (protegido por senha)
    # ======================================================

    def zerar_pedidos(self, apenas_hoje):

        senha_cadastrada = config.obter("senha_reset").strip()

        if not senha_cadastrada:
            messagebox.showwarning(
                "Segurança",
                "Você ainda não cadastrou uma senha de administrador.\n\n"
                "Vá em Configurações → Segurança e cadastre uma senha antes "
                "de usar esta função."
            )
            return

        janela = ctk.CTkInputDialog(
            text="Digite a senha de administrador:",
            title="Confirmar Senha"
        )
        senha_digitada = janela.get_input()

        if senha_digitada is None:
            return

        if senha_digitada != senha_cadastrada:
            messagebox.showerror("Segurança", "Senha incorreta.")
            return

        escopo = (
            "os pedidos de HOJE" if apenas_hoje
            else "TODO o histórico de pedidos (todos os dias)"
        )

        confirmar = messagebox.askyesno(
            "Confirmação final",
            f"Isso vai apagar {escopo} permanentemente do banco de dados.\n\n"
            "Essa ação NÃO pode ser desfeita. Deseja continuar?"
        )

        if not confirmar:
            return

        if apenas_hoje:

            hoje = datetime.now().strftime("%d/%m/%Y")

            pedidos_do_dia = banco.buscar(
                "SELECT id FROM pedidos WHERE data=?", (hoje,)
            )

            for (pedido_id,) in pedidos_do_dia:
                banco.executar(
                    "DELETE FROM itens_pedido WHERE pedido_id=?", (pedido_id,)
                )
                banco.executar(
                    "DELETE FROM movimentos_ingrediente WHERE pedido_id=?", (pedido_id,)
                )

            banco.executar("DELETE FROM pedidos WHERE data=?", (hoje,))

            mensagem = "Os pedidos de hoje foram zerados."

        else:

            banco.executar("DELETE FROM itens_pedido")
            banco.executar("DELETE FROM movimentos_ingrediente")
            banco.executar("DELETE FROM pedidos")

            mensagem = "Todo o histórico de pedidos foi zerado."

        messagebox.showinfo("Relatórios", mensagem)

        self.carregar_pedidos()
        self.aplicar_filtro()

    # ======================================================
    # CANCELAR PEDIDO (devolve estoque de produto + ingredientes)
    # ======================================================

    def cancelar_pedido(self):

        selecionado = self.tabela.selection()

        if not selecionado:
            messagebox.showwarning(
                "Relatórios",
                "Selecione um pedido na lista para cancelar."
            )
            return

        valores = self.tabela.item(selecionado[0], "values")
        pedido_id, numero, status_atual = valores[0], valores[1], valores[7]

        if status_atual == "Cancelado":
            messagebox.showinfo("Relatórios", f"O pedido Nº {numero} já está cancelado.")
            return

        confirmar = messagebox.askyesno(
            "Cancelar Pedido",
            f"Cancelar o pedido Nº {numero}?\n\n"
            "O estoque de produtos e de ingredientes usados nesse pedido "
            "será devolvido automaticamente. O pedido continua no "
            "histórico, só marcado como \"Cancelado\" — essa ação não "
            "apaga nada."
        )

        if not confirmar:
            return

        try:
            self.devolver_estoque_pedido(pedido_id)

            banco.executar_sem_commit(
                "UPDATE pedidos SET status='Cancelado' WHERE id=?", (pedido_id,)
            )

        except Exception as erro:
            banco.rollback()
            messagebox.showerror(
                "Erro ao cancelar pedido",
                f"Não foi possível cancelar o pedido:\n\n{erro}"
            )
            return

        banco.commit()

        messagebox.showinfo(
            "Relatórios",
            f"Pedido Nº {numero} cancelado. Estoque devolvido."
        )

        self.carregar_pedidos()
        self.aplicar_filtro()

    # ======================================================

    def devolver_estoque_pedido(self, pedido_id):
        """Devolve ao estoque cada produto vendido no pedido e, se o
        produto tiver receita, também cada ingrediente usado — o
        inverso exato do abatimento feito em `Pedidos.gravar_pedido()`.
        Roda dentro da transação manual de `cancelar_pedido`."""

        agora = datetime.now()
        data_str = agora.strftime("%d/%m/%Y")
        hora_str = agora.strftime("%H:%M")

        itens = banco.buscar(
            "SELECT produto_id, quantidade FROM itens_pedido WHERE pedido_id=?",
            (pedido_id,)
        )

        for produto_id, quantidade in itens:

            banco.executar_sem_commit(
                "UPDATE produtos SET estoque = estoque + ? WHERE id=?",
                (quantidade, produto_id)
            )

            receita = banco.buscar(
                "SELECT ingrediente_id, quantidade FROM receita_produto WHERE produto_id=?",
                (produto_id,)
            )

            for ingrediente_id, quantidade_unitaria in receita:

                quantidade_total = quantidade_unitaria * quantidade

                banco.executar_sem_commit(
                    "UPDATE ingredientes SET estoque_atual = estoque_atual + ? WHERE id=?",
                    (quantidade_total, ingrediente_id)
                )

                banco.executar_sem_commit(
                    """
                    INSERT INTO movimentos_ingrediente
                        (ingrediente_id, tipo, quantidade, pedido_id, data, hora)
                    VALUES (?, 'devolucao', ?, ?, ?, ?)
                    """,
                    (ingrediente_id, quantidade_total, pedido_id, data_str, hora_str)
                )

    # ======================================================

    def carregar_pedidos(self):

        self.todos_pedidos = banco.buscar(
            """
            SELECT p.id, p.numero, p.data, p.hora,
                   COALESCE(c.nome, 'Cliente Balcão'), p.total, p.pagamento, p.status
            FROM pedidos p
            LEFT JOIN clientes c ON c.id = p.cliente_id
            ORDER BY p.id DESC
            """
        )

    # ======================================================

    def aplicar_filtro(self):

        agora = datetime.now()
        periodo = self.periodo.get()
        termo = self.busca.get().strip().lower()

        filtrados = []

        for pedido_id, numero, data, hora, cliente, total, pagamento, status in self.todos_pedidos:

            try:
                data_dt = datetime.strptime(data, "%d/%m/%Y")
            except (ValueError, TypeError):
                data_dt = None

            if periodo == "Hoje" and data_dt and data_dt.date() != agora.date():
                continue

            if periodo == "7 dias" and data_dt and (agora - data_dt).days > 7:
                continue

            if periodo == "Este mês" and data_dt and (
                data_dt.month != agora.month or data_dt.year != agora.year
            ):
                continue

            if termo:
                if not busca.contem(termo, cliente) and termo not in str(numero):
                    continue

            filtrados.append((pedido_id, numero, data, hora, cliente, total, pagamento, status))

        for linha in self.tabela.get_children():
            self.tabela.delete(linha)

        for pedido_id, numero, data, hora, cliente, total, pagamento, status in filtrados:

            cancelado = status == "Cancelado"

            self.tabela.insert(
                "", "end",
                values=(
                    pedido_id, f"{numero:04d}", data, hora, cliente,
                    f"R$ {total:.2f}", pagamento, status or "Finalizado"
                ),
                tags=("cancelado",) if cancelado else ()
            )

        # Cards de resumo só contam pedidos não cancelados, senão o
        # faturamento ficaria inflado com vendas que foram desfeitas.
        validos = [p for p in filtrados if p[7] != "Cancelado"]

        self.atualizar_cards(validos)

    # ======================================================

    def atualizar_cards(self, filtrados):

        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        total_vendas = sum(p[5] for p in filtrados)
        quantidade = len(filtrados)
        ticket_medio = total_vendas / quantidade if quantidade else 0.0

        self.card(self.cards_frame, "Pedidos no período", str(quantidade), 0)
        self.card(self.cards_frame, "Faturamento no período", f"R$ {total_vendas:.2f}", 1)
        self.card(self.cards_frame, "Ticket Médio", f"R$ {ticket_medio:.2f}", 2)

    # ======================================================

    def card(self, master, titulo, valor, coluna):

        c = ctk.CTkFrame(master)
        c.grid(row=0, column=coluna, padx=10, sticky="nsew")
        master.grid_columnconfigure(coluna, weight=1)

        ctk.CTkLabel(c, text=titulo, font=("Arial", 14)).pack(pady=(15, 5))
        ctk.CTkLabel(c, text=valor, font=("Arial", 22, "bold")).pack(pady=(0, 15))
