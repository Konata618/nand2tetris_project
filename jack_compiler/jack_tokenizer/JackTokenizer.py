from pathlib import Path
"""
不能直接split来分割
"""
class JackTokenizer:
    def __init__(self, jack_file:Path):
        self.jack_file = jack_file
        self.token_stream = []
        self._tokenize()



    _KEYWORDS = {
        'class', 'constructor', 'function', 'method', 'field', 'static',
        'var', 'int', 'char', 'boolean', 'void', 'true', 'false',
        'null', 'this', 'let', 'do', 'if', 'else', 'while', 'return'
    }

    _SYMBOLS = {
        '{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-',
        '*', '/', '&', '|', '<', '>', '=', '~'
    }

    def _read_source(self) -> str:
        # Jack spec uses ASCII-ish source; keep raw text as-is.
        return Path(self.jack_file).read_text(encoding="utf-8")

    def _tokenize(self) -> None:
        """
        Tokenize Jack source into XML-ish tokens stored in self.token_stream.

        Handles:
        - Symbols without whitespace: main() -> identifier, (, )
        - String constants with spaces: "a b" -> one token
        - Line comments // and block comments /* ... */ (incl /** ... */)
        - Does not treat comment markers inside strings as comments
        """
        src = self._read_source()
        n = len(src)
        i = 0

        in_block_comment = False

        while i < n:
            c = src[i]

            # Inside /* ... */ comment
            if in_block_comment:
                if c == '*' and i + 1 < n and src[i + 1] == '/':
                    in_block_comment = False
                    i += 2
                else:
                    i += 1
                continue

            # Whitespace
            if c.isspace():
                i += 1
                continue

            # Comments (only when not in string)
            if c == '/' and i + 1 < n:
                nxt = src[i + 1]
                if nxt == '/':  # line comment
                    i += 2
                    while i < n and src[i] not in '\r\n':
                        i += 1
                    continue
                if nxt == '*':  # block comment
                    in_block_comment = True
                    i += 2
                    continue

            # String constant
            if c == '"':
                i += 1
                start = i
                while i < n and src[i] != '"':
                    i += 1
                if i >= n:
                    raise ValueError(f"Unterminated string constant in {self.jack_file}")
                s = src[start:i]
                self.token_stream.append(f"<stringConstant> {s} </stringConstant>")
                i += 1  # consume closing quote
                continue

            # Symbol
            if c in self._SYMBOLS:
                self.token_stream.append(f"<symbol> {c} </symbol>")
                i += 1
                continue

            # Integer constant
            if c.isdigit():
                start = i
                while i < n and src[i].isdigit():
                    i += 1
                num = src[start:i]
                # Jack spec: 0..32767
                try:
                    val = int(num)
                except ValueError:
                    raise ValueError(f"Invalid integer constant: {num}")
                if not (0 <= val <= 32767):
                    raise ValueError(f"Integer constant out of range (0..32767): {num}")
                self.token_stream.append(f"<integerConstant> {num} </integerConstant>")
                continue

            # Identifier / keyword
            if c.isalpha() or c == '_':
                start = i
                i += 1
                while i < n and (src[i].isalnum() or src[i] == '_'):
                    i += 1
                ident = src[start:i]
                if ident in self._KEYWORDS:
                    self.token_stream.append(f"<keyword> {ident} </keyword>")
                else:
                    self.token_stream.append(f"<identifier> {ident} </identifier>")
                continue

            # Anything else is invalid in Jack
            raise ValueError(f"Unexpected character {c!r} at index {i} in {self.jack_file}")