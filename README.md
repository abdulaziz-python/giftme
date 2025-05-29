# GiftMe Telegram bot
**This bot is for gifts**
Used Frameworks:
 - aiogram - for telegram bot
 - FastAPI - for API
 - NextJs - for frotnend(future)


Made by Abdulaziz also subscribe my telegram channel: https://t.me/pythonnews_uzbekistan

Error : 
(.venv) PS D:\Projects\giftme> python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
INFO:     Will watch for changes in these directories: ['D:\\Projects\\giftme']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [3656] using StatReload
Process SpawnProcess-1:
Traceback (most recent call last):
  File "C:\Users\User\AppData\Local\Programs\Python\Python313\Lib\multiprocessing\process.py", line 313, in _bootstrap
    self.run()
    ~~~~~~~~^^
  File "C:\Users\User\AppData\Local\Programs\Python\Python313\Lib\multiprocessing\process.py", line 108, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Projects\giftme\.venv\Lib\site-packages\uvicorn\_subprocess.py", line 80, in subprocess_started
    target(sockets=sockets)
    ~~~~~~^^^^^^^^^^^^^^^^^
  File "D:\Projects\giftme\.venv\Lib\site-packages\uvicorn\server.py", line 66, in run
    return asyncio.run(self.serve(sockets=sockets))
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\User\AppData\Local\Programs\Python\Python313\Lib\asyncio\runners.py", line 194, in run
    return runner.run(main)
           ~~~~~~~~~~^^^^^^
  File "C:\Users\User\AppData\Local\Programs\Python\Python313\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Users\User\AppData\Local\Programs\Python\Python313\Lib\asyncio\base_events.py", line 720, in run_until_complete
    return future.result()
           ~~~~~~~~~~~~~^^
  File "D:\Projects\giftme\.venv\Lib\site-packages\uvicorn\server.py", line 70, in serve
    await self._serve(sockets)
  File "D:\Projects\giftme\.venv\Lib\site-packages\uvicorn\server.py", line 77, in _serve
    config.load()
    ~~~~~~~~~~~^^
  File "D:\Projects\giftme\.venv\Lib\site-packages\uvicorn\config.py", line 435, in load
    self.loaded_app = import_from_string(self.app)
                      ~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "D:\Projects\giftme\.venv\Lib\site-packages\uvicorn\importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
  File "C:\Users\User\AppData\Local\Programs\Python\Python313\Lib\importlib\__init__.py", line 88, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 1026, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "D:\Projects\giftme\app\main.py", line 9, in <module>
    from app.core.config import settings
  File "D:\Projects\giftme\app\core\config.py", line 33, in <module>
    settings = Settings()
  File "D:\Projects\giftme\.venv\Lib\site-packages\pydantic_settings\main.py", line 176, in __init__
    super().__init__(
    ~~~~~~~~~~~~~~~~^
        **__pydantic_self__._settings_build_values(
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<26 lines>...
        )
        ^
    )
