# 胶片日期水印

用于批量为 JPG/JPEG 照片添加胶片机/数码相机日期戳风格水印的 Windows 桌面工具。

## 开发运行

```bash
python -m pip install -r requirements.txt
python app.py
```

## 功能概览

- 选择多个文件或递归选择文件夹
- 默认使用 EXIF 拍摄日期
- 支持统一指定日期
- 支持缺少 EXIF 时改用文件修改日期
- 支持右下角自适应定位
- 支持实时预览
- 支持保存/加载设置
- 成功输出到 `dated_output`
- 失败输出到 `dated_failed`

## 打包

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```
