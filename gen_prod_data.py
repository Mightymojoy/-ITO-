import sys, os, runpy
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
runpy.run_path('生成产品看板数据.py', run_name='__main__')
