import asyncio
import threading

# Создаем один event loop
loop = asyncio.new_event_loop()

# Запускаем его в отдельном потоке
thread = threading.Thread(target=lambda: asyncio.run(loop.run_forever()), daemon=True)
thread.start()