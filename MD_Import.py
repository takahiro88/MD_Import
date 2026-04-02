# 2026.04.03 MD import script for Jama
# Need to set environment variables before running this script.

# set  AUTH_TYPE=BASIC or set  AUTH_TYPE=OAUTH
# set  JAMA_URL=https://your-target-jama-instance.com
# set  JAMA_USERNAME=your_username  (Only for BASIC auth)
# set  JAMA_PASSWORD=your_password  (Only for BASIC auth)
# if auth type is not BASIC, then set the following environment variables instead of above 3 variables.
# set JAMA_CLIENT_ID=XXX
# set JAMA_CLIENT_SECRET=XXX

# Usage: python MD_Import.py

from asyncio.log import logger
import time
import os
import re
from enum import Enum
import yaml
from datetime import datetime, date, timedelta
from py_jama_rest_client.client import JamaClient
from collections import OrderedDict
from markdown.extensions import toc

SETTING_FILE = "importSetting.yaml"

class JAMA_TYPE_ID(Enum):
    Component = 30
    Set = 31
    Folder = 32
    Item = 140  # STD ASE User Requirements (default from config)

# 設定ファイルの読み込み
if not os.path.exists(SETTING_FILE):
    logger.info(f"Setting file ({SETTING_FILE}) is not exist.")
    exit()
else:
    with open(SETTING_FILE, encoding="utf-8") as f:
        try:
            o = yaml.safe_load(f)
            if "settings" in o:
                if "input_file" in o["settings"]:
                    MD_DATA_FILE = o["settings"]["input_file"]
                else:
                    logger.error("入力するMDファイル名を指定してください")
                    exit()
                if "project_id" in o["settings"]:
                    PROJECT_ID = o["settings"]["project_id"]
                else:
                    logger.error("プロジェクトIDを指定してください")
                    exit()
                if "itemType" in o["settings"]:
                    ITEM_TYPE_ID = o["settings"]["itemType"]
                else:
                    ITEM_TYPE_ID = 140  # default

        except FileNotFoundError as e:
            logger.error("[ERROR] Config file is not found.")
            raise e
        except ValueError as e:
            logger.error("[ERROR] Config file is invalid.")
            raise e


class JamaAccess(JamaClient):

    def __init__(self):
        print('Started JamaAccess initialization')
        now = datetime.now()
        print(now)
        
        AUTH_TYPE = os.environ.get('AUTH_TYPE')

        if AUTH_TYPE == 'BASIC':
            import urllib3
            from urllib3.exceptions import InsecureRequestWarning
            urllib3.disable_warnings(InsecureRequestWarning)

            print('Using BASIC authentication')
            
            JAMA_URL = os.environ.get('JAMA_URL').rstrip('/')
            CREDENTIALS = (os.environ.get('JAMA_USERNAME'), os.environ.get('JAMA_PASSWORD'))
            super().__init__(JAMA_URL, credentials=CREDENTIALS, verify=False, allowed_results_per_page=50)

        else:
            print('Using OAUTH authentication')
            JAMA_URL = os.environ.get('JAMA_URL').rstrip('/')
            # 認証情報は環境変数にある前提
            CREDENTIALS = (os.environ.get('JAMA_CLIENT_ID'), os.environ.get('JAMA_CLIENT_SECRET')) 
            super().__init__(JAMA_URL, credentials=CREDENTIALS, oauth=True)
        self.JAMA_URL = JAMA_URL
        self.target_item_types_cache = None

    def print_error(self, message):
        """
        エラーメッセージを赤色で表示する
        """
        print(f"\033[91m{message}\033[0m")

    def print_warning(self, message):
        """
        警告メッセージを黄色で表示する
        """
        print(f"\033[93m{message}\033[0m")

    def create_item(self, name, description, item_type_id, parent_id=None, project_id=None):
        """
        Jamaアイテムを作成する
        """
        try:
            dct_fields = {
                "name": name,
                "description": description,
            }
            # 親のID指定
            locationItem = {"item": parent_id} if parent_id else {"project": project_id}  
            
            if item_type_id == JAMA_TYPE_ID.Set.value:
                child_itemType = ITEM_TYPE_ID
                dct_fields["setKey"] = "ABC"  # Setの必須フィールド（適宜変更）
            else:
                child_itemType = None
                    
            item_id = self.post_item(
                project=project_id,
                item_type_id = item_type_id,
                child_item_type_id=child_itemType,
                location=locationItem,
                fields=dct_fields
            )
            print(f"Created item: {name} (ID: {item_id})")
            return item_id
        except Exception as e:
            self.print_error(f"Error creating item '{name}': {str(e)}")
            return None

class MarkdownParser:
    """
    Markdownファイルを解析してJama用の階層構造を作成する
    """
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.hierarchy = []
        
    def parse(self):
        """
        Markdownファイルを解析して階層構造を返す
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            current_section = None
            current_content = []
            
            for line in lines:
                # 見出しの検出
                heading_match = re.match(r'^(#{2,5})\s*(.*)', line)
                
                if heading_match:
                    # 前のセクションを保存
                    if current_section:
                        current_section['content'] = '\n'.join(current_content).strip()
                        self.hierarchy.append(current_section)
                    
                    # 新しいセクションを開始
                    level = len(heading_match.group(1))
                    title = heading_match.group(2).strip()
                    
                    current_section = {
                        'level': level,
                        'title': title,
                        'content': '',
                        'jama_type': self._get_jama_type(level)
                    }
                    current_content = []
                    
                elif current_section:
                    # 現在のセクションの内容に追加
                    current_content.append(line)
            
            # 最後のセクションを保存
            if current_section:
                current_section['content'] = '\n'.join(current_content).strip()
                self.hierarchy.append(current_section)
                
            return self.hierarchy
            
        except Exception as e:
            print(f"Error parsing markdown file: {str(e)}")
            return []
    
    def _get_jama_type(self, level):
        """
        見出しレベルに応じたJamaタイプを返す
        ## (level 2) → Component
        ### (level 3) → Set  
        #### (level 4) → Item
        ##### (level 5) → Item (子)
        """
        if level == 2:
            return 'Component'
        elif level == 3:
            return 'Set'
        elif level >= 4:
            return 'Item'
        else:
            return 'Item'

def main():
    jama_access = JamaAccess()
    
    # Markdownファイルを解析
    print(f"Parsing Markdown file: {MD_DATA_FILE}")
    parser = MarkdownParser(MD_DATA_FILE)
    sections = parser.parse()
    
    if not sections:
        print("No sections found in the markdown file.")
        return
    
    print(f"Found {len(sections)} sections")
    
    # 階層構造を管理するためのスタック
    parent_stack = []  # [(level, item_id), ...]
    
    for section in sections:
        level = section['level']
        title = section['title']
        content = section['content']
        jama_type = section['jama_type']
        
        # 親を見つける（現在のレベルより小さいレベルの最後のアイテム）
        while parent_stack and parent_stack[-1][0] >= level:
            parent_stack.pop()
        
        parent_id = parent_stack[-1][1] if parent_stack else None
        
        # Jamaアイテムタイプを決定
        if jama_type == 'Component':
            item_type_id = JAMA_TYPE_ID.Component.value
        elif jama_type == 'Set':
            item_type_id = JAMA_TYPE_ID.Set.value
        else:
            item_type_id = ITEM_TYPE_ID  # config file setting
        
        # アイテムを作成
        print(f"Creating {jama_type}: {title} (parent: {parent_id})")
        item_id = jama_access.create_item(
            name=title,
            description=content,
            item_type_id=item_type_id,
            parent_id=parent_id,
            project_id=PROJECT_ID
        )
        
        if item_id:
            parent_stack.append((level, item_id))
            time.sleep(0.5)  # API制限を避けるための待機
        else:
            jama_access.print_error(f"Failed to create item: {title}")
    
    print("\nImport completed!")



if __name__ == "__main__":
    main()
