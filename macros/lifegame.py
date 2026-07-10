# SPDX-FileCopyrightText: 2026 Your Name
# SPDX-License-Identifier: MIT

# MACROPAD Hotkeys: Game of Life

import random
import time
import displayio
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label

# グリッド設定 (128x64ピクセルの画面を4x4のセルで区切る)
# Yの0〜11ピクセルはメニュー用。残り52ピクセル分（52 // 4 = 13行）をゲーム領域にする
BLOCK_SIZE = 4
GRID_WIDTH = 128 // BLOCK_SIZE  # 32
GRID_HEIGHT = 52 // BLOCK_SIZE  # 13
Y_OFFSET = 12

# ゲームの状態データ
data = {
    "grid": [[0 for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)],
    "cursor_x": GRID_WIDTH // 2,
    "cursor_y": GRID_HEIGHT // 2,
    "running": False,   # 自動進行中かどうか
    "generation": 0,
}

def randomize_grid():
    """ランダムにセルを配置する"""
    data["generation"] = 0
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            data["grid"][x][y] = 1 if random.random() < 0.25 else 0

def clear_grid():
    """グリッドをクリアする"""
    data["generation"] = 0
    data["running"] = False
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            data["grid"][x][y] = 0

def get_neighbors(x, y):
    """指定したセルの周囲8マスの生存数を数える（画面端はループする宇宙）"""
    count = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx = (x + dx) % GRID_WIDTH
            ny = (y + dy) % GRID_HEIGHT
            count += data["grid"][nx][ny]
    return count

def next_generation():
    """ライフゲームの基本ルールに従って世代を進める"""
    new_grid = [[0 for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
    changed = False
    
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            neighbors = get_neighbors(x, y)
            current = data["grid"][x][y]
            
            if current == 1:
                if neighbors == 2 or neighbors == 3:
                    new_grid[x][y] = 1
                else:
                    new_grid[x][y] = 0 # 過疎または過密で死亡
                    changed = True
            else:
                if neighbors == 3:
                    new_grid[x][y] = 1 # 誕生
                    changed = True
                else:
                    new_grid[x][y] = 0
                    
    data["grid"] = new_grid
    if changed:
        data["generation"] += 1
    return changed

def GameOfLife(macropad, encoder_position):
    # LED（ネオピクセル）の初期化
    macropad.pixels.fill((0, 0, 0))
    # 操作キーのインジケータ（青：移動、緑：編集/再生、赤：クリア）
    macropad.pixels[1] = (0, 0, 40)   # カーソル上
    macropad.pixels[3] = (0, 0, 40)   # カーソル左
    macropad.pixels[4] = (0, 0, 40)   # カーソル下
    macropad.pixels[5] = (0, 0, 40)   # カーソル右
    macropad.pixels[7] = (0, 40, 0)   # 反転(エディット)
    macropad.pixels[6] = (0, 40, 20)  # ランダム配置
    macropad.pixels[9] = (0, 50, 0)   # スタート/ストップ
    macropad.pixels[11] = (50, 0, 0)  # クリア
    macropad.pixels.show()

    group = displayio.Group()

    # 1. タイトルバー (白背景に黒文字)
    group.append(Rect(0, 0, macropad.display.width, 12, fill=0xFFFFFF))
    title_label = label.Label(
        terminalio.FONT,
        text="LIFE: PAUSED (G:0)",
        color=0x000000,
        anchored_position=(macropad.display.width // 2, -2),
        anchor_point=(0.5, 0.0),
    )
    group.append(title_label)

    # 2. セルを描画するためのグループ
    cell_group = displayio.Group()
    group.append(cell_group)

    macropad.display.root_group = group
    macropad.display.refresh()

    # 初期状態でいくつかランダムに配置しておく
    randomize_grid()

    last_gen_time = time.monotonic()
    gen_interval = 0.1  # 世代交代のスピード（秒）

    while True:
        # ロータリーエンコーダーによる終了検知
        if not macropad.encoder == encoder_position:
            return

        # キー入力の処理
        event = macropad.keys.events.get()
        if event and event.pressed:
            key = event.key_number
            
            # --- カーソル移動 (十字キーに見立てる) ---
            if key == 1:   # 上
                data["cursor_y"] = (data["cursor_y"] - 1) % GRID_HEIGHT
            elif key == 4: # 下
                data["cursor_y"] = (data["cursor_y"] + 1) % GRID_HEIGHT
            elif key == 3: # 左
                data["cursor_x"] = (data["cursor_x"] - 1) % GRID_WIDTH
            elif key == 5: # 右
                data["cursor_x"] = (data["cursor_x"] + 1) % GRID_WIDTH
                
            # --- アクションキー ---
            elif key == 7: # カーソル位置のセルを反転（生⇔死）
                cx, cy = data["cursor_x"], data["cursor_y"]
                data["grid"][cx][cy] = 1 - data["grid"][cx][cy]
                macropad.play_tone(440, 0.05)
                
            elif key == 6: # ランダム配置
                randomize_grid()
                macropad.play_tone(600, 0.05)
                
            elif key == 9: # シミュレーションの再生 / 一時停止
                data["running"] = not data["running"]
                macropad.play_tone(880 if data["running"] else 330, 0.08)
                
            elif key == 11: # クリア
                clear_grid()
                macropad.play_tone(220, 0.1)

        # 自動世代更新（ランニング中かつ一定時間経過時）
        if data["running"]:
            current_time = time.monotonic()
            if current_time - last_gen_time >= gen_interval:
                last_gen_time = current_time
                has_changed = next_generation()
                if not has_changed: # 変化がなくなったら自動停止
                    data["running"] = False

        # --- 描画処理 ---
        # 以前の描写をクリア
        while len(cell_group) > 0:
            cell_group.pop()

        # ヘッダーテキストの更新
        status_str = "RUN" if data["running"] else "PAUSE"
        title_label.text = f"{status_str} | GEN: {data['generation']}"

        # 生きているセルを画面に描画
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if data["grid"][x][y] == 1:
                    cell_group.append(
                        Rect(x * BLOCK_SIZE, Y_OFFSET + (y * BLOCK_SIZE), BLOCK_SIZE, BLOCK_SIZE, fill=0xFFFFFF)
                    )

        # ポーズ中のみカーソル（点滅用の枠などではなく、ここでは簡易的にグレー/細線四角形）を描画
        if not data["running"]:
            cx, cy = data["cursor_x"], data["cursor_y"]
            cell_group.append(
                Rect(cx * BLOCK_SIZE, Y_OFFSET + (cy * BLOCK_SIZE), BLOCK_SIZE, BLOCK_SIZE, outline=0xFFFFFF)
            )

        macropad.display.refresh()
        time.sleep(0.01)

# hotkeyメニュー登録用
app = {
    "name": "Game of Life",
    "macros": [],
    "custom_func": GameOfLife,
}