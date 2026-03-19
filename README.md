# Spots Detector and Correlator (SpotDetec)

最初的功能是用于 Single-vesicle tethering 的数据处理，即对 TIRF 下固定的脂质体荧光图像进行点检测与单/双通道统计。也可胜任于其他点检测和定位分析的任务。
支持批量处理与图形界面，可打包为 Windows 上可运行的 exe 文件（exe运行无需额外依赖，但打包时需要）。
有两个版本，中文和英文，不想自己打包可以直接下载 .exe 运行。

Originally designed for processing Single-vesicle tethering data, specifically performing spot detection and single/dual-channel statistics on fluorescence images of immobilized liposomes under TIRF microscopy. It is also capable of handling other spot detection and localization analysis tasks.
The software supports batch processing and features a graphical user interface (GUI). It can be packaged as a standalone Windows executable (.exe). Note that while running the .exe requires no additional dependencies, they are necessary during the packaging process.
This package has two version, Simplified Chinese and English. You may also download the .exe to run.

## 环境 Environment requirments

- git clone 到本地
- Python 3.10，Conda 推荐
- 创建环境：`conda env create -f environment.yml`
- 激活：`conda activate spotdetec`

- git clone ...
- [Recommend Python 3.10]
- Setup environments: `conda env create -f environment.yml`
- Activate environment: `conda activate spotdetec`


## 运行方式 How to run

### 图形界面 GUI

中文模式
```bash
conda activate spotdetec
python run_gui.py 
```
English version
```bash
conda activate spotdetec
python run_gui_en.py 
```

- **单通道模式**：选一张图或一个文件夹。统计每个视野的斑点大小分布、荧光强度分布、总个数、占视野面积比；结果与分布图保存到输出文件夹。
- **双通道模式**：下层/上层各选一个文件或两个文件夹（按文件名配对）；或单文件多通道时只选一个文件并设置通道索引。以下层为 mask，统计每个下层斑点上的上层荧光强度与上层点个数，并做强度比（上/下）与计数分布。

- **Single channel mode**: Select a single image or an input folder. The software quantifies, for each field of view (FOV): spot size distribution, fluorescence intensity distribution, total spot count, and area occupancy ratio. Results and distribution plots are automatically saved to the output folder.
- **Dual channel mode**: i) Input options: Select one file or a pair of folders for the lower/upper channels (images are paired by filename); or For multi-channel single files, select one file and specify the channel indices. Analysis workflow: Using spots detected in the lower channel as a mask, the software quantifies the upper-channel fluorescence intensity and spot count colocalized with each lower-channel spot. It then calculates the intensity ratio (upper/lower) and generates distribution plots for both ratio and colocalized spot counts.

### 命令行批量 CLI

```bash
python run_batch.py --mode single --input <文件或文件夹> --output <输出目录>
python run_batch.py --mode dual --input <下层文件夹> --input-upper <上层文件夹> --output <输出目录>
```

可选参数：`--diameter`、`--minmass`、`--separation`、`--sub-mask-radius`、`--preprocess-sigma`。

```bash
python run_batch.py --mode single --input <file or dir> --output <output dir>
python run_batch.py --mode dual --input <channel 1 dir> --input-upper <channel 2 dir> --output <output dir>
```

Optional parameters：`--diameter`、`--minmass`、`--separation`、`--sub-mask-radius`、`--preprocess-sigma`。

## 打包 Windows exe

在项目根目录：

```bash
conda activate spotdetec
pip install pyinstaller
pyinstaller Spots_Detector_and_Correlator_zh.spec
```

生成的 exe 在 `dist/Spots_Detector_and_Correlator_zh.exe`，可复制到无 Python 的 Windows 电脑上直接运行。


In the root dir：

```bash
conda activate spotdetec
pip install pyinstaller
pyinstaller Spots_Detector_and_Correlator.spec
```

The .exe could be found in `dist/Spots_Detector_and_Correlator.exe`.

## 参数说明 Parameters

- **Diameter**：斑点近似直径（像素，奇数），约 200 nm 脂质体在 TIRF 下常用 5–9。
- **Min mass**：最小积分亮度，用于过滤噪声。
- **Separation**：斑点最小间距（0 表示自动）。
- **Sub-mask radius**：双通道时以每个下层点为圆心、该半径（像素）画圆，在此圆内统计上层荧光和上层点个数。
- **Preprocess σ**：预处理高斯平滑强度，0 表示不做平滑。

- **Diameter**：Spot diameter（px，odds）
- **Min mass**：minimal integrated intensity, for noise filtering
- **Separation**：estimated minimal distance between two spots （for automatically determined by the program, set it to 0 ）。
- **Sub-mask radius**： For each spot detected in the lower channel, a circular region of interest (ROI) is defined centered at the spot centroid with a user-specified radius (in pixels). Within this ROI, the program quantifies: i) The integrated/mean fluorescence intensity of the upper channel; ii) The number of upper-channel spots colocalized within the circle.
- **Preprocess σ**：Gaussian smoothing, set it to 0 if do not want to do smoothing

## 输入格式 Inputs

- 图像格式：TIFF、PNG 等（TIFF 推荐，支持多通道）。
- 双通道：两个独立文件（下层/上层）或同一文件中的两个通道索引（0/1 等）。

- Image format：TIFF, PNG (Support multi-channel)。
- Dual channel：i) two separate files: one for the lower channel and one for the upper channel; or ii) Single multi-channel file: specify the channel indices (e.g., 0/1) to designate the lower and upper channels.

## 输出 Outputs

- 单通道：`<原名>_single.csv`（每行一个斑点：x, y, mass, size, area），`<原名>_summary.csv`，`<原名>_single_distributions.png`。
- 双通道：`<原名>_dual.csv`（每行一个下层斑点及对应上层强度、计数、强度比），`<原名>_summary.csv`，`<原名>_dual_distributions.png`。
- 批量汇总：批量处理完成后会额外生成 `batch_summary_single.csv` 或 `batch_summary_dual.csv`（每行对应一张图片/一对图片的 summary）。

- Single-Channel Mode:
  <original_name>_single.csv: One row per detected spot, containing columns: x, y, mass, size, area.
  <original_name>_summary.csv: Summary statistics for the entire field of view.
  <original_name>_single_distributions.png: Distribution plots (e.g., size, intensity) for visual inspection.
- Dual-Channel Mode:
  <original_name>_dual.csv: One row per lower-channel spot, with appended columns for colocalized upper-channel fluorescence intensity, spot count, and intensity ratio (upper/lower).
  <original_name>_summary.csv: Summary statistics for dual-channel analysis.
  <original_name>_dual_distributions.png: Distribution plots for intensity ratio, colocalized counts, etc.
- Batch Processing Summary: Upon completion of batch analysis, an additional aggregate file is generated:
  batch_summary_single.csv (for single-channel runs) or batch_summary_dual.csv (for dual-channel runs).
  Each row corresponds to the summary statistics of one image (or one image pair), enabling cross-sample comparison.


## 致谢 Acknowledgements

感谢一些开源轮子！
- trackpy : https://soft-matter.github.io/trackpy/dev/index.html
