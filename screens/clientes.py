import json
import threading
import urllib.request

import customtkinter as ctk
from tkinter import ttk, messagebox
from database.conexao import banco
from utils import tema
from utils import busca


class Clientes(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.pack(fill="both", expand=True, padx=20, pady=20)

        titulo = ctk.CTkLabel(
            self,
            text="Cadastro de Clientes",
            font=("Arial", 30, "bold")
        )
        titulo.pack(pady=(10, 20))

        formulario = ctk.CTkFrame(self)
        formulario.pack(fill="x", padx=20)

        # Nome
        ctk.CTkLabel(
            formulario,
            text="Nome"
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.nome = ctk.CTkEntry(
            formulario,
            width=320
        )
        self.nome.grid(row=0, column=1, padx=10)

        # Telefone
        ctk.CTkLabel(
            formulario,
            text="Telefone"
        ).grid(row=0, column=2, padx=10)

        self.telefone = ctk.CTkEntry(
            formulario,
            width=180
        )
        self.telefone.grid(row=0, column=3, padx=10)

        ctk.CTkLabel(
            formulario,
            text="Os endereços são cadastrados depois de salvar o cliente,\n"
                 "usando o botão \"📍 Endereços\" na lista abaixo — um cliente\n"
                 "pode ter vários (casa, trabalho, etc).",
            font=("Arial", 12),
            text_color="gray",
            justify="left"
        ).grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 10), sticky="w")

        botoes_form = ctk.CTkFrame(formulario, fg_color="transparent")
        botoes_form.grid(row=2, column=0, columnspan=4, pady=20)

        self.btn_salvar = ctk.CTkButton(
            botoes_form,
            text="Salvar Cliente",
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
        # Só aparece quando estiver editando um cliente existente

        self.cliente_id_editando = None

        # Busca
        busca_frame = ctk.CTkFrame(self, fg_color="transparent")
        busca_frame.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(
            busca_frame,
            text="🔍 Buscar cliente (nome ou telefone)"
        ).pack(side="left", padx=(0, 10))

        self.busca = ctk.CTkEntry(
            busca_frame,
            width=350,
            placeholder_text="Digite para buscar..."
        )
        self.busca.pack(side="left")
        self.busca.bind("<KeyRelease>", lambda evento: self.carregar())

        ctk.CTkButton(
            busca_frame,
            text="Limpar busca",
            width=120,
            fg_color="gray40",
            hover_color="gray30",
            command=self.limpar_busca
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            busca_frame,
            text="📍 Endereços do Cliente Selecionado",
            width=260,
            fg_color=tema.COR_LARANJA,
            hover_color=tema.COR_LARANJA_ESCURO,
            command=self.abrir_enderecos
        ).pack(side="left", padx=10)

        # Tabela
        self.tabela = ttk.Treeview(
            self,
            columns=("id", "nome", "telefone", "endereco", "cep"),
            show="headings",
            height=15
        )

        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome")
        self.tabela.heading("telefone", text="Telefone")
        self.tabela.heading("endereco", text="Endereço principal")
        self.tabela.heading("cep", text="CEP")

        self.tabela.column("id", width=60, anchor="center")
        self.tabela.column("nome", width=220)
        self.tabela.column("telefone", width=140)
        self.tabela.column("endereco", width=380)
        self.tabela.column("cep", width=100, anchor="center")

        self.tabela.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        self.tabela.bind("<Double-1>", self.editar_selecionado)

        self.carregar()

    def salvar(self):

        nome = self.nome.get().strip()
        telefone = self.telefone.get().strip()

        if nome == "":
            messagebox.showwarning("Clientes", "Informe o nome do cliente.")
            return

        if self.cliente_id_editando is not None:

            banco.executar(
                "UPDATE clientes SET nome=?, telefone=? WHERE id=?",
                (nome, telefone, self.cliente_id_editando)
            )

            self.cliente_id_editando = None
            self.btn_salvar.configure(text="Salvar Cliente")
            self.btn_cancelar.pack_forget()

        else:

            banco.executar(
                "INSERT INTO clientes (nome, telefone) VALUES (?, ?)",
                (nome, telefone)
            )

        self.limpar_formulario()
        self.carregar()

    # ======================================================
    # EDITAR / CANCELAR EDIÇÃO
    # ======================================================

    def editar_selecionado(self, evento=None):

        selecionado = self.tabela.selection()

        if not selecionado:
            return

        valores = self.tabela.item(selecionado[0], "values")
        cliente_id = int(valores[0])

        registro = banco.buscar_um(
            "SELECT nome, telefone FROM clientes WHERE id=?",
            (cliente_id,)
        )

        if not registro:
            return

        nome, telefone = registro

        self.cliente_id_editando = cliente_id

        campos = [
            (self.nome, nome),
            (self.telefone, telefone),
        ]

        for campo, valor in campos:
            campo.delete(0, "end")
            campo.insert(0, valor or "")

        self.btn_salvar.configure(text="Atualizar Cliente")
        self.btn_cancelar.pack(side="left")

        self.nome.focus()

    # ======================================================

    def cancelar_edicao(self):

        self.cliente_id_editando = None
        self.limpar_formulario()

        self.btn_salvar.configure(text="Salvar Cliente")
        self.btn_cancelar.pack_forget()

    # ======================================================

    def limpar_formulario(self):

        self.nome.delete(0, "end")
        self.telefone.delete(0, "end")

    # ======================================================
    # ENDEREÇOS (múltiplos por cliente, numa janela separada)
    # ======================================================

    def abrir_enderecos(self):

        selecionado = self.tabela.selection()

        if not selecionado:
            messagebox.showwarning(
                "Clientes",
                "Selecione um cliente na lista para gerenciar os endereços."
            )
            return

        valores = self.tabela.item(selecionado[0], "values")
        cliente_id = int(valores[0])
        nome = valores[1]

        JanelaEnderecos(self, cliente_id, nome, ao_fechar=self.carregar)

    # ======================================================

    def limpar_busca(self):

        self.busca.delete(0, "end")
        self.carregar()

    def carregar(self):

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        filtro = self.busca.get().strip()

        # Mesma lógica do Produtos: busca tudo e filtra em Python,
        # pra maiúscula/minúscula e acento funcionarem certo.
        # O endereço mostrado na lista é o marcado como "principal"
        # na tabela enderecos_cliente (um cliente pode ter vários).

        banco.cursor.execute("""
            SELECT c.id, c.nome, c.telefone,
                   e.endereco, e.numero, e.bairro, e.cidade, e.cep
            FROM clientes c
            LEFT JOIN enderecos_cliente e
                ON e.cliente_id = c.id AND e.principal = 1
            ORDER BY c.nome
        """)

        clientes = banco.cursor.fetchall()

        if filtro:
            clientes = [
                c for c in clientes
                if busca.contem(filtro, c[1]) or busca.contem(filtro, c[2])
            ]

        for cliente_id, nome, telefone, endereco, numero, bairro, cidade, cep in clientes:

            partes = [p for p in [endereco, numero, bairro, cidade] if p]
            endereco_completo = ", ".join(partes)

            self.tabela.insert(
                "", "end",
                values=(cliente_id, nome, telefone, endereco_completo, cep or "")
            )


# =============================================================
# JANELA: ENDEREÇOS DO CLIENTE (múltiplos)
# =============================================================

class JanelaEnderecos(ctk.CTkToplevel):

    def __init__(self, master, cliente_id, nome_cliente, ao_fechar=None):
        super().__init__(master)

        self.cliente_id = cliente_id
        self.ao_fechar = ao_fechar
        self.endereco_id_editando = None

        self.title(f"Endereços de {nome_cliente}")
        self.geometry("700x600")

        # Modal: trava a janela principal enquanto essa estiver aberta
        self.transient(master)
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.fechar)

        ctk.CTkLabel(
            self,
            text=f"📍 Endereços — {nome_cliente}",
            font=("Arial", 20, "bold")
        ).pack(pady=(15, 10))

        formulario = ctk.CTkFrame(self)
        formulario.pack(fill="x", padx=20)

        # Apelido
        ctk.CTkLabel(
            formulario,
            text="Apelido"
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.apelido = ctk.CTkEntry(
            formulario,
            width=200,
            placeholder_text="Ex: Casa, Trabalho..."
        )
        self.apelido.grid(row=0, column=1, padx=10, sticky="w")

        # CEP (com busca automática de endereço)
        ctk.CTkLabel(
            formulario,
            text="CEP"
        ).grid(row=0, column=2, padx=10, sticky="w")

        self.cep = ctk.CTkEntry(
            formulario,
            width=140,
            placeholder_text="00000-000"
        )
        self.cep.grid(row=0, column=3, padx=10, sticky="w")
        self.cep.bind("<FocusOut>", self.buscar_endereco_por_cep)
        self.cep.bind("<Return>", self.buscar_endereco_por_cep)

        self.lbl_status_cep = ctk.CTkLabel(
            formulario,
            text="",
            font=("Arial", 12),
            text_color="gray"
        )
        self.lbl_status_cep.grid(row=1, column=0, columnspan=4, padx=10, sticky="w")

        # Endereço (rua)
        ctk.CTkLabel(
            formulario,
            text="Endereço"
        ).grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.endereco = ctk.CTkEntry(
            formulario,
            width=430
        )
        self.endereco.grid(row=2, column=1, columnspan=3, padx=10, sticky="we")

        # Número
        ctk.CTkLabel(
            formulario,
            text="Número"
        ).grid(row=3, column=0, padx=10, pady=10, sticky="w")

        self.numero = ctk.CTkEntry(
            formulario,
            width=100
        )
        self.numero.grid(row=3, column=1, padx=10, sticky="w")

        # Bairro
        ctk.CTkLabel(
            formulario,
            text="Bairro"
        ).grid(row=3, column=2, padx=10, sticky="w")

        self.bairro = ctk.CTkEntry(
            formulario,
            width=180
        )
        self.bairro.grid(row=3, column=3, padx=10, sticky="w")

        # Cidade
        ctk.CTkLabel(
            formulario,
            text="Cidade"
        ).grid(row=4, column=0, padx=10, pady=10, sticky="w")

        self.cidade = ctk.CTkEntry(
            formulario,
            width=300
        )
        self.cidade.grid(row=4, column=1, columnspan=2, padx=10, sticky="w")

        botoes_form = ctk.CTkFrame(formulario, fg_color="transparent")
        botoes_form.grid(row=5, column=0, columnspan=4, pady=(10, 15))

        self.btn_salvar = ctk.CTkButton(
            botoes_form,
            text="Adicionar Endereço",
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
        # Só aparece quando estiver editando um endereço existente

        # Tabela de endereços já cadastrados
        self.tabela = ttk.Treeview(
            self,
            columns=("id", "apelido", "endereco", "cep", "principal"),
            show="headings",
            height=8
        )

        self.tabela.heading("id", text="ID")
        self.tabela.heading("apelido", text="Apelido")
        self.tabela.heading("endereco", text="Endereço")
        self.tabela.heading("cep", text="CEP")
        self.tabela.heading("principal", text="Principal")

        self.tabela.column("id", width=50, anchor="center")
        self.tabela.column("apelido", width=110)
        self.tabela.column("endereco", width=340)
        self.tabela.column("cep", width=90, anchor="center")
        self.tabela.column("principal", width=80, anchor="center")

        self.tabela.pack(fill="both", expand=True, padx=20, pady=(10, 10))

        self.tabela.bind("<Double-1>", self.editar_selecionado)

        acoes = ctk.CTkFrame(self, fg_color="transparent")
        acoes.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            acoes,
            text="⭐ Definir como Principal",
            width=200,
            command=self.definir_principal
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            acoes,
            text="🗑 Remover",
            width=120,
            fg_color=tema.COR_VERMELHO,
            hover_color="#a33002",
            command=self.remover
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            acoes,
            text="Fechar",
            width=120,
            fg_color="gray40",
            hover_color="gray30",
            command=self.fechar
        ).pack(side="right")

        self.carregar()

    # ======================================================

    def salvar(self):

        apelido = self.apelido.get().strip()
        cep = self.cep.get().strip()
        endereco = self.endereco.get().strip()
        numero = self.numero.get().strip()
        bairro = self.bairro.get().strip()
        cidade = self.cidade.get().strip()

        if not any([apelido, endereco, numero, bairro, cidade, cep]):
            messagebox.showwarning("Endereços", "Preencha ao menos um campo do endereço.")
            return

        if self.endereco_id_editando is not None:

            banco.executar(
                """
                UPDATE enderecos_cliente
                SET apelido=?, endereco=?, numero=?, bairro=?, cidade=?, cep=?
                WHERE id=?
                """,
                (apelido, endereco, numero, bairro, cidade, cep, self.endereco_id_editando)
            )

            self.endereco_id_editando = None
            self.btn_salvar.configure(text="Adicionar Endereço")
            self.btn_cancelar.pack_forget()

        else:

            # O primeiro endereço cadastrado pro cliente já vira o principal
            ja_tem_algum = banco.buscar_um(
                "SELECT COUNT(*) FROM enderecos_cliente WHERE cliente_id=?",
                (self.cliente_id,)
            )[0]

            principal = 1 if ja_tem_algum == 0 else 0

            banco.executar(
                """
                INSERT INTO enderecos_cliente
                    (cliente_id, apelido, endereco, numero, bairro, cidade, cep, principal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (self.cliente_id, apelido, endereco, numero, bairro, cidade, cep, principal)
            )

        self.limpar_formulario()
        self.carregar()

    # ======================================================

    def editar_selecionado(self, evento=None):

        selecionado = self.tabela.selection()

        if not selecionado:
            return

        endereco_id = int(self.tabela.item(selecionado[0], "values")[0])

        registro = banco.buscar_um(
            "SELECT apelido, endereco, numero, bairro, cidade, cep FROM enderecos_cliente WHERE id=?",
            (endereco_id,)
        )

        if not registro:
            return

        apelido, endereco, numero, bairro, cidade, cep = registro

        self.endereco_id_editando = endereco_id

        campos = [
            (self.apelido, apelido),
            (self.cep, cep),
            (self.endereco, endereco),
            (self.numero, numero),
            (self.bairro, bairro),
            (self.cidade, cidade),
        ]

        for campo, valor in campos:
            campo.delete(0, "end")
            campo.insert(0, valor or "")

        self.btn_salvar.configure(text="Atualizar Endereço")
        self.btn_cancelar.pack(side="left")

        self.apelido.focus()

    # ======================================================

    def cancelar_edicao(self):

        self.endereco_id_editando = None
        self.limpar_formulario()

        self.btn_salvar.configure(text="Adicionar Endereço")
        self.btn_cancelar.pack_forget()

    # ======================================================

    def limpar_formulario(self):

        for campo in (self.apelido, self.cep, self.endereco, self.numero, self.bairro, self.cidade):
            campo.delete(0, "end")

        self.lbl_status_cep.configure(text="")

    # ======================================================

    def definir_principal(self):

        selecionado = self.tabela.selection()

        if not selecionado:
            messagebox.showwarning("Endereços", "Selecione um endereço na lista.")
            return

        endereco_id = int(self.tabela.item(selecionado[0], "values")[0])

        banco.executar(
            "UPDATE enderecos_cliente SET principal=0 WHERE cliente_id=?",
            (self.cliente_id,)
        )
        banco.executar(
            "UPDATE enderecos_cliente SET principal=1 WHERE id=?",
            (endereco_id,)
        )

        self.carregar()

    # ======================================================

    def remover(self):

        selecionado = self.tabela.selection()

        if not selecionado:
            messagebox.showwarning("Endereços", "Selecione um endereço na lista.")
            return

        valores = self.tabela.item(selecionado[0], "values")
        endereco_id = int(valores[0])
        era_principal = valores[4] == "Sim"

        confirmar = messagebox.askyesno(
            "Remover Endereço",
            "Tem certeza que deseja remover este endereço?"
        )

        if not confirmar:
            return

        banco.executar("DELETE FROM enderecos_cliente WHERE id=?", (endereco_id,))

        if era_principal:

            # Promove outro endereço do cliente a principal, se existir algum
            proximo = banco.buscar_um(
                "SELECT id FROM enderecos_cliente WHERE cliente_id=? ORDER BY id LIMIT 1",
                (self.cliente_id,)
            )

            if proximo:
                banco.executar(
                    "UPDATE enderecos_cliente SET principal=1 WHERE id=?",
                    (proximo[0],)
                )

        self.carregar()

    # ======================================================
    # BUSCA DE ENDEREÇO PELO CEP (API ViaCEP - gratuita, sem chave)
    # ======================================================

    def buscar_endereco_por_cep(self, evento=None):

        cep_digitado = self.cep.get().strip()
        cep_limpo = cep_digitado.replace("-", "").replace(".", "").strip()

        if len(cep_limpo) != 8 or not cep_limpo.isdigit():
            return

        self.lbl_status_cep.configure(text="🔎 Buscando endereço...", text_color="gray")

        threading.Thread(
            target=self._consultar_viacep,
            args=(cep_limpo,),
            daemon=True
        ).start()

    def _consultar_viacep(self, cep):

        try:
            url = f"https://viacep.com.br/ws/{cep}/json/"

            with urllib.request.urlopen(url, timeout=6) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))

            if dados.get("erro"):
                self.after(0, lambda: self.lbl_status_cep.configure(
                    text="❌ CEP não encontrado.", text_color="#c33"
                ))
                return

            self.after(0, lambda: self._preencher_endereco(dados))

        except Exception:
            self.after(0, lambda: self.lbl_status_cep.configure(
                text="⚠️ Não foi possível buscar o CEP (verifique a internet).",
                text_color="#c80"
            ))

    def _preencher_endereco(self, dados):

        self.endereco.delete(0, "end")
        self.endereco.insert(0, dados.get("logradouro", ""))

        self.bairro.delete(0, "end")
        self.bairro.insert(0, dados.get("bairro", ""))

        self.cidade.delete(0, "end")
        self.cidade.insert(0, dados.get("localidade", ""))

        self.lbl_status_cep.configure(text="✅ Endereço preenchido!", text_color="#2a7")

        self.numero.focus()

    # ======================================================

    def carregar(self):

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        enderecos = banco.buscar(
            """
            SELECT id, apelido, endereco, numero, bairro, cidade, cep, principal
            FROM enderecos_cliente
            WHERE cliente_id=?
            ORDER BY principal DESC, apelido
            """,
            (self.cliente_id,)
        )

        for endereco_id, apelido, endereco, numero, bairro, cidade, cep, principal in enderecos:

            partes = [p for p in [endereco, numero, bairro, cidade] if p]
            endereco_completo = ", ".join(partes)

            self.tabela.insert(
                "", "end",
                values=(
                    endereco_id, apelido or "", endereco_completo,
                    cep or "", "Sim" if principal else "Não"
                )
            )

    # ======================================================

    def fechar(self):

        if self.ao_fechar:
            self.ao_fechar()

        self.destroy()
