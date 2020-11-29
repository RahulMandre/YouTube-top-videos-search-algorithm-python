# -*- coding: utf-8 -*-
"""
Created on Sat Nov 28 21:27:06 2020

@author: Rahul
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from apiclient.discovery import build
from sklearn.preprocessing import StandardScaler
import pickle
import sys
import yaml

if len(sys.argv) < 3:
    print('Usage: python ytsearch.py [keyword num_to_watch] - search top videos')
    sys.exit()
    

keyword=sys.argv[1]
print("keyword:",keyword)

num_to_watch=int(sys.argv[2])
print("number of videos (max 50):",num_to_watch)

#apr-key-from-youtube-data-api
with open(r'C:\Users\Rahul\Documents\python\youtube-search-results\youtubeProject\config.yaml', 'r') as cf:
      config= yaml.safe_load(cf)

apiKey=config['apiKey']

#open already watched video list
with open(r"C:\Users\Rahul\Documents\python\youtube-search-results\youtubeProject\already_watched_list.txt", "rb") as fp:   # Unpickling
      already_watched_videos = pickle.load(fp)

scaler = StandardScaler()

##custom_functions

def vid_stats(vid_id,youtube_api):
      """Get video statistics such as view counts, likes to dislike ratio and comment count"""
      video_statistics = youtube_api.videos().list(id=vid_id,part='statistics').execute()
      stat_dict=video_statistics['items'][0]['statistics']
      if 'likeCount' in stat_dict.keys():
            likes=int(stat_dict['likeCount'])
      else:
            likes=0
      if 'dislikeCount' in stat_dict.keys():
            dislikes=int(stat_dict['dislikeCount'])
      else:
            dislikes=0
      if dislikes==0:
            likes_dislike_ratio = likes
      else:
            likes_dislike_ratio=float(likes/dislikes)
      if 'commentCount' in stat_dict.keys():
            commentCount = int(stat_dict['commentCount'])
      else:
            commentCount =  -1
      view_cnt = int(stat_dict['viewCount'])
      return likes_dislike_ratio, commentCount, view_cnt     


def scan_results(keyword,apiKey):
      columns=['ID','Title', 'Video Link','Views','likes_dislike_ratio','commentCount','Publish Time']
      scale_cols=['Views','likes_dislike_ratio']
      df = pd.DataFrame()
      youtube_api = build('youtube', 'v3', developerKey = apiKey)
      results = youtube_api.search().list(q=keyword, part='snippet', type='video', order='viewCount', maxResults=50,relevanceLanguage='en',regionCode="IN").execute()
      for item in results['items']:
            vid_id=item['id']['videoId']
            title = item['snippet']['title']
            published_time=item['snippet']['publishedAt']
            vid_link = "https://www.youtube.com/watch?v=" + vid_id
            likes_dislike_ratio, commentCount, view_cnt = vid_stats(vid_id,youtube_api)
#            points = get_score(view_cnt, likes_dislike_ratio, commentCount)
            df_temp = pd.DataFrame([[vid_id,title, vid_link, view_cnt, likes_dislike_ratio, commentCount,published_time]],columns=columns)
            df=pd.concat([df,df_temp])
      scaler.fit(df[scale_cols])
      df[scale_cols]=scaler.transform(df[scale_cols])
      df['score']=df['Views']+df['likes_dislike_ratio']
      return df

def final_list(df,already_watched_videos,num_to_watch):
      df1=df.sort_values(['score'],ascending=False)
      df1=df1[~df1.ID.isin(already_watched_videos)]
      df1=df1.iloc[:num_to_watch,:]
      return df1


def top_videos(keyword,apiKey,already_watched_videos,num_to_watch):
      df=scan_results(keyword,apiKey)
      final_df=final_list(df,already_watched_videos,num_to_watch)
      already_watched_videos.extend(final_df.ID.tolist())
      with open(r"C:\Users\Rahul\Documents\python\youtube-search-results\youtubeProject\already_watched_list.txt", "wb") as fp:   #Pickling
            pickle.dump(already_watched_videos, fp)
      i=1
      for index,row in final_df.iterrows():
            print("#"*100)
            print("{}: Title: {}, Link: {}, Date: {}".format(i,row['Title'],row['Video Link'],row['Publish Time']))
            i=i+1
      return final_df


#final_command
recom=top_videos(keyword,apiKey, already_watched_videos,num_to_watch)