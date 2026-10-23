#!/usr/bin/env python3
import argparse
import hashlib
import os
import re
import sys
import urllib.request
from pathlib import Path


SIMPLE_TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
SHA_TOKEN_RE = re.compile(r"\{\{SHA256:([^}]+)\}\}")


def class_name_for(name: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in name.split("-") if part)


def load_checksums(path: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        sha, name = parts[0], Path(parts[-1].lstrip("*")).name
        checksums[name] = sha
    return checksums


def render_simple_tokens(text: str, variables: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            raise KeyError(f"missing template variable: {key}")
        return variables[key]

    return SIMPLE_TOKEN_RE.sub(replace, text)


def render_sha_tokens(text: str, checksums: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        asset = match.group(1)
        sha = checksums.get(asset)
        if not sha:
            raise KeyError(f"missing checksum for asset: {asset}")
        return sha

    return SHA_TOKEN_RE.sub(replace, text)


def verify_downloads(text: str, checksums: dict[str, str], base_url: str) -> None:
    for asset in sorted(set(SHA_TOKEN_RE.findall(text))):
        sha = checksums.get(asset, "")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", asset) or not re.fullmatch(r"[a-fA-F0-9]{64}", sha):
            raise ValueError(f"invalid release checksum: {asset}")
        digest = hashlib.sha256()
        with urllib.request.urlopen(f"{base_url}/{asset}", timeout=120) as response:
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
        if digest.hexdigest() != sha.lower():
            raise ValueError(f"download checksum mismatch: {asset}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Scoop manifest template.")
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--checksums", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--verify-downloads", action="store_true")
    args = parser.parse_args()

    tool = os.environ.get("TOOL", "")
    tag = os.environ.get("TAG", "")
    repo = os.environ.get("REPO", "")

    variables = {
        key: value
        for key, value in os.environ.items()
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", key) and value
    }
    if tool:
        variables.setdefault("CLASS_NAME", class_name_for(tool))
    if tag:
        variables.setdefault("VERSION", tag.removeprefix("v"))
    if repo and tag:
        variables.setdefault("BASE_URL", f"https://github.com/{repo}/releases/download/{tag}")

    try:
        template = args.template.read_text(encoding="utf-8")
        checksums = load_checksums(args.checksums)
        rendered = render_simple_tokens(template, variables)
        if args.verify_downloads:
            verify_downloads(rendered, checksums, variables["BASE_URL"])
        rendered = render_sha_tokens(rendered, checksums)
    except Exception as exc:
        print(f"render_manifest.py: {exc}", file=sys.stderr)
        return 1

    if "{{" in rendered or "}}" in rendered:
        print("render_manifest.py: unresolved template token remains", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
