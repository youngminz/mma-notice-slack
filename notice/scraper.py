import hashlib
import logging
import shlex
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from django.core.files import File

from .models import Attachment, Notice

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
        shlex.split(link["onclick"].split("(")[1].split(")")[0].replace(",", " "))[2]
        for link in soup.select("td a")
    ]

    for serial_number in serial_numbers:
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
            logger.info("[정보] 병무청 공지사항에 새로운 글이 생성되었습니다: %s", title)

        attachments = [
            (file["href"], file.text.strip()) for file in attachments.select("a")
        ]

        for link, file_name in attachments:
            attachment_serial_number = link.split("cheombu_sn=")[1]

            try:
                r = session.get("https://work.mma.go.kr" + link, stream=True)
                r.raise_for_status()

                bytes_ = BytesIO()
                for chunk in r.iter_content(1024):
                    bytes_.write(chunk)

                file = File(bytes_, file_name)

                Attachment.objects.update_or_create(
                    notice=notice,
                    serial_number=attachment_serial_number,
                    file_name=file_name,
                    defaults={"file": file},
                )

            except requests.RequestException:
                logger.exception("파일을 내려받는 중 오류가 발생했습니다.")
                Attachment.objects.update_or_create(
                    notice=notice, serial_number=serial_number, file_name=file_name
                )
