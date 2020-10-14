import html
import logging
import shlex
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from django.conf import settings
from django.core.files import File

from .models import Notice

logger = logging.getLogger(__name__)


def scrap_work_mma():
    session = requests.Session()

    # 네트워크 통신에 실패했을 경우 {backoff factor} * (2 ^ ({number of total retries} - 1))초 이후 재시도
    retry = Retry(
        total=10,
        read=10,
        connect=5,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
        }
    )

    r = session.post(
        "https://work.mma.go.kr/caisBYIS/board/boardList.do",
        data={
            "gesipan_gbcd": 13,
            "tmpl_id": 1,
            "menu_id": "m_m8_6",
            "pageUnit": 999_999,
            "pageIndex": 1,
        },
    )

    soup = BeautifulSoup(r.text, "lxml")

    serial_numbers = [
        link["onclick"].split("(")[1].split(")")[0].replace(",", " ").split("'")[5]
        for link in soup.select("td a")
    ]

    for serial_number in serial_numbers:
        if Notice.objects.filter(serial_number=serial_number).exists():
            continue

        r = requests.post(
            "https://work.mma.go.kr/caisBYIS/board/boardView.do",
            data={
                "menu_id": "m_m8_6",
                "gesipan_gbcd": 13,
                "ilryeon_no": serial_number,
                "searchCondition": "",
                "searchKeyword": "",
                "pageIndex": 2,
                "pageUnit": 10,
            },
        )

        soup = BeautifulSoup(r.text, "lxml")

        title, writer, date, view, attachments, content = soup.select(
            "#boardViewform td"
        )

        title = title.text.strip()
        writer = writer.text.strip()
        date = date.text.strip()
        view = view.text.strip()
        content = str(content)
        content = content.replace('<td class="context" colspan="4">', '').replace('</td>', '').replace('<br/>', '\n')
        content = html.unescape(content)

        notice = Notice.objects.create(
            serial_number=serial_number,
            title=title,
            writer=writer,
            date=date,
            view=view,
            content=content,
        )

        if writer not in settings.MMA_LOCATION_LIST:
            continue

        slack_message = (
            "병무청 공지사항에 새로운 글이 생성되었습니다. \n\n```\n제목: %s\n작성자: %s\n작성일: %s\n내용: %s\n```"
            % (title, writer, date, content)
        )
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": slack_message,
                    }
                }
            ]
        }

        logger.info(slack_message)
        requests.post(settings.SLACK_INCOMING_WEBHOOK_URL, json=payload)
