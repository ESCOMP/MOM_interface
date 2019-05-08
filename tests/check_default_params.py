from __future__ import print_function

print("travis CI initial test")

try:
    import yaml
    print("yaml module exists")
except:
    print("no yaml module")
