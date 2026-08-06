import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

import sys
import webbrowser

from utils import config
from utils import impressora
from utils import tema
from utils import atualizacao


class Configuracoes(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.pack(fill="both", expand=True, padx=15, pady=12)

        # Tudo fica dentro de um frame com rolagem: em telas menores
        # (notebooks antigos, resolução baixa) o conteúdo desta tela
        # não cabe inteiro na altura da janela — sem isso, os botões
        # de baixo ficavam inacessíveis, sem nenhuma barra de rolagem.
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        titulo = ctk.CTkLabel(
            self.scroll,
            text="Configurações",
            font=("Arial", 24, "bold")
        )
        titulo.pack(pady=(6, 12))

        # =========================================================
        # DADOS DA LOJA
        # =========================================================

        bloco_loja = ctk.CTkFrame(self.scroll)
        bloco_loja.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(
            bloco_loja,
            text="Dados da Loja (aparecem no topo do cupom)",
            font=("Arial", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 6))

        ctk.CTkLabel(bloco_loja, text="Nome da loja").grid(
            row=1, column=0, sticky="w", padx=15, pady=4
        )
        self.loja_nome = ctk.CTkEntry(bloco_loja, width=350, height=26)
        self.loja_nome.grid(row=1, column=1, padx=15, pady=4, sticky="w")

        ctk.CTkLabel(bloco_loja, text="Endereço").grid(
            row=2, column=0, sticky="w", padx=15, pady=4
        )
        self.loja_endereco = ctk.CTkEntry(bloco_loja, width=350, height=26)
        self.loja_endereco.grid(row=2, column=1, padx=15, pady=4, sticky="w")

        ctk.CTkLabel(bloco_loja, text="Telefone").grid(
            row=3, column=0, sticky="w", padx=15, pady=(4, 8)
        )
        self.loja_telefone = ctk.CTkEntry(bloco_loja, width=350, height=26)
        self.loja_telefone.grid(row=3, column=1, padx=15, pady=(4, 8), sticky="w")

        # =========================================================
        # IMPRESSORA
        # =========================================================

        bloco_impressora = ctk.CTkFrame(self.scroll)
        bloco_impressora.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(
            bloco_impressora,
            text="Impressora Térmica",
            font=("Arial", 14, "bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(10, 6))

        ctk.CTkLabel(bloco_impressora, text="Impressora instalada").grid(
            row=1, column=0, sticky="w", padx=15, pady=4
        )

        self.combo_impressoras = ctk.CTkComboBox(
            bloco_impressora,
            width=350,
            height=26,
            values=["(clique em Atualizar lista)"]
        )
        self.combo_impressoras.grid(row=1, column=1, padx=15, pady=4, sticky="w")

        ctk.CTkButton(
            bloco_impressora,
            text="🔄 Atualizar lista",
            width=150,
            height=26,
            fg_color=tema.COR_LARANJA,
            hover_color=tema.COR_LARANJA_ESCURO,
            command=self.atualizar_lista_impressoras
        ).grid(row=1, column=2, padx=15, pady=4)

        ctk.CTkLabel(bloco_impressora, text="Tamanho do papel").grid(
            row=2, column=0, sticky="w", padx=15, pady=(4, 8)
        )

        self.papel = ctk.CTkSegmentedButton(
            bloco_impressora,
            height=26,
            values=["58mm (32 col.)", "80mm (48 col.)"]
        )
        self.papel.set("58mm (32 col.)")
        self.papel.grid(row=2, column=1, padx=15, pady=(4, 8), sticky="w")

        # =========================================================
        # ESTOQUE DE INGREDIENTES
        # =========================================================

        bloco_ingredientes = ctk.CTkFrame(self.scroll)
        bloco_ingredientes.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(
            bloco_ingredientes,
            text="Estoque de Ingredientes",
            font=("Arial", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 6))

        self.bloquear_estoque_ingrediente = ctk.CTkSwitch(
            bloco_ingredientes,
            text="Bloquear a venda quando faltar ingrediente no estoque",
            onvalue="1",
            offvalue="0"
        )
        self.bloquear_estoque_ingrediente.grid(
            row=1, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 4)
        )

        ctk.CTkLabel(
            bloco_ingredientes,
            text="Desligado (padrão): o sistema só avisa que falta ingrediente e\n"
                 "deixa continuar a venda mesmo assim, igual já acontece hoje\n"
                 "com o estoque de produto.",
            font=("Arial", 11),
            text_color="gray",
            justify="left"
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 8))

        # =========================================================
        # SEGURANÇA
        # =========================================================

        bloco_seguranca = ctk.CTkFrame(self.scroll)
        bloco_seguranca.pack(fill="x", padx=10, pady=6)

        ctk.CTkLabel(
            bloco_seguranca,
            text="Segurança",
            font=("Arial", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 6))

        ctk.CTkLabel(
            bloco_seguranca,
            text="Senha para zerar relatórios"
        ).grid(row=1, column=0, sticky="w", padx=15, pady=(4, 4))

        self.senha_reset = ctk.CTkEntry(bloco_seguranca, width=200, height=26, show="•")
        self.senha_reset.grid(row=1, column=1, padx=15, pady=(4, 4), sticky="w")

        ctk.CTkLabel(
            bloco_seguranca,
            text="Essa senha é pedida sempre que alguém tentar apagar\n"
                 "os pedidos/relatórios na tela de Relatórios.",
            font=("Arial", 11),
            text_color="gray",
            justify="left"
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 8))

        # =========================================================
        # BOTÕES DE AÇÃO
        # =========================================================

        acoes = ctk.CTkFrame(self.scroll, fg_color="transparent")
        acoes.pack(fill="x", padx=10, pady=8)

        ctk.CTkButton(
            acoes,
            text="💾 Salvar Configurações",
            width=220,
            height=34,
            fg_color=tema.COR_VERDE,
            hover_color="#1F6B40",
            command=self.salvar
        ).pack(side="left", padx=(5, 10))

        ctk.CTkButton(
            acoes,
            text="🖨 Imprimir Cupom de Teste",
            width=220,
            height=34,
            fg_color=tema.COR_LARANJA,
            hover_color=tema.COR_LARANJA_ESCURO,
            command=self.imprimir_teste
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            acoes,
            text="🗄 Fazer Backup Agora",
            width=220,
            height=34,
            fg_color=tema.COR_TEXTO_CLARO,
            hover_color=tema.COR_TEXTO,
            command=self.fazer_backup_manual
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            acoes,
            text="🔄 Verificar Atualização",
            width=220,
            height=34,
            fg_color=tema.COR_TEXTO_CLARO,
            hover_color=tema.COR_TEXTO,
            command=self.verificar_atualizacao_manual
        ).pack(side="left", padx=10)

        self.lbl_status = ctk.CTkLabel(self.scroll, text="", font=("Arial", 13))
        self.lbl_status.pack(pady=(4, 0))

        # =========================================================
        # RODAPÉ - VERSÃO E CRÉDITOS
        # =========================================================

        rodape = ctk.CTkFrame(self.scroll, fg_color="transparent")
        rodape.pack(fill="x", pady=(10, 4))

        ctk.CTkLabel(
            rodape,
            text=atualizacao.texto_versao(),
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

        if config.bloquear_venda_sem_estoque_ingrediente():
            self.bloquear_estoque_ingrediente.select()
        else:
            self.bloquear_estoque_ingrediente.deselect()

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
        config.definir("bloquear_venda_sem_estoque_ingrediente", self.bloquear_estoque_ingrediente.get())

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

    # ======================================================

    def verificar_atualizacao_manual(self):
        """Checagem de atualização pedida na mão pelo usuário — ao
        contrário da checagem automática do startup, essa sempre dá uma
        resposta visível (achou, não achou, ou deu erro)."""

        if not getattr(sys, "frozen", False):
            messagebox.showinfo(
                "Verificar Atualização",
                "A checagem de atualização só funciona na versão "
                "compilada (.exe), baixada do GitHub."
            )
            return

        if atualizacao.obter_versao_atual() is None:
            messagebox.showwarning(
                "Verificar Atualização",
                "Não foi possível identificar a versão deste "
                ".exe (ele não foi gerado pela Action do GitHub)."
            )
            return

        self.lbl_status.configure(text="🔎 Verificando atualização...", text_color="gray")

        atualizacao.verificar_manualmente(
            lambda atual, nova, url: self.after(0, lambda: self._resultado_atualizacao(atual, nova, url)),
            lambda erro: self.after(0, lambda: self._erro_atualizacao(erro))
        )

    # ======================================================

    def _resultado_atualizacao(self, versao_atual, versao_nova, url_release):

        self.lbl_status.configure(text="")

        if versao_nova > versao_atual:

            abrir = messagebox.askyesno(
                "Atualização disponível",
                f"Você está usando a versão {atualizacao.formatar_versao(versao_atual)}.\n"
                f"A versão {atualizacao.formatar_versao(versao_nova)} já está disponível no GitHub.\n\n"
                "Deseja abrir a página de download agora?"
            )

            if abrir:
                webbrowser.open(url_release)

        else:

            messagebox.showinfo(
                "Verificar Atualização",
                f"Você já está com a versão mais recente "
                f"({atualizacao.formatar_versao(versao_atual)})."
            )

    # ======================================================

    def _erro_atualizacao(self, erro):

        self.lbl_status.configure(text="")

        messagebox.showerror(
            "Verificar Atualização",
            f"Não foi possível verificar atualizações agora:\n\n{erro}\n\n"
            "Confira sua conexão com a internet."
        )
