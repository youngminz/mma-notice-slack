# 병무청 공지사항 슬랙봇

병무청 산업지원 병역일터에 공지사항이 올라오면 슬랙으로 메시지를 전송합니다.

![screenshot](screenshot.png)

## 사용법

1. .env.example 파일을 참고하여 .env 파일을 만듭니다.
2. crontab으로 10분에 한 번씩 아래 명령어를 실행하도록 만듭니다.
```
$ python3 manage.py work_mma_scrap
```
