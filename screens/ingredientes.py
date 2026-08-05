import customtkinter as ctk
from tkinter import ttk, messagebox
from database.conexao import banco
from utils import tema
from utils import busca
from utils import responsivo


class Ingredientes(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Frame com rolagem: em telas menores o conteúdo não cabia
        # inteiro na altura da janela e não tinha como rolar até o
        # resto dos botões/tabela.
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        titulo = ctk.CTkLabel(
            self.scroll,
            text="Ingredientes (Estoque de Insumos)",
            font=("Arial", 30, "bold")
        )
        titulo.pack(pady=(10, 20))

        filtro_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        filtro_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            filtro_frame,
            text="🔍 Buscar"
        ).pack(side="left", padx=(0, 10))

        self.busca = ctk.CTkEntry(
            filtro_frame,
            width=280,
            placeholder_text="Digite para buscar..."
        )
        self.busca.pack(side="left")
        self.busca.bind("<KeyRelease>", lambda evento: self.carregar())

        ctk.CTkButton(
            filtro_frame,
            text="Limpar filtro",
            width=120,
            command=self.limpar_filtro
        ).pack(side="left", padx=10)

        formulario = ctk.CTkFrame(self.scroll)
        formulario.pack(fill="x", padx=20)

        ctk.CTkLabel(formulario, text="Nome").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.nome = ctk.CTkEntry(formulario, width=220)
        self.nome.grid(row=0, column=1, padx=10)

        ctk.CTkLabel(formulario, text="Categoria").grid(row=0, column=2, padx=10, pady=10)
        self.categoria = ctk.CTkEntry(formulario, width=160)
        self.categoria.grid(row=0, column=3, padx=10)

        ctk.CTkLabel(formulario, text="Unidade").grid(row=0, column=4, padx=10, pady=10)
        self.unidade = ctk.CTkComboBox(
            formulario,
            width=110,
            values=["porção", "un", "g", "kg", "ml", "l"]
        )
        self.unidade.set("porção")
        self.unidade.grid(row=0, column=5, padx=10)

        ctk.CTkLabel(formulario, text="Estoque Atual").grid(row=1, column=0, padx=10, pady=10)
        self.estoque_atual = ctk.CTkEntry(formulario, width=120)
        self.estoque_atual.grid(row=1, column=1, padx=10)

        ctk.CTkLabel(formulario, text="Estoque Mínimo").grid(row=1, column=2, padx=10, pady=10)
        self.estoque_minimo = ctk.CTkEntry(formulario, width=120)
        self.estoque_minimo.grid(row=1, column=3, padx=10)

        ctk.CTkLabel(formulario, text="Custo Unitário (R$)").grid(row=1, column=4, padx=10, pady=10)
        self.custo_unitario = ctk.CTkEntry(formulario, width=110)
        self.custo_unitario.grid(row=1, column=5, padx=10)

        botoes_form = ctk.CTkFrame(formulario, fg_color="transparent")
        botoes_form.grid(row=2, column=0, columnspan=6, pady=20)

        self.btn_salvar = ctk.CTkButton(
            botoes_form,
            text="Salvar Ingrediente",
            fg_color=tema.COR_LARANJA,
            hover_color=tema.COR_LARANJA_ESCURO,
            command=self.salvar
        )
        self.btn_salvar.pack(side="left", padx=(0, 10))

        self.btn_cancelar = ctk.CTkButton(
            botoes_form,
            text="Cancelar edição",
            fg_color="gray40",
            hover_color="gray30",
            command=self.cancelar_edicao
        )
        # Só aparece quando estiver editando um ingrediente existente

        ctk.CTkButton(
            botoes_form,
            text="✏️ Editar Selecionado",
            fg_color=tema.COR_LARANJA_ESCURO,
            hover_color="#A85D08",
            command=self.carregar_para_edicao
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            botoes_form,
            text="🗑 Excluir Selecionado",
            fg_color=tema.COR_VERMELHO,
            hover_color="#B93601",
            command=self.excluir
        ).pack(side="left", padx=10)

        self.ingrediente_id_editando = None

        dica = ctk.CTkLabel(
            self.scroll,
            text="Dica: linhas em vermelho estão no estoque mínimo ou abaixo dele. "
                 "O estoque desconta sozinho quando um produto que usa esse "
                 "ingrediente na receita é vendido (aba Produtos → Receita).",
            font=("Arial", 12),
            text_color="gray"
        )
        dica.pack(anchor="w", padx=20, pady=(0, 5))

        linhas = responsivo.linhas_para_tabela(self, self.scroll, pady_tabela=20)

        self.tabela = ttk.Treeview(
            self.scroll,
            columns=("id", "nome", "categoria", "unidade", "estoque_atual", "estoque_minimo", "custo"),
            show="headings",
            height=linhas
        )

        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome")
        self.tabela.heading("categoria", text="Categoria")
        self.tabela.heading("unidade", text="Unidade")
        self.tabela.heading("estoque_atual", text="Estoque Atual")
        self.tabela.heading("estoque_minimo", text="Estoque Mínimo")
        self.tabela.heading("custo", text="Custo Unit.")

        self.tabela.column("id", width=50)
        self.tabela.column("nome", width=220)
        self.tabela.column("categoria", width=150)
        self.tabela.column("unidade", width=80, anchor="center")
        self.tabela.column("estoque_atual", width=110, anchor="e")
        self.tabela.column("estoque_minimo", width=110, anchor="e")
        self.tabela.column("custo", width=100, anchor="e")

        self.tabela.tag_configure("estoque_baixo", foreground=tema.COR_VERMELHO)

        self.tabela.pack(fill="both", expand=True, padx=20, pady=20)

        responsivo.tornar_dinamica(self, self.scroll, lambda: self.tabela, pady_tabela=20)

        self.carregar()

    # ======================================================

    def _numero(self, texto):

        texto = texto.strip().replace(",", ".")

        if not texto:
            return 0.0

        return float(texto)

    def salvar(self):

        nome = self.nome.get().strip()

        if not nome:
            messagebox.showwarning("Ingredientes", "Informe o nome do ingrediente.")
            return

        try:
            estoque_atual = self._numero(self.estoque_atual.get())
            estoque_minimo = self._numero(self.estoque_minimo.get())
            custo_unitario = self._numero(self.custo_unitario.get())
        except ValueError:
            messagebox.showwarning("Ingredientes", "Estoque e custo devem ser números, ex: 1,5")
            return

        categoria = self.categoria.get().strip()
        unidade = self.unidade.get().strip() or "porção"

        if self.ingrediente_id_editando is not None:

            banco.executar(
                """
                UPDATE ingredientes
                SET nome=?, categoria=?, unidade_medida=?, estoque_atual=?,
                    estoque_minimo=?, custo_unitario=?
                WHERE id=?
                """,
                (nome, categoria, unidade, estoque_atual, estoque_minimo,
                 custo_unitario, self.ingrediente_id_editando)
            )

            self.ingrediente_id_editando = None
            self.btn_salvar.configure(text="Salvar Ingrediente")
            self.btn_cancelar.pack_forget()

        else:

            banco.executar(
                """
                INSERT INTO ingredientes
                    (nome, categoria, unidade_medida, estoque_atual, estoque_minimo, custo_unitario)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (nome, categoria, unidade, estoque_atual, estoque_minimo, custo_unitario)
            )

        self.limpar_formulario()
        self.carregar()

    # ======================================================

    def carregar_para_edicao(self):

        selecionado = self.tabela.selection()

        if not selecionado:
            messagebox.showwarning(
                "Ingredientes",
                "Selecione um ingrediente na lista para editar."
            )
            return

        valores = self.tabela.item(selecionado[0], "values")
        ingrediente_id = valores[0]

        registro = banco.buscar_um(
            """
            SELECT nome, categoria, unidade_medida, estoque_atual, estoque_minimo, custo_unitario
            FROM ingredientes WHERE id=?
            """,
            (ingrediente_id,)
        )

        if not registro:
            return

        nome, categoria, unidade, estoque_atual, estoque_minimo, custo_unitario = registro

        self.ingrediente_id_editando = ingrediente_id

        self.nome.delete(0, "end")
        self.nome.insert(0, nome or "")

        self.categoria.delete(0, "end")
        self.categoria.insert(0, categoria or "")

        self.unidade.set(unidade or "porção")

        self.estoque_atual.delete(0, "end")
        self.estoque_atual.insert(0, str(estoque_atual).replace(".", ","))

        self.estoque_minimo.delete(0, "end")
        self.estoque_minimo.insert(0, str(estoque_minimo).replace(".", ","))

        self.custo_unitario.delete(0, "end")
        self.custo_unitario.insert(0, str(custo_unitario).replace(".", ","))

        self.btn_salvar.configure(text="Atualizar Ingrediente")
        self.btn_cancelar.pack(side="left", padx=10)

        self.nome.focus()

    # ======================================================

    def cancelar_edicao(self):

        self.ingrediente_id_editando = None
        self.limpar_formulario()

        self.btn_salvar.configure(text="Salvar Ingrediente")
        self.btn_cancelar.pack_forget()

    # ======================================================

    def limpar_formulario(self):

        self.nome.delete(0, "end")
        self.categoria.delete(0, "end")
        self.unidade.set("porção")
        self.estoque_atual.delete(0, "end")
        self.estoque_minimo.delete(0, "end")
        self.custo_unitario.delete(0, "end")

    # ======================================================

    def limpar_filtro(self):

        self.busca.delete(0, "end")
        self.carregar()

    def carregar(self):

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        termo = self.busca.get().strip()

        ingredientes = banco.buscar(
            """
            SELECT id, nome, categoria, unidade_medida, estoque_atual, estoque_minimo, custo_unitario
            FROM ingredientes
            WHERE ativo=1
            ORDER BY nome
            """
        )

        if termo:
            ingredientes = [i for i in ingredientes if busca.contem(termo, i[1])]

        for (ingrediente_id, nome, categoria, unidade, estoque_atual,
             estoque_minimo, custo_unitario) in ingredientes:

            estoque_baixo = estoque_atual <= estoque_minimo

            self.tabela.insert(
                "", "end",
                values=(
                    ingrediente_id, nome, categoria, unidade,
                    f"{estoque_atual:g}", f"{estoque_minimo:g}",
                    f"R$ {custo_unitario:.2f}"
                ),
                tags=("estoque_baixo",) if estoque_baixo else ()
            )

    # ======================================================

    def excluir(self):

        selecionado = self.tabela.selection()

        if not selecionado:
            messagebox.showwarning(
                "Ingredientes",
                "Selecione um ingrediente na lista para excluir."
            )
            return

        valores = self.tabela.item(selecionado[0], "values")
        ingrediente_id = valores[0]
        nome = valores[1]

        confirmar = messagebox.askyesno(
            "Excluir Ingrediente",
            f"Tem certeza que deseja excluir \"{nome}\"?"
        )

        if not confirmar:
            return

        usado_em_receita = banco.buscar_um(
            "SELECT COUNT(*) FROM receita_produto WHERE ingrediente_id=?",
            (ingrediente_id,)
        )

        if usado_em_receita and usado_em_receita[0] > 0:

            # Está na receita de algum produto: não apaga (quebraria a
            # receita), só desativa para não aparecer mais nos cadastros.
            banco.executar("UPDATE ingredientes SET ativo=0 WHERE id=?", (ingrediente_id,))

            messagebox.showinfo(
                "Ingredientes",
                f"\"{nome}\" está usado na receita de algum produto, então "
                "foi apenas DESATIVADO, para não quebrar a receita existente."
            )

        else:

            banco.executar("DELETE FROM ingredientes WHERE id=?", (ingrediente_id,))

            messagebox.showinfo(
                "Ingredientes",
                f"\"{nome}\" foi excluído definitivamente."
            )

        self.carregar()
