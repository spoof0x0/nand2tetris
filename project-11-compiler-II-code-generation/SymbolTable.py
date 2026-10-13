class SymbolTable:
    def __init__(self):
        self.class_scope = {}
        self.subroutine_scope = {}
        self.counts = {"static": 0, "field": 0, "arg": 0, "var": 0}

    def define(self, name, var_type, kind):
        if kind not in self.counts:
            raise ValueError(f"Invalid symbol kind: {kind}")
        symbol = {"type": var_type, "kind": kind, "index": self.counts[kind]}
        if kind in {"static", "field"}:
            self.class_scope[name] = symbol
        else:
            self.subroutine_scope[name] = symbol
        self.counts[kind] += 1

    def varCount(self, kind):
        if kind not in self.counts:
            raise ValueError(f"Invalid symbol kind: {kind}")
        return self.counts[kind]

    def startSubroutine(self):
        self.subroutine_scope.clear()
        self.counts["arg"] = 0
        self.counts["var"] = 0

    def lookUp(self, name):
        if name in self.subroutine_scope:
            return self.subroutine_scope[name]
        return self.class_scope.get(name)

    def kindOf(self, name):
        s = self.lookUp(name)
        return s["kind"] if s else None

    def typeOf(self, name):
        s = self.lookUp(name)
        return s["type"] if s else None

    def indexOf(self, name):
        s = self.lookUp(name)
        return s["index"] if s else None
