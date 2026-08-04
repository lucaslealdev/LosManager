import customtkinter as ctk
from PIL import Image

from database.conexao import banco
from screens.dashboard import Dashboard
from screens.produtos import Produtos
from screens.clientes import Clientes
from screens.pedidos import Pedidos
from screens.configuracoes import Configuracoes
from screens.caixa import Caixa
from screens.relatorios import Relatorios
from utils import config
from utils import tema

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class LosManager(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Los Manager")
        self.geometry("1400x800")
        self.minsize(1200, 700)
        self.configure(fg_color=tema.COR_CREME_CLARO)

        tema.aplicar_estilo_tabela()

        _ = banco

        self.fazer_backup_inicial()

        self.definir_icone()

        self.criar_interface()

    # ==================================================

    def definir_icone(self):

        try:
            caminho_icone = config.caminho_asset("icone.ico")
            self.iconbitmap(caminho_icone)
        except Exception as e:
            print(f"[ERRO ICONE] {e}")

    # ==================================================

    def fazer_backup_inicial(self):

        try:
            config.fazer_backup_banco()
        except Exception as e:
            print(f"[ERRO BACKUP] {e}")

    # ==================================================

    def criar_interface(self):

        self.menu = ctk.CTkFrame(
            self,
            width=250,
            corner_radius=20,
            fg_color=tema.COR_MENU      # ALTERADO
        )

        self.menu.pack(
            side="left",
            fill="y",
            padx=15,
            pady=15
        )

        self.menu.pack_propagate(False)

        self.mostrar_logo_menu()

        self.definicao_botoes = [

            ("dashboard", "🏠 Dashboard", self.abrir_dashboard),
            ("produtos", "🍔 Produtos", self.abrir_produtos),
            ("clientes", "👥 Clientes", self.abrir_clientes),
            ("pedidos", "🛒 Pedidos", self.abrir_pedidos),
            ("caixa", "💰 Caixa", self.abrir_caixa),
            ("relatorios", "📊 Relatórios", self.abrir_relatorios),
            ("configuracoes", "⚙ Configurações", self.abrir_configuracoes)

        ]

        self.botoes = {}

        for chave, texto, comando in self.definicao_botoes:

            botao = ctk.CTkButton(
                self.menu,
                text=texto,
                height=52,
                corner_radius=16,
                font=("Segoe UI", 15, "bold"),
                fg_color="transparent",
                hover_color=tema.COR_LARANJA_CLARO,
                text_color=tema.COR_TEXTO,      # ALTERADO
                command=lambda c=comando, k=chave: self.navegar(k, c)
            )

            botao.pack(
                fill="x",
                padx=15,
                pady=6
            )

            self.botoes[chave] = botao

        self.area = ctk.CTkFrame(
            self,
            corner_radius=20,
            fg_color=tema.COR_CREME
        )

        self.area.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(0,15),
            pady=15
        )

        self.navegar("dashboard", self.abrir_dashboard)

    # ==================================================

    def navegar(self, chave, comando):

        for k, botao in self.botoes.items():

            if k == chave:
                botao.configure(
                    fg_color=tema.COR_LARANJA,
                    hover_color=tema.COR_LARANJA,
                    text_color=tema.COR_BRANCO
                )
            else:
                botao.configure(
                    fg_color="transparent",
                    text_color=tema.COR_TEXTO     # ALTERADO
                )

        comando()

    # ==================================================

    def mostrar_logo_menu(self):

        caminho_logo = config.caminho_asset("logo_menu.png")

        try:

            imagem_pil = Image.open(caminho_logo)

            largura, altura = imagem_pil.size
            proporcao = altura / largura

            largura_exibida = 170
            altura_exibida = int(largura_exibida * proporcao)

            logo_ctk = ctk.CTkImage(
                light_image=imagem_pil,
                dark_image=imagem_pil,
                size=(largura_exibida, altura_exibida)
            )

            ctk.CTkLabel(
                self.menu,
                image=logo_ctk,
                text=""
            ).pack(pady=(25, 20))

        except Exception:

            ctk.CTkLabel(
                self.menu,
                text="LOS MANAGER",
                font=("Arial", 26, "bold"),
                text_color=tema.COR_TEXTO
            ).pack(pady=(30, 25))

    # ==================================================

    def limpar_area(self):

        for widget in self.area.winfo_children():
            widget.destroy()

    # ==================================================

    def abrir_dashboard(self):

        self.limpar_area()
        Dashboard(self.area)

    # ==================================================

    def abrir_produtos(self):

        self.limpar_area()
        Produtos(self.area)

    # ==================================================

    def abrir_clientes(self):

        self.limpar_area()
        Clientes(self.area)

    # ==================================================

    def abrir_pedidos(self):

        self.limpar_area()
        Pedidos(self.area)

    # ==================================================

    def abrir_relatorios(self):

        self.limpar_area()
        Relatorios(self.area)

    # ==================================================

    def abrir_caixa(self):

        self.limpar_area()
        Caixa(self.area)

    # ==================================================

    def abrir_configuracoes(self):

        self.limpar_area()
        Configuracoes(self.area)

    # ==================================================

    def em_desenvolvimento(self):

        self.limpar_area()

        frame = ctk.CTkFrame(self.area)
        frame.pack(expand=True)

        ctk.CTkLabel(
            frame,
            text="🚧",
            font=("Arial", 60)
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            frame,
            text="Módulo em desenvolvimento",
            font=("Arial", 28, "bold")
        ).pack()

        ctk.CTkLabel(
            frame,
            text="Esta funcionalidade será adicionada nas próximas versões.",
            font=("Arial", 16)
        ).pack(pady=10)


if __name__ == "__main__":
    app = LosManager()
    app.mainloop()