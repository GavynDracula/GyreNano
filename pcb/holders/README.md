# Left / right holders

The current editable designs are the corrected native JLCEDA V22 projects:

- [Left holder](eda/GyreNanoHolderLeft/GyreNanoHolderLeft.eprj3).
- [Right holder](eda/GyreNanoHolderRight/GyreNanoHolderRight.eprj3).

Keep each project folder intact. Each holder has seven 6-pin FFC sockets: J1–J5 main columns, J6 thumb, J7 sensor (unused on the left). The controller/header mounting datums and battery/switch interfaces are retained. Source stack thickness is 1.6 mm; the actual order selections are not independently verified.

[EDA validation and deliberate changes](../eda-validation/README.md) · [BOM](../keyfield-fpc/BOM.zh-CN.md)

`reference-kicad/` contains the original V12 source boards and a local footprint library. **These older boards omit controller PTH solder-mask openings that were corrected in EDA.** They are provenance references, not the recommended reorder source.

中文：左右 holder 用户已打板；当前入口为原生嘉立创 EDA 工程，每侧七个插座。参考 KiCad 版保留原始数据，但旧阻焊开窗问题没有回填，重新下单请使用 EDA 版。项目叠层厚度与实际订单参数应区分。
