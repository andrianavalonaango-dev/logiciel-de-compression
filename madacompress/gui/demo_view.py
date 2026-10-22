import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from ..engine.lz77 import LZ77Engine
from . import theme

class DemoView(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.steps_data = []
        self.current_step_idx = 0
        self.is_auto_playing = False
        self._auto_play_id = None
        self._build_ui()
        self._load_course_example()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        title_label = ctk.CTkLabel(self, text='Comprendre LZ77 — Visualisation Pédagogique', font=theme.TITLE_FONT)
        title_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky='w')
        subtitle = ctk.CTkLabel(self, text="Visualisez l'état dynamique de la fenêtre glissante, des tampons et des triplets calculés en temps réel par le moteur.", font=theme.BODY_FONT, text_color='gray')
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 15), sticky='w')
        config_card = ctk.CTkFrame(self, corner_radius=10)
        config_card.grid(row=2, column=0, padx=20, pady=(0, 15), sticky='ew')
        config_card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(config_card, text='Texte à coder :', font=theme.SUBHEADER_FONT).grid(row=0, column=0, padx=(15, 10), pady=10, sticky='w')
        self.text_entry = ctk.CTkEntry(config_card, placeholder_text='Entrez une chaîne de caractères...', font=theme.MONO_FONT, height=34)
        self.text_entry.grid(row=0, column=1, padx=(0, 10), pady=10, sticky='ew')
        self.course_btn = ctk.CTkButton(config_card, text='Exemple du cours', width=130, height=34, command=self._load_course_example, font=theme.BODY_FONT)
        self.course_btn.grid(row=0, column=2, padx=(0, 15), pady=10)
        params_row = ctk.CTkFrame(config_card, fg_color='transparent')
        params_row.grid(row=1, column=0, columnspan=3, padx=15, pady=(0, 10), sticky='ew')
        ctk.CTkLabel(params_row, text='Tampon Recherche (Search) :', font=theme.BODY_FONT).pack(side='left', padx=(0, 5))
        self.search_entry = ctk.CTkEntry(params_row, width=60, font=theme.MONO_FONT, height=28)
        self.search_entry.insert(0, '7')
        self.search_entry.pack(side='left', padx=(0, 20))
        ctk.CTkLabel(params_row, text='Tampon Entrée (Lookahead) :', font=theme.BODY_FONT).pack(side='left', padx=(0, 5))
        self.lookahead_entry = ctk.CTkEntry(params_row, width=60, font=theme.MONO_FONT, height=28)
        self.lookahead_entry.insert(0, '6')
        self.lookahead_entry.pack(side='left', padx=(0, 20))
        self.run_btn = ctk.CTkButton(params_row, text="Lancer l'analyse", font=theme.SUBHEADER_FONT, height=32, fg_color=theme.PRIMARY_COLOR, hover_color=theme.PRIMARY_HOVER, command=self._calculate_steps)
        self.run_btn.pack(side='right')
        self.stage_card = ctk.CTkFrame(self, corner_radius=10)
        self.stage_card.grid(row=3, column=0, padx=20, pady=(0, 15), sticky='ew')
        self.stage_card.grid_columnconfigure(0, weight=1)
        nav_frame = ctk.CTkFrame(self.stage_card, fg_color='transparent')
        nav_frame.pack(fill='x', padx=15, pady=(12, 10))
        self.first_btn = ctk.CTkButton(nav_frame, text='⏮ Début', width=80, height=30, command=self._go_first)
        self.first_btn.pack(side='left', padx=2)
        self.prev_btn = ctk.CTkButton(nav_frame, text='◀ Précédent', width=90, height=30, command=self._go_prev)
        self.prev_btn.pack(side='left', padx=2)
        self.step_label = ctk.CTkLabel(nav_frame, text='Étape 0 / 0', font=theme.HEADER_FONT, width=140)
        self.step_label.pack(side='left', padx=10)
        self.next_btn = ctk.CTkButton(nav_frame, text='Suivant ▶', width=90, height=30, command=self._go_next)
        self.next_btn.pack(side='left', padx=2)
        self.last_btn = ctk.CTkButton(nav_frame, text='⏭ Fin', width=80, height=30, command=self._go_last)
        self.last_btn.pack(side='left', padx=2)
        self.play_btn = ctk.CTkButton(nav_frame, text='⏵ Lecture auto', width=110, height=30, fg_color=theme.ACCENT_COLOR, command=self._toggle_auto_play)
        self.play_btn.pack(side='right', padx=5)
        buffers_frame = ctk.CTkFrame(self.stage_card, fg_color='transparent')
        buffers_frame.pack(fill='x', padx=15, pady=(0, 10))
        buffers_frame.grid_columnconfigure((0, 1), weight=1)
        sb_box = ctk.CTkFrame(buffers_frame)
        sb_box.grid(row=0, column=0, padx=(0, 8), sticky='ew')
        ctk.CTkLabel(sb_box, text='Tampon de Recherche (Historique)', font=theme.SUBHEADER_FONT, text_color='#3498db').pack(pady=(6, 2))
        self.sb_display = ctk.CTkLabel(sb_box, text='[       ]', font=theme.MONO_FONT_BOLD)
        self.sb_display.pack(pady=(2, 6))
        lb_box = ctk.CTkFrame(buffers_frame)
        lb_box.grid(row=0, column=1, padx=(8, 0), sticky='ew')
        ctk.CTkLabel(lb_box, text="Tampon d'Entrée (Anticipation)", font=theme.SUBHEADER_FONT, text_color='#e67e22').pack(pady=(6, 2))
        self.lb_display = ctk.CTkLabel(lb_box, text='[      ]', font=theme.MONO_FONT_BOLD)
        self.lb_display.pack(pady=(2, 6))
        triplet_card = ctk.CTkFrame(self.stage_card, fg_color=('gray90', 'gray20'), corner_radius=6)
        triplet_card.pack(fill='x', padx=15, pady=(0, 10))
        self.triplet_title = ctk.CTkLabel(triplet_card, text="Triplet produit : (offset=0, longueur=0, caractère='?')", font=theme.HEADER_FONT, text_color=theme.SUCCESS_COLOR)
        self.triplet_title.pack(anchor='w', padx=12, pady=(6, 2))
        self.explanation_label = ctk.CTkLabel(triplet_card, text='Explication didactique du triplet.', font=theme.BODY_FONT, wraplength=700, justify='left')
        self.explanation_label.pack(anchor='w', padx=12, pady=(0, 6))
        decoded_row = ctk.CTkFrame(self.stage_card, fg_color='transparent')
        decoded_row.pack(fill='x', padx=15, pady=(0, 12))
        ctk.CTkLabel(decoded_row, text='Texte décodé à cette étape :', font=theme.SUBHEADER_FONT).pack(side='left', padx=(0, 10))
        self.decoded_display = ctk.CTkLabel(decoded_row, text='--', font=theme.MONO_FONT_BOLD, text_color='#2ecc71')
        self.decoded_display.pack(side='left')
        table_container = ctk.CTkFrame(self, corner_radius=10)
        table_container.grid(row=4, column=0, padx=20, pady=(0, 15), sticky='nsew')
        self.grid_rowconfigure(4, weight=1)
        table_header = ctk.CTkLabel(table_container, text='Tableau Récapitulatif Complet (Conforme au document de cours)', font=theme.SUBHEADER_FONT)
        table_header.pack(anchor='w', padx=15, pady=(8, 4))
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Treeview', background='#2b2b2b', foreground='white', fieldbackground='#2b2b2b', rowheight=24, font=('Consolas', 10))
        style.configure('Treeview.Heading', background='#1f538d', foreground='white', font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#3498db')])
        columns = ('step', 'search_buf', 'lookahead_buf', 'triplet', 'decoded')
        self.tree = ttk.Treeview(table_container, columns=columns, show='headings', height=6)
        self.tree.heading('step', text='Étape')
        self.tree.heading('search_buf', text='Tampon de Recherche')
        self.tree.heading('lookahead_buf', text="Tampon d'Entrée")
        self.tree.heading('triplet', text='Codage (Triplet)')
        self.tree.heading('decoded', text='Résultat du Décodage')
        self.tree.column('step', width=60, anchor='center')
        self.tree.column('search_buf', width=160, anchor='center')
        self.tree.column('lookahead_buf', width=140, anchor='center')
        self.tree.column('triplet', width=120, anchor='center')
        self.tree.column('decoded', width=220, anchor='w')
        tree_scroll = ttk.Scrollbar(table_container, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side='left', fill='both', expand=True, padx=(15, 0), pady=(0, 10))
        tree_scroll.pack(side='right', fill='y', padx=(0, 15), pady=(0, 10))
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

    def _load_course_example(self):
        self.text_entry.delete(0, 'end')
        self.text_entry.insert(0, 'CABRACADABRARRARRAD')
        self.search_entry.delete(0, 'end')
        self.search_entry.insert(0, '7')
        self.lookahead_entry.delete(0, 'end')
        self.lookahead_entry.insert(0, '6')
        self._calculate_steps()

    def _calculate_steps(self):
        self._stop_auto_play()
        text = self.text_entry.get().strip()
        if not text:
            return
        try:
            s_size = int(self.search_entry.get().strip())
            l_size = int(self.lookahead_entry.get().strip())
        except ValueError:
            s_size, l_size = (7, 6)
        engine = LZ77Engine(search_buffer_size=s_size, lookahead_buffer_size=l_size)
        self.steps_data = list(engine.step_by_step_encode(text))
        for row in self.tree.get_children():
            self.tree.delete(row)
        for s in self.steps_data:
            self.tree.insert('', 'end', values=(s['step'], f'[{s['search_buffer']:>{s_size}}]', f'[{s['lookahead_buffer']:<{l_size}}]', str(s['triplet']), s['decoded_so_far']))
        self.current_step_idx = 0
        self._render_current_step()

    def _render_current_step(self):
        total = len(self.steps_data)
        if total == 0:
            self.step_label.configure(text='Étape 0 / 0')
            self.sb_display.configure(text='[       ]')
            self.lb_display.configure(text='[      ]')
            self.triplet_title.configure(text='Aucune étape')
            self.explanation_label.configure(text='')
            self.decoded_display.configure(text='--')
            return
        step = self.steps_data[self.current_step_idx]
        self.step_label.configure(text=f'Étape {step['step']} / {total}')
        s_size = int(self.search_entry.get().strip() or '7')
        l_size = int(self.lookahead_entry.get().strip() or '6')
        sb_txt = step['search_buffer']
        lb_txt = step['lookahead_buffer']
        self.sb_display.configure(text=f'[{sb_txt:>{s_size}}]')
        self.lb_display.configure(text=f'[{lb_txt:<{l_size}}]')
        t = step['triplet']
        self.triplet_title.configure(text=f'Triplet émis : (offset={t.offset}, longueur={t.length}, symbole={t._format_symbol(t.next_symbol)})')
        self.explanation_label.configure(text=step['explanation'])
        self.decoded_display.configure(text=step['decoded_so_far'])
        items = self.tree.get_children()
        if 0 <= self.current_step_idx < len(items):
            self.tree.selection_set(items[self.current_step_idx])
            self.tree.see(items[self.current_step_idx])

    def _go_prev(self):
        if self.current_step_idx > 0:
            self.current_step_idx -= 1
            self._render_current_step()

    def _go_next(self):
        if self.current_step_idx < len(self.steps_data) - 1:
            self.current_step_idx += 1
            self._render_current_step()
        else:
            self._stop_auto_play()

    def _go_first(self):
        self.current_step_idx = 0
        self._render_current_step()

    def _go_last(self):
        if self.steps_data:
            self.current_step_idx = len(self.steps_data) - 1
            self._render_current_step()

    def _toggle_auto_play(self):
        if self.is_auto_playing:
            self._stop_auto_play()
        else:
            self.is_auto_playing = True
            self.play_btn.configure(text='⏸ Pause', fg_color=theme.WARNING_COLOR)
            self._auto_play_tick()

    def _auto_play_tick(self):
        if not self.is_auto_playing:
            return
        if self.current_step_idx < len(self.steps_data) - 1:
            self.current_step_idx += 1
            self._render_current_step()
            self._auto_play_id = self.after(1000, self._auto_play_tick)
        else:
            self._stop_auto_play()

    def _stop_auto_play(self):
        self.is_auto_playing = False
        self.play_btn.configure(text='⏵ Lecture auto', fg_color=theme.ACCENT_COLOR)
        if self._auto_play_id:
            self.after_cancel(self._auto_play_id)
            self._auto_play_id = None

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            idx = self.tree.index(selected[0])
            self.current_step_idx = idx
            self._render_current_step()
