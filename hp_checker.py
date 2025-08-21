# 必要なライブラリを読み込む
import requests
from bs4 import BeautifulSoup
import os
import json
import re
import difflib # 差分を比較するためのライブラリ

### 設定が必要な項目 ###

MONITORING_TARGETS = {
    'NEWS': {
        'url': 'https://www.thecaptains.jp/news',
        'webhook': 'https://discord.com/api/webhooks/1407661947691859999/uagFLjRLlaPKZ_sVDxfHwjgLY4rX6Zjf5RMTXSpJxEA_VVThJgYe5tuL7rBKLgiS83HE' # WEBHOOK_A
    },
    'LIVE': {
        'url': 'https://www.thecaptains.jp/live/',
        'webhook': 'https://discord.com/api/webhooks/1407664774229262410/HR_wZOngqFe7u6Qb35WMZS1kxD4eh_ODDRAdbIO9yZvCtFVYE1_VZ7JNMZWAZbBZAi3v' # WEBHOOK_B
    },
    'BLOG': {
        'url': 'https://www.fmgunma.com/captens_blog/',
        'webhook': 'https://discord.com/api/webhooks/1407700201426391070/yuUPY3ga1s3ndKqPIyK6O2-1s3nUgqvQSy2G-NhWPQQ4DpGvNENM60NTpOhp87HdbkT9' # WEBHOOK_C
    }
}

DATA_FOLDER = 'previous_data'

### ここから下がプログラムの本体 ###

def get_website_content(url):
    """Webサイトにアクセスして、タグを除いたテキスト内容を取得する関数"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        return '\n'.join(line.strip() for line in soup.get_text().splitlines() if line.strip())
    except requests.exceptions.RequestException as e:
        print(f"エラー: {url} にアクセスできませんでした。 {e}")
        return None

def send_discord_notification(message, webhook_url):
    """Discordに通知を送る関数"""
    headers = {'Content-Type': 'application/json'}
    data = {'content': message}
    try:
        response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
        response.raise_for_status()
        print("Discordに通知を送信しました。")
    except requests.exceptions.RequestException as e:
        print(f"エラー: Discordへの通知に失敗しました。 {e}")

# ### 変更点 ###
# 「追加」または「置換」が含まれているかを判定する新しい関数
def has_additions(old_text, new_text):
    """
    2つのテキストを比較し、内容に「追加」か「置換」が含まれている場合にTrueを返す関数。
    削除が同時にあっても、追加さえあればTrueになる。
    """
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    
    # 'equal'(変更なし), 'replace'(置換), 'delete'(削除), 'insert'(追加) の操作をチェック
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        # 追加(insert)か置換(replace)が見つかった時点でTrueを返してチェック終了
        if tag == 'insert' or tag == 'replace':
            return True
            
    # ループが終わっても追加・置換がなければFalse
    return False

def main():
    """メインの処理を実行する関数"""
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    for site_name, info in MONITORING_TARGETS.items():
        url = info['url']
        webhook = info['webhook']

        print(f"\n--- '{site_name}' ({url}) の更新をチェックします... ---")
        
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", site_name)
        data_file_path = os.path.join(DATA_FOLDER, f"{safe_filename}.txt")
        
        current_content = get_website_content(url)
        
        if current_content is None:
            continue
            
        previous_content = ""
        if os.path.exists(data_file_path):
            with open(data_file_path, 'r', encoding='utf-8') as f:
                previous_content = f.read()

        # ### 変更点 ###
        # 比較ロジックを新しい関数に入れ替え
        if current_content == previous_content:
            print("更新はありませんでした。")
        else:
            # 変更があった場合、「追加」か「置換」が含まれているかチェック
            if has_additions(previous_content, current_content):
                print(f"'{site_name}' が更新され、新しい内容が追加されました！")
                notification_message = f"[{site_name}] が更新され、新しい情報が追加されました。\n{url}"
                send_discord_notification(notification_message, webhook)
            else:
                print(f"'{site_name}' は更新されましたが、内容の追加はなく削除のみのため通知しません。")

            # 変更があった場合は、通知するしないに関わらず、最新の内容を保存する
            with open(data_file_path, 'w', encoding='utf-8') as f:
                f.write(current_content)
            print(f"新しい内容を {data_file_path} に保存しました。")


if __name__ == '__main__':
    main()
