# Development workspace

Modeling sources and reference data live here so the repository root stays focused on delivery.

| Directory | Contents |
| --- | --- |
| `src/` | Baseline enclosure generators and mesh helpers |
| `parameters/` | Hardware dimensions and historical reference profiles |
| `references/` | Required upstream geometry, provenance and license records |
| `checks/` | Geometric regression and assembly checks |
| `scripts/` | Restore/export, rendering and delivery verification tools |

[Environment, commands and coordinates](../docs/DEVELOPMENT.md). Generated `exports/`, `reports/` and `previews/` stay local and are ignored. The integrated PCB-era pipeline is preserved in the optional release engineering snapshot.

中文：这里集中建模源、参数、基准模型和检查工具。打印/下单请回到根目录的 `files/`、`pcb/`；运行脚本前阅读开发说明，临时输出不再出现在主目录。
