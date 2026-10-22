import customtkinter as ctk
from . import theme
from .archive_view import ArchiveView
from .demo_view import DemoView
from .about_view import AboutView

class MadaCompressApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title('MadaCompress — Logiciel de Compression & Décompression LZ77')
        self.geometry('1020x720')
        self.minsize(920, 640)
        ctk.set_appearance_mode('Dark')
        ctk.set_default_color_theme('blue')
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_views()
        self._select_view('archive')

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky='nsew')
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text='🗜️ MadaCompress', font=(theme.FONT_FAMILY, 20, 'bold'), text_color='#3498db')
        self.logo_label.grid(row=0, column=0, padx=20, pady=(25, 5))
        self.version_label = ctk.CTkLabel(self.sidebar_frame, text='Édition Universitaire 2026', font=theme.SMALL_FONT, text_color='gray')
        self.version_label.grid(row=1, column=0, padx=20, pady=(0, 25))
        self.nav_archive_btn = ctk.CTkButton(self.sidebar_frame, text='📦  Archivage (.mdc)', font=theme.SUBHEADER_FONT, height=40, anchor='w', fg_color='transparent', text_color=('gray10', 'gray90'), hover_color=('gray70', 'gray30'), command=lambda: self._select_view('archive'))
        self.nav_archive_btn.grid(row=2, column=0, padx=15, pady=5, sticky='ew')
        self.nav_demo_btn = ctk.CTkButton(self.sidebar_frame, text='🎓  Comprendre LZ77', font=theme.SUBHEADER_FONT, height=40, anchor='w', fg_color='transparent', text_color=('gray10', 'gray90'), hover_color=('gray70', 'gray30'), command=lambda: self._select_view('demo'))
        self.nav_demo_btn.grid(row=3, column=0, padx=15, pady=5, sticky='ew')
        self.nav_about_btn = ctk.CTkButton(self.sidebar_frame, text='ℹ️  À Propos & Théorie', font=theme.SUBHEADER_FONT, height=40, anchor='w', fg_color='transparent', text_color=('gray10', 'gray90'), hover_color=('gray70', 'gray30'), command=lambda: self._select_view('about'))
        self.nav_about_btn.grid(row=4, column=0, padx=15, pady=5, sticky='ew')
        theme_label = ctk.CTkLabel(self.sidebar_frame, text='Apparence :', font=theme.SMALL_FONT, text_color='gray')
        theme_label.grid(row=6, column=0, padx=20, pady=(10, 0), sticky='w')
        self.theme_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=['Dark', 'Light', 'System'], command=self._change_appearance_mode, font=theme.BODY_FONT, height=30)
        self.theme_menu.grid(row=7, column=0, padx=15, pady=(0, 20), sticky='ew')

    def _build_views(self):
        self.views = {'archive': ArchiveView(self, corner_radius=0, fg_color='transparent'), 'demo': DemoView(self, corner_radius=0, fg_color='transparent'), 'about': AboutView(self, corner_radius=0, fg_color='transparent')}

    def _select_view(self, view_name: str):
        buttons = {'archive': self.nav_archive_btn, 'demo': self.nav_demo_btn, 'about': self.nav_about_btn}
        for name, btn in buttons.items():
            if name == view_name:
                btn.configure(fg_color=theme.PRIMARY_COLOR, text_color='white')
            else:
                btn.configure(fg_color='transparent', text_color=('gray10', 'gray90'))
        for name, view in self.views.items():
            if name == view_name:
                view.grid(row=0, column=1, sticky='nsew')
            else:
                view.grid_forget()

    def _change_appearance_mode(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)

def launch_gui():
    app = MadaCompressApp()
    app.mainloop()
if __name__ == '__main__':
    launch_gui()
