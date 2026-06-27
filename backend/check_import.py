import sys
import traceback
sys.path.insert(0, r'C:\Users\salav\OneDrive\Desktop\ai-interview-platform\backend')
try:
    import app.main as m
    print('IMPORT_OK')
except Exception as e:
    traceback.print_exc()
    print('IMPORT_ERR')
