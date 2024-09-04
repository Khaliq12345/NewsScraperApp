
from nicegui import ui, app
from pathlib import Path
import os, sys
cur_dir = os.getcwd()
parent_dir = Path(cur_dir).parent.as_posix()
sys.path.append(cur_dir)
sys.path.append(parent_dir)
sys.path.append(f'{parent_dir}/scrapers')
from pages import homepage, loginpage
from dateparser import parse
                     
@ui.page('/')
def run():
    runner = homepage.HomePage()
    if app.storage.user.get('user'):
        if parse('now') < parse(app.storage.user['user']['exp']): 
            runner.main()
        else:
            ui.navigate.to('/login')
    else:
        ui.navigate.to('/login')
    
@ui.page('/login')
def run():
    runner = loginpage.LoginPage()
    if app.storage.user.get('user'):
        if parse('now') < parse(app.storage.user['user']['exp']):
            ui.navigate.to('/')
        else:
            runner.main()
    else:
        runner.main()
    
ui.run(port=2000, storage_secret='adminapp')