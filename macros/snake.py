# SPDX-FileCopyrightText: 2026 Your Name
# SPDX-License-Identifier: MIT

# MACROPAD Hotkeys: Snake Game

import random
import time
import displayio
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label

# ゲームの状態管理データ
data = {
    "snake": [],         # 蛇の体の座標リスト [(x, y), ...]
    "direction": (1, 0), # 現在の進行方向 (dx, dy)
    "food": (0, 0),      # エサの座標 (x, y)
    "score": 0,
    "game_over": True,
}

# グリッド設定 (128x64ピクセルの画面を4x4ピクセルのブロックで区切る)
# 上部12ピクセルはタイトルバー用にするため、ゲーム領域は Y: 12 〜 64
BLOCK_SIZE = 4
GRID_WIDTH = 128 // BLOCK_SIZE    # 32
GRID_MIN_Y = 12 // BLOCK_SIZE    # 3
GRID_MAX_Y = 64 // BLOCK_SIZE    # 16

def spawn_food():
    """蛇の体と被らない位置にエサを再配置する"""
    while True:
        fx = random.randint(0, GRID_WIDTH - 1)
        fy = random.randint(GRID_MIN_Y, GRID_MAX_Y - 1)
        if (fx, fy) not in data["snake"]:
            data["food"] = (fx, fy)
            break

def reset_game():
    """ゲームの初期化"""
    data["snake"] = [(5, 8), (4, 8), (3, 8)] # 初期位置（真ん中らへん、長さ3）
    data["direction"] = (1, 0)               # 初期方向：右
    data["score"] = 0
    data["game_over"] = False
    spawn_food()

def SnakeGame(macropad, encoder_position):
    # LED（ネオピクセル）の初期化（消灯、一部を方向キーのインジケータにしても面白いです）
    macropad.pixels.fill((0, 0, 0))
    # キー配置のヒントとして、移動に使うキーを薄く光らせる（例: キー3=左, キー4=下, キー5=右, キー1=上）
    macropad.pixels[1] = (0, 0, 50)  # 上
    macropad.pixels[3] = (0, 0, 50)  # 左
    macropad.pixels[4] = (0, 0, 50)  # 下
    macropad.pixels[5] = (0, 0, 50)  # 右
    macropad.pixels.show()

    group = displayio.Group()

    # 1. タイトルバー (白背景に黒文字)
    group.append(Rect(0, 0, macropad.display.width, 12, fill=0xFFFFFF))
    title_label = label.Label(
        terminalio.FONT,
        text="SNAKE GAME",
        color=0x000000,
        anchored_position=(macropad.display.width // 2, -2),
        anchor_point=(0.5, 0.0),
    )
    group.append(title_label)

    # 2. ゲームオーバー / スコア表示用のテキストレイヤー
    status_label = label.Label(
        terminalio.FONT,
        text="Press Key 0 to Start",
        color=0xFFFFFF,
        anchored_position=(macropad.display.width // 2, 38),
        anchor_point=(0.5, 0.5),
    )
    group.append(status_label)

    # 3. 蛇とエサを描画するためのグループ
    # CircuitPythonの性能上、一からRectを作り直すと重いので、このグループ内に描画オブジェクトを都度追加/削除します
    game_objects = displayio.Group()
    group.append(game_objects)

    macropad.display.root_group = group
    macropad.display.refresh()

    last_move_time = time.monotonic()
    move_interval = 0.2  # 蛇が動く速度（秒）。小さくすると難易度が上がります。

    while True:
        # 1. ロータリーエンコーダーによる終了検知 (Pomodoroと同様)
        if not macropad.encoder == encoder_position:
            return

        # 2. キー入力のチェック（方向転換とスタート）
        event = macropad.keys.events.get()
        if event:
            if event.pressed:
                key = event.key_number
                
                if data["game_over"]:
                    if key == 0: # キー0番でスタート/再開
                        reset_game()
                        status_label.text = ""
                else:
                    # キーパッドの配置（3x4）を十字キーに見立てる
                    #       [1: 上]
                    # [3: 左] [4: 下] [5: 右]
                    if key == 1 and data["direction"] != (0, 1):    # 上 (下進行中は不可)
                        data["direction"] = (0, -1)
                    elif key == 4 and data["direction"] != (0, -1):  # 下 (上進行中は不可)
                        data["direction"] = (0, 1)
                    elif key == 3 and data["direction"] != (1, 0):   # 左 (右進行中は不可)
                        data["direction"] = (-1, 0)
                    elif key == 5 and data["direction"] != (-1, 0):  # 右 (左進行中は不可)
                        data["direction"] = (1, 0)

        # 3. ゲームのメインロジック（一定時間ごとに進行）
        if not data["game_over"]:
            current_time = time.monotonic()
            if current_time - last_move_time >= move_interval:
                last_move_time = current_time

                # 新しい頭の座標を計算
                head_x, head_y = data["snake"][0]
                dx, dy = data["direction"]
                new_head = (head_x + dx, head_y + dy)

                # 壁衝突 または 自分の体に衝突したかチェック
                if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or
                    new_head[1] < GRID_MIN_Y or new_head[1] >= GRID_MAX_Y or
                    new_head in data["snake"]):
                    
                    # ゲームオーバー処理
                    data["game_over"] = True
                    macropad.play_tone(150, 0.5) # ブーという音
                    status_label.text = f"GAME OVER\nScore: {data['score']}"
                    # 全LEDを赤にフラッシュ
                    macropad.pixels.fill((100, 0, 0))
                    macropad.pixels.show()
                    time.sleep(0.2)
                    macropad.pixels.fill((0, 0, 0))
                    macropad.pixels[1] = (0, 0, 50)
                    macropad.pixels[3] = (0, 0, 50)
                    macropad.pixels[4] = (0, 0, 50)
                    macropad.pixels[5] = (0, 0, 50)
                    macropad.pixels.show()
                else:
                    # 蛇を前進させる
                    data["snake"].insert(0, new_head)

                    # エサを食べたかチェック
                    if new_head == data["food"]:
                        data["score"] += 1
                        macropad.play_tone(440, 0.1) # ピッという音
                        spawn_food()
                    else:
                        # 食べていなければ尻尾を消す
                        data["snake"].pop()

                # --- 描画処理 ---
                # 描画グループをクリア
                while len(game_objects) > 0:
                    game_objects.pop()

                if not data["game_over"]:
                    # タイトルバーにスコアをリアルタイム表示
                    title_label.text = f"SCORE: {data['score']}"

                    # エサの描画 (白の塗りつぶし四角形)
                    fx, fy = data["food"]
                    game_objects.append(Rect(fx * BLOCK_SIZE, fy * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE, fill=0xFFFFFF))

                    # 蛇の体の描画 (枠線のみ、または塗りつぶしでエサと区別)
                    for idx, (sx, sy) in enumerate(data["snake"]):
                        # 頭は少し目立たせる（塗りつぶし）、体は枠だけ等（ここではすべて白で描画）
                        game_objects.append(Rect(sx * BLOCK_SIZE, sy * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE, fill=0xFFFFFF))

                macropad.display.refresh()

        # CPUの負荷を抑えるためのわずかなディレイ
        time.sleep(0.01)

# hotkeyメニューに登録するための辞書型定義
app = {
    "name": "Snake Game",
    "macros": [],
    "custom_func": SnakeGame,
}