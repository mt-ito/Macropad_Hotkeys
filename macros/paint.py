# SPDX-FileCopyrightText: 2026 Your Name
# SPDX-License-Identifier: MIT

# MACROPAD Hotkeys: Mini Paint

import time
import displayio
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label

# グリッド設定 (128x64ピクセルの画面を4x4のセルで区切る)
# Yの0〜11ピクセルはメニュー用。残り52ピクセル分（13行）を作業キャンバスにする
BLOCK_SIZE = 4
GRID_WIDTH = 128 // BLOCK_SIZE  # 32
GRID_HEIGHT = 52 // BLOCK_SIZE  # 13
Y_OFFSET = 12

# キャンバスの状態データ
data = {
    "canvas": [[0 for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)],
    "cursor_x": GRID_WIDTH // 2,
    "cursor_y": GRID_HEIGHT // 2,
    "tool": "PEN",         # 現在のツール ("PEN" または "ERASER")
    "color_invert": False, # 画面の白黒反転フラグ
}

def Paint(macropad, encoder_position):
    # LED（ネオピクセル）の初期化
    macropad.pixels.fill((0, 0, 0))
    # 操作キーのインジケータ（青：移動、緑：ペン/消しゴム、紫：特殊、赤：クリア）
    macropad.pixels[1] = (0, 0, 40)   # カーソル上
    macropad.pixels[3] = (0, 0, 40)   # カーソル左
    macropad.pixels[4] = (0, 0, 40)   # カーソル下
    macropad.pixels[5] = (0, 0, 40)   # カーソル右
    macropad.pixels[6] = (0, 40, 0)   # ペンツール選択
    macropad.pixels[7] = (40, 20, 0)  # 消しゴムツール選択
    macropad.pixels[8] = (30, 0, 40)  # スタンプ（一発で全点を打つ/消すなど、今回は反転に割り当て）
    macropad.pixels[9] = (40, 0, 40)  # キャンバス色反転
    macropad.pixels[11] = (50, 0, 0)  # 全消去（クリア）
    macropad.pixels.show()

    group = displayio.Group()

    # 1. タイトル/ステータスバー (白背景に黒文字)
    header_bg = Rect(0, 0, macropad.display.width, 12, fill=0xFFFFFF)
    group.append(header_bg)
    
    status_label = label.Label(
        terminalio.FONT,
        text="MODE: PEN | X:16 Y:6",
        color=0x000000,
        anchored_position=(macropad.display.width // 2, -2),
        anchor_point=(0.5, 0.0),
    )
    group.append(status_label)

    # 2. 描画ドットを表示するためのグループ
    canvas_group = displayio.Group()
    group.append(canvas_group)

    macropad.display.root_group = group
    macropad.display.refresh()

    # ロータリーエンコーダーのプッシュスイッチを検知するための状態
    macropad.encoder_switch_debounced.update()

    while True:
        # ロータリーエンコーダーによる終了検知
        if not macropad.encoder == encoder_position:
            return

        # キー入力の処理
        event = macropad.keys.events.get()
        
        # エンコーダーのボタン（押し込み）が押されたら、現在の位置にドットをプロット
        macropad.encoder_switch_debounced.update()
        if macropad.encoder_switch_debounced.pressed:
            cx, cy = data["cursor_x"], data["cursor_y"]
            data["canvas"][cx][cy] = 1 if data["tool"] == "PEN" else 0
            macropad.play_tone(600, 0.03)

        if event and event.pressed:
            key = event.key_number
            
            # --- カーソル移動 (十字キー配置) ---
            if key == 1:   # 上
                data["cursor_y"] = (data["cursor_y"] - 1) % GRID_HEIGHT
            elif key == 4: # 下
                data["cursor_y"] = (data["cursor_y"] + 1) % GRID_HEIGHT
            elif key == 3: # 左
                data["cursor_x"] = (data["cursor_x"] - 1) % GRID_WIDTH
            elif key == 5: # 右
                data["cursor_x"] = (data["cursor_x"] + 1) % GRID_WIDTH
                
            # --- ツール切り替え ---
            elif key == 6: # ペン
                data["tool"] = "PEN"
                macropad.play_tone(880, 0.05)
            elif key == 7: # 消しゴム
                data["tool"] = "ERASER"
                macropad.play_tone(440, 0.05)
                
            # --- キャンバス操作 ---
            elif key == 9: # ネガポジ反転 (インバート)
                data["color_invert"] = not data["color_invert"]
                macropad.play_tone(700, 0.08)
                
            elif key == 11: # 全消去
                for x in range(GRID_WIDTH):
                    for y in range(GRID_HEIGHT):
                        data["canvas"][x][y] = 0
                data["color_invert"] = False
                # ピポパ音
                macropad.play_tone(523, 0.05)
                macropad.play_tone(659, 0.05)
                macropad.play_tone(784, 0.05)

        # --- 描画処理 ---
        # 以前の表示オブジェクトをクリア
        while len(canvas_group) > 0:
            canvas_group.pop()

        # 白黒反転モードに応じた色定義
        bg_color = 0x000000 if not data["color_invert"] else 0xFFFFFF
        fg_color = 0xFFFFFF if not data["color_invert"] else 0x000000
        
        # 画面背景（タイトルバーより下の領域）を塗りつぶし（反転時のみ追加）
        if data["color_invert"]:
            canvas_group.append(Rect(0, Y_OFFSET, 128, 52, fill=bg_color))

        # ヘッダーテキストのリアルタイム更新
        status_label.text = f"TOOL: {data['tool']} | X:{data['cursor_x']} Y:{data['cursor_y']}"

        # キャンバス上のドットを描画
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if data["canvas"][x][y] == 1:
                    canvas_group.append(
                        Rect(x * BLOCK_SIZE, Y_OFFSET + (y * BLOCK_SIZE), BLOCK_SIZE, BLOCK_SIZE, fill=fg_color)
                    )

        # カーソルの描画 (見失わないように、ツールによって形を変える)
        cx, cy = data["cursor_x"], data["cursor_y"]
        if data["tool"] == "PEN":
            # ペンはドットの周りを囲う四角い枠線
            canvas_group.append(
                Rect(cx * BLOCK_SIZE, Y_OFFSET + (cy * BLOCK_SIZE), BLOCK_SIZE, BLOCK_SIZE, outline=fg_color)
            )
        else:
            # 消しゴムは「×」のような中心点をイメージして、小さめの十字にするか、今回は「塗りつぶし」で存在をアピール
            # （反転させて点滅の代わりにする）
            current_pixel = data["canvas"][cx][cy]
            cursor_fill = bg_color if current_pixel == 1 else fg_color
            canvas_group.append(
                Rect(cx * BLOCK_SIZE, Y_OFFSET + (cy * BLOCK_SIZE), BLOCK_SIZE, BLOCK_SIZE, fill=cursor_fill)
            )

        macropad.display.refresh()
        time.sleep(0.01)

# hotkeyメニュー登録用
app = {
    "name": "Mini Paint",
    "macros": [],
    "custom_func": Paint,
}