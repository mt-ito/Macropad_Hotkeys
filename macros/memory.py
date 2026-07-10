# SPDX-FileCopyrightText: 2026 Your Name
# SPDX-License-Identifier: MIT

# MACROPAD Hotkeys: Simon Memory Game

import random
import time
import displayio
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label

# ゲームの状態データ
data = {
    "sequence": [],       # 正解の光る順番（キー番号のリスト）
    "player_index": 0,    # プレイヤーが今何番目の入力をしているか
    "game_state": "START",# "START", "SHOW", "PLAY", "GAMEOVER"
    "score": 0,           # 現在のスコア（クリアしたレベル数）
    "high_score": 0,
}

# キーごとに割り当てる「光る色」と「音の周波数」
# 12マスそれぞれに異なる鮮やかな色と、上に行くほど高くなる音階を設定
KEY_TONES = [
    (262, (100, 0, 0)),    # 0: 赤 (ド)
    (294, (100, 50, 0)),   # 1: 橙 (レ)
    (330, (100, 100, 0)),  # 2: 黄 (ミ)
    (349, (0, 100, 0)),    # 3: 緑 (ファ)
    (392, (0, 100, 50)),   # 4: 薄緑 (ソ)
    (440, (0, 100, 100)),  # 5: シアン (ラ)
    (494, (0, 50, 100)),   # 6: 青 (シ)
    (523, (0, 0, 100)),    # 7: 濃青 (高いド)
    (587, (50, 0, 100)),   # 8: 紫 (高いレ)
    (659, (100, 0, 100)),  # 9: マゼンタ (高いミ)
    (698, (100, 0, 50)),   # 10: ピンク (高いファ)
    (784, (100, 100, 100)) # 11: 白 (高いソ)
]

def flash_key(macropad, key_num, duration):
    """指定したキーを一瞬光らせて音を鳴らす"""
    tone, color = KEY_TONES[key_num]
    macropad.pixels.fill((0, 0, 0))
    macropad.pixels[key_num] = color
    macropad.pixels.show()
    macropad.play_tone(tone, duration)
    macropad.pixels.fill((0, 0, 0))
    macropad.pixels.show()

def play_sequence(macropad):
    """記憶すべき光のパターンを再生する"""
    time.sleep(0.5)
    # レベルが上がるごとに再生速度を少しずつ速くする（最低0.1秒）
    duration = max(0.1, 0.4 - (len(data["sequence"]) * 0.02))
    
    for key_num in data["sequence"]:
        flash_key(macropad, key_num, duration)
        time.sleep(duration * 0.5)

def MemoryGame(macropad, encoder_position):
    group = displayio.Group()

    # 1. タイトルバー
    group.append(Rect(0, 0, macropad.display.width, 12, fill=0xFFFFFF))
    title_label = label.Label(
        terminalio.FONT,
        text="MEMORY GAME",
        color=0x000000,
        anchored_position=(macropad.display.width // 2, -2),
        anchor_point=(0.5, 0.0),
    )
    group.append(title_label)

    # 2. メインステータス文字
    status_label = label.Label(
        terminalio.FONT,
        text="Press Key 0\nTo Start",
        color=0xFFFFFF,
        anchored_position=(macropad.display.width // 2, 34),
        anchor_point=(0.5, 0.5),
        line_spacing=0.9
    )
    group.append(status_label)

    # 3. スコア表示
    score_label = label.Label(
        terminalio.FONT,
        text="SCORE: 0  HI: 0",
        color=0x888888,
        anchored_position=(macropad.display.width // 2, 54),
        anchor_point=(0.5, 0.5),
    )
    group.append(score_label)

    macropad.display.root_group = group
    macropad.display.refresh()

    while True:
        # ロータリーエンコーダーによる終了検知
        if not macropad.encoder == encoder_position:
            return

        event = macropad.keys.events.get()

        # --- 各ゲーム状態のロジック ---
        if data["game_state"] == "START":
            macropad.pixels.fill((0, 0, 0))
            # 開始待ちのときはキー0をゆっくり点滅させる（擬似点滅）
            macropad.pixels[0] = (20, 20, 20)
            macropad.pixels.show()
            
            if event and event.pressed and event.key_number == 0:
                # ゲーム開始！初期化
                data["sequence"] = []
                data["score"] = 0
                score_label.text = f"SCORE: 0  HI: {data['high_score']}"
                # 最初の1つ目を追加して手本再生へ
                data["sequence"].append(random.randint(0, 11))
                data["game_state"] = "SHOW"
                macropad.play_tone(880, 0.1)
                time.sleep(0.3)

        elif data["game_state"] == "SHOW":
            status_label.text = "WATCH\nTHE LIGHTS!"
            macropad.display.refresh()
            
            # 手本パターンを再生
            play_sequence(macropad)
            
            # プレイヤーの入力受付モードへ移行
            data["player_index"] = 0
            data["game_state"] = "PLAY"
            status_label.text = "YOUR TURN!"
            macropad.display.refresh()

        elif data["game_state"] == "PLAY":
            if event and event.pressed:
                key = event.key_number
                
                # 押したキーを一瞬光らせて鳴らす
                flash_key(macropad, key, 0.15)
                
                # 正解判定
                if key == data["sequence"][data["player_index"]]:
                    # 正解！
                    data["player_index"] += 1
                    
                    # パターンを最後まで全部押しきれたかチェック
                    if data["player_index"] == len(data["sequence"]):
                        data["score"] += 1
                        if data["score"] > data["high_score"]:
                            data["high_score"] = data["score"]
                        score_label.text = f"SCORE: {data['score']}  HI: {data['high_score']}"
                        status_label.text = "CORRECT!\nLEVEL UP"
                        macropad.display.refresh()
                        
                        # 正解ファンファーレ（ピローン！）
                        macropad.play_tone(523, 0.05)
                        macropad.play_tone(659, 0.05)
                        macropad.play_tone(784, 0.05)
                        
                        # 次のレベルのランダムな1音を追加して次のターンへ
                        data["sequence"].append(random.randint(0, 11))
                        data["game_state"] = "SHOW"
                else:
                    # 不正解！ゲームオーバー
                    data["game_state"] = "GAMEOVER"
                    status_label.text = f"WRONG!\nGAME OVER"
                    macropad.display.refresh()
                    
                    # LEDを真っ赤にフラッシュしてブーと鳴らす
                    macropad.pixels.fill((150, 0, 0))
                    macropad.pixels.show()
                    macropad.play_tone(130, 0.6)
                    time.sleep(0.2)
                    macropad.pixels.fill((0, 0, 0))
                    macropad.pixels.show()

        elif data["game_state"] == "GAMEOVER":
            # 2秒待って自動的に最初の画面に戻す
            time.sleep(2.0)
            status_label.text = "Press Key 0\nTo Restart"
            macropad.display.refresh()
            data["game_state"] = "START"

        macropad.display.refresh()
        time.sleep(0.01)

# hotkeyメニュー登録用
app = {
    "name": "Simon Memory",
    "macros": [],
    "custom_func": MemoryGame,
}