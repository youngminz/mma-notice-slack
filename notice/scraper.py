import logging
import shlex
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from slackclient import SlackClient
from urllib3 import Retry

from django.conf import settings
from django.core.files import File

from .models import Attachment, Notice

logger = logging.getLogger(__name__)


def scrap_work_mma():
    session = requests.Session()
    slack_client = SlackClient(settings.SLACK_OAUTH2_TOKEN)

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
        shlex.split(link["onclick"].split("(")[1].split(")")[0].replace(",", " "))[2]
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
        content = content.text.strip()

        logger.debug(
            f"serial_number: %s, title: %s, writer: %s, date: %s",
            serial_number,
            title,
            writer,
            date,
        )

        notice, created = Notice.objects.update_or_create(
            serial_number=serial_number,
            defaults={
                "title": title,
                "writer": writer,
                "date": date,
                "view": view,
                "content": content,
            },
        )

        if created:
            slack_message = (
                "<!here> 병무청 공지사항에 새로운 글이 생성되었습니다. \n\n제목: %s\n작성자: %s\n작성일: %s\n조회수: %s\n내용: %s\n"
                % (title, writer, date, view, content)
            )

        attachments = [
            (file["href"], file.text.strip()) for file in attachments.select("a")
        ]

        for link, file_name in attachments:
            attachment_serial_number = link.split("cheombu_sn=")[1]

            if Attachment.objects.filter(
                notice=notice,
                serial_number=attachment_serial_number,
                file_name=file_name,
            ).exists():
                continue

            try:
                r = session.get("https://work.mma.go.kr" + link, stream=True)
                r.raise_for_status()

                bytes_ = BytesIO()
                for chunk in r.iter_content(1024):
                    bytes_.write(chunk)

                file = File(bytes_, file_name)

                attachment, _ = Attachment.objects.update_or_create(
                    notice=notice,
                    serial_number=attachment_serial_number,
                    file_name=file_name,
                    defaults={"file": file},
                )
                slack_message += f"\n{file_name}: {attachment.file.url}"

            except requests.RequestException:
                logger.exception("파일을 내려받는 중 오류가 발생했습니다.")
                Attachment.objects.update_or_create(
                    notice=notice, serial_number=serial_number, file_name=file_name
                )
                slack_message += f"\n{file_name}: (다운로드 실패)"

        logger.info(slack_message)
        slack_client.api_call(
            "chat.postMessage",
            channel=settings.SLACK_CHANNEL,
            text=slack_message,
            timeout=10,
            as_user=True,
        )
