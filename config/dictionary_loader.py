import os
from dataclasses import dataclass


@dataclass
class EggEntry:
    name: str
    image: str       # e.g. "shenqi_egg.png"
    selected: str    # e.g. "shenqi_egg_selected.png"


@dataclass
class GuluEntry:
    name: str
    image: str       # e.g. "putong_gulu.png"
    selected: str    # e.g. "putong_gulu_selected.png"


def _parse_md_table(filepath: str) -> list[list[str]]:
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        header_skipped = False
        for line in f:
            line = line.strip()
            if not line or line.startswith("|---"):
                continue
            if line.startswith("|") and line.endswith("|"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                if not header_skipped:
                    header_skipped = True
                    continue
                rows.append(cells)
    return rows


def load_eggs(filepath: str, images_dir: str) -> list[EggEntry]:
    rows = _parse_md_table(filepath)
    entries = []
    for row in rows:
        if len(row) < 3:
            continue
        name, img, sel = row[0], row[1], row[2]
        if not os.path.exists(os.path.join(images_dir, img)):
            raise FileNotFoundError(f"蛋图像缺失: {img}")
        if not os.path.exists(os.path.join(images_dir, sel)):
            raise FileNotFoundError(f"蛋检验图像缺失: {sel}")
        entries.append(EggEntry(name=name, image=img, selected=sel))
    if not entries:
        raise ValueError(f"蛋字典为空或格式错误: {filepath}")
    return entries


def load_gulus(filepath: str, images_dir: str) -> list[GuluEntry]:
    rows = _parse_md_table(filepath)
    entries = []
    for row in rows:
        if len(row) < 3:
            continue
        name, img, sel = row[0], row[1], row[2]
        if not os.path.exists(os.path.join(images_dir, img)):
            raise FileNotFoundError(f"咕噜球图像缺失: {img}")
        if not os.path.exists(os.path.join(images_dir, sel)):
            raise FileNotFoundError(f"咕噜球检验图像缺失: {sel}")
        entries.append(GuluEntry(name=name, image=img, selected=sel))
    if not entries:
        raise ValueError(f"咕噜球字典为空或格式错误: {filepath}")
    return entries
