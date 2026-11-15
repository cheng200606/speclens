"""加载 spec.yaml 与 cases 目录（约定优于配置：repo 即数据库，无后端服务）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from bench.harness.schemas import CaseMeta, SpecMeta


@dataclass
class Case:
    """一个基准样本：meta.yaml + 若干代码文件。"""

    meta: CaseMeta
    root: Path
    _file_cache: dict[str, str] = field(default_factory=dict, repr=False)

    def read_file(self, name: str) -> str:
        """按 meta.files 中记录的相对路径读取代码文件（带缓存）。"""
        if name not in self._file_cache:
            self._file_cache[name] = (self.root / name).read_text(encoding="utf-8")
        return self._file_cache[name]

    def spec_dir(self) -> "Path":
        """案例所属规范目录（bench/cases/<spec>/<ID> -> bench/specs/<spec>）。

        I5：RQ4 仓库集目录带 "-repo" 后缀（react19-repo），共享 react19 的
        快照与冻结规则库，由 spec_name_for_case 剥离后缀。
        """
        return self.root.parents[2] / "specs" / spec_name_for_case(self)


def load_spec(spec_dir: Path) -> SpecMeta:
    data = yaml.safe_load((spec_dir / "spec.yaml").read_text(encoding="utf-8"))
    return SpecMeta.model_validate(data)


def spec_name_for_case(case: "Case") -> str:
    """案例所属规范名：目录名去掉 RQ4 仓库集的 "-repo" 后缀。

    I5 起真实仓库梯度案例放 bench/cases/react19-repo/（共享 react19 的快照与
    冻结规则库），目录名后缀用于与生死实验的 40 条基准分离口径。
    """
    return case.root.parent.name.removesuffix("-repo")


def load_cases(cases_dir: Path) -> list[Case]:
    """加载 cases_dir 下所有 `<CASE-ID>/meta.yaml`，按 case_id 排序。"""
    cases: list[Case] = []
    for case_dir in sorted(p for p in cases_dir.iterdir() if p.is_dir()):
        meta_path = case_dir / "meta.yaml"
        if not meta_path.exists():
            continue
        meta = CaseMeta.model_validate(
            yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        )
        if meta.case_id != case_dir.name:
            raise ValueError(
                f"case_id 与目录名不一致：meta={meta.case_id!r}, dir={case_dir.name!r}"
            )
        for rel in meta.files:
            if not (case_dir / rel).exists():
                raise FileNotFoundError(f"{meta.case_id}: 缺少代码文件 {rel!r}")
        cases.append(Case(meta=meta, root=case_dir))
    return cases
