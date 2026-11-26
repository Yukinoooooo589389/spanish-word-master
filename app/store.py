"""数据层：词库装载、SRS 复习调度、进度持久化。

刻意不依赖数据库：全部状态落在一个 JSON 里，方便备份与迁移。
"""
from __future__ import annotations

import json
import os
import random
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))

if FROZEN:
    # 打包成 exe 后：数据随包解到临时目录，用户进度写在 exe 旁边
    APP_ROOT = Path(sys.executable).resolve().parent
    DATA_DIR = Path(getattr(sys, "_MEIPASS", APP_ROOT)) / "data"
else:
    APP_ROOT = Path(__file__).resolve().parent.parent
    DATA_DIR = APP_ROOT / "data"

USER_DIR = Path(os.environ.get("PALABRA_USER_DIR") or (APP_ROOT / "userdata"))
STATE_FILE = USER_DIR / "state.json"

# Leitner 间隔（天）；box 0 表示当天重来
INTERVALS = [0, 1, 2, 4, 7, 15, 30]
MAX_BOX = 5

LEVELS = ["A1", "A2", "B1"]
RATING_AGAIN, RATING_HARD, RATING_GOOD = 1, 2, 3


@dataclass(slots=True)
class Word:
    id: str
    es: str
    zh: str
    pos: str
    level: str
    theme: str
    ex_es: str = ""
    ex_zh: str = ""

    @property
    def primary(self) -> str:
        """去掉冠词后的词形，用于检索与去重展示。"""
        for art in ("el ", "la ", "los ", "las "):
            if self.es.lower().startswith(art):
                return self.es[len(art):]
        return self.es


@dataclass(slots=True)
class Card:
    box: int = 0
    due: str = ""
    seen: int = 0
    correct: int = 0
    wrong: int = 0
    last: str = ""

    def to_json(self) -> dict:
        return {
            "box": self.box, "due": self.due, "seen": self.seen,
            "correct": self.correct, "wrong": self.wrong, "last": self.last,
        }

    @classmethod
    def from_json(cls, d: dict) -> "Card":
        return cls(
            box=int(d.get("box", 0)), due=str(d.get("due", "")),
            seen=int(d.get("seen", 0)), correct=int(d.get("correct", 0)),
            wrong=int(d.get("wrong", 0)), last=str(d.get("last", "")),
        )


# 词库文件缺失时的最小可用集合（保证程序永远能打开）
FALLBACK_WORDS = [
    ("la casa", "房子；家", "n.f.", "A1", "居家", "Mi casa está cerca del parque.", "我的家离公园很近。"),
    ("el agua", "水", "n.f.", "A1", "饮食", "Bebo mucha agua todos los días.", "我每天喝很多水。"),
    ("el libro", "书", "n.m.", "A1", "学习", "Este libro es muy interesante.", "这本书很有意思。"),
    ("hablar", "说；讲", "v.", "A1", "社会", "¿Hablas español un poco?", "你说一点西班牙语吗？"),
    ("comer", "吃", "v.", "A1", "饮食", "Comemos a las dos de la tarde.", "我们下午两点吃饭。"),
    ("vivir", "居住；生活", "v.", "A1", "生活", "Vivo en una ciudad pequeña.", "我住在一座小城市。"),
    ("trabajar", "工作", "v.", "A1", "工作", "Trabajo en una oficina del centro.", "我在市中心的一间办公室工作。"),
    ("el amigo", "朋友", "n.m.", "A1", "情感", "Mi amigo vive en Madrid.", "我的朋友住在马德里。"),
    ("la ciudad", "城市", "n.f.", "A1", "旅行", "La ciudad está llena de turistas.", "这座城市到处都是游客。"),
    ("el tiempo", "时间；天气", "n.m.", "A1", "时间", "Hoy no tengo mucho tiempo.", "今天我没有很多时间。"),
    ("bonito", "漂亮的；好看的", "adj.", "A1", "抽象", "El jardín es muy bonito en primavera.", "春天的花园非常漂亮。"),
    ("siempre", "总是", "adv.", "A1", "时间", "Siempre desayuno antes de salir.", "我出门前总是先吃早饭。"),
    ("el viaje", "旅行", "n.m.", "A1", "旅行", "El viaje duró tres horas.", "这趟旅行持续了三个小时。"),
    ("aprender", "学习；学会", "v.", "A1", "学习", "Quiero aprender español este año.", "今年我想学西班牙语。"),
    ("la salud", "健康", "n.f.", "A2", "身体", "La salud es lo más importante.", "健康是最重要的。"),
    ("el trabajo", "工作；作品", "n.m.", "A1", "工作", "Termino el trabajo a las seis.", "我六点完成工作。"),
    ("la familia", "家庭", "n.f.", "A1", "情感", "Mi familia es bastante grande.", "我的家庭人挺多。"),
    ("la playa", "海滩", "n.f.", "A1", "旅行", "En verano vamos a la playa.", "夏天我们去海滩。"),
    ("el mercado", "市场", "n.m.", "A1", "购物", "Compro fruta en el mercado.", "我在市场买水果。"),
    ("entender", "理解；明白", "v.", "A1", "学习", "No entiendo esta palabra.", "我不明白这个词。"),
    ("la luz", "光；灯", "n.f.", "A2", "自然", "La luz de la tarde es muy suave.", "傍晚的光很柔和。"),
    ("el camino", "道路；途径", "n.m.", "A2", "旅行", "El camino al pueblo es largo.", "去村庄的路很长。"),
    ("cansado", "累的；疲倦的", "adj.", "A1", "身体", "Estoy cansado después del viaje.", "旅行之后我很累。"),
    ("la pregunta", "问题", "n.f.", "A1", "社会", "Tengo una pregunta sobre el examen.", "我有一个关于考试的问题。"),
]


def _today_str() -> str:
    return date.today().isoformat()


def _norm_key(word: str) -> str:
    w = word.strip().lower()
    for art in ("el ", "la ", "los ", "las "):
        if w.startswith(art):
            return w[len(art):]
    return w


class Store:
    """全局单一数据源。UI 只读，写入走 rate()/set_setting() 等方法。"""

    def __init__(self) -> None:
        self.words: list[Word] = []
        self.by_id: dict[str, Word] = {}
        self.cards: dict[str, Card] = {}
        self.settings: dict = {"daily_goal": 20, "theme": "light", "tts": True}
        self.history: dict[str, dict] = {}
        self.load_words()
        self.load_state()

    # ------------------------------------------------------------ 载入

    def load_words(self) -> None:
        raw: list[dict] = []
        if DATA_DIR.exists():
            for path in sorted(DATA_DIR.glob("words_*.json")):
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(payload, list):
                        raw.extend(x for x in payload if isinstance(x, dict))
                except Exception:
                    continue

        if not raw:
            raw = [
                {"es": es, "zh": zh, "pos": pos, "level": lv, "theme": th,
                 "ex_es": ex, "ex_zh": exz}
                for es, zh, pos, lv, th, ex, exz in FALLBACK_WORDS
            ]

        seen: set[str] = set()
        for i, item in enumerate(raw, start=1):
            es = str(item.get("es", "")).strip()
            zh = str(item.get("zh", "")).strip()
            if not es or not zh:
                continue
            key = _norm_key(es)
            if key in seen:
                continue
            seen.add(key)
            wid = str(item.get("id") or f"w{i:04d}")
            while wid in self.by_id:
                wid += "x"
            w = Word(
                id=wid, es=es, zh=zh,
                pos=str(item.get("pos", "")).strip() or "—",
                level=str(item.get("level", "A1")).strip().upper()[:2] if str(item.get("level", "A1")).strip().upper()[:2] in LEVELS else "A1",
                theme=str(item.get("theme", "")).strip() or "日常",
                ex_es=str(item.get("ex_es", "")).strip(),
                ex_zh=str(item.get("ex_zh", "")).strip(),
            )
            self.words.append(w)
            self.by_id[w.id] = w

        # A1 在前，保证新词由易到难
        self.words.sort(key=lambda w: (LEVELS.index(w.level), w.es.lower()))

    def load_state(self) -> None:
        if not STATE_FILE.exists():
            return
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return
        for wid, payload in (data.get("cards") or {}).items():
            if wid in self.by_id and isinstance(payload, dict):
                self.cards[wid] = Card.from_json(payload)
        if isinstance(data.get("settings"), dict):
            self.settings.update(data["settings"])
        if isinstance(data.get("history"), dict):
            self.history = data["history"]

    def save(self) -> None:
        USER_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "settings": self.settings,
            "history": self.history,
            "cards": {wid: c.to_json() for wid, c in self.cards.items()},
        }
        fd, tmp = tempfile.mkstemp(dir=str(USER_DIR), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=1)
            os.replace(tmp, STATE_FILE)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)

    # ------------------------------------------------------------ 设置

    @property
    def daily_goal(self) -> int:
        return int(self.settings.get("daily_goal", 20))

    def set_setting(self, key: str, value) -> None:
        self.settings[key] = value
        self.save()

    # ------------------------------------------------------------ 查询

    def card(self, wid: str) -> Card:
        c = self.cards.get(wid)
        if c is None:
            c = Card(due=_today_str())
            self.cards[wid] = c
        return c

    def is_due(self, wid: str) -> bool:
        c = self.cards.get(wid)
        if c is None:
            return True
        return c.due <= _today_str()

    def mastery(self, wid: str) -> float:
        """0..1 的掌握度，用于 UI 进度条。"""
        c = self.cards.get(wid)
        if c is None or c.seen == 0:
            return 0.0
        return min(1.0, (c.box + 0.35) / (MAX_BOX + 1))

    def day_record(self, d: str | None = None) -> dict:
        return self.history.get(d or _today_str(), {"studied": [], "correct": 0, "wrong": 0})

    def today_studied(self) -> int:
        return len(self.day_record().get("studied", []))

    # ------------------------------------------------------------ 组卷

    def build_session(self, limit: int | None = None) -> list[Word]:
        """今日队列：到期词优先 → 新词补足。"""
        goal = limit or self.daily_goal
        today = _today_str()
        due = [w for w in self.words if w.id in self.cards and self.cards[w.id].due <= today
               and self.cards[w.id].seen > 0]
        due.sort(key=lambda w: (self.cards[w.id].due, -self.cards[w.id].box))
        fresh = [w for w in self.words if w.id not in self.cards]
        queue = due + fresh
        if len(queue) < goal:
            rest = [w for w in self.words if w not in queue]
            random.shuffle(rest)
            queue += rest
        return queue[:goal]

    def build_quiz(self, size: int = 10) -> list[tuple[Word, list[Word]]]:
        """四选一题目：优先取已学过的词作为题干。"""
        pool = [w for w in self.words if self.cards.get(w.id, Card()).seen > 0] or list(self.words)
        random.shuffle(pool)
        questions: list[tuple[Word, list[Word]]] = []
        for target in pool[:size]:
            distractors = [w for w in self.words if w.id != target.id and w.zh != target.zh]
            random.shuffle(distractors)
            options = distractors[:3] + [target]
            random.shuffle(options)
            questions.append((target, options))
        return questions

    # ------------------------------------------------------------ 评分

    def rate(self, wid: str, rating: int) -> None:
        c = self.card(wid)
        today = date.today()
        if rating == RATING_GOOD:
            c.box = min(MAX_BOX, c.box + 1)
            c.correct += 1
        elif rating == RATING_HARD:
            c.box = max(1, c.box)
            c.wrong += 1
        else:
            c.box = 0
            c.wrong += 1
            c.due = today.isoformat()

        if rating != RATING_AGAIN:
            c.due = (today + timedelta(days=INTERVALS[c.box])).isoformat()
        c.seen += 1
        c.last = today.isoformat()

        rec = self.history.setdefault(today.isoformat(), {"studied": [], "correct": 0, "wrong": 0})
        if wid not in rec["studied"]:
            rec["studied"].append(wid)
        if rating == RATING_GOOD:
            rec["correct"] += 1
        else:
            rec["wrong"] += 1
        self.save()

    def review_later(self, wid: str) -> None:
        c = self.card(wid)
        c.due = _today_str()
        c.box = 0
        self.save()

    # ------------------------------------------------------------ 统计

    def streak(self) -> int:
        n = 0
        d = date.today()
        while True:
            rec = self.history.get(d.isoformat())
            if rec and rec.get("studied"):
                n += 1
                d -= timedelta(days=1)
            else:
                break
        return n

    def summary(self) -> dict:
        total = len(self.words)
        seen = [w for w in self.words if self.cards.get(w.id, Card()).seen > 0]
        mastered = [w for w in seen if self.cards[w.id].box >= 4]
        learning = [w for w in seen if 1 <= self.cards[w.id].box <= 3]
        rec = self.day_record()
        answered = rec.get("correct", 0) + rec.get("wrong", 0)
        return {
            "total": total,
            "seen": len(seen),
            "mastered": len(mastered),
            "learning": len(learning),
            "fresh": total - len(seen),
            "today_studied": len(rec.get("studied", [])),
            "today_correct": rec.get("correct", 0),
            "today_wrong": rec.get("wrong", 0),
            "today_accuracy": (rec.get("correct", 0) / answered) if answered else 0.0,
            "streak": self.streak(),
            "goal": self.daily_goal,
            "due": sum(1 for w in seen if self.cards[w.id].due <= _today_str()),
        }

    def week_activity(self) -> list[tuple[str, int]]:
        out = []
        names = ["一", "二", "三", "四", "五", "六", "日"]
        for i in range(6, -1, -1):
            d = date.today() - timedelta(days=i)
            rec = self.history.get(d.isoformat(), {})
            out.append((names[d.weekday()], len(rec.get("studied", []))))
        return out

    def heatmap(self, days: int = 28) -> list[int]:
        out = []
        for i in range(days - 1, -1, -1):
            d = date.today() - timedelta(days=i)
            rec = self.history.get(d.isoformat(), {})
            out.append(len(rec.get("studied", [])))
        return out

    def level_distribution(self) -> dict[str, tuple[int, int]]:
        """level -> (已学, 总数)"""
        out: dict[str, tuple[int, int]] = {}
        for lv in LEVELS:
            pool = [w for w in self.words if w.level == lv]
            done = [w for w in pool if self.cards.get(w.id, Card()).seen > 0]
            out[lv] = (len(done), len(pool))
        return out

    def recent(self, n: int = 4) -> list[Word]:
        items = [(c.last, w) for w in self.words if (c := self.cards.get(w.id)) and c.seen > 0]
        items.sort(key=lambda t: t[0], reverse=True)
        seen_ids = set()
        out = []
        for _, w in items:
            if w.id in seen_ids:
                continue
            seen_ids.add(w.id)
            out.append(w)
            if len(out) >= n:
                break
        return out

    def reset(self) -> None:
        self.cards.clear()
        self.history.clear()
        self.save()

    def search(self, query: str = "", level: str = "全部", theme: str = "全部") -> list[Word]:
        q = query.strip().lower()
        out = []
        for w in self.words:
            if level != "全部" and w.level != level:
                continue
            if theme != "全部" and w.theme != theme:
                continue
            if q and q not in w.es.lower() and q not in w.zh and q not in w.theme.lower():
                continue
            out.append(w)
        return out

    @property
    def themes(self) -> list[str]:
        return sorted({w.theme for w in self.words})


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store