# 사내 도우미 호스트

조가 만든 MCP 서버를 붙여 쓰는 채팅 앱이다. Day 13 조별 과제에 쓴다.

조가 낼 것은 **`server.py` 파일 하나**다. 호스트는 손대지 않는다.

```
mcp-host/
  compose.yml
  env.example
  host/            채팅창 · 모델 · MCP 클라이언트
  teams/
    team1/server.py   ← 조가 낸 파일
    team2/server.py
```

## 조가 낼 파일

`teams/조이름/server.py` 로 넣는다. 맨 아래는 **`mcp.run()`** 한 줄로 끝낸다.
전송 방식은 호스트나 `Dockerfile` 이 정하므로 여기에 적지 않는다.

```python
from fastmcp import FastMCP

mcp = FastMCP('점검 도우미')

@mcp.tool()
def defect_rate(machine: str) -> str:
    '''설비호기의 불량률을 돌려준다. 설비 품질을 물으면 이것을 쓴다.

    machine: 설비호기. 1호기 ~ 4호기
    '''
    ...

if __name__ == '__main__':
    mcp.run()
```

`teams/team1/` 을 그대로 베껴 쓰면 된다. `requirements.txt` 와 `Dockerfile` 도 같이 있다.

## 한 대에서 돌리기

키를 넣고 호스트만 띄운다. `teams/` 밑의 서버를 알아서 찾아 붙인다.

```bash
pip install -r host/requirements.txt
NVIDIA_API_KEY=nvapi-... python host/host.py
```

http://127.0.0.1:8000 을 연다.

## 컨테이너로 돌리기

```bash
cp env.example .env        # 키를 채운다
docker compose up -d --build
docker compose ps
```

http://127.0.0.1:8080 을 연다. 내릴 때는 `docker compose down`.

조를 늘리려면 `compose.yml` 에 서비스 한 칸을 더 적고 `TEAM_URLS` 에 주소를 더한다.

```yaml
  team3:
    build: ./teams/team3
    expose: ["8000"]
```

## 붙는 규칙

`teams/team1/server.py` 의 도구 `defect_rate` 는 **`team1_defect_rate`** 가 된다.

접두어를 안 붙이면 같은 이름의 도구끼리 **말없이 덮인다.** 먼저 붙은 것이 이기고
나중 것은 목록에서 사라진다. 조마다 접두어가 자동으로 붙으므로 이름이 겹쳐도 된다.

## 사내망에서

바깥이 막힌 곳에서는 세 자리가 걸린다.

| 막히는 곳 | 푸는 법 |
|---|---|
| `FROM python:3.12-slim` | 사내 저장소 주소로 바꾼다 |
| `pip install` | `--index-url` 로 사내 미러를 본다 |
| 아무것도 없을 때 | 바깥에서 `docker save`, 사내에서 `docker load` |

프록시만 있으면 빌드할 때 넘긴다.

```bash
docker build --build-arg HTTP_PROXY=$HTTP_PROXY --build-arg HTTPS_PROXY=$HTTPS_PROXY .
```

## 키

`NVIDIA_API_KEY` 는 환경변수나 `.env` 로 넘긴다. **`.env` 는 커밋하지 않는다.**
