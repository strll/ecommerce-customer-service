import json
from pathlib import Path

import yaml

YAML_PATH = Path(__file__).resolve().parents[3] / "flow_config" / "user_flows.yml"

if __name__ == '__main__':
    with open(YAML_PATH, 'r', encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)

    # 将 Python 字典转换为格式化后的 JSON 字符串并打印
    formatted_json = json.dumps(yaml_data, indent=4, ensure_ascii=False)
    print(formatted_json)