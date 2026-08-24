# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

repo = Path(SPECPATH).resolve().parent
import ast
_init = (repo / "backend" / "pca" / "__init__.py").read_text()
version = next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(_init))
               if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "__version__")
frontend_dist = repo / "frontend" / "dist"

hidden = (
    collect_submodules("seabreeze")
    + collect_submodules("uvicorn")
    + collect_submodules("webview")
)
datas = [(str(frontend_dist), "frontend/dist")]
datas += collect_data_files("seabreeze")
datas += collect_data_files("colour")

a = Analysis(
    [str(repo / "desktop" / "app.py")],
    pathex=[str(repo / "backend")],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    excludes=["pytest", "httpx", "tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="PCA-100",
          console=False, target_arch="arm64")
coll = COLLECT(exe, a.binaries, a.datas, name="PCA-100")
app = BUNDLE(
    coll,
    name="PCA-100.app",
    icon=str(repo / "packaging" / "icon" / "pca100.icns"),
    bundle_identifier="cz.xctech.pca100",
    version=version,
    info_plist={
        "CFBundleShortVersionString": version,
        "CFBundleVersion": "1",
        "NSHighResolutionCapable": True,
    },
)
