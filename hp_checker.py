# 必要なライブラリを読み込む
import requests
from bs4 import BeautifulSoup
import os
import json
import re # ファイル名に使えない文字を削除するために追加

### 設定が必要な項目 ###

# ### 変更点 ###
# 監視したいサイトの情報をここにまとめて設定します
# '任意の名前': {
#     'url': '監視したいサイトのURL',
#     'webhook': '通知を送りたいDiscordチャンネルのWebhook URL'
# }
# という形式で、カンマ(,)で区切って好きなだけ追加できます。

# Webhook URLを環境変数（Secrets）から読み込む
WEBHOOK_A = os.environ.get('WEBHOOK_A')
WEBHOOK_B = os.environ.get('WEBHOOK_B')
WEBHOOK_C = os.environ.get('WEBHOOK_C')

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


# 前回取得したWebページの内容を保存しておくフォルダ名
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
    # ### 変更点 ###
    # 通知先のwebhook_urlを引数で受け取るように変更
    headers = {'Content-Type': 'application/json'}
    data = {'content': message}
    try:
        response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
        response.raise_for_status()
        print("Discordに通知を送信しました。")
    except requests.exceptions.RequestException as e:
        print(f"エラー: Discordへの通知に失敗しました。 {e}")

def main():
    """メインの処理を実行する関数"""
    # 前回のデータを保存するフォルダがなければ作成する
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        print(f"データ保存用のフォルダ '{DATA_FOLDER}' を作成しました。")

    # ### 変更点 ###
    # 設定リスト(MONITORING_TARGETS)を一つずつ処理するループ
    for site_name, info in MONITORING_TARGETS.items():
        url = info['url']
        webhook = info['webhook']

        print(f"\n--- '{site_name}' ({url}) の更新をチェックします... ---")
        
        # サイト名からファイル名として使える文字列を生成
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", site_name) # ファイル名に使えない文字を除去
        data_file_path = os.path.join(DATA_FOLDER, f"{safe_filename}.txt")
        
        # 1. 現在のWebページの内容を取得
        current_content = get_website_content(url)
        
        if current_content is None:
            continue
            
        # 2. 前回の内容をファイルから読み込む
        previous_content = ""
        if os.path.exists(data_file_path):
            with open(data_file_path, 'r', encoding='utf-8') as f:
                previous_content = f.read()

        # 3. 前回と今回の内容を比較
        if current_content == previous_content:
            print("更新はありませんでした。")
        else:
            print(f"'{site_name}' が更新されました！")
            notification_message = f"[{site_name}] が更新されました。\n{url}"
            # ### 変更点 ###
            # そのサイトに対応するWebhook URLを使って通知を送る
            send_discord_notification(notification_message, webhook)
            
            # 4. 今回の内容をサイトごとのファイルに保存
            with open(data_file_path, 'w', encoding='utf-8') as f:
                f.write(current_content)
            print(f"新しい内容を {data_file_path} に保存しました。")

if __name__ == '__main__':
    main()

