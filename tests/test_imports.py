import time

print("Testing import times...")

start = time.time()
print(f"PIL: {time.time() - start:.2f}s")

start = time.time()
print(f"Flask: {time.time() - start:.2f}s")

start = time.time()
print(f"rembg: {time.time() - start:.2f}s")

print("\nTotal startup complete")
