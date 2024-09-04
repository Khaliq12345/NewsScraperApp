
from nicegui import ui, app, context
from dateparser import parse
import config

class LoginPage:
    def __init__(self):
        self.username = None
        self.password = None
    
    def login_engine(self):
        print(self.username, self.password)
        if (not self.username) or (not self.password):
            self.send_notif("Email or password cannot be empty")
        elif (self.username == config.user_db['username']) and (self.password == config.user_db['password']):
            app.storage.user['user'] = {'username': self.username, 
                                        'exp': parse('in 5 minutes').strftime("%Y-%m-%dT%T")}
            ui.navigate.reload()
        
    def send_notif(self, msg, n_type: str = 'info'):
        with self.body:
            ui.notification(
                message=msg,
                position='top',
                close_button=True,
                multi_line=True,
                type=n_type
            )
        
    def login_ui(self):
        with ui.element('div')\
        .classes('rounded-lg bg-yellow row-start-2 row-span-3 lg:col-start-2 lg:col-span-1 h-full w-full'):
            with ui.card().classes('w-full h-full rounded-lg'):
                with ui.card_section().classes('w-full'):
                    ui.icon("👤").classes('text-h4 text-center w-full')
                with ui.card_actions().classes('w-full'):
                    ui.input("Email").classes('w-full').bind_value(self, 'username')
                with ui.card_actions().classes('w-full'):  
                    ui.input("Password", password_toggle_button=True, password=True)\
                    .classes('w-full').bind_value(self, 'password')
                with ui.card_actions().classes('w-full justify-center'):  
                    ui.button("Login In").props('unelevated').on_click(self.login_engine)
    
    def main(self):
        print(app.storage.user)
        ui.colors(primary='red', info='black', negative='#A04747')
        self.body = ui.query('body').element
        self.body.style("""
            background-color: #A04747;
            """)
        with ui.column().classes('mine grid grid-rows-5 lg:grid-cols-3 w-full')\
        .style('min-height: 700px;'):
            self.login_ui()
            