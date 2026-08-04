import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

from database.conexao import banco
from utils import config
from utils import busca


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

        # ---------------- Tabela ----------------

        self.tabela = ttk.Treeview(
            self.scroll,
            columns=("numero", "data", "hora", "cliente", "total", "pagamento"),
            show="headings",
            height=15
        )

        colunas = [
            ("numero", "Nº", 70, "center"),
            ("data", "Data", 90, "center"),
            ("hora", "Hora", 70, "center"),
            ("cliente", "Cliente", 280, "w"),
            ("total", "Total", 100, "e"),
            ("pagamento", "Pagamento", 110, "center"),
        ]

        for chave, texto, largura, ancora in colunas:
            self.tabela.heading(chave, text=texto)
            self.tabela.column(chave, width=largura, anchor=ancora)

        self.tabela.pack(fill="x", pady=10)

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

            banco.executar("DELETE FROM pedidos WHERE data=?", (hoje,))

            mensagem = "Os pedidos de hoje foram zerados."

        else:

            banco.executar("DELETE FROM itens_pedido")
            banco.executar("DELETE FROM pedidos")

            mensagem = "Todo o histórico de pedidos foi zerado."

        messagebox.showinfo("Relatórios", mensagem)

        self.carregar_pedidos()
        self.aplicar_filtro()

    # ======================================================

    def carregar_pedidos(self):

        self.todos_pedidos = banco.buscar(
            """
            SELECT p.numero, p.data, p.hora,
                   COALESCE(c.nome, 'Cliente Balcão'), p.total, p.pagamento
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

        for numero, data, hora, cliente, total, pagamento in self.todos_pedidos:

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

            filtrados.append((numero, data, hora, cliente, total, pagamento))

        for linha in self.tabela.get_children():
            self.tabela.delete(linha)

        for numero, data, hora, cliente, total, pagamento in filtrados:
            self.tabela.insert(
                "", "end",
                values=(
                    f"{numero:04d}", data, hora, cliente,
                    f"R$ {total:.2f}", pagamento
                )
            )

        self.atualizar_cards(filtrados)

    # ======================================================

    def atualizar_cards(self, filtrados):

        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        total_vendas = sum(p[4] for p in filtrados)
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
