import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from utils import config
from utils import impressora
from utils import tema


class Configuracoes(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.pack(fill="both", expand=True, padx=20, pady=20)

        titulo = ctk.CTkLabel(
            self,
            text="Configurações",
            font=("Arial", 30, "bold")
        )
        titulo.pack(pady=(10, 25))

        # =========================================================
        # DADOS DA LOJA
        # =========================================================

        bloco_loja = ctk.CTkFrame(self)
        bloco_loja.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            bloco_loja,
            text="Dados da Loja (aparecem no topo do cupom)",
            font=("Arial", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(bloco_loja, text="Nome da loja").grid(
            row=1, column=0, sticky="w", padx=15, pady=5
        )
        self.loja_nome = ctk.CTkEntry(bloco_loja, width=350)
        self.loja_nome.grid(row=1, column=1, padx=15, pady=5, sticky="w")

        ctk.CTkLabel(bloco_loja, text="Endereço").grid(
            row=2, column=0, sticky="w", padx=15, pady=5
        )
        self.loja_endereco = ctk.CTkEntry(bloco_loja, width=350)
        self.loja_endereco.grid(row=2, column=1, padx=15, pady=5, sticky="w")

        ctk.CTkLabel(bloco_loja, text="Telefone").grid(
            row=3, column=0, sticky="w", padx=15, pady=(5, 15)
        )
        self.loja_telefone = ctk.CTkEntry(bloco_loja, width=350)
        self.loja_telefone.grid(row=3, column=1, padx=15, pady=(5, 15), sticky="w")

        # =========================================================
        # IMPRESSORA
        # =========================================================

        bloco_impressora = ctk.CTkFrame(self)
        bloco_impressora.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            bloco_impressora,
            text="Impressora Térmica",
            font=("Arial", 16, "bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(bloco_impressora, text="Impressora instalada").grid(
            row=1, column=0, sticky="w", padx=15, pady=5
        )

        self.combo_impressoras = ctk.CTkComboBox(
            bloco_impressora,
            width=350,
            values=["(clique em Atualizar lista)"]
        )
        self.combo_impressoras.grid(row=1, column=1, padx=15, pady=5, sticky="w")

        ctk.CTkButton(
            bloco_impressora,
            text="🔄 Atualizar lista",
            width=150,
            fg_color=tema.COR_LARANJA,
            hover_color=tema.COR_LARANJA_ESCURO,
            command=self.atualizar_lista_impressoras
        ).grid(row=1, column=2, padx=15, pady=5)

        ctk.CTkLabel(bloco_impressora, text="Tamanho do papel").grid(
            row=2, column=0, sticky="w", padx=15, pady=(5, 15)
        )

        self.papel = ctk.CTkSegmentedButton(
            bloco_impressora,
            values=["58mm (32 col.)", "80mm (48 col.)"]
        )
        self.papel.set("58mm (32 col.)")
        self.papel.grid(row=2, column=1, padx=15, pady=(5, 15), sticky="w")

        # =========================================================
        # SEGURANÇA
        # =========================================================

        bloco_seguranca = ctk.CTkFrame(self)
        bloco_seguranca.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            bloco_seguranca,
            text="Segurança",
            font=("Arial", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            bloco_seguranca,
            text="Senha para zerar relatórios"
        ).grid(row=1, column=0, sticky="w", padx=15, pady=(5, 5))

        self.senha_reset = ctk.CTkEntry(bloco_seguranca, width=200, show="•")
        self.senha_reset.grid(row=1, column=1, padx=15, pady=(5, 5), sticky="w")

        ctk.CTkLabel(
            bloco_seguranca,
            text="Essa senha é pedida sempre que alguém tentar apagar\n"
                 "os pedidos/relatórios na tela de Relatórios.",
            font=("Arial", 12),
            text_color="gray",
            justify="left"
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 15))

        # =========================================================
        # BOTÕES DE AÇÃO
        # =========================================================

        acoes = ctk.CTkFrame(self, fg_color="transparent")
        acoes.pack(fill="x", padx=10, pady=15)

        ctk.CTkButton(
            acoes,
            text="💾 Salvar Configurações",
            width=220,
            height=42,
            fg_color=tema.COR_VERDE,
            hover_color="#1F6B40",
            command=self.salvar
        ).pack(side="left", padx=(5, 10))

        ctk.CTkButton(
            acoes,
            text="🖨 Imprimir Cupom de Teste",
            width=220,
            height=42,
            fg_color=tema.COR_LARANJA,
            hover_color=tema.COR_LARANJA_ESCURO,
            command=self.imprimir_teste
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            acoes,
            text="🗄 Fazer Backup Agora",
            width=220,
            height=42,
            fg_color=tema.COR_TEXTO_CLARO,
            hover_color=tema.COR_TEXTO,
            command=self.fazer_backup_manual
        ).pack(side="left", padx=10)

        self.lbl_status = ctk.CTkLabel(self, text="", font=("Arial", 13))
        self.lbl_status.pack(pady=(5, 0))

        # =========================================================
        # RODAPÉ - VERSÃO E CRÉDITOS
        # =========================================================

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", pady=(20, 5))

        ctk.CTkLabel(
            rodape,
            text="Los Manager — versão 2.0",
            font=("Arial", 12, "bold"),
            text_color=tema.COR_TEXTO_CLARO
        ).pack()

        ctk.CTkLabel(
            rodape,
            text="Desenvolvido por Ramon Oliveira",
            font=("Arial", 11),
            text_color=tema.COR_TEXTO_CLARO
        ).pack()

        self.carregar()

    # ======================================================

    def carregar(self):
        """Carrega os valores salvos no banco pros campos da tela."""

        self.loja_nome.delete(0, "end")
        self.loja_nome.insert(0, config.obter("loja_nome"))

        self.loja_endereco.delete(0, "end")
        self.loja_endereco.insert(0, config.obter("loja_endereco"))

        self.loja_telefone.delete(0, "end")
        self.loja_telefone.insert(0, config.obter("loja_telefone"))

        largura_salva = config.obter_largura_papel()
        self.papel.set("80mm (48 col.)" if largura_salva == 48 else "58mm (32 col.)")

        self.senha_reset.delete(0, "end")
        self.senha_reset.insert(0, config.obter("senha_reset"))

        impressora_salva = config.obter_impressora_nome()

        if impressora_salva:
            self.combo_impressoras.configure(values=[impressora_salva])
            self.combo_impressoras.set(impressora_salva)

    # ======================================================

    def atualizar_lista_impressoras(self):
        """Consulta o Windows e lista as impressoras instaladas."""

        try:
            lista = impressora.listar_impressoras()

        except Exception as erro:

            messagebox.showerror(
                "Erro",
                f"Não foi possível listar as impressoras do Windows:\n\n{erro}\n\n"
                "Isso só funciona rodando o programa no Windows, com o "
                "pacote pywin32 instalado (pip install pywin32)."
            )
            return

        if not lista:
            messagebox.showwarning(
                "Impressoras",
                "Nenhuma impressora foi encontrada instalada no Windows."
            )
            return

        self.combo_impressoras.configure(values=lista)
        self.combo_impressoras.set(lista[0])

    # ======================================================

    def salvar(self):

        largura = 48 if self.papel.get().startswith("80mm") else 32

        config.definir("loja_nome", self.loja_nome.get().strip())
        config.definir("loja_endereco", self.loja_endereco.get().strip())
        config.definir("loja_telefone", self.loja_telefone.get().strip())
        config.definir("senha_reset", self.senha_reset.get().strip())
        config.definir("impressora_nome", self.combo_impressoras.get().strip())
        config.definir("impressora_largura", str(largura))

        self.lbl_status.configure(
            text="✅ Configurações salvas com sucesso!",
            text_color="#2a7"
        )

        messagebox.showinfo("Configurações", "Configurações salvas com sucesso!")

    # ======================================================

    def imprimir_teste(self):
        """Salva as configurações atuais e imprime um cupom de teste,
        sem gravar nada na tabela de pedidos."""

        self.salvar()

        dados_loja = {
            "nome": self.loja_nome.get().strip(),
            "endereco": self.loja_endereco.get().strip(),
            "telefone": self.loja_telefone.get().strip(),
        }

        agora = datetime.now()

        pedido_teste = {
            "numero": 0,
            "cliente": "Cliente de Teste",
            "data": agora.strftime("%d/%m/%Y"),
            "hora": agora.strftime("%H:%M"),
            "subtotal": 10.00,
            "desconto": 0.00,
            "acrescimo": 0.00,
            "total": 10.00,
            "pagamento": "TESTE",
            "observacao": "Isto é apenas um teste de impressão."
        }

        itens_teste = [
            {
                "nome": "Item de Teste",
                "qtd": 1,
                "valor_unitario": 10.00,
                "subtotal": 10.00
            }
        ]

        try:
            impressora.imprimir_cupom(dados_loja, pedido_teste, itens_teste)

            messagebox.showinfo(
                "Teste de Impressão",
                "Cupom de teste enviado! Verifique a impressora."
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro ao imprimir",
                f"Não foi possível imprimir o cupom de teste:\n\n{erro}"
            )

    # ======================================================

    def fazer_backup_manual(self):
        """Copia o banco de dados agora mesmo pra pasta backups/,
        independente do backup automático feito na abertura do programa."""

        try:
            config.fazer_backup_banco()

            messagebox.showinfo(
                "Backup",
                "Backup do banco de dados feito com sucesso!\n\n"
                "O arquivo foi salvo na pasta \"backups\", do lado do programa."
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro ao fazer backup",
                f"Não foi possível fazer o backup do banco de dados:\n\n{erro}"
            )
