"""
=================================================================
SELETOR DE DATA (calendário em popup)
=================================================================
Feito com CustomTkinter puro + o módulo `calendar` da biblioteca
padrão, de propósito: uma biblioteca de terceiro (tkcalendar) teria
que ser instalada em cada máquina e declarada como hidden import no
PyInstaller, e o projeto evita dependência nova só pra isso.

Uso:

    calendario.escolher_data(
        self,                       # widget de origem (qualquer um)
        aoescolher=minha_funcao,    # recebe uma string "dd/mm/aaaa"
        data_inicial="05/08/2026"   # opcional
    )
=================================================================
"""

import calendar
from datetime import date, datetime

import customtkinter as ctk

from utils import tema


MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# Cabeçalho começando no domingo (como todo calendário de parede daqui)
DIAS_SEMANA = ["D", "S", "T", "Q", "Q", "S", "S"]

FORMATO = "%d/%m/%Y"


class JanelaCalendario(ctk.CTkToplevel):

    def __init__(self, master, ao_escolher, data_inicial=None):
        super().__init__(master.winfo_toplevel())

        self.ao_escolher = ao_escolher

        self.title("Escolher data")
        self.transient(master.winfo_toplevel())
        self.resizable(False, False)

        hoje = date.today()

        if data_inicial:
            try:
                inicial = datetime.strptime(data_inicial, FORMATO).date()
            except (ValueError, TypeError):
                inicial = hoje
        else:
            inicial = hoje

        self.ano = inicial.year
        self.mes = inicial.month
        self.selecionada = inicial

        self.montar_cabecalho()

        self.grade = ctk.CTkFrame(self, fg_color="transparent")
        self.grade.pack(padx=12, pady=(0, 8))

        self.montar_rodape()

        self.desenhar_mes()

        # O tamanho só é aplicado depois que o Tk processa os `after`
        # internos do CustomTkinter (rotina de cor da barra de título no
        # Windows) — chamando geometry() direto aqui a janela abre
        # minúscula. Mesmo motivo dos outros popups do sistema.
        self.after(60, self._ajustar_tamanho)

        self.grab_set()

    # ======================================================

    def _ajustar_tamanho(self):

        self.update_idletasks()

        largura = max(self.winfo_reqwidth(), 320)
        altura = max(self.winfo_reqheight(), 330)

        self.geometry(f"{largura}x{altura}")
        self.minsize(largura, altura)

    # ======================================================

    def montar_cabecalho(self):

        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", padx=12, pady=(12, 8))

        ctk.CTkButton(
            cabecalho,
            text="◀",
            width=38,
            command=self.mes_anterior
        ).pack(side="left")

        self.lbl_mes = ctk.CTkLabel(
            cabecalho,
            text="",
            font=("Arial", 15, "bold")
        )
        self.lbl_mes.pack(side="left", expand=True)

        ctk.CTkButton(
            cabecalho,
            text="▶",
            width=38,
            command=self.mes_seguinte
        ).pack(side="right")

    # ======================================================

    def montar_rodape(self):

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkButton(
            rodape,
            text="Hoje",
            width=90,
            command=lambda: self.escolher(date.today())
        ).pack(side="left")

        ctk.CTkButton(
            rodape,
            text="Cancelar",
            width=90,
            fg_color="#777",
            hover_color="#555",
            command=self.destroy
        ).pack(side="right")

    # ======================================================

    def mes_anterior(self):

        self.mes -= 1

        if self.mes < 1:
            self.mes = 12
            self.ano -= 1

        self.desenhar_mes()

    def mes_seguinte(self):

        self.mes += 1

        if self.mes > 12:
            self.mes = 1
            self.ano += 1

        self.desenhar_mes()

    # ======================================================

    def desenhar_mes(self):

        for widget in self.grade.winfo_children():
            widget.destroy()

        self.lbl_mes.configure(text=f"{MESES[self.mes - 1]} {self.ano}")

        for coluna, nome in enumerate(DIAS_SEMANA):
            ctk.CTkLabel(
                self.grade,
                text=nome,
                width=38,
                font=("Arial", 12, "bold"),
                text_color="gray"
            ).grid(row=0, column=coluna, padx=1, pady=(0, 4))

        hoje = date.today()

        # Semanas começando no domingo, igual ao cabeçalho acima
        semanas = calendar.Calendar(firstweekday=6).monthdayscalendar(self.ano, self.mes)

        for linha, semana in enumerate(semanas, start=1):

            for coluna, dia in enumerate(semana):

                if dia == 0:
                    continue

                data_dia = date(self.ano, self.mes, dia)

                if data_dia == self.selecionada:
                    cor, cor_hover = tema.COR_LARANJA, tema.COR_LARANJA
                elif data_dia == hoje:
                    cor, cor_hover = "#0ea5e9", "#0284c7"
                else:
                    cor, cor_hover = "transparent", tema.COR_LARANJA_CLARO

                ctk.CTkButton(
                    self.grade,
                    text=str(dia),
                    width=38,
                    height=30,
                    fg_color=cor,
                    hover_color=cor_hover,
                    text_color=tema.COR_BRANCO if cor != "transparent" else tema.COR_TEXTO,
                    command=lambda d=data_dia: self.escolher(d)
                ).grid(row=linha, column=coluna, padx=1, pady=1)

    # ======================================================

    def escolher(self, data_escolhida):

        self.ao_escolher(data_escolhida.strftime(FORMATO))
        self.destroy()


# =================================================================

def escolher_data(master, ao_escolher, data_inicial=None):
    """Abre o calendário. `ao_escolher` recebe a data como string
    no formato "dd/mm/aaaa" (o mesmo usado no banco)."""

    JanelaCalendario(master, ao_escolher, data_inicial)
