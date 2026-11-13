# PMW3610 FFC sensor

[Native JLCEDA project](eda/GyreNanoSensor/GyreNanoSensor.eprj3) · [validation](../eda-validation/README.md) · [BOM](../keyfield-fpc/BOM.zh-CN.md)

The six-wire interface is replaced with a Molex 2005280060 FFC socket. Sensor pins 1–6 are SCLK_2 / SDIO_2 / NCS_2 / MOTION_2 / VCC / GND; preserve the verified reversed conductor mapping to the right holder J7. Sensor VCC is not a direct battery input.

The native EDA V22 version corrects U2 PTH solder-mask openings and increases mounting-hole ground-copper clearance. The old V5 KiCad and upstream files remain in `reference-kicad/` and `upstream/` for provenance; do not use them as interchangeable manufacturing exports.

The source stack totals 1.29 mm, not a confirmed finished-thickness order. Optical stack, cover clamp, real screw engagement and the original 34 mm trackball assembly still require physical checking.

Based on [ufan/charybdis-pmw3610-breakout](https://github.com/ufan/charybdis-pmw3610-breakout) and [victorlucachi/charybdis-pmw3610-breakout](https://github.com/victorlucachi/charybdis-pmw3610-breakout). The user's original Gerber was identified as victorlucachi's 2023-05-12 release; historical commit/file evidence is preserved in the engineering snapshot. Upstream authorship and license terms are retained.

中文：当前使用修正过阻焊开窗的 EDA 工程；旧 KiCad 仅作来源参考。继续使用原版镜片、传感器盖和轨迹球结构，实物光学堆叠尚未重新验证。
