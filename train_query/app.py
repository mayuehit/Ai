import re
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

_station_cache: dict[str, str] = {}


def load_stations() -> dict[str, str]:
    if _station_cache:
        return _station_cache
    url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.12306.cn/",
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    # Each entry: @pinyin|中文站名|CODE|...
    for name, code in re.findall(r"@[\w]+\|([一-龥]+)\|([A-Z]+)\|", resp.text):
        _station_cache[name] = code
    return _station_cache


def parse_ticket(raw: str, station_map: dict) -> dict | None:
    p = raw.split("|")
    if len(p) < 35:
        return None
    duration_str = p[10]  # e.g. "04:48"
    try:
        h, m = map(int, duration_str.split(":"))
        duration_minutes = h * 60 + m
    except ValueError:
        duration_minutes = 9999

    def seat(val: str) -> str:
        return val if val and val != "0" else "无"

    return {
        "train_code": p[3],
        "from_station": station_map.get(p[6], p[6]),
        "to_station": station_map.get(p[7], p[7]),
        "depart_time": p[8],
        "arrive_time": p[9],
        "duration": duration_str,
        "duration_minutes": duration_minutes,
        "can_buy": p[11] == "Y",
        "business_seat": seat(p[32]),   # 商务座
        "first_class": seat(p[31]),     # 一等座
        "second_class": seat(p[30]),    # 二等座
        "soft_sleeper": seat(p[23]),    # 软卧
        "hard_sleeper": seat(p[28]),    # 硬卧
        "hard_seat": seat(p[29]),       # 硬座
        "no_seat": seat(p[26]),         # 无座
    }


def query_tickets(from_name: str, to_name: str, date: str):
    stations = load_stations()
    from_code = stations.get(from_name)
    to_code = stations.get(to_name)
    if not from_code:
        return None, f"找不到出发站「{from_name}」，请检查站名是否正确"
    if not to_code:
        return None, f"找不到到达站「{to_name}」，请检查站名是否正确"

    url = "https://kyfw.12306.cn/otn/leftTicket/query"
    params = {
        "leftTicketDTO.train_date": date,
        "leftTicketDTO.from_station": from_code,
        "leftTicketDTO.to_station": to_code,
        "purpose_codes": "ADULT",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
    }
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("status"):
        msg = data.get("messages") or data.get("message") or "12306 返回错误"
        return None, str(msg)

    result_list = data.get("data", {}).get("result", [])
    station_map = data.get("data", {}).get("map", {})
    trains = [t for raw in result_list if (t := parse_ticket(raw, station_map))]
    return trains, None


@app.route("/", methods=["GET", "POST"])
def index():
    trains = None
    error = None
    form = {"from_station": "", "to_station": "", "date": "", "sort_by": "duration"}

    if request.method == "POST":
        form = {
            "from_station": request.form.get("from_station", "").strip(),
            "to_station": request.form.get("to_station", "").strip(),
            "date": request.form.get("date", "").strip(),
            "sort_by": request.form.get("sort_by", "duration"),
        }
        try:
            trains, error = query_tickets(
                form["from_station"], form["to_station"], form["date"]
            )
            if trains is not None:
                key = "duration_minutes" if form["sort_by"] == "duration" else "depart_time"
                trains.sort(key=lambda t: t[key])
        except requests.RequestException as e:
            error = f"网络请求失败：{e}"
        except Exception as e:
            error = f"查询出错：{e}"

    return render_template("index.html", trains=trains, error=error, form=form)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
