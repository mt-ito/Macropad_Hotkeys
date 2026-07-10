# SPDX-FileCopyrightText: 2026 Your Name
# SPDX-License-Identifier: MIT

# MACROPAD Hotkeys: Dot-Art Planetarium

import random
import time
import displayio
from adafruit_display_shapes.line import Line
from adafruit_display_shapes.rect import Rect

# 星空の状態データ
data = {
    "stars": [],          # 星の座標と輝度リスト [(x, y, brightness, speed)]
    "shooting_star": None,# 流れ星の状態 [x, y, dx, dy, length]
    "constellations": [], # 星座の線リスト
    "mode": "CALM",       # "CALM" (通常), "METEOR" (流星群), "NEON" (LED連動)
    "star_count": 40,     # 星の数
}

def init_stars(width, height):
    """星をランダムに再配置"""
    data["stars"] = []
    for _ in range(data["star_count"]):
        x = random.randint(0, width - 1)
        y = random.randint(13, height - 1) # タイトルバーの下から
        # 輝度の揺らぎ速度
        speed = random.uniform(0.05, 0.2)
        data["stars"].append([x, y, random.randint(0, 1), speed])

def Planetarium(macropad, encoder_position):
    width = macropad.display.width
    height = macropad.display.height
    
    # LEDを夜空のような静かなディープブルーに
    macropad.pixels.fill((0, 0, 10))
    macropad.pixels.show()

    group = displayio.Group()
    
    # 星空を描画するためのサブグループ
    sky_group = displayio.Group()
    group.append(sky_group)

    macropad.display.root_group = group
    macropad.display.refresh()

    init_stars(width, height)
    last_update = time.monotonic()

    while True:
        # 1. ロータリーエンコーダーによる終了検知（メニュー離脱）
        if not macropad.encoder == encoder_position:
            return

        # 2. キー入力によるインタラクティブ操作
        event = macropad.keys.events.get()
        if event and event.pressed:
            key = event.key_number
            
            if key == 0: # 流れ星を強制的に流す
                macropad.play_tone(880, 0.02)
                data["shooting_star"] = [random.randint(10, 80), 15, 3, 2, 8]
            
            elif key == 1: # 星座の線をON/OFF（ランダムに数本の星を繋ぐ）
                macropad.play_tone(587, 0.02)
                if data["constellations"]:
                    data["constellations"] = []
                else:
                    # ランダムにいくつかの星同士を結ぶ
                    for _ in range(4):
                        if len(data["stars"]) >= 2:
                            s1 = random.choice(data["stars"])
                            s2 = random.choice(data["stars"])
                            data["constellations"].append((s1[0], s1[1], s2[0], s2[1]))
            
            elif key == 2: # 星の数を増やす（最大80個）
                macropad.play_tone(659, 0.02)
                data["star_count"] = min(80, data["star_count"] + 10)
                init_stars(width, height)
                
            elif key == 3: # 星の数を減らす（最低10個）
                macropad.play_tone(440, 0.02)
                data["star_count"] = max(10, data["star_count"] - 10)
                init_stars(width, height)

            elif key == 4: # 流星群モード切り替え
                if data["mode"] == "METEOR":
                    data["mode"] = "CALM"
                    macropad.pixels.fill((0, 0, 10))
                else:
                    data["mode"] = "METEOR"
                    macropad.pixels.fill((10, 0, 20)) # 怪しげな紫に
                macropad.pixels.show()

        # 3. 定期的な星空の更新 (約10Hzで描画)
        now = time.monotonic()
        if now - last_update >= 0.08:
            last_update = now

            # 画面を一度クリア
            while len(sky_group) > 0:
                sky_group.pop()

            # --- 流星群モードの時のランダム流れ星発生 ---
            if data["mode"] == "METEOR" and random.random() < 0.15 and not data["shooting_star"]:
                data["shooting_star"] = [random.randint(0, width - 20), random.randint(13, 30), 4, 2, 10]

            # --- 1. 星座の線を描画 ---
            for line in data["constellations"]:
                sky_group.append(Line(line[0], line[1], line[2], line[3], color=0xFFFFFF))

            # --- 2. 通常の星（ドット）を描画 ---
            for star in data["stars"]:
                # 確率で星の瞬き（表示/非表示）を切り替える
                if random.random() < star[3]:
                    star[2] = 1 - star[2]
                
                if star[2] == 1:
                    # 1x1のドット（小さなRect）として描画
                    sky_group.append(Rect(star[0], star[1], 1, 1, fill=0xFFFFFF))

            # --- 3. 流れ星の描画と移動 ---
            if data["shooting_star"]:
                sx, sy, dx, dy, length = data["shooting_star"]
                # 流れ星の軌跡を線で描画
                sky_group.append(Line(int(sx), int(sy), int(sx - dx * 2), int(sy - dy * 2), color=0xFFFFFF))
                
                # 座標を移動
                sx += dx
                sy += dy
                data["shooting_star"][0] = sx
                data["shooting_star"][1] = sy
                
                # 画面外に出たら消滅
                if sx > width or sy > height:
                    data["shooting_star"] = None

            # --- 4. LEDのバックライト演出 ---
            # 通常モードの時は、星の瞬きに合わせてキーのLEDも極めて淡く白に明滅させる
            if data["mode"] == "CALM":
                for i in range(12):
                    if random.random() < 0.05:
                        val = random.randint(0, 15)
                        macropad.pixels[i] = (val, val, val + 10) # ほのかな青み
                macropad.pixels.show()

            macropad.display.refresh()

        time.sleep(0.01)

# hotkeyメニュー登録用
app = {
    "name": "Planetarium",
    "macros": [],
    "custom_func": Planetarium,
}