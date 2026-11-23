@echo off
rem 用正确的 Python 环境 + UTF-8 模式运行拼豆图纸生成器
"C:\Users\Lenovo\AppData\Local\Python\bin\python.exe" -X utf8 "%~dp0perler_pattern.py" %*
