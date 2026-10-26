"""Conservative static index. Edges mean syntactic references, not runtime proof."""
import ast
import hashlib
import os
import re
import tokenize
from pathlib import Path

SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist", ".reporadar", ".tox"}
MAX_FILE = 1_000_000
MAX_FILES = 5000


def module_name(path):
    parts = list(Path(path).with_suffix("").parts)
    if parts and parts[0] == "src":
        parts.pop(0)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted(node.value)
        return parent + "." + node.attr if parent else ""
    return ""


def markdown_sections(path, content):
    lines = content.splitlines()
    starts, fence = [(0, Path(path).name)], None
    for i, line in enumerate(lines):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            char = marker[1][0]
            if fence is None:
                fence = (char, len(marker[1]))
            elif char == fence[0] and len(marker[1]) >= fence[1]:
                fence = None
            continue
        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading and fence is None:
            if i == 0:
                starts[0] = (0, heading[1])
            else:
                starts.append((i, heading[1]))
    result = []
    for n, (start, title) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        text = "\n".join(lines[start:end]).strip()
        if text:
            result.append(dict(id=f"{path}:{start+1}", path=path, title=title,
                               line=start + 1, end_line=end, text=text))
    return result


class Collector(ast.NodeVisitor):
    def __init__(self, path, tree, source):
        self.path, self.module, self.source = path, module_name(path), source
        self.symbols, self.calls, self.imports = [], [], {}
        self.scope, self.classes = [], []
        self.bindings = {}
        # Module-level import aliases only; function-local imports are recorded below.
        self.imports[""] = self.import_map(tree.body)

    def import_map(self, body):
        result = {}
        package = self.module if self.path.endswith("__init__.py") else self.module.rpartition(".")[0]
        for node in body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result[alias.asname or alias.name.split(".")[0]] = alias.name if alias.asname else alias.name.split(".")[0]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    prefix = package.split(".") if package else []
                    keep = len(prefix) - node.level + 1
                    base = ".".join(prefix[:max(0, keep)] + ([base] if base else []))
                for alias in node.names:
                    if alias.name != "*":
                        result[alias.asname or alias.name] = ".".join(filter(None, [base, alias.name]))
        return result

    def add_symbol(self, node, kind):
        qualname = ".".join(self.scope + [node.name])
        full = ".".join(filter(None, [self.module, qualname]))
        identifier = self.path + "::" + qualname
        signature = node.name
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            signature += "(" + ast.unparse(node.args) + ")"
            if node.returns:
                signature += " -> " + ast.unparse(node.returns)
        self.symbols.append(dict(id=identifier, name=node.name, qualname=qualname, qualified=full,
            module=self.module, path=self.path, line=node.lineno, end_line=node.end_lineno,
            kind=kind, signature=signature, docstring=ast.get_docstring(node) or "",
            source=ast.get_source_segment(self.source, node) or "",
            fingerprint=hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()))
        return identifier

    def visit_ClassDef(self, node):
        self.add_symbol(node, "class")
        self.scope.append(node.name)
        self.classes.append(".".join(self.scope))
        for child in node.body:
            self.visit(child)
        self.classes.pop()
        self.scope.pop()

    def visit_FunctionDef(self, node):
        identifier = self.add_symbol(node, "async function" if isinstance(node, ast.AsyncFunctionDef) else "function")
        self.scope.append(node.name)
        key = ".".join(self.scope)
        self.imports[key] = self.import_map(node.body)
        # Any local binding can shadow an imported/global callable. Do not guess its type.
        bindings = {a.arg for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs}
        if node.args.vararg:
            bindings.add(node.args.vararg.arg)
        if node.args.kwarg:
            bindings.add(node.args.kwarg.arg)
        def local_walk(n):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                return
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                bindings.add(n.id)
            for child in ast.iter_child_nodes(n):
                local_walk(child)
        for child in node.body:
            local_walk(child)
        self.bindings[key] = bindings
        for child in node.body:
            self.visit(child)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node):
        if self.scope and ".".join(self.scope) in self.bindings:
            self.calls.append(dict(source=self.path + "::" + ".".join(self.scope),
                expression=dotted(node.func) or ast.unparse(node.func), line=node.lineno,
                scope=".".join(self.scope), class_scope=self.classes[-1] if self.classes else None))
        self.generic_visit(node)


def analyze(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("Repository directory does not exist")
    symbols, documents, warnings, collectors, files = [], [], [], [], []
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith(".")
                         and not (Path(current) / d).is_symlink())
        for name in sorted(names):
            p = Path(current) / name
            if p.suffix.lower() not in {".py", ".md"} or p.is_symlink():
                continue
            files.append(p)
            if len(files) > MAX_FILES:
                raise ValueError(f"Repository exceeds {MAX_FILES} source/document files")
    for p in files:
        path = p.relative_to(root).as_posix()
        try:
            if p.stat().st_size > MAX_FILE:
                warnings.append(dict(path=path, message="File exceeds 1 MB; skipped"))
                continue
            if p.suffix.lower() == ".md":
                documents.extend(markdown_sections(path, p.read_text(encoding="utf-8")))
                continue
            with tokenize.open(str(p)) as handle:
                source = handle.read()
            tree = ast.parse(source, filename=path)
            collector = Collector(path, tree, source)
            collector.visit(tree)
            collectors.append(collector)
            symbols.extend(collector.symbols)
        except (SyntaxError, UnicodeError, OSError, RecursionError, ValueError) as exc:
            warnings.append(dict(path=path, message=str(exc)))
    by_name = {}
    for symbol in symbols:
        by_name.setdefault(symbol["qualified"], []).append(symbol["id"])
    edges, unresolved = [], []
    for collector in collectors:
        for call in collector.calls:
            expression, scope = call["expression"], call["scope"]
            head, *tail = expression.split(".")
            aliases = dict(collector.imports[""])
            for i in range(1, len(scope.split(".")) + 1):
                aliases.update(collector.imports.get(".".join(scope.split(".")[:i]), {}))
            candidates, reason = [], "external, dynamic or unresolved"
            shadowed = any(head in collector.bindings.get(".".join(scope.split(".")[:i]), set())
                          for i in range(1, len(scope.split(".")) + 1))
            if head in {"self", "cls"} and len(tail) == 1 and call["class_scope"]:
                # Only direct receiver syntax. This does not prove runtime dispatch.
                candidates = [collector.module + "." + call["class_scope"] + "." + tail[0]]
                reason = "direct receiver reference"
            elif shadowed:
                reason = "local binding; runtime target unknown"
            elif head in aliases:
                candidates = [".".join([aliases[head]] + tail)]
                reason = "explicit import"
            elif not tail:
                parts = scope.split(".")
                # Search lexical function scopes, skipping class namespace.
                for i in range(len(parts), -1, -1):
                    prefix = ".".join(parts[:i])
                    if prefix == call["class_scope"]:
                        continue
                    candidates.append(".".join(filter(None, [collector.module, prefix, head])))
                reason = "lexical name"
            target = None
            for candidate in candidates:
                matches = by_name.get(candidate, [])
                if len(matches) == 1:
                    target = matches[0]
                    break
                if len(matches) > 1:
                    break
            evidence = dict(source=call["source"], line=call["line"], expression=expression, reason=reason)
            if target:
                edges.append(dict(evidence, target=target))
            else:
                unresolved.append(evidence)
    # Duplicate definitions are ambiguous; preserve a single navigable record and warn.
    unique = {}
    for symbol in symbols:
        if symbol["id"] in unique:
            warnings.append(dict(path=symbol["path"], message="Duplicate definition: " + symbol["qualname"]))
        unique[symbol["id"]] = symbol
    return dict(root=str(root), name=root.name, symbols=list(unique.values()), documents=documents,
                edges=edges, unresolved=unresolved, warnings=warnings, file_count=len(files))
