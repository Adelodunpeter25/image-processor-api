import time

print("Testing import times...")

start = time.time()
from PIL import Image
print(f"PIL: {time.time() - start:.2f}s")

start = time.time()
from flask import Flask
print(f"Flask: {time.time() - start:.2f}s")

start = time.time()
from rembg import remove
print(f"rembg: {time.time() - start:.2f}s")

print("\nTotal startup complete")
