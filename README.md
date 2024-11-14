# Image printer tool for ubuntu

## Install

```
sudo apt-get install cups python3-cups
sudo apt-get install libcups2-dev
pip install -r requirements.txt
```

## Run

- example

```
python cups-image-printer.py --help
python cups-image-printer.py --list-printers
python cups-image-printer.py test.jpg --dpi 300 --printer Canon_LBP621C_a0_93_53_8_a0_93_53_a0_93_5_a0_a0_USB
```

## License

GPL v3
