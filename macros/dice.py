# SPDX-FileCopyrightText: 2026 Your Name
# SPDX-License-Identifier: MIT

# MACROPAD Hotkeys: Digital Dice & Coin

import random
import time
import displayio
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label

# ダイスの設定定義 (キーの配置に合わせて12種類をマッピング)
# [ 2面(コイン),  4面ダイス,   6面ダイス ]
# [ 8面ダイス,   10面ダイス,  12面ダイス ]
# [ 20面ダイス,  100面ダイス, 2個セット(2d6) ]
# [ 3個セット(3d6), 値を+1する,  値を-1する ]
DICE_TYPES = [
    {"name": "COIN (D2)", "sides": 2,    "desc": "HEADS / TAILS"},
    {"name": "D4",        "sides": 4,    "desc": "4-sided dice"},
    {"name": "D6",        "sides": 6,    "desc": "6-sided dice"},
    {"name": "D8",        "sides": 8,    "desc": "8-sided dice"},
    {"name": "D10",       "sides": 10,   "desc": "10-sided dice"},
    {"name": "D12",       "sides": 12,   "desc": "12-sided dice"},
    {"name": "D20",       "sides": 20,   "desc": "20-sided dice"},
    {"name": "D100",      "sides": 100,  "desc": "Percentile 1-100"},
    {"name": "2d6",       "sides": 206,  "desc": "2 x 6-sided dice"}, # 特殊フラグ
    {"name": "3d6",       "sides": 306,  "desc": "3 x 6-sided dice"}, # 特殊フラグ
    {"name": "+1 MOD",    "sides": -1,   "desc": "Add +1 Modifier"},
    {"name": "-1 MOD",    "sides": -2,   "desc": "Sub -1 Modifier"},
]

data = {
    "last_roll": "READY",
    "dice_name": "SELECT A DICE",
    "modifier": 0,
}

def roll_logic(sides):
    """ダイスの種類に応じた乱数を返す"""
    if sides == 2:
        return "HEADS" if random.randint(1, 2) == 1 else "TAILS"
    elif sides == 206: # 2d6
        r1 = random.randint(1, 6)
        r2 = random.randint(1, 6)
        return f"{r1}+{r2} ={r1+r2}"
    elif sides == 306: # 3d6
        r1 = random.randint(1, 6)
        r2 = random.randint(1, 6)
        r3 = random.randint(1, 6)
        return f"{r1}+{r2}+{r3}={r1+r2+r3}"
    else:
        result = random.randint(1, sides)
        return str(result)

def DiceRoller(macropad, encoder_position):
    # LEDをサイコロの色（今回は神秘的なパープル＆ゴールド）に点灯
    for i in range(12):
        if i >= 10:
            macropad.pixels[i] = (40, 20, 0)  # 修正値キーはオレンジ
        elif i >= 8:
            macropad.pixels[i] = (0, 40, 40)  # 複数ダイスはシアン
        else:
            macropad.pixels[i] = (30, 0, 50)  # 通常ダイスは紫
    macropad.pixels.show()

    group = displayio.Group()

    # 1. タイトルバー (白背景に黒文字)
    group.append(Rect(0, 0, macropad.display.width, 12, fill=0xFFFFFF))
    title_label = label.Label(
        terminalio.FONT,
        text="DIGITAL DICE SYSTEM",
        color=0x000000,
        anchored_position=(macropad.display.width // 2, -2),
        anchor_point=(0.5, 0.0),
    )
    group.append(title_label)

    # 2. メインの出目表示 (大きな文字)
    result_label = label.Label(
        terminalio.FONT,
        text=data["last_roll"],
        color=0xFFFFFF,
        anchored_position=(macropad.display.width // 2, 34),
        anchor_point=(0.5, 0.5),
        scale=2,
    )
    group.append(result_label)

    # 3. 下部のサブ情報（どのダイスを振ったか、修正値など）
    info_label = label.Label(
        terminalio.FONT,
        text=data["dice_name"],
        color=0xAAAAAA,
        anchored_position=(macropad.display.width // 2, 54),
        anchor_point=(0.5, 0.5),
    )
    group.append(info_label)

    macropad.display.root_group = group
    macropad.display.refresh()

    while True:
        # ロータリーエンコーダーによる終了検知
        if not macropad.encoder == encoder_position:
            return

        event = macropad.keys.events.get()
        if event and event.pressed:
            key = event.key_number
            dice = DICE_TYPES[key]

            # --- 修正値（Modifier）の処理 ---
            if dice["sides"] == -1: # +1
                data["modifier"] += 1
                macropad.play_tone(600, 0.05)
                info_label.text = f"Modifier: {data['modifier']:+d}"
                macropad.display.refresh()
                continue
            elif dice["sides"] == -2: # -1
                data["modifier"] -= 1
                macropad.play_tone(500, 0.05)
                info_label.text = f"Modifier: {data['modifier']:+d}"
                macropad.display.refresh()
                continue

            # --- ダイスロール演出（シャッフル） ---
            data["dice_name"] = dice["name"]
            
            # LEDを一時的に全消灯して、選択したキーだけを白く光らせる
            macropad.pixels.fill((0, 0, 0))
            macropad.pixels[key] = (255, 255, 255)
            macropad.pixels.show()

            # カタカタカタ…と回転するアニメーション演出
            shuffle_count = 12
            for s in range(shuffle_count):
                # 徐々にシャッフルの間隔を遅くしていく
                delay = 0.02 + (s * 0.02)
                
                # ダミーのランダムな数字を表示
                tmp_res = roll_logic(dice["sides"])
                result_label.text = tmp_res
                
                # 低いカタカタ音を鳴らす
                macropad.play_tone(150 + (s * 20), 0.01)
                macropad.display.refresh()
                time.sleep(delay)

            # --- 最終結果の確定 ---
            final_res = roll_logic(dice["sides"])
            
            # 修正値の適用 (純粋な数字ダイスの場合のみ末尾に付与)
            if dice["sides"] not in [2, 206, 306]:
                val = int(final_res) + data["modifier"]
                if data["modifier"] != 0:
                    result_label.text = f"{val} ({final_res}{data['modifier']:+d})"
                else:
                    result_label.text = str(val)
            else:
                # コインや複数個ダイスはそのまま表示
                result_label.text = final_res

            # 下部インフォメーションを更新
            if data["modifier"] != 0:
                info_label.text = f"{dice['name']} (Mod: {data['modifier']:+d})"
            else:
                info_label.text = f"Rolled {dice['name']}"

            # 確定時のファンファーレ音
            macropad.play_tone(523, 0.05) # ド
            macropad.play_tone(659, 0.05) # ミ
            macropad.play_tone(784, 0.1)  # ソ

            # LEDの色を元に戻す
            for i in range(12):
                if i >= 10: macropad.pixels[i] = (40, 20, 0)
                elif i >= 8: macropad.pixels[i] = (0, 40, 40)
                else: macropad.pixels[i] = (30, 0, 50)
            macropad.pixels.show()
            
            # 修正値は一回振ったらリセット（TRPGの仕様に合わせる）
            data["modifier"] = 0

        macropad.display.refresh()
        time.sleep(0.01)

# hotkeyメニュー登録用
app = {
    "name": "Digital Dice",
    "macros": [],
    "custom_func": DiceRoller,
}