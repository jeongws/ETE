# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request
import random
import urllib
from datetime import datetime, timedelta
from string import punctuation
from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = "xoxb-506274278966-508887142774-011NYeCDldk3keKmn9cDrqSt"
slack_client_id = "506274278966.508536747767"
slack_client_secret = "bcdb8c45e6640b574c1f4a604402a08f"
slack_verification = "DSlqei9RiyU2Cp2JOcf3oDDg"
sc = SlackClient(slack_token)

last_listen_word = ""
last_post_word = ""

# 크롤링 함수
def _crawl_portal_keywords(text):
    # 챗봇의 단어 리스트
    main_keywords = []
    lose_comment = "그런 단어는 없단다 나의 승리란다"
    temp1_keywords = []
    temp2_keywords = []

    ischatbot_lose = False
    fil = re.compile("<@[A-Z0-9]+>")
    fil_r = fil.findall(text)
    # 사용자의 마지막 단어
    user_word = text.replace(fil_r[0], "").replace(' ','') # <@!!!!!!> 가을

    # user_word = input()
    # user_word가 정상적인 단어라면,
    if iscurrect_user_word(user_word):

        #그 단어의 끝단어로 시작하는 리스트를 가져옴.
        main_keywords = startswith_endof_userword(user_word)

        chatbot_lose_test = main_keywords[0].find('a').get_text().strip().replace(' ','').replace('\n','')
        if chatbot_lose_test == "1패배敗北":
            temp2_keywords.append("내가졌다")
            ischatbot_lose = True

        # 패배한게 아니면 진행
        if not ischatbot_lose :
            #그 리스트에서 2글자 미만, 4글자 이상단어 삭제함
            main_keywords = word_2to3(main_keywords)

            #이, 히, 로 끝나는 것들 삭제
            for word in main_keywords:
                if remove_letter(word.find('a').get_text().strip()):
                    temp1_keywords.append(word)

            # 방언, 북한어 등 삭제
            for word in temp1_keywords:
                if contants_filter(word.find('small').get_text().strip()):
                    temp2_keywords.append(word)

            main_keywords = []
            for word in temp2_keywords:
                main_keywords.append(word.find('a').get_text().strip())
        # 패배 했으면
        else:
            main_keywords = []
            main_keywords.append(temp2_keywords[0])


        #리스트를 랜덤으로 돌려서 봇이 대답할 것 하나 골라줌
        ran_num = random.randrange(0,len(main_keywords))
        bot_answer = main_keywords[ran_num]

        # 마지막 전송 단어 저장
        global last_post_word
        last_post_word = bot_answer

    # user_word가 비정상적인 단어라면
    else:
        # user에게 패배를 선언해준다
        # main_keywords.append(lose_comment)
        bot_answer = lose_comment

    print(bot_answer)
    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return bot_answer
    # return u''.join(bot_answer)
    # return u'\n'.join(bot_answer)

# -----------------------------------------------------
# 방언, 규범, 북한어 음역어, 법호, 년도 같은 설명이 있는 단어 제외
# str(설명)를 입력받고
# True/False를 리턴한다.
# -----------------------------------------------------
def contants_filter(contents):
    # 사용 가능한 단어로 판별되면 True, 사용 불가 단어로 판별되면 False
    contents_tf = True
    filterword_list = ['규범', '북한어', '방언', '음역어', '법호']
    filteryear = re.compile(r"\d{4}~")
    filter_count = 0
    filter_count_cut = 5
    # 문자열의 리스트로 변환
    contents_list = contents.split('. ')
    # 문자열 리스트에서 하나씩 받아와서
    for content in contents_list:
        # filterword_list 가 있는지 찾아서 있으면, 사용불가 단어로 판별 후 탈출
        for filterword in filterword_list:
            if content.find(filterword) != -1:
                contents_tf = False
                break
        if not contents_tf:
            break
        # '년도~' 가 있는지 찾아서 있으면, 사용불가 단어로 판별 후 탈출
        if filteryear.search(content):
            contents_tf = False
            break
        # 몇 번째 문자열까지 필터 중인지 파악하고 필터횟수 제한
        filter_count += 1
        if filter_count == filter_count_cut:
            break
    return contents_tf

# -----------------------------------------------------
# 특정 단어로 끝나는 단어들 골라내기.
# str(단어)를 입력받고
# True/False를 리턴한다.
# -----------------------------------------------------
def remove_letter (word):

    compile_text = re.compile("[가-힣]")
    match_text = compile_text.findall(word)
    if len(word) != len(match_text):
        return False
    if word.endswith('다'):
        return False
    if word.endswith('히'):
        return False
    if word.endswith('이'):
        return False
    if word.endswith('한'):
        return False
    for i in word:
        if i == ' ':
            return False

    return True

# -----------------------------------------------------
# 유저 단어의 끝 단어로 검색하는 함수
# str(단어)를 입력받고
# list(단어 명단)을 리턴한다.
# -----------------------------------------------------
def startswith_endof_userword(text):

    page_num = 1
    main_keywords = []
    # 가져올 샘플단어 수 최소단위 100
    word_num = 100
    # 단어 검색 counter
    length = 0

    # %EF%95%90
    # 유저 단어맨 끝 글자를 유니코드로 변환
    user_word_uni = urllib.parse.quote(text[-1])
    # 검색 결과에 따라 엄청 다를 수가 있다. 제일 많은 '가'가 11000개로 110페이지까지 있으니 넉넉하게 30페이지로
    for i in range(0,(word_num//100)):
        url = "https://www.wordrow.kr/%EC%8B%9C%EC%9E%91%ED%95%98%EB%8A%94-%EB%A7%90/"+user_word_uni+"/?%EC%AA%BD="+str(page_num+i)
        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "lxml")

        # 시작하는 단어가 있는 경우 단어들 리스트에 추가
        for i in soup.find_all("h3", class_="card-caption"):
            if length >= word_num:
                break
            # tag a = 단어 / 단어를 keywords에 추가
            main_keywords.append(i)
            length += 1


        # 시작하는 단어가 없을 경우 / 게임 패배 했을 경우
        # 패배 한거 확인하는 조건 추가
        first_word = main_keywords[0].find('a').get_text().strip()
        if first_word[0] != text[-1]:
            main_keywords = []
            url = "https://www.wordrow.kr/%EC%9D%98%EB%AF%B8/%ED%8C%A8%EB%B0%B0/?q=%ED%8C%A8%EB%B0%B0"
            lose_sourcecode = urllib.request.urlopen(url).read()
            lose_soup = BeautifulSoup(lose_sourcecode, "lxml")
            for i in lose_soup.find_all("h3", class_="card-caption"):
                main_keywords.append(i)


    return main_keywords

# -----------------------------------------------------
# 유저 단어 검사 함수
# str(단어)를 입력받고
# True/False를 리턴한다.
# -----------------------------------------------------
def iscurrect_user_word(text):
    # 자음만 입력했으면 빠이
    consonants = ['ㄱ','ㄴ','ㄷ','ㄹ','ㅁ','ㅂ','ㅅ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
    for i in text:
        if i in consonants:
            return False

    # 모음만 입력했으면 빠이
    collections = ['ㅏ','ㅑ','ㅓ','ㅕ','ㅗ','ㅛ','ㅜ','ㅠ','ㅡ','ㅣ']
    for i in text:
        if i in collections:
            return False

    # 특수문자 있으면 빠이
    for i in text:
        if i in punctuation:
            return False

    # 한글자 단어면 빠이
    if len(text) < 2:
        return False

    # 공백이 있으면 빠이
    if i in text:
        if i == ' ':
            return False

    # # 마지막 전송 단어의 끝말잇기가 아니면 빠이
    # global last_post_word

    # if len(last_post_word) > 0:
    #     if text[0] is not last_post_word[-1]:
    #         return False

    # 검색 결과
    # 사용자 단어를 유니코드화 함
    try:
        user_word_uni = urllib.parse.quote(text)
        url = "https://www.wordrow.kr/%EC%9D%98%EB%AF%B8/"+user_word_uni
        sourcecode = urllib.request.urlopen(url).read()
    except :
        return False

    soup = BeautifulSoup(sourcecode, "lxml")

    # 검색했는데 없는 페이지 뜨면 빠이
    for i in soup.find_all("h2", class_= "card-caption"):
        return False

    # 저것들이 다 아닌 괜찮은 단어면 단어면 ㅇㅋ
    return True

# -----------------------------------------------------
# 2글자 미만, 4글자 이상 글자 다 걸러냄
# list(단어 명단)을 입력받고
# list(단어 명단)을 리턴한다.
# -----------------------------------------------------
def word_2to3(main_keywords):
    new_list = []
    for i in main_keywords:

        if len(i.find('a').get_text().strip()) > 3:
            continue
        elif 2 <= len(i.find('a').get_text().strip()) <= 3:
            new_list.append(i)
        else:
            continue

    return new_list


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print("event_handler", slack_event["event"])
    print(event_type)

    if event_type == "app_mention":

        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        #! 마지막 입력 단어와 비교 & 저장
        compile_word = re.compile("<@[A-Z0-9]+>")
        finded_text = compile_word.findall(text)
        compiled_text = text.replace(finded_text[0], "").replace(' ','') # <@!!!!!!> 가을

        global last_listen_word

        if last_listen_word is not compiled_text:
            last_listen_word = compiled_text
            keywords = _crawl_portal_keywords(text)
            sc.api_call(
                "chat.postMessage",
                channel=channel,
                text=keywords
            )

        return make_response("App mention message has been sent", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})

@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)



    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                            })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    # 슬랙 챗봇이 대답한다.
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # if "event" in slack_event and slack_event["event"]["type"] == "app_mention":
    #     _event_handler(slack_event["event"]["type"], slack_event)
    #     return make_response("App mention message has been sent", 200,)


    # hears 함수의 slack_event 아래에 코드 두줄을 넣어주세요
    if slack_event['event_time'] < (datetime.now() - timedelta(seconds=1)).timestamp():
        return make_response("this message is before sent.", 200, {"X-Slack-No-Retry": 1})

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})



@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    app.run(debug= True)
