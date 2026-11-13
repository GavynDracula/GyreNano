# GyreNano 电路板

[English](README.md)

现在按部件查找，不再从数十个版本目录中挑文件。文件名保留实际硬件版本号，方便与收到的样板对应。

| 部件 | 当前版本 | 状态 |
| --- | --- | --- |
| [FR4 键区](keyfield-fr4/README.zh-CN.md) | V33，KiCad + 嘉立创 EDA | 99.70 × 99.80 mm，**0.6 mm**，跨区域有真实电气连接；用户已上传 KiCad 版打样 |
| [FR4 独立区域备选](keyfield-fr4/alternative-isolated/README.md) | V32 KiCad | 保留原始备选；区域之间无电气连接 |
| [FPC 键区](keyfield-fpc/README.zh-CN.md) | V27 KiCad | 97.18 × 96.47 mm，0.11 mm；用户已提交试样 |
| [左右 holder](holders/README.md) | V22 原生嘉立创 EDA | 每侧七个 FFC 插座；用户已打板 |
| [PMW3610 sensor](sensor/README.md) | V22 原生嘉立创 EDA | 插座连接，保留原传感器光学结构 |

[采购 BOM](keyfield-fpc/BOM.zh-CN.md) · [可填写 CSV](keyfield-fpc/BOM.csv) · [打印文件入口](../files/README.md)

holder/sensor 的 `reference-kicad/` 仅保留旧设计来源；其中部分通孔缺阻焊开窗，EDA 版本已修正。重新下单请使用 EDA 工程，不要混用旧 Gerber。详见 [EDA 检查记录](eda-validation/README.md)。

当前等待实物折弯、焊接、承托和整机装配验证；尚不是量产放行版。0.4/0.8 mm 仅讨论过，文件仍是 0.6 mm。厂家审核与优惠资格以实际订单为准。

旧版生成脚本及跨版本依赖集中封存在 [工程快照](https://github.com/GavynDracula/GyreNano/releases/download/v0.2.0-prototype.1/GyreNano-EngineeringSnapshot-20261113.tar.gz)；恢复说明见 [开发文档](../docs/DEVELOPMENT.md)。
