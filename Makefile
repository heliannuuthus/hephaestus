# 定义模板目录
TEMPLATE_DIR := templates

# 获取所有子目录名（过滤掉普通文件，只保留目录）
SUBDIRS := $(patsubst $(TEMPLATE_DIR)/%,%,$(shell find $(TEMPLATE_DIR) -mindepth 1 -maxdepth 1 -type d))

# 定义最终输出文件路径
OUTPUT_DIR := .github/workflows
OUTPUT_FILES := $(addprefix $(OUTPUT_DIR)/call-,$(addsuffix .yml,$(SUBDIRS)))

# 默认目标：构建所有文件
all: $(OUTPUT_FILES)

# 确保输出目录存在
$(OUTPUT_DIR):
	@mkdir -p $@

# 单个文件的构建规则（增加输出目录依赖）
$(OUTPUT_DIR)/call-%.yml: templates/%/data.json templates/%/index.j2 | $(OUTPUT_DIR)
	@echo "🛠️  Building $@..."
	@python scripts/build.py $*

# 列出可用的模板
list:
	@echo "📋 Available templates:"
	@for dir in $(SUBDIRS); do echo "  - $$dir"; done

# 构建指定的模板
# 使用: make build TEMPLATE=workflow1
build:
ifdef TEMPLATE
	@echo "🛠️  Building $(TEMPLATE) template..."
	@python scripts/build.py $(TEMPLATE)
else
	@echo "❌ Please specify a template with TEMPLATE=name"
	@echo "Available templates:"
	@$(MAKE) -s list
endif

# 清理生成文件
clean:
	@echo "🧹 Cleaning generated files..."
	@rm -f $(OUTPUT_FILES)

.PHONY: all clean list build