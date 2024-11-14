#!/usr/bin/env python3
import os
import cups
from PIL import Image
import argparse
import tempfile
import json

class ImagePrinter:
    def __init__(self):
        """CUPSクライアントの初期化"""
        self.conn = cups.Connection()
    
    def list_printers(self, show_options=False):
        """
        利用可能なプリンターの一覧を取得
        show_options: Trueの場合、各プリンターの詳細オプションも表示
        """
        printers = self.conn.getPrinters()
        if not printers:
            print("利用可能なプリンターが見つかりません")
            return []
        
        print("\n利用可能なプリンター:")
        for i, (printer_name, printer_info) in enumerate(printers.items(), 1):
            state = "待機中" if printer_info["printer-state"] == 3 else "エラーまたはオフライン"
            default = " (デフォルト)" if printer_info.get("is-default", False) else ""
            print(f"{i}. {printer_name}{default} - {state}")
            
            if show_options:
                self.show_printer_options(printer_name)
                print()
        
        return list(printers.keys())

    def show_printer_options(self, printer_name):
        """プリンターの利用可能なオプションを表示"""
        try:
            # プリンターの属性を取得
            attrs = self.conn.getPrinterAttributes(printer_name)
            
            # 給紙トレイオプション
            input_trays = attrs.get('InputSlot-supported', [])
            if input_trays:
                print("\n  利用可能な給紙トレイ:")
                for tray in input_trays:
                    print(f"    - {tray}")
            
            # 用紙サイズ
            media_sizes = attrs.get('media-supported', [])
            if media_sizes:
                print("\n  利用可能な用紙サイズ:")
                for size in media_sizes:
                    print(f"    - {size}")
            
            # 解像度
            resolutions = attrs.get('printer-resolution-supported', [])
            if resolutions:
                print("\n  利用可能な解像度:")
                for res in resolutions:
                    print(f"    - {res}")
            
            # その他のオプション
            print("\n  その他の設定可能なオプション:")
            for option, values in attrs.items():
                if option.endswith('-supported') and isinstance(values, list):
                    option_name = option.replace('-supported', '')
                    if option_name not in ['InputSlot', 'media', 'printer-resolution']:
                        print(f"    {option_name}:")
                        for value in values:
                            print(f"      - {value}")
        
        except Exception as e:
            print(f"  オプション取得エラー: {str(e)}")

    def prepare_image(self, image_path, dpi=300, width=None, height=None):
        """画像の前処理（リサイズと解像度の設定）"""
        try:
            # 画像を開く
            image = Image.open(image_path)
            
            # RGBモードに変換（必要な場合）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # リサイズが指定されている場合
            if width and height:
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            # DPIの設定
            image.info['dpi'] = (dpi, dpi)
            
            return image
            
        except Exception as e:
            raise Exception(f"画像の処理中にエラーが発生しました: {str(e)}")

    def print_image(self, image_path, printer_name=None, input_tray=None, 
                   media=None, dpi=300, width=None, height=None, options=None):
        """画像を印刷する"""
        try:
            # プリンターの選択
            if not printer_name:
                # デフォルトプリンターを使用
                printers = self.conn.getPrinters()
                for name, info in printers.items():
                    if info.get('is-default', False):
                        printer_name = name
                        break
                if not printer_name:
                    raise Exception("デフォルトプリンターが設定されていません")
            
            # プリンターの存在確認
            if printer_name not in self.conn.getPrinters():
                raise Exception(f"プリンター '{printer_name}' が見つかりません")
            
            # 画像の準備
            image = self.prepare_image(image_path, dpi, width, height)
            
            # 一時ファイルとして保存
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                image.save(tmp_file.name, 'PNG', dpi=(dpi, dpi))
                tmp_path = tmp_file.name
            
            # 基本印刷オプションの設定
            print_options = {
                'fit-to-page': 'True',           # ページに合わせる
                'resolution': f'{dpi}dpi',       # 解像度
            }
            
            # 給紙トレイの設定
            if input_tray:
                print_options['InputSlot'] = input_tray
            
            # 用紙サイズの設定
            if media:
                print_options['media'] = media
            
            # 追加のオプションがある場合は統合
            if options:
                print_options.update(options)
            
            # 印刷ジョブの送信
            job_id = self.conn.printFile(printer_name, tmp_path, "Image Printing", print_options)
            
            # 一時ファイルの削除
            os.unlink(tmp_path)
            
            print(f"\n印刷ジョブを送信しました")
            print(f"プリンター: {printer_name}")
            print(f"給紙トレイ: {input_tray if input_tray else 'デフォルト'}")
            print(f"用紙サイズ: {media if media else 'デフォルト'}")
            print(f"解像度: {dpi} DPI")
            print(f"ジョブID: {job_id}")
            
            # 使用したオプションの表示
            print("\n使用した印刷オプション:")
            for key, value in print_options.items():
                print(f"  {key}: {value}")
            
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Ubuntu用画像印刷プログラム')
    parser.add_argument('image_path', nargs='?', help='印刷する画像のパス')
    parser.add_argument('--printer', help='プリンター名（指定しない場合はデフォルトプリンター）')
    parser.add_argument('--tray', help='給紙トレイの指定')
    parser.add_argument('--media', help='用紙サイズ（例：A4, Letter）')
    parser.add_argument('--dpi', type=int, default=300, help='印刷解像度（DPI）')
    parser.add_argument('--width', type=int, help='出力画像の幅（ピクセル）')
    parser.add_argument('--height', type=int, help='出力画像の高さ（ピクセル）')
    parser.add_argument('--list-printers', action='store_true', help='利用可能なプリンターを表示')
    parser.add_argument('--show-options', action='store_true', help='プリンターのオプションを表示')
    parser.add_argument('--options', help='追加の印刷オプション（JSON形式）')
    
    args = parser.parse_args()
    
    printer = ImagePrinter()
    
    if args.list_printers or args.show_options:
        printer.list_printers(show_options=args.show_options)
        return
    
    if not args.image_path:
        parser.print_help()
        return
    
    if not os.path.exists(args.image_path):
        print(f"エラー: 指定されたファイル '{args.image_path}' が見つかりません。")
        return
    
    # 追加オプションの解析
    additional_options = {}
    if args.options:
        try:
            additional_options = json.loads(args.options)
        except json.JSONDecodeError:
            print("エラー: オプションのJSONフォーマットが不正です")
            return
    
    printer.print_image(
        args.image_path,
        printer_name=args.printer,
        input_tray=args.tray,
        media=args.media,
        dpi=args.dpi,
        width=args.width,
        height=args.height,
        options=additional_options
    )

if __name__ == "__main__":
    main()