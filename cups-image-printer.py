#!/usr/bin/env python3
import os
import cups
from PIL import Image
import argparse
import tempfile

class ImagePrinter:
    def __init__(self):
        """CUPSクライアントの初期化"""
        self.conn = cups.Connection()
    
    def list_printers(self):
        """利用可能なプリンターの一覧を取得"""
        printers = self.conn.getPrinters()
        if not printers:
            print("利用可能なプリンターが見つかりません")
            return []
        
        print("\n利用可能なプリンター:")
        for i, (printer_name, printer_info) in enumerate(printers.items(), 1):
            state = "待機中" if printer_info["printer-state"] == 3 else "エラーまたはオフライン"
            default = " (デフォルト)" if printer_info.get("is-default", False) else ""
            print(f"{i}. {printer_name}{default} - {state}")
        
        return list(printers.keys())

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

    def print_image(self, image_path, printer_name=None, dpi=300, width=None, height=None):
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
            
            # 印刷オプションの設定
            options = {
                'media': 'A4',                    # 用紙サイズ
                'fit-to-page': 'True',           # ページに合わせる
                'resolution': f'{dpi}dpi',       # 解像度
            }
            
            # 印刷ジョブの送信
            job_id = self.conn.printFile(printer_name, tmp_path, "Image Printing", options)
            
            # 一時ファイルの削除
            os.unlink(tmp_path)
            
            print(f"印刷ジョブを送信しました")
            print(f"プリンター: {printer_name}")
            print(f"解像度: {dpi} DPI")
            print(f"ジョブID: {job_id}")
            
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Ubuntu用画像印刷プログラム')
    parser.add_argument('image_path', nargs='?', help='印刷する画像のパス')
    parser.add_argument('--printer', help='プリンター名（指定しない場合はデフォルトプリンター）')
    parser.add_argument('--dpi', type=int, default=300, help='印刷解像度（DPI）')
    parser.add_argument('--width', type=int, help='出力画像の幅（ピクセル）')
    parser.add_argument('--height', type=int, help='出力画像の高さ（ピクセル）')
    parser.add_argument('--list-printers', action='store_true', help='利用可能なプリンターを表示')
    
    args = parser.parse_args()
    
    printer = ImagePrinter()
    
    if args.list_printers:
        printer.list_printers()
        return
    
    if not args.image_path:
        parser.print_help()
        return
    
    if not os.path.exists(args.image_path):
        print(f"エラー: 指定されたファイル '{args.image_path}' が見つかりません。")
        return
    
    printer.print_image(args.image_path, args.printer, args.dpi, args.width, args.height)

if __name__ == "__main__":
    main()