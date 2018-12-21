import urllib.request
from bs4 import BeautifulSoup
import urllib
import time
from string import punctuation

def main():
    # 챗봇의 단어 리스트
    keywords = []

    # 사용자의 마지막 단어
    user_word = input()
    # user_word가 정상적인 단어라면,
    if iscurrect_user_word(user_word):
        #그 단어의 끝단어로 시작하는 리스트를 가져옴.
        keywords = startswith_endof_userword(user_word)
        #그 리스트에서 2글자 미만, 4글자 이상단어 삭제함
        keywords = word_2to3(keywords)
    else: 
        keywords.append("그런 단어는 없단다 나의 승리란다")
    print(keywords)

# -----------------------------------------------------
# 유저 단어의 끝 단어로 검색하는 함수
# str(단어)를 입력받고
# list(단어 명단)을 리턴한다.
# -----------------------------------------------------
def startswith_endof_userword(text):
    page_num = 1
    keywords = []
    # 가져올 샘플단어 수 최소단위 100
    word_num = 100
    # 단어 검색 counter
    length = 0
    lose_game = False

    # 유저 단어맨 끝 글자를 유니코드로 변환
    user_word_uni = urllib.parse.quote(text[-1])
    # 검색 결과에 따라 엄청 다를 수가 있다. 제일 많은 '가'가 11000개로 110페이지까지 있으니 넉넉하게 30페이지로 
    for i in range(0,(word_num//100)):
        url = "https://www.wordrow.kr/%EC%8B%9C%EC%9E%91%ED%95%98%EB%8A%94-%EB%A7%90/"+user_word_uni+"/?%EC%AA%BD="+str(page_num+i)
        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "lxml")

        # 시작하는 단어가 없을 경우 / 게임 패배 했을 경우
        for i in soup.find_all("span", class_= "h4 text-warning"):
            keywords.append("졌다")
            lose_game = True
            break
        
        if lose_game:
            lose_game = False
            break

        # 시작하는 단어가 있는 경우 단어들 리스트에 추가
        for i in soup.find_all("h3", class_="card-caption"):
            if length >= word_num:
                break
            # tag a = 단어 / 단어를 keywords에 추가
            keywords.append(i.find('a').get_text().strip())
            length += 1
    return keywords

# -----------------------------------------------------
# 유저 단어 검사 함수
# str(단어)를 입력받고
# True/False를 리턴한다.
# -----------------------------------------------------
def iscurrect_user_word(text):
    
    # 자음을 입력했으면 빠이
    consonants = ['ㄱ','ㄴ','ㄷ','ㄹ','ㅁ','ㅂ','ㅅ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
    for i in text:
        if i in consonants:
            return False

    # 특수문자 있으면 빠이
    for i in text:
        if i in punctuation:
            return False

    # 한글자 단어면 빠이
    if len(text) < 2:
        return False
    
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
def word_2to3(keywords):
    new_list = []
    for i in keywords:
        if len(i) > 3:
            continue
        elif 2 <= len(i) <= 3:
            new_list.append(i)
        else:
            continue

    return new_list


if __name__ == "__main__":
    main()
