# FR4 键区 — V33

[English](README.md)

当前为 **99.700 × 99.804 mm、双层、0.6 mm FR4、1 oz 铜**。整理没有修改 PCB、Gerber 或 EDA 工程内容；0.4 mm 只是讨论，尚未应用。

- 下单文件：[GyreNanoKeyfieldFR4V33-Gerber.zip](fabrication/GyreNanoKeyfieldFR4V33-Gerber.zip)，与此前交付一致。
- [KiCad 工程](kicad/GyreNanoKeyfieldFR4V33.kicad_pro)。
- [嘉立创 EDA 工程](eda/GyreNanoKeyfieldFR4V33/GyreNanoKeyfieldFR4V33.eprj3)，请保留整个目录；也可先解压 [EDA 工程包](eda/deliverables/GyreNanoKeyfieldFR4V33-EDAProject.zip)。不要把工程 ZIP 当 Gerber 上传。
- [V32 独立区域备选](alternative-isolated/README.md) 单独保留。

每半边仍需五根主列 FFC 加一根拇指 FFC。左手安装 C0–C4 + TL（18 键），右手 C0–C4 + TR（17 键）；不要同时接入两种拇指区。

区域间六条桥带有真实矩阵信号，平放时可通电测试。**装进曲面外壳前必须剪除跨区域桥并修齐边缘**，保留各列和拇指内部的原连接臂。断电裁切、清除铜屑后检查导通和绝缘。

已有 DRC/ERC、原生数据对照、128 种左右/裁切组合、承托接触面和板边检查记录；详见 [checks](checks/)。这些结果不代表薄 FR4 已通过材料折弯寿命或实际装配验证。

用户已上传 KiCad 版尝试打样；厂家最终审核和到货尚待确认。保持原 holder 与承托结构，收到空板后先试装和测导通，再逐步焊接。
