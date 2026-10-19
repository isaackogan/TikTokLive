#!/usr/bin/env python3
"""Generate the API reference and protobuf schema reference as Starlight Markdown.

``TikTokLive`` and ``TikTokLiveProto`` are loaded statically with griffe (nothing is
imported), then one page is written per public module, class, and function under
``docs/src/content/docs/api/`` and one per protobuf message and enum under
``.../schema/``. Both directories are build outputs: they are wiped on every run.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import shutil
import subprocess
import sysconfig
from functools import cache
from pathlib import Path
from typing import Iterator

import griffe
from griffe import DocstringSectionKind, ParameterKind

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = REPO_ROOT / "docs" / "src" / "content" / "docs"
SITE_PACKAGES = Path(sysconfig.get_paths()["purelib"])

API_PACKAGE = "TikTokLive"
PROTO_PACKAGE = "TikTokLiveProto"
SCHEMA_SUBPACKAGE = "v3"
SCHEMA_ROOT = f"{PROTO_PACKAGE}.{SCHEMA_SUBPACKAGE}"
PROTO_REEXPORT_MODULE = f"{API_PACKAGE}.proto"
GITHUB_BLOB = "https://github.com/isaackogan/TikTokLive/blob"

INLINE_METHOD_LIMIT = 5  # classes with more public methods get one page per method
SIGNATURE_WIDTH = 88  # longer signatures are wrapped one parameter per line
VALUE_WIDTH = 60  # longer attribute values are omitted

# One collection for every load so aliases from TikTokLive into TikTokLiveProto resolve.
_collection = griffe.ModulesCollection()


# --- Loading ---------------------------------------------------------------------------


def package_version() -> str:
    """Version stamped in ``TikTokLive/__version__.py``."""
    text = (REPO_ROOT / API_PACKAGE / "__version__.py").read_text()
    match = re.search(r'^PACKAGE_VERSION(?:\s*:\s*str)?\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if match is None:
        raise RuntimeError("PACKAGE_VERSION not found in TikTokLive/__version__.py")
    return match.group(1)


def proto_version() -> str:
    """Installed version of the proto package."""
    return importlib.metadata.version(PROTO_PACKAGE)


def load_module(name: str) -> griffe.Module:
    """Load a package statically, parsing Sphinx-style docstrings."""
    return griffe.load(
        name,
        docstring_parser="sphinx",
        resolve_aliases=True,
        search_paths=[REPO_ROOT, SITE_PACKAGES],
        modules_collection=_collection,
    )


def reexported_modules() -> set[str]:
    """Absolute modules star-imported by ``TikTokLive/proto/__init__.py``."""
    text = (REPO_ROOT / API_PACKAGE / "proto" / "__init__.py").read_text()
    return set(re.findall(r"^from\s+([A-Za-z]\S*)\s+import\s+\*", text, re.MULTILINE))


# --- Paths and scope -------------------------------------------------------------------


def api_slug(path: str) -> str:
    """``TikTokLive.client.client.TikTokLiveClient`` -> ``tiktoklive/client/client/tiktokliveclient``."""
    return path.lower().replace(".", "/")


def schema_slug(path: str) -> str:
    """``TikTokLiveProto.v3.webcast.model.message.WebcastChatMessage`` -> ``webcast/model/message/webcastchatmessage``."""
    return api_slug(path.removeprefix(f"{SCHEMA_ROOT}."))


def page_url(path: str) -> str:
    """Root-relative URL of the page generated for a dotted path."""
    if path.startswith(f"{SCHEMA_ROOT}."):
        return f"/schema/{schema_slug(path)}/"
    return f"/api/{api_slug(path)}/"


def in_api_scope(path: str) -> bool:
    """Whether a dotted path belongs to the rendered API reference.

    Private names are out. Of the ``TikTokLive.proto`` subtree only ``custom_proto``
    is in: the rest re-exports the proto package, which the schema reference covers.
    """
    parts = path.split(".")
    if parts[0] != API_PACKAGE or any(part.startswith("_") for part in parts):
        return False
    if parts[1:2] == ["proto"]:
        return parts[1:3] == ["proto", "custom_proto"]
    return True


def schema_kind(cls: griffe.Class) -> str | None:
    """``"message"`` or ``"enum"`` for betterproto2 classes, ``None`` for anything else."""
    bases = {str(base).rsplit(".", 1)[-1] for base in cls.bases}
    if "Message" in bases:
        return "message"
    if "Enum" in bases:
        return "enum"
    return None


def public_members(obj: griffe.Object) -> list[griffe.Object]:
    """Members defined on ``obj`` itself (no imports), public names only, in source order."""
    return [m for m in obj.members.values() if not m.is_alias and not m.name.startswith("_")]


def public_methods(cls: griffe.Class) -> list[griffe.Function]:
    return [m for m in public_members(cls) if m.is_function]


def iter_modules(module: griffe.Module) -> Iterator[griffe.Module]:
    """``module`` and every public submodule, depth first."""
    yield module
    for member in public_members(module):
        if member.is_module:
            yield from iter_modules(member)


def reexported_members(module: griffe.Module) -> list[griffe.Object]:
    """Classes and functions a package re-exports under their own name, resolved."""
    targets: dict[str, griffe.Object] = {}
    for name, member in module.members.items():
        if name.startswith("_") or not member.is_alias:
            continue
        try:
            target = member.final_target
        except griffe.GriffeError:
            continue  # imported from a package that is not loaded
        if target.name != name or not (target.is_class or target.is_function):
            continue
        if target.parent.is_module and in_api_scope(target.path):
            targets.setdefault(target.path, target)
    return list(targets.values())


def resolve_path(scope: griffe.Object, path: str) -> griffe.Object | None:
    """The loaded object at a dotted path, following aliases, or ``None``."""
    try:
        target = scope.modules_collection[path]
        return target.final_target if target.is_alias else target
    except (KeyError, griffe.GriffeError):
        return None


def link_for(scope: griffe.Object, path: str) -> str | None:
    """URL of the generated page documenting ``path``, or ``None`` when none is generated."""
    target = resolve_path(scope, path)
    if target is None:
        return None
    if target.path.startswith(f"{SCHEMA_ROOT}."):
        return page_url(target.path) if target.is_class and schema_kind(target) else None
    if in_api_scope(target.path) and (target.is_module or (target.is_class and target.parent.is_module)):
        return page_url(target.path)
    return None


# --- Annotations -----------------------------------------------------------------------

Token = tuple[str, str | None]  # (text, link URL)
_GENERATED_MODULE_ALIAS = re.compile(r"^_.*__$")  # betterproto2's ``__shared__message__`` style imports


def _canonical(expr: str | griffe.Expr) -> str:
    if isinstance(expr, str):
        return expr
    try:
        return expr.canonical_path
    except Exception:  # noqa: BLE001 - resolution is best effort; fall back to the source text
        return str(expr)


def _join(groups: list[list[Token]], separator: str) -> list[Token]:
    tokens: list[Token] = []
    for index, group in enumerate(groups):
        if index:
            tokens.append((separator, None))
        tokens.extend(group)
    return tokens


def annotation_tokens(expr: str | griffe.Expr | None, scope: griffe.Object) -> list[Token]:
    """Flatten an annotation into text tokens, linking names that have a generated page.

    ``typing.Annotated[T, ...]`` collapses to ``T`` and the module aliases betterproto2
    generates (``__shared__message__.X``) collapse to ``X``.
    """
    if expr is None:
        return []
    if isinstance(expr, str):
        return [(expr, None)]
    if isinstance(expr, griffe.ExprName):
        return [(expr.name, link_for(scope, _canonical(expr)))]
    if isinstance(expr, griffe.ExprAttribute):
        url = link_for(scope, _canonical(expr))
        first = expr.first
        if url or (isinstance(first, griffe.ExprName) and _GENERATED_MODULE_ALIAS.match(first.name)):
            return [(str(expr.last), url)]
        return [(str(expr), None)]
    if isinstance(expr, griffe.ExprSubscript):
        if _canonical(expr.left) in ("typing.Annotated", "Annotated"):
            inner = expr.slice
            return annotation_tokens(inner.elements[0] if isinstance(inner, griffe.ExprTuple) else inner, scope)
        return [*annotation_tokens(expr.left, scope), ("[", None), *annotation_tokens(expr.slice, scope), ("]", None)]
    if isinstance(expr, griffe.ExprTuple):
        inner = _join([annotation_tokens(e, scope) for e in expr.elements], ", ")
        return inner if expr.implicit else [("(", None), *inner, (")", None)]
    if isinstance(expr, griffe.ExprList):
        return [("[", None), *_join([annotation_tokens(e, scope) for e in expr.elements], ", "), ("]", None)]
    if isinstance(expr, griffe.ExprBinOp):
        return [*annotation_tokens(expr.left, scope), (f" {expr.operator} ", None), *annotation_tokens(expr.right, scope)]
    return [(str(expr), None)]


def annotation_text(expr: str | griffe.Expr | None, scope: griffe.Object) -> str:
    """Plain annotation for code blocks."""
    return "".join(text for text, _ in annotation_tokens(expr, scope))


def annotation_markdown(expr: str | griffe.Expr | None, scope: griffe.Object) -> str:
    """Annotation as code spans, with linked names where a page exists."""
    parts: list[str] = []
    run: list[str] = []

    def flush() -> None:
        if run:
            parts.append(f"`{''.join(run)}`")
            run.clear()

    for text, url in annotation_tokens(expr, scope):
        if url:
            flush()
            parts.append(f"[`{text}`]({url})")
        else:
            run.append(text)
    flush()
    return "".join(parts)


# --- Docstrings ------------------------------------------------------------------------

_RST_ROLE = re.compile(r":[a-z:]+:`([^`]+)`")  # :class:`X` -> `X`
_CODE_SPAN = re.compile(r"(`[^`]*`)")
_TAG_LIKE = re.compile(r"<(?=[A-Za-z/])")  # ``<user_id>`` would otherwise be dropped as HTML


def markdown_text(text: str) -> str:
    """Docstring prose as Markdown: RST roles become code, tag-like text stays literal."""
    text = _RST_ROLE.sub(r"`\1`", text)
    pieces = _CODE_SPAN.split(text)
    return "".join(piece if piece.startswith("`") else _TAG_LIKE.sub(r"\<", piece) for piece in pieces)


def _oneline(text: str) -> str:
    return " ".join(text.split())


def _sections(obj: griffe.Object, kind: DocstringSectionKind) -> list[griffe.DocstringSection]:
    if obj.docstring is None:
        return []
    return [section for section in obj.docstring.parsed if section.kind is kind]


def docstring_text(obj: griffe.Object) -> str:
    """All prose sections of the docstring, as Markdown."""
    texts = [section.value.strip() for section in _sections(obj, DocstringSectionKind.text)]
    return "\n\n".join(markdown_text(text) for text in texts if text)


def summary(obj: griffe.Object) -> str:
    """First docstring paragraph on one line, or an empty string."""
    for section in _sections(obj, DocstringSectionKind.text):
        paragraph = _oneline(section.value.strip().split("\n\n")[0])
        if paragraph:
            return _RST_ROLE.sub(r"`\1`", paragraph)
    return ""


def description(obj: griffe.Object) -> str:
    return summary(obj) or f"{obj.kind.value} {obj.path}"


# --- Markdown blocks -------------------------------------------------------------------

_PLAIN_YAML = re.compile(r"^[A-Za-z_][A-Za-z0-9_ .()\-]*[A-Za-z0-9_.)]$")
_YAML_RESERVED = {"true", "false", "null", "yes", "no", "on", "off"}


def yaml_scalar(value: str) -> str:
    if _PLAIN_YAML.match(value) and value.lower() not in _YAML_RESERVED:
        return value
    return json.dumps(value)


def frontmatter(title: str, blurb: str, *, label: str, order: int | None = None) -> str:
    lines = ["---", f"title: {yaml_scalar(title)}", f"description: {json.dumps(blurb)}", "sidebar:", f"  label: {yaml_scalar(label)}"]
    if order is not None:
        lines.append(f"  order: {order}")
    return "\n".join([*lines, "---", ""])


def code_block(source: str) -> list[str]:
    return ["```python", source, "```", ""]


def _wrap_call(head: str, items: list[str], tail: str) -> str:
    """``head(item, item)tail`` on one line, or one item per line when it gets long."""
    one_line = f"{head}{', '.join(items)}{tail}"
    if not items or len(one_line) <= SIGNATURE_WIDTH:
        return one_line
    return f"{head}\n" + "".join(f"    {item},\n" for item in items) + tail


def signature_parameters(func: griffe.Function) -> list[griffe.Parameter]:
    """Parameters as a caller sees them: no ``self``/``cls`` on methods."""
    params = list(func.parameters)
    if params and func.parent.is_class and "staticmethod" not in func.labels:
        params = params[1:]
    return params


def _parameter_prefix(param: griffe.Parameter) -> str:
    return {ParameterKind.var_positional: "*", ParameterKind.var_keyword: "**"}.get(param.kind, "")


def _parameter_default(param: griffe.Parameter) -> str | None:
    """The default as written, or ``None``; griffe's synthetic ``()``/``{}`` for ``*args``/``**kwargs`` is dropped."""
    if param.default is None or _parameter_prefix(param):
        return None
    return str(param.default)


def _parameter_sources(func: griffe.Function) -> list[str]:
    items: list[str] = []
    params = signature_parameters(func)
    star_seen = False
    for index, param in enumerate(params):
        if param.kind is ParameterKind.keyword_only and not star_seen:
            items.append("*")
            star_seen = True
        source = _parameter_prefix(param) + param.name
        if param.annotation is not None:
            source += f": {annotation_text(param.annotation, func)}"
        default = _parameter_default(param)
        if default is not None:
            source += f" = {default}" if param.annotation is not None else f"={default}"
        items.append(source)
        if param.kind is ParameterKind.var_positional:
            star_seen = True
        if param.kind is ParameterKind.positional_only and (index + 1 == len(params) or params[index + 1].kind is not ParameterKind.positional_only):
            items.append("/")
    return items


def function_signature(func: griffe.Function) -> str:
    decorators = [f"@{label}" for label in ("classmethod", "staticmethod") if label in func.labels]
    keyword = "async def" if "async" in func.labels else "def"
    returns = f" -> {annotation_text(func.returns, func)}" if func.returns is not None else ""
    return "\n".join([*decorators, _wrap_call(f"{keyword} {func.name}(", _parameter_sources(func), f"){returns}")])


def own_init(cls: griffe.Class) -> griffe.Function | None:
    init = cls.members.get("__init__")
    return init if init is not None and not init.is_alias and init.is_function else None


def class_signature(cls: griffe.Class) -> str:
    """The class line with its bases, then the constructor call when the class defines one."""
    bases = ", ".join(annotation_text(base, cls) for base in cls.bases)
    lines = [f"class {cls.name}({bases})" if bases else f"class {cls.name}"]
    init = own_init(cls)
    if init is not None:
        lines += ["", _wrap_call(f"{cls.name}(", _parameter_sources(init), ")")]
    return "\n".join(lines)


def parameters_section(func: griffe.Function, level: int) -> list[str]:
    """Signature parameters merged with the documented ones, so each shows its type, default and description."""
    documented = {
        param.name.lstrip("*"): param
        for section in _sections(func, DocstringSectionKind.parameters)
        for param in section.value
    }
    lines = []
    for param in signature_parameters(func):
        doc = documented.get(param.name)
        annotation = param.annotation if param.annotation is not None else (doc.annotation if doc else None)
        meta = []
        if annotation is not None:
            meta.append(annotation_markdown(annotation, func))
        default = _parameter_default(param)
        if default is not None:
            meta.append(f"default `{default}`")
        line = f"- **`{_parameter_prefix(param)}{param.name}`**"
        if meta:
            line += f" ({', '.join(meta)})"
        if doc and doc.description.strip():
            line += f" — {_oneline(markdown_text(doc.description))}"
        lines.append(line)
    if not lines:
        return []
    return [f"{'#' * level} Parameters", "", *lines, ""]


def returns_section(func: griffe.Function, level: int) -> list[str]:
    documented = [item for section in _sections(func, DocstringSectionKind.returns) for item in section.value]
    annotation = func.returns if func.returns is not None else (documented[0].annotation if documented else None)
    text = _oneline(markdown_text(" ".join(item.description for item in documented if item.description)))
    if annotation is None or (str(annotation) == "None" and not text):
        return []
    parts = [annotation_markdown(annotation, func)]
    if text:
        parts.append(text)
    return [f"{'#' * level} Returns", "", " — ".join(parts), ""]


def raises_section(func: griffe.Function, level: int) -> list[str]:
    documented = [item for section in _sections(func, DocstringSectionKind.raises) for item in section.value]
    if not documented:
        return []
    lines = [f"- {annotation_markdown(item.annotation, func)} — {_oneline(markdown_text(item.description))}" for item in documented]
    return [f"{'#' * level} Raises", "", *lines, ""]


def function_sections(func: griffe.Function, level: int) -> list[str]:
    """Signature block then parameters, returns and raises, with headings at ``level``.

    Level 2 is a function's own page and gets a Signature heading; deeper levels are
    methods inlined under their class, where the code block follows the method heading.
    """
    lines = [f"{'#' * level} Signature", ""] if level == 2 else []
    lines += code_block(function_signature(func))
    return lines + parameters_section(func, level) + returns_section(func, level) + raises_section(func, level)


def attributes_section(obj: griffe.Object) -> list[str]:
    """Public attributes with type, short literal value and description; properties are marked."""
    lines = []
    for member in public_members(obj):
        if not member.is_attribute:
            continue
        meta = ["property"] if "property" in member.labels else []
        if member.annotation is not None:
            meta.append(annotation_markdown(member.annotation, obj))
        line = f"- **`{member.name}`**"
        if meta:
            line += f" ({', '.join(meta)})"
        value = member.value  # literals are strings; calls and bare names (``= some_param``) say nothing useful
        if value is not None and not isinstance(value, (griffe.ExprCall, griffe.ExprName)) and len(str(value)) <= VALUE_WIDTH:
            line += f" = `{value}`"
        if blurb := summary(member):
            line += f" — {markdown_text(blurb)}"
        lines.append(line)
    if not lines:
        return []
    return ["## Attributes", "", *lines, ""]


def methods_section(cls: griffe.Class) -> list[str]:
    """Inline method docs, or links to per-method pages for classes with many methods."""
    methods = public_methods(cls)
    if not methods:
        return []
    lines = ["## Methods", ""]
    if len(methods) <= INLINE_METHOD_LIMIT:
        for method in methods:
            lines += [f"### {method.name}", ""]
            if text := docstring_text(method):
                lines += [text, ""]
            lines += function_sections(method, 4)
        return lines
    for method in methods:
        line = f"- [`{method.name}()`]({page_url(method.path)})"
        if blurb := summary(method):
            line += f" — {markdown_text(blurb)}"
        lines.append(line)
    return [*lines, ""]


def bases_section(cls: griffe.Class) -> list[str]:
    if not cls.bases:
        return []
    return ["## Bases", "", *[f"- {annotation_markdown(base, cls)}" for base in cls.bases], ""]


def listing(heading: str, objects: list[griffe.Object], *, qualified: bool = False) -> list[str]:
    """A linked bullet list of objects with their summaries.

    ``qualified`` names modules by their dotted path and other objects by their module,
    for index pages that list objects from many modules.
    """
    if not objects:
        return []
    lines = []
    for obj in objects:
        line = f"- [`{obj.path if qualified and obj.is_module else obj.name}`]({page_url(obj.path)})"
        if qualified and not obj.is_module:
            line += f" (`{obj.parent.path}`)"
        if blurb := summary(obj):
            line += f" — {markdown_text(blurb)}"
        lines.append(line)
    return [heading, "", *lines, ""]


def import_section(statement: str) -> list[str]:
    return ["## Import", "", *code_block(statement)]


def repo_path(obj: griffe.Object) -> Path | None:
    """The object's file relative to the repository root, or ``None`` outside it."""
    filepath = obj.filepath
    if isinstance(filepath, list) or not filepath.is_relative_to(REPO_ROOT):
        return None
    return filepath.relative_to(REPO_ROOT)


def source_section(obj: griffe.Object, source_url: str | None) -> list[str]:
    if source_url is None:
        return []
    relative = repo_path(obj)
    label = relative.as_posix() if relative else obj.name
    if obj.lineno:
        label += f":{obj.lineno}"
    return ["## Source", "", f"[{label}]({source_url})", ""]


# --- Pages -----------------------------------------------------------------------------


def page_for(obj: griffe.Object, *, import_path: str, source_url: str | None) -> str:
    """Starlight Markdown documenting a module, class or function.

    ``import_path`` is the module users should import the object from (for modules, the
    module itself). ``source_url`` links the Source section; ``None`` omits it.
    """
    if obj.is_module:
        return _module_page(obj, import_path, source_url)
    if obj.is_class:
        return _class_page(obj, import_path, source_url)
    if obj.is_function:
        return _function_page(obj, import_path, source_url)
    raise ValueError(f"no page layout for {obj.kind.value} {obj.path}")


def _module_page(module: griffe.Module, import_path: str, source_url: str | None) -> str:
    members = public_members(module)
    lines = [frontmatter(module.name, description(module), label=module.name, order=0)]
    if text := docstring_text(module):
        lines += [text, ""]
    lines += listing("## Submodules", [m for m in members if m.is_module and in_api_scope(m.path)])
    lines += listing("## Classes", [m for m in members if m.is_class])
    lines += listing("## Functions", [m for m in members if m.is_function])
    if module.is_init_module:
        lines += listing("## Re-exports", reexported_members(module))
    lines += attributes_section(module)
    lines += import_section(f"import {import_path}")
    lines += source_section(module, source_url)
    return "\n".join(lines)


def _class_page(cls: griffe.Class, import_path: str, source_url: str | None) -> str:
    lines = [frontmatter(cls.name, description(cls), label=cls.name, order=0)]
    text = docstring_text(cls)
    if text:
        lines += [text, ""]
    lines += ["## Signature", "", *code_block(class_signature(cls))]
    init = own_init(cls)
    if init is not None:
        init_text = docstring_text(init)
        if init_text and init_text != text:
            lines += [init_text, ""]
        lines += parameters_section(init, 2)
    lines += attributes_section(cls)
    lines += methods_section(cls)
    lines += bases_section(cls)
    lines += import_section(f"from {import_path} import {cls.name}")
    lines += source_section(cls, source_url)
    return "\n".join(lines)


def _function_page(func: griffe.Function, import_path: str, source_url: str | None) -> str:
    lines = [frontmatter(func.name, description(func), label=func.name)]
    owner = func.parent if func.parent.is_class else None
    if owner is not None:
        lines += [f"Method of [`{owner.name}`]({page_url(owner.path)}).", ""]
    if text := docstring_text(func):
        lines += [text, ""]
    lines += function_sections(func, 2)
    lines += import_section(f"from {import_path} import {owner.name if owner else func.name}")
    lines += source_section(func, source_url)
    return "\n".join(lines)


def index_page(title: str, blurb: str, sections: list[tuple[str, list[griffe.Object]]]) -> str:
    lines = [frontmatter(title, blurb, label="Overview", order=0), blurb, ""]
    for heading, objects in sections:
        ordered = sorted(objects, key=lambda obj: (obj.path.lower() if obj.is_module else obj.name.lower(), obj.path.lower()))
        lines += listing(heading, ordered, qualified=True)
    return "\n".join(lines)


# --- Rendering -------------------------------------------------------------------------


@cache
def source_ref() -> str:
    """The ``v<version>`` tag when it exists, else ``master``."""
    tag = f"v{package_version()}"
    try:
        listed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "tag", "--list", tag], capture_output=True, text=True, check=True
        ).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        return "master"
    return tag if tag in listed else "master"


def source_url_for(obj: griffe.Object) -> str | None:
    """GitHub link to the object's definition; ``None`` for objects outside the repository."""
    relative = repo_path(obj)
    if relative is None:
        return None
    url = f"{GITHUB_BLOB}/{source_ref()}/{relative.as_posix()}"
    return f"{url}#L{obj.lineno}" if obj.lineno else url


def import_paths(root: griffe.Module) -> dict[str, str]:
    """Shortest public module each class or function can be imported from."""
    paths: dict[str, str] = {}
    for module in sorted(iter_modules(root), key=lambda m: m.path.count(".")):
        if module.is_init_module:
            for target in reexported_members(module):
                paths.setdefault(target.path, module.path)
    return paths


def _write(out_dir: Path, slug: str, markdown: str) -> Path:
    path = out_dir / slug / "index.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown)
    return path


def render_api(root: griffe.Module, out_dir: Path) -> list[Path]:
    """Write the API reference for every public module, class and function in scope."""
    imports = import_paths(root)
    modules = [module for module in iter_modules(root) if in_api_scope(module.path)]
    classes: list[griffe.Class] = []
    functions: list[griffe.Function] = []
    written = []
    for module in modules:
        written.append(_write(out_dir, api_slug(module.path), page_for(module, import_path=module.path, source_url=source_url_for(module))))
        for obj in public_members(module):
            if not (obj.is_class or obj.is_function):
                continue
            import_path = imports.get(obj.path, module.path)
            written.append(_write(out_dir, api_slug(obj.path), page_for(obj, import_path=import_path, source_url=source_url_for(obj))))
            if obj.is_class:
                classes.append(obj)
                if len(public_methods(obj)) > INLINE_METHOD_LIMIT:
                    for method in public_methods(obj):
                        written.append(_write(out_dir, api_slug(method.path), page_for(method, import_path=import_path, source_url=source_url_for(method))))
            else:
                functions.append(obj)
    version = package_version()
    index = index_page(
        f"{API_PACKAGE} {version}",
        f"API reference generated from the docstrings and signatures of {API_PACKAGE} {version}.",
        [("## Modules", modules), ("## Classes", classes), ("## Functions", functions)],
    )
    index_path = out_dir / "index.md"
    index_path.write_text(index)
    return [index_path, *written]


def schema_import_path(cls: griffe.Class, reexported: set[str]) -> str:
    """``TikTokLive.proto`` when it star-imports the class, else the class's own module."""
    module = cls.module
    exported = module.exports is None or any(str(name) == cls.name for name in module.exports)
    return PROTO_REEXPORT_MODULE if module.path in reexported and exported else module.path


def render_schema(proto_root: griffe.Module, reexported: set[str], out_dir: Path) -> list[Path]:
    """Write one page per betterproto2 message and enum under ``TikTokLiveProto.v3``."""
    messages: list[griffe.Class] = []
    enums: list[griffe.Class] = []
    written = []
    for module in iter_modules(proto_root[SCHEMA_SUBPACKAGE]):
        for cls in public_members(module):
            if not cls.is_class or schema_kind(cls) is None:
                continue
            (messages if schema_kind(cls) == "message" else enums).append(cls)
            markdown = page_for(cls, import_path=schema_import_path(cls, reexported), source_url=None)
            written.append(_write(out_dir, schema_slug(cls.path), markdown))
    version = proto_version()
    index = index_page(
        f"TikTok Webcast v3 schema ({version})",
        f"Every protobuf message and enum in TikTokLiveProto {version}, the schema TikTokLive decodes events from.",
        [("## Messages", messages), ("## Enums", enums)],
    )
    index_path = out_dir / "index.md"
    index_path.write_text(index)
    return [index_path, *written]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate the API and protobuf schema reference pages.")
    parser.add_argument("--out", type=Path, default=CONTENT_ROOT, help="content directory holding api/ and schema/")
    args = parser.parse_args(argv)

    proto_root = load_module(PROTO_PACKAGE)  # first, so TikTokLive.proto's star re-exports resolve
    api_root = load_module(API_PACKAGE)
    api_dir, schema_dir = args.out / "api", args.out / "schema"
    for directory in (api_dir, schema_dir):
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir(parents=True)
    api_pages = render_api(api_root, api_dir)
    schema_pages = render_schema(proto_root, reexported_modules(), schema_dir)
    print(f"Wrote {len(api_pages)} API pages to {api_dir} and {len(schema_pages)} schema pages to {schema_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
