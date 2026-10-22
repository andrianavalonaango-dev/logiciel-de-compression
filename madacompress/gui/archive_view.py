import os
import threading
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk
from ..format.file_manager import FileManager
from ..format.mdc_format import MDCError
from ..engine.lz77 import LZ77Engine
from . import theme

def format_size(size_bytes: int) -> str:
    for unit in ['octets', 'Ko', 'Mo', 'Go']:
        if size_bytes < 1024.0:
            return f'{size_bytes:.2f} {unit}' if unit != 'octets' else f'{size_bytes} {unit}'
        size_bytes /= 1024.0
    return f'{size_bytes:.2f} To'

class ArchiveView(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.mode = 'compress'
        self._is_working = False
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        title_label = ctk.CTkLabel(self, text="Opérations d'Archivage MadaCompress", font=theme.TITLE_FONT)
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky='w')
        subtitle = ctk.CTkLabel(self, text="Compressez n'importe quel fichier au format propriétaire sécurisé .mdc ou décompressez vos archives.", font=theme.BODY_FONT, text_color='gray')
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 15), sticky='w')
        self.mode_selector = ctk.CTkSegmentedButton(self, values=['Compresser un fichier', 'Décompresser un fichier'], command=self._on_mode_change, font=theme.SUBHEADER_FONT, height=40)
        self.mode_selector.set('Compresser un fichier')
        self.mode_selector.grid(row=2, column=0, padx=20, pady=(0, 20), sticky='ew')
        form_card = ctk.CTkFrame(self, corner_radius=10)
        form_card.grid(row=3, column=0, padx=20, pady=(0, 15), sticky='ew')
        form_card.grid_columnconfigure(1, weight=1)
        self.src_label = ctk.CTkLabel(form_card, text='Fichier source :', font=theme.SUBHEADER_FONT)
        self.src_label.grid(row=0, column=0, padx=(15, 10), pady=12, sticky='w')
        self.src_entry = ctk.CTkEntry(form_card, placeholder_text='Sélectionnez le fichier à traiter...', font=theme.BODY_FONT, height=36)
        self.src_entry.grid(row=0, column=1, padx=(0, 10), pady=12, sticky='ew')
        self.browse_src_btn = ctk.CTkButton(form_card, text='Parcourir...', width=110, height=36, command=self._browse_source, font=theme.BODY_FONT)
        self.browse_src_btn.grid(row=0, column=2, padx=(0, 15), pady=12)
        self.dst_label = ctk.CTkLabel(form_card, text='Destination :', font=theme.SUBHEADER_FONT)
        self.dst_label.grid(row=1, column=0, padx=(15, 10), pady=(0, 12), sticky='w')
        self.dst_entry = ctk.CTkEntry(form_card, placeholder_text='Chemin automatique ou personnalisé...', font=theme.BODY_FONT, height=36)
        self.dst_entry.grid(row=1, column=1, padx=(0, 10), pady=(0, 12), sticky='ew')
        self.browse_dst_btn = ctk.CTkButton(form_card, text='Changer...', width=110, height=36, command=self._browse_destination, font=theme.BODY_FONT)
        self.browse_dst_btn.grid(row=1, column=2, padx=(0, 15), pady=(0, 12))
        self.params_frame = ctk.CTkFrame(form_card, fg_color='transparent')
        self.params_frame.grid(row=2, column=0, columnspan=3, padx=15, pady=(0, 12), sticky='ew')
        self.params_frame.grid_columnconfigure((1, 3), weight=1)
        search_label = ctk.CTkLabel(self.params_frame, text='Tampon de recherche :', font=theme.BODY_FONT)
        search_label.grid(row=0, column=0, padx=(0, 5), sticky='w')
        self.search_combo = ctk.CTkComboBox(self.params_frame, values=['4096 octets (Recommandé)', '2048 octets', '1024 octets', '7 octets (Exemple cours)'], font=theme.BODY_FONT, height=32)
        self.search_combo.set('4096 octets (Recommandé)')
        self.search_combo.grid(row=0, column=1, padx=(0, 15), sticky='ew')
        lookahead_label = ctk.CTkLabel(self.params_frame, text="Tampon d'entrée :", font=theme.BODY_FONT)
        lookahead_label.grid(row=0, column=2, padx=(0, 5), sticky='w')
        self.lookahead_combo = ctk.CTkComboBox(self.params_frame, values=['256 octets (Recommandé)', '128 octets', '64 octets', '6 octets (Exemple cours)'], font=theme.BODY_FONT, height=32)
        self.lookahead_combo.set('256 octets (Recommandé)')
        self.lookahead_combo.grid(row=0, column=3, sticky='ew')
        self.action_btn = ctk.CTkButton(self, text='Compresser en .mdc', font=theme.HEADER_FONT, height=46, fg_color=theme.PRIMARY_COLOR, hover_color=theme.PRIMARY_HOVER, command=self._start_action)
        self.action_btn.grid(row=4, column=0, padx=20, pady=(0, 15), sticky='ew')
        self.progress_bar = ctk.CTkProgressBar(self, height=12)
        self.progress_bar.set(0.0)
        self.progress_bar.grid(row=5, column=0, padx=20, pady=(0, 5), sticky='ew')
        self.status_label = ctk.CTkLabel(self, text='Prêt à traiter vos fichiers.', font=theme.BODY_FONT, text_color='gray')
        self.status_label.grid(row=6, column=0, padx=20, pady=(0, 15), sticky='w')
        self.stats_card = ctk.CTkFrame(self, corner_radius=10)
        self.stats_card.grid(row=7, column=0, padx=20, pady=(0, 20), sticky='ew')
        self.stats_card.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.stat_orig = self._create_stat_box(self.stats_card, 0, 'Taille initiale', '--')
        self.stat_final = self._create_stat_box(self.stats_card, 1, 'Taille résultante', '--')
        self.stat_ratio = self._create_stat_box(self.stats_card, 2, 'Taux de compression', '--')
        self.stat_gain = self._create_stat_box(self.stats_card, 3, "Gain d'espace", '--')

    def _create_stat_box(self, parent, col, title, initial_val):
        frame = ctk.CTkFrame(parent, fg_color='transparent')
        frame.grid(row=0, column=col, padx=10, pady=12)
        lbl_t = ctk.CTkLabel(frame, text=title, font=theme.SMALL_FONT, text_color='gray')
        lbl_t.pack()
        lbl_v = ctk.CTkLabel(frame, text=initial_val, font=theme.SUBHEADER_FONT)
        lbl_v.pack()
        return lbl_v

    def _on_mode_change(self, value):
        if value == 'Compresser un fichier':
            self.mode = 'compress'
            self.action_btn.configure(text='Compresser en .mdc', fg_color=theme.PRIMARY_COLOR)
            self.params_frame.grid()
        else:
            self.mode = 'decompress'
            self.action_btn.configure(text="Décompresser l'archive .mdc", fg_color=theme.SUCCESS_COLOR)
            self.params_frame.grid_remove()
        self._auto_update_destination()

    def _browse_source(self):
        if self.mode == 'compress':
            filename = filedialog.askopenfilename(title='Choisir le fichier à compresser', filetypes=[('Tous les fichiers', '*.*')])
        else:
            filename = filedialog.askopenfilename(title="Choisir l'archive MadaCompress (.mdc)", filetypes=[('Archives MadaCompress (*.mdc)', '*.mdc'), ('Tous les fichiers', '*.*')])
        if filename:
            self.src_entry.delete(0, 'end')
            self.src_entry.insert(0, filename)
            self._auto_update_destination()

    def _browse_destination(self):
        src_text = self.src_entry.get().strip()
        initial_dir = os.path.dirname(src_text) if src_text else None
        if self.mode == 'compress':
            filename = filedialog.asksaveasfilename(title="Enregistrer l'archive compressée sous", defaultextension='.mdc', filetypes=[('Archive MadaCompress (*.mdc)', '*.mdc')], initialdir=initial_dir)
        else:
            folder = filedialog.askdirectory(title='Choisir le dossier de décompression', initialdir=initial_dir)
            filename = folder
        if filename:
            self.dst_entry.delete(0, 'end')
            self.dst_entry.insert(0, filename)

    def _auto_update_destination(self):
        src_path = self.src_entry.get().strip()
        if not src_path:
            return
        p = Path(src_path)
        if self.mode == 'compress':
            suggested = f'{src_path}.mdc'
        elif p.suffix.lower() == '.mdc':
            suggested = str(p.with_suffix(''))
        else:
            suggested = str(p.parent / f'{p.stem}_restaure{p.suffix}')
        self.dst_entry.delete(0, 'end')
        self.dst_entry.insert(0, suggested)

    def _parse_buffer_sizes(self):
        search_val = self.search_combo.get()
        lookahead_val = self.lookahead_combo.get()
        s_size = 4096
        if '7' in search_val:
            s_size = 7
        elif '2048' in search_val:
            s_size = 2048
        elif '1024' in search_val:
            s_size = 1024
        l_size = 256
        if '6' in lookahead_val:
            l_size = 6
        elif '128' in lookahead_val:
            l_size = 128
        elif '64' in lookahead_val:
            l_size = 64
        return (s_size, l_size)

    def _start_action(self):
        if self._is_working:
            return
        src = self.src_entry.get().strip()
        dst = self.dst_entry.get().strip()
        if not src or not os.path.isfile(src):
            self.status_label.configure(text='Erreur : veuillez sélectionner un fichier source valide.', text_color=theme.DANGER_COLOR)
            return
        self._is_working = True
        self.action_btn.configure(state='disabled')
        self.progress_bar.set(0.0)
        threading.Thread(target=self._worker, args=(src, dst if dst else None), daemon=True).start()

    def _worker(self, src: str, dst: str):
        try:
            if self.mode == 'compress':
                self._update_status('Compression LZ77 en cours...', 'gray')
                s_size, l_size = self._parse_buffer_sizes()

                def on_progress(current, total):
                    pct = current / total if total > 0 else 1.0
                    self.after(0, lambda: self.progress_bar.set(pct))
                    self.after(0, lambda: self.status_label.configure(text=f'Compression : {int(pct * 100)}% ({format_size(current)} / {format_size(total)})'))
                stats = FileManager.compress_file(source_path=src, dest_path=dst, search_buffer_size=s_size, lookahead_buffer_size=l_size, progress_callback=on_progress)
                self.after(0, lambda: self._on_success_compress(stats))
            else:
                self._update_status('Décompression LZ77 et vérification CRC32...', 'gray')

                def on_progress(current, total):
                    pct = current / total if total > 0 else 1.0
                    self.after(0, lambda: self.progress_bar.set(pct))
                    self.after(0, lambda: self.status_label.configure(text=f'Décompression : {int(pct * 100)}% ({current} / {total} triplets)'))
                stats = FileManager.decompress_file(source_path=src, dest_path=dst, progress_callback=on_progress)
                self.after(0, lambda: self._on_success_decompress(stats))
        except Exception as exc:
            self.after(0, lambda: self._on_error(str(exc)))
        finally:
            self._is_working = False
            self.after(0, lambda: self.action_btn.configure(state='normal'))

    def _on_success_compress(self, stats):
        self.progress_bar.set(1.0)
        self.status_label.configure(text=f'Succès ! Fichier compressé enregistré sous : {os.path.basename(stats['dest_path'])}', text_color=theme.SUCCESS_COLOR)
        self.stat_orig.configure(text=format_size(stats['source_size']))
        self.stat_final.configure(text=format_size(stats['compressed_size']))
        self.stat_ratio.configure(text=f'{stats['compression_ratio']:.4f}')
        self.stat_gain.configure(text=f'{stats['saving_percent']}%')

    def _on_success_decompress(self, stats):
        self.progress_bar.set(1.0)
        self.status_label.configure(text=f'Succès ! Archive décompressée avec succès (Intégrité CRC32 validée).', text_color=theme.SUCCESS_COLOR)
        self.stat_orig.configure(text=format_size(os.path.getsize(stats['source_path'])))
        self.stat_final.configure(text=format_size(stats['restored_size']))
        self.stat_ratio.configure(text='1.0000')
        self.stat_gain.configure(text='Intact (100%)')

    def _on_error(self, error_msg):
        self.progress_bar.set(0.0)
        self.status_label.configure(text=f'Erreur : {error_msg}', text_color=theme.DANGER_COLOR)

    def _update_status(self, text, color):
        self.after(0, lambda: self.status_label.configure(text=text, text_color=color))
