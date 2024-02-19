#!/usr/bin/env python
# coding: utf-8

# In[25]:


import requests
from bs4 import BeautifulSoup
from retry import retry
import urllib
import time
import numpy as np
import pandas as pd
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy import text


# In[36]:


# 複数ページの情報をまとめて取得
data_samples = []

# スクレイピングするページ数
max_page = 100
# SUUMOを桜山のみ指定して検索して出力した画面のurl(ページ数フォーマットが必要)
base_url = 'https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=050&bs=040&ra=023&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&ek=323016210&rn=3230'

# リクエストがうまく行かないパターンを回避するためのやり直し
@retry(tries=3, delay=10, backoff=2)
def load_page(url):
    html = requests.get(url)
    soup = BeautifulSoup(html.content, 'html.parser')
    return soup

# 処理時間を測りたい
start = time.time()
times = []


for page in range(1, max_page + 1):
    # ページネーション用のクエリパラメータを追加
    url = f'{base_url}&page={page}'
    soup = load_page(url)
    before = time.time()
    # 物件情報リストを指定
    mother = soup.find_all(class_='cassetteitem')
        
    # 物件ごとの処理
    for child in mother:

        # 建物情報
        data_home = []
        # カテゴリ
        data_home.append(child.find(class_='ui-pct ui-pct--util1').text)
        # 建物名
        data_home.append(child.find(class_='cassetteitem_content-title').text)
        # 住所
        data_home.append(child.find(class_='cassetteitem_detail-col1').text)
        # 最寄り駅のアクセス
        children = child.find(class_='cassetteitem_detail-col2')
        for id,grandchild in enumerate(children.find_all(class_='cassetteitem_detail-text')):
            data_home.append(grandchild.text)
        # 築年数と階数
        children = child.find(class_='cassetteitem_detail-col3')
        for grandchild in children.find_all('div'):
            data_home.append(grandchild.text)

        # 部屋情報
        rooms = child.find(class_='cassetteitem_other')
        for room in rooms.find_all(class_='js-cassette_link'):
            data_room = []
            
            # 部屋情報が入っている表を探索
            for id_, grandchild in enumerate(room.find_all('td')):
                # 階
                if id_ == 2:
                    data_room.append(grandchild.text.strip())
                # 家賃と管理費
                elif id_ == 3:
                    data_room.append(grandchild.find(class_='cassetteitem_other-emphasis ui-text--bold').text)
                    data_room.append(grandchild.find(class_='cassetteitem_price cassetteitem_price--administration').text)
                # 敷金と礼金
                elif id_ == 4:
                    data_room.append(grandchild.find(class_='cassetteitem_price cassetteitem_price--deposit').text)
                    data_room.append(grandchild.find(class_='cassetteitem_price cassetteitem_price--gratuity').text)
                # 間取りと面積
                elif id_ == 5:
                    data_room.append(grandchild.find(class_='cassetteitem_madori').text)
                    data_room.append(grandchild.find(class_='cassetteitem_menseki').text)
                # url
                elif id_ == 8:
                    get_url = grandchild.find(class_='js-cassette_link_href cassetteitem_other-linktext').get('href')
                    abs_url = urllib.parse.urljoin(url,get_url)
                    data_room.append(abs_url)
            # 物件情報と部屋情報をくっつける
            data_sample = data_home + data_room
            data_samples.append(data_sample)
    
    # 1アクセスごとに1秒休む
    time.sleep(1)
    
    # 進捗確認
    # このページの作業時間を表示
    after = time.time()
    running_time = after - before
    times.append(running_time)
    print(f'{page}ページ目：{running_time}秒')
    # 取得した件数
    print(f'総取得件数：{len(data_samples)}')
    # 作業進捗
    complete_ratio = round(page/max_page*100,3)
    print(f'完了：{complete_ratio}%')
    # 作業の残り時間目安を表示
    running_mean = np.mean(times)
    running_required_time = running_mean * (max_page - page)
    hour = int(running_required_time/3600)
    minute = int((running_required_time%3600)/60)
    second = int(running_required_time%60)
    print(f'残り時間：{hour}時間{minute}分{second}秒\n')

# 処理時間を測りたい
finish = time.time()
running_all = finish - start
print('総経過時間：',running_all)


# In[37]:


# data_samplesをDataFrameに変換
columns = ['property_type', 'building_name', 'address', 'access_1', 'access_2', 'access_3',
    'age', 'building_floors', 'room_floor', 'rent', 'management_fee',
    'deposit', 'gratuity', 'layout', 'area', 'url']
df = pd.DataFrame(data_samples, columns=columns)

# 現在の日付を掲載日として入力
current_date = date.today()
df['posting_date'] = current_date


# In[38]:


df


# In[39]:


# 重複行を削除
df_unique = df.drop_duplicates()

df_unique


# # データの保存

# In[40]:


df_unique.to_csv('scraped_data.csv')


# # データベース関連の処理

# In[41]:


# CSVファイルを読み込む
df = pd.read_csv('scraped_data.csv', index_col=0)


# In[42]:


import configparser

config = configparser.ConfigParser()
config.read('config.ini')

db_user = config['database']['user']
db_password = config['database']['password']
db_host = config['database']['host']
db_name = config['database']['name']


# In[43]:


# PostgreSQLデータベースへの接続情報
engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}')

# dbを読み込み
db_df = pd.read_sql_table('rental_properties', engine)


# In[44]:


# 新規レコードの挿入
## スクレイピングしたデータ（df）にあって、データベース（db_df）にないレコードを特定
new_records = df.merge(db_df, on=['url'], how='left', indicator=True).loc[lambda x : x['_merge']=='left_only']

## 不要なカラムを削除
new_records = new_records.drop(columns=['_merge'])

## 新規レコードに掲載日を設定
new_records['posting_date'] = current_date

# カラム名を修正するためのrename操作
new_records.rename(columns={
    'property_type_x': 'property_type',
    'building_name_x': 'building_name',
    'address_x': 'address',
    'access_1_x': 'access_1',
    'access_2_x': 'access_2',
    'access_3_x': 'access_3',
    'age_x': 'age',
    'building_floors_x': 'building_floors',
    'room_floor_x': 'room_floor',
    'rent_x': 'rent',
    'management_fee_x': 'management_fee',
    'deposit_x': 'deposit',
    'gratuity_x': 'gratuity',
    'layout_x': 'layout',
    'area_x': 'area',
    'url_x': 'url',
    'posting_date_x': 'posting_date'
}, inplace=True)

# 例: 不要なカラムを削除し、必要なカラムのみを選択
cleaned_df = new_records[['building_name', 'address', 'access_1', 'access_2', 'access_3', 'age', 'building_floors', 'room_floor', 'rent', 'management_fee', 'deposit', 'gratuity', 'layout', 'area', 'url', 'posting_date']].copy()

## 新規レコードをデータベースに挿入
cleaned_df.to_sql('rental_properties', engine, if_exists='append', index=False)


# In[45]:


# 削除されたレコードの特定と更新
## データベースにあって、スクレイピングしたデータにないレコードを特定
removed_records = db_df.merge(df, on=['url'], how='left', indicator=True).loc[lambda x : x['_merge'] == 'left_only']

## removed_dateを更新
for index, row in removed_records.iterrows():
    update_query = text("UPDATE rental_properties SET removed_date = :current_date WHERE url = :url")
    engine.execute(update_query, current_date=current_date, url=row['url'])


# In[ ]:




