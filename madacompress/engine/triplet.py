from typing import Any, Optional, Tuple

class LZ77Triplet:
    __slots__ = ('offset', 'length', 'next_symbol')

    def __init__(self, offset: int, length: int, next_symbol: Any=None):
        if offset < 0:
            raise ValueError(f"L'offset ne peut pas être négatif : {offset}")
        if length < 0:
            raise ValueError(f'La longueur ne peut pas être négative : {length}')
        self.offset = int(offset)
        self.length = int(length)
        self.next_symbol = next_symbol

    def to_tuple(self) -> Tuple[int, int, Any]:
        return (self.offset, self.length, self.next_symbol)

    def explain(self) -> str:
        char_repr = self._format_symbol(self.next_symbol)
        if self.length == 0:
            return f"Aucune correspondance trouvée dans le tampon d'historique. Émission du caractère littéral {char_repr} (offset=0, longueur=0)."
        overlap_note = ' (avec chevauchement / répétition périodique)' if self.length > self.offset else ''
        return f"Correspondance de {self.length} caractère(s){overlap_note} trouvée à {self.offset} position(s) en arrière dans l'historique, suivie du caractère littéral {char_repr}."

    def _format_symbol(self, sym: Any) -> str:
        if sym is None:
            return '<Fin de flux (EOF)>'
        if isinstance(sym, int):
            if 32 <= sym <= 126:
                return f"'{chr(sym)}' (0x{sym:02X})"
            return f'0x{sym:02X}'
        if isinstance(sym, str):
            return f"'{sym}'"
        return repr(sym)

    def __repr__(self) -> str:
        sym_str = 'None' if self.next_symbol is None else repr(self.next_symbol)
        return f'LZ77Triplet(offset={self.offset}, length={self.length}, next_symbol={sym_str})'

    def __str__(self) -> str:
        sym_str = '' if self.next_symbol is None else str(self.next_symbol)
        if isinstance(self.next_symbol, str):
            return f'({self.offset}, {self.length}, {self.next_symbol})'
        elif isinstance(self.next_symbol, int):
            if 32 <= self.next_symbol <= 126:
                return f"({self.offset}, {self.length}, '{chr(self.next_symbol)}')"
            return f'({self.offset}, {self.length}, 0x{self.next_symbol:02X})'
        return f'({self.offset}, {self.length}, {sym_str})'

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, LZ77Triplet):
            return self.offset == other.offset and self.length == other.length and (self.next_symbol == other.next_symbol)
        if isinstance(other, tuple) and len(other) == 3:
            return (self.offset, self.length, self.next_symbol) == other
        return False

    def __hash__(self) -> int:
        return hash((self.offset, self.length, self.next_symbol))
