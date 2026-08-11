#!/usr/bin/env python3
"""RAG 실습용 문서 수집기.  python3 data/fetch_docs.py

위키문헌(ko.wikisource.org)에서 법령 조문을 받아 docs/data/docs/*.txt 로 저장한다.
법령은 저작권법 제7조에 따라 보호 대상이 아니라 그대로 쓸 수 있다.
지어낸 문서가 아니라 실제 조문이라, 검색 결과를 원문과 대조해 볼 수 있다.

받는 것
  근로기준법                      연차·근로시간·휴게 — 누구나 궁금한 질문이 나온다
  산업안전보건법                   안전보건교육·작업중지 — 제조 현장 질문
  산업기술의 유출방지 및 보호에 관한 법률   국가핵심기술 — 반출 통제와 이어진다
  개인정보 보호법                  수집·이용·파기 — 데이터 다루는 사람 질문
"""
import json
import os
import re
import urllib.parse
import urllib.request

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "docs", "data", "docs")
UA = "posco-lecture/1.0 (lecture material)"

DOCS = [
    ("근로기준법",                          "labor_standards.txt"),
    ("산업안전보건법",                       "occupational_safety.txt"),
    ("산업기술의 유출방지 및 보호에 관한 법률",   "industrial_tech.txt"),
    ("개인정보 보호법",                      "privacy.txt"),
]


def extract(title):
    u = ("https://ko.wikisource.org/w/api.php?action=query&prop=extracts"
         "&explaintext=1&format=json&redirects=1&titles=" + urllib.parse.quote(title))
    req = urllib.request.Request(u, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as f:
        page = list(json.load(f)["query"]["pages"].values())[0]
    return page.get("extract", "") or ""


def clean(text, title):
    text = text.replace(" ", " ")
    text = re.sub(r"^\s*==+\s*(부칙|별표|연혁|같이 보기|라이선스)[\s\S]*$", "", text,
                  flags=re.M)
    # 조문만 남긴다
    i = text.find("제1조")
    if i > 0:
        text = text[i:]
    # 장 제목은 남기되 위키 마크업은 지운다
    text = re.sub(r"=+\s*([^=\n]+?)\s*=+", r"\n[\1]\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    head = ("# %s\n"
            "# 출처: 위키문헌 ko.wikisource.org · 법령은 저작권법 제7조에 따라 보호 대상이 아니다\n"
            "# 강의 실습용으로 조문 부분만 추려 담았다. 최신 개정 여부는 국가법령정보센터에서 확인한다.\n\n"
            % title)
    return head + text


def main():
    os.makedirs(OUT, exist_ok=True)
    for title, fn in DOCS:
        body = clean(extract(title), title)
        p = os.path.join(OUT, fn)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
        print("%-28s %6d자  %s" % (title, len(body), fn))


if __name__ == "__main__":
    main()
