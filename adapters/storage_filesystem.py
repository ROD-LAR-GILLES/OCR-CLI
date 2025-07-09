# adapters/storage_filesystem.py
import json
import shutil
from pathlib import Path
from typing import List, Any
import pandas as pd
from tabulate import tabulate

from application.ports import StoragePort


class FileStorage(StoragePort):
    def __init__(self, out_dir: Path) -> None:
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, text: str, tables: List[Any], original: Path) -> None:
        base = self.out_dir / name.stem

        # 1. texto plano
        (base.with_suffix(".txt")).write_text(text, encoding="utf-8")

        # 2. tablas -> json por tabla
        for i, df in enumerate(tables, start=1):
            df.to_json(base.with_name(f"{base.stem}_table_{i}.json"), orient="split")
        # 3. tabla ASCII en un único .txt (opcional)
        if tables:
            concat_ascii = "\n\n".join(tabulate(df, tablefmt="github") for df in tables)
            (base.with_name(f"{base.stem}_tables.txt")).write_text(concat_ascii, "utf-8")

        # 4. Copia PDF original
        shutil.copy(original, base.with_suffix(".pdf"))