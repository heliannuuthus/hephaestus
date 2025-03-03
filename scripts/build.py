#!/usr/bin/env python3
# scripts/build.py

import json
import os
import sys

from jinja2 import Environment, FileSystemLoader, select_autoescape

# 确保至少有一个命令行参数
if len(sys.argv) < 2:
    print("Usage: python build.py <template_name>")
    sys.exit(1)

# 获取模板名称
template_name = sys.argv[1]
template_dir = "templates"

# 初始化 Jinja2 环境
env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(),
    enable_async=True,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)

# 确保输出目录存在
os.makedirs(".github/workflows", exist_ok=True)

try:
    # 加载数据文件
    data_file_path = f"{template_dir}/{template_name}/data.json"
    with open(data_file_path) as f:
        data = json.load(f)

    # 渲染模板并输出到目标文件
    output_file = f".github/workflows/call-{template_name}.yml"
    env.get_template(f"{template_name}/index.j2").stream(
        data=data).dump(output_file)

    print(f"✅ Successfully generated {output_file}")

except FileNotFoundError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"❌ Error: Invalid JSON in {data_file_path}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
