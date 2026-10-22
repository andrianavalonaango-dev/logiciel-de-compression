import customtkinter as ctk
from . import theme

class AboutView(ctk.CTkScrollableFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._build_ui()

    def _build_ui(self):
        title_label = ctk.CTkLabel(self, text='MadaCompress — À Propos & Principes Théoriques', font=theme.TITLE_FONT)
        title_label.pack(anchor='w', padx=20, pady=(20, 5))
        version_badge = ctk.CTkLabel(self, text="Version 1.0.0 — Format propriétaire .mdc — Conforme au cours d'algorithmique", font=theme.BODY_FONT, text_color='gray')
        version_badge.pack(anchor='w', padx=20, pady=(0, 20))
        univ_card = self._create_card('Contexte Universitaire & Objectifs')
        univ_text = "Ce logiciel a été développé dans le cadre d'un projet universitaire portant sur la compression et décompression sans perte de données.\n\n• Date de livraison : 24 octobre 2026 à 23 h 59\n• Inspiration ergonomique : WinRAR, 7-Zip, HuffPressor\n• Objectif pédagogique : Fournir une implémentation claire, modulaire, orientée objet, directement démontrable et modifiable en direct devant le professeur."
        ctk.CTkLabel(univ_card, text=univ_text, font=theme.BODY_FONT, justify='left').pack(anchor='w', padx=15, pady=10)
        theory_card = self._create_card('Algorithme LZ77 (Lempel-Ziv 1977)')
        theory_text = "L'algorithme LZ77 repose sur le principe d'un dictionnaire dynamique basé sur une fenêtre glissante. Plutôt que d'émettre des symboles répétés, il émet des pointeurs vers leurs apparitions passées.\n\nComposants de la fenêtre glissante :\n1. Tampon de recherche (Search Buffer) : Contient l'historique des derniers octets décodés.\n2. Tampon d'entrée (Lookahead Buffer) : Contient les prochains caractères à compresser.\n\nConvention du triplet (offset, longueur, caractère_suivant) :\n• offset : Distance en arrière depuis la position courante dans l'historique (1-indexé, 0 si aucun match).\n• longueur : Nombre de caractères correspondants consécutifs.\n• caractère_suivant : Le premier caractère littéral qui suit la correspondance.\n\nGestion du chevauchement (Overlapping) :\nLorsque la longueur dépasse l'offset (longueur > offset), la référence se répète périodiquement. Cette propriété permet de compresser de très longues suites de répétitions (ex: 50 fois 'A') en un seul triplet compact, comme illustré dans l'exemple du cours à l'étape finale."
        ctk.CTkLabel(theory_card, text=theory_text, font=theme.BODY_FONT, justify='left').pack(anchor='w', padx=15, pady=10)
        format_card = self._create_card('Format Binaire Propriétaire (.mdc)')
        format_text = "Chaque archive générée possède une extension .mdc et respecte une structure binaire stricte :\n• Signature Magique (4 octets) : b'MDC1'\n• Version du format (2 octets) : uint16 (1)\n• Identifiant d'algorithme (1 octet) : 0x01 (LZ77)\n• Tailles des tampons (4 octets) : Search Size & Lookahead Size\n• Taille originale décompressée (8 octets) : uint64 (protection anti-dépassement)\n• Somme de contrôle CRC32 (4 octets) : Contrôle d'intégrité bit-à-bit\n• Corps des triplets : Packés de manière binaire (6 octets par triplet)."
        ctk.CTkLabel(format_card, text=format_text, font=theme.BODY_FONT, justify='left').pack(anchor='w', padx=15, pady=10)
        math_card = self._create_card('Formules & Métriques de Performance')
        math_text = "• Taux de compression : T = Taille_Compressée / Taille_Originale\n• Pourcentage de gain d'espace : Gain(%) = (1 - T) × 100%\n• Un gain positif (> 0%) indique une réduction effective de la taille du fichier."
        ctk.CTkLabel(math_card, text=math_text, font=theme.BODY_FONT, justify='left').pack(anchor='w', padx=15, pady=10)
        ref_card = self._create_card('Références Techniques & Attributions')
        ref_text = "Le projet s'inspire des travaux techniques de référence suivants :\n\n1. lz77-algorithm (wolfie-things)\n   Dépôt : https://github.com/wolfie-things/lz77-algorithm\n   Licence : Open Education / MIT\n   Rôle : Référence pour la structure des tampons et les options de ligne de commande.\n\n2. HuffPressor (Varaxion)\n   Dépôt : https://github.com/Varaxion/HuffPressor\n   Licence : GPL-3.0 / Open Source\n   Rôle : Référence d'inspiration pour l'ergonomie sobre et moderne d'un utilitaire d'archivage.\n\n3. Documents de Cours Universitaires\n   Exemples canoniques : 'CABRACADABRARRARRAD' et 'ABBBTTAYFGCABRYUIUUIACADBRARRARRAD'.\n\nTous les modules de MadaCompress ont été intégralement réécrits et structurés en Python 3 pour garantir l'originalité du travail et la totale maîtrise lors de la soutenance."
        ctk.CTkLabel(ref_card, text=ref_text, font=theme.BODY_FONT, justify='left').pack(anchor='w', padx=15, pady=10)

    def _create_card(self, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self, corner_radius=10)
        card.pack(fill='x', padx=20, pady=(0, 15))
        lbl = ctk.CTkLabel(card, text=title, font=theme.SUBHEADER_FONT, text_color=theme.ACCENT_COLOR)
        lbl.pack(anchor='w', padx=15, pady=(10, 0))
        return card
