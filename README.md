# TIRF 脂质体荧光分析 (SpotDetec)

对 TIRF 下固定/游离脂质体荧光图像进行点检测与单/双通道统计，支持批量与 GUI，可打包为 Windows 单机 exe。

## 环境

- Python 3.10，Conda 推荐
- 创建环境：`conda env create -f environment.yml`
- 激活：`conda activate spotdetec`

## 运行方式

### GUI（推荐）

```bash
conda activate spotdetec
python run_gui.py
```

- **单通道模式**：选一张图或一个文件夹。统计每个视野的斑点大小分布、荧光强度分布、总个数、占视野面积比；结果与分布图保存到输出文件夹。
- **双通道模式**：下层/上层各选一个文件或两个文件夹（按文件名配对）；或单文件多通道时只选一个文件并设置通道索引。以下层为 mask，统计每个下层斑点上的上层荧光强度与上层点个数，并做强度比（上/下）与计数分布。

### 命令行批量

```bash
python run_batch.py --mode single --input <文件或文件夹> --output <输出目录>
python run_batch.py --mode dual --input <下层文件夹> --input-upper <上层文件夹> --output <输出目录>
```

可选参数：`--diameter`、`--minmass`、`--separation`、`--sub-mask-radius`、`--preprocess-sigma`。

## 打包 Windows exe

在项目根目录：

```bash
conda activate spotdetec
pip install pyinstaller
pyinstaller TIRF_Liposome_Analysis.spec
```

生成的 exe 在 `dist/TIRF_Liposome_Analysis.exe`，可复制到无 Python 的 Windows 电脑上直接运行。

## 参数说明

- **Diameter**：斑点近似直径（像素，奇数），约 200 nm 脂质体在 TIRF 下常用 5–9。
- **Min mass**：最小积分亮度，用于过滤噪声。
- **Separation**：斑点最小间距（0 表示自动）。
- **Sub-mask radius**：双通道时以每个下层点为圆心、该半径（像素）画圆，在此圆内统计上层荧光和上层点个数。
- **Preprocess σ**：预处理高斯平滑强度，0 表示不做平滑。

## 输入格式

- 图像格式：TIFF、PNG 等（TIFF 推荐，支持多通道）。
- 双通道：两个独立文件（下层/上层）或同一文件中的两个通道索引（0/1 等）。

## 输出

- 单通道：`<原名>_single.csv`（每行一个斑点：x, y, mass, size, area），`<原名>_summary.csv`，`<原名>_single_distributions.png`。
- 双通道：`<原名>_dual.csv`（每行一个下层斑点及对应上层强度、计数、强度比），`<原名>_summary.csv`，`<原名>_dual_distributions.png`。
- 批量汇总：批量处理完成后会额外生成 `batch_summary_single.csv` 或 `batch_summary_dual.csv`（每行对应一张图片/一对图片的 summary）。
