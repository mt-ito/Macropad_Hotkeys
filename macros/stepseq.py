# SPDX-FileCopyrightText: 2026 Your Name
# SPDX-License-Identifier: MIT

# MACROPAD Hotkeys: Step Sequencer (Fix: Exit Issue)

import time
import displayio
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label

# シーケンサーの状態データ
data = {
    "steps": [0] * 12,       # 12個のキーのON/OFF状態 (0:OFF, 1:ON)
    "current_step": 0,      # 現在再生中のステップ (0〜11)
    "bpm": 120,             # テンポ (Beats Per Minute)
    "playing": True,        # 再生中フラグ
}

NOTE_FREQS = [
    262, 294, 330,
    349, 392, 440,
    523, 587, 659,
    698, 784, 880
]

def Sequencer(macropad, encoder_position):
    # 【修正点】BPM変更の追従用として、現在のエンコーダー位置を単独で記録
    last_encoder_pos = macropad.encoder

    group = displayio.Group()

    # 1. タイトルバー (白背景に黒文字)
    group.append(Rect(0, 0, macropad.display.width, 12, fill=0xFFFFFF))
    title_label = label.Label(
        terminalio.FONT,
        text="SEQUENCER | BPM: 120",
        color=0x000000,
        anchored_position=(macropad.display.width // 2, -2),
        anchor_point=(0.5, 0.0),
    )
    group.append(title_label)

    # 2. 視覚的なシーケンサーのグリッド表示 (12マス)
    grid_group = displayio.Group()
    group.append(grid_group)

    macropad.display.root_group = group
    macropad.display.refresh()

    last_step_time = time.monotonic()

    while True:
        # 1. 【修正点】ロータリーエンコーダーによる終了検知
        # 起動時の基準位置（encoder_position）から1メモリでも動いたら、即座に関数を終了して親メニューに戻す
        if not macropad.encoder == encoder_position:
            return

        # 2. 【修正点】BPM変更のロジックをキー入力に変更
        # エンコーダーでのBPM変更は終了検知と競合するため、
        # エンコーダーではなく「ロータリースイッチの押し込み」と「特定のキー」の組み合わせや、
        # あるいは「再生一時停止」のみに絞る、または純粋にキーでのBPM操作にするのが安全です。
        # ここでは一番トラブルの少ない【キー10とキー11をBPMのアップダウンに変更】する構成に修正します。
        
        # エンコーダーボタンの押し込みで 再生 / 一時停止
        macropad.encoder_switch_debounced.update()
        if macropad.encoder_switch_debounced.pressed:
            data["playing"] = not data["playing"]
            macropad.play_tone(440, 0.05)

        # 3. キー入力の処理 (ステップON/OFF ＆ BPM変更)
        event = macropad.keys.events.get()
        if event and event.pressed:
            key = event.key_number
            
            # 【仕様変更】右下の2つのキー（10と11）をBPMコントロールに変更して操作性をアップ
            if key == 10:   # BPMダウン
                data["bpm"] = max(40, data["bpm"] - 5)
                macropad.play_tone(330, 0.03)
            elif key == 11: # BPMアップ
                data["bpm"] = min(300, data["bpm"] + 5)
                macropad.play_tone(660, 0.03)
            else:
                # 0〜9のキーは通常通りステップのON/OFF切り替え
                data["steps"][key] = 1 - data["steps"][key]
                macropad.play_tone(NOTE_FREQS[key], 0.02)

        # 4. 時間経過によるステップの進行 (自動ループ)
        if data["playing"]:
            step_duration = 60.0 / data["bpm"] / 3
            current_time = time.monotonic()

            if current_time - last_step_time >= step_duration:
                last_step_time = current_time
                
                # 次のステップへ（0〜9の範囲でループするように変更、10,11はBPM用）
                data["current_step"] = (data["current_step"] + 1) % 10
                
                # 現在のステップがONなら音を鳴らす
                if data["steps"][data["current_step"]] == 1:
                    macropad.play_tone(NOTE_FREQS[data["current_step"]], 0.08)

        # 5. --- LEDバックライトの更新 ---
        for i in range(12):
            if i >= 10:
                # BPM調整キーは常時薄いオレンジ
                macropad.pixels[i] = (20, 10, 0)
            elif i == data["current_step"] and data["playing"]:
                if data["steps"][i] == 1:
                    macropad.pixels[i] = (255, 255, 255) # ONかつ再生中 = 白
                else:
                    macropad.pixels[i] = (0, 100, 100)  # OFFかつ再生中 = 水色
            else:
                if data["steps"][i] == 1:
                    macropad.pixels[i] = (0, 150, 0)    # ONの状態 = 緑
                else:
                    macropad.pixels[i] = (0, 0, 0)
        macropad.pixels.show()

        # 6. --- 画面（OLED）描画処理 ---
        while len(grid_group) > 0:
            grid_group.pop()

        title_label.text = f"{'RUN' if data['playing'] else 'STOP'} | BPM: {data['bpm']}"

        # 10個のステップの状態を画面に表示 (下段の右2つはBPMインジケータ)
        box_w, box_h = 36, 10
        gap_x, gap_y = 6, 2
        start_x, start_y = 4, 15

        for i in range(12):
            col = i % 3
            row = i // 3
            bx = start_x + col * (box_w + gap_x)
            by = start_y + row * (box_h + gap_y)

            if i >= 10:
                # BPMボタンの描画
                title_text = "-" if i == 10 else "+"
                grid_group.append(Rect(bx, by, box_w, box_h, outline=0x555555))
                continue

            if data["steps"][i] == 1:
                grid_group.append(Rect(bx, by, box_w, box_h, fill=0xFFFFFF))
            else:
                grid_group.append(Rect(bx, by, box_w, box_h, outline=0xFFFFFF))

            if i == data["current_step"] and data["playing"]:
                inner_color = 0x000000 if data["steps"][i] == 1 else 0xFFFFFF
                grid_group.append(Rect(bx + 4, by + 3, box_w - 8, box_h - 6, fill=inner_color))

        macropad.display.refresh()
        time.sleep(0.01)

# hotkeyメニュー登録用
app = {
    "name": "Step Sequencer",
    "macros": [],
    "custom_func": Sequencer,
}