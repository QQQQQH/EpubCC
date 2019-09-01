#  EpubCC —— 基于OpenCC的Epub简繁中文转换工具

EpubCC支持epub格式的电子书的简繁体转换，依赖[OpenCC](https://github.com/BYVoid/OpenCC)。

## 使用方法

```
epubcc.py <infile> config
```

`<infile>`必须是epub格式，`config`为OpenCC中的json格式的配置文件，具体参考[OpenCC](https://github.com/BYVoid/OpenCC)的文档。
若`<infile>`的文件名为`in.epub`，则会在同一目录下生成`in.converted.epub`，若存在同名文件，则会覆盖。

## 依赖
- [Python3](https://www.python.org/)
    - lxml库(`pip install lxml`)
- [OpenCC](https://github.com/BYVoid/OpenCC)(请确保添加到系统环境)

## 注意
- EpubCC只支持epub格式的文件的转换。
- epub内的文件不能出现中文等非英文字符，否则会出现错误。

## 致谢
这个项目的实现离不开以下项目，感谢这些项目的开发者们：
- [OpenCC](https://github.com/BYVoid/OpenCC)