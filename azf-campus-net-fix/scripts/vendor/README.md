# vendor 说明

## yaml/ —— PyYAML

- **来源**：PyPI 包 `PyYAML`
- **版本**：6.0.2
- **许可证**：MIT（见 https://github.com/yaml/pyyaml/blob/main/LICENSE ）
- **只取了纯 Python 部分**：不含 C 扩展 `_yaml*.pyd`。

### 为什么要 vendor

换电脑后目标机器可能没有 PyYAML，而本工具**不应该联网 pip 安装依赖**。
内置一份之后，只要有 Python 3 就能直接跑。

### 为什么只取纯 Python 部分

`_yaml.cp313-win_amd64.pyd` 是 Python 3.13 + Windows amd64 专用的；带到别的
Python 版本上加载不了。纯 Python 版本跨版本、跨平台通用。

实测代价可接受：解析 452 KB / 70 节点的真实 Clash 配置耗时 **0.35 秒**
（本机 Clash Verge 生成的运行时配置）。

### 为什么不能绕开 YAML

Clash Verge 生成的配置有 **block-style** 与 **flow-style** 两种写法：

```yaml
# block-style
- name: A
  type: vless

# flow-style
- { name: A, type: vless }
```

早期版本用正则解析，在 flow-style 上整段漏掉了 45 个节点。所以必须有真正的
YAML 解析器。回归测试见 `scripts/tests/test_all.py::TestYaml`。

### 加载顺序

`scripts/campus_net_fix/yamlcompat.py` 会先尝试系统安装的 PyYAML，
缺失时才回退到这里的副本，并在机器档案里记录实际来源（`runtime.yaml_source`）。
