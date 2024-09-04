from nicegui import ui
import pandas as pd
from pathlib import Path
import helper_functions as hf
from threading import Thread
from scrapers import run_scraper as rs
from io import BytesIO
#ideas - Ability to download scraped data

social_medias = ['Twitter', 'FB', 'IG', 'LinkedIn']
BLACK_LIST_TABLE = 'black_list3'

class HomePage:
    def __init__(self):
        self.failed_posts_info = 'No failed posts'
        self.page_num = 0
        self.page_size = 20
        self.select_all = False
        self.media_to_select = []
        self.scraped_data = []
        self.saved_posts = []
        self.failed_df = pd.DataFrame()
        self.log_name = 'None'
    
    #Backend
    def start_scripts(self):
        def engine():
            self.progress_ui.visible = True
            self.spinner.visible = True
            try:
                db = rs.MyDb()
                to_add = 1/len(rs.all_scripts)
                for a_script in rs.all_scripts:
                    self.log_name = a_script['name']
                    rs.script_runner(a_script['code'], db)
                    self.progress.value += round(to_add, 2)
                
                if len(db.all_posts_df) > 0:
                    dataframe = pd.concat(db.all_posts_df, ignore_index=True)
                    dataframe = rs.clean_data(dataframe)
                else:
                    dataframe = pd.DataFrame({"Data": "No data"}, index=[0])
                if len(db.all_fails) > 0:
                    fail_df = pd.concat(db.all_fails, ignore_index=True)
                else:
                    fail_df = pd.DataFrame({"failed": "None"}, index=[0])
                    
                rs.save_data(dataframe, fail_df)
                print("DONE!")
            except Exception as e:
                self.send_notif(e, n_type='negative')
            finally:
                self.body_ui.refresh()
                #self.progress_ui.visible = False
                #self.spinner.visible = False

        Thread(target=engine).start()
     
     
    def filter_data_from_black_list(self, df: pd.DataFrame):
        try:
            black_list = hf.get_table_from_db(BLACK_LIST_TABLE)
            return df[~(df['post_id'].isin(black_list['post_id']))]
        except:
            return df
        
        
    def load_scraped_data(self):
        self.spinner.visible = True
        def engine():
            try:
                path_str = 'outputs/database.xlsx'
                failed_path_str = 'outputs/fails.xlsx'
                db_path = Path(path_str)
                if db_path.exists():
                    df = pd.read_excel(path_str)
                    self.failed_df = pd.read_excel(failed_path_str)
                    df = self.filter_data_from_black_list(df)
                    self.scraped_data = df.to_dict(orient='records')
                else:
                    self.scraped_data = []
            except Exception as e:
                self.send_notif(e, 'negative')
            finally:
                self.spinner.visible = False
            self.content_ui.refresh()
        Thread(target=engine).start()
    
    
    def load_failed_data(self):
        buffer = BytesIO()
        writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
        self.failed_df.to_excel(writer, index=False)
        writer.close()
        ui.download(
        buffer.getvalue(), 
        f"failed.xlsx",
        'application/vnd.ms-excel')
    
    
    def send_to_blacklist_db(self):
        to_dels = list(filter(lambda x: x['selected'] == True, self.scraped_data))
        try:
            to_del_df = pd.DataFrame(to_dels)
            hf.save_to_sql(to_del_df, BLACK_LIST_TABLE)
        except Exception as e:
            self.send_notif(e, 'negative')
        finally:
            self.page_num = 0
            self.body_ui.refresh()


    def send_to_google_sheet(self):
        self.spinner.visible = True
        def engine():
            try:
                to_commit_df = pd.DataFrame(self.saved_posts)
                hf.engine_send_to_gsheet(to_commit_df)
            except Exception as e:
                self.send_notif(e, 'negative')
            finally:
                self.spinner.visible = False
        Thread(target=engine).start()


    def delete_post(self):
        self.spinner.visible = True
        Thread(target=self.send_to_blacklist_db).start()
       
        
    def commit_post(self):
        to_process = []
        self.spinner.visible = True
        def engine():
            for x in self.scraped_data:
                if x['selected'] == True:
                    to_process.append(x)
            for tp in to_process:
                self.saved_posts.append(tp)
                self.scraped_data.remove(tp)
            self.listing_ui.refresh()
            self.spinner.visible = False
        Thread(target=engine).start()
    
            
    def update_keyword(self, post, keyword):
        insta_text = "👉VISIT THE LINK IN OUR BIO TO READ THIS ARTICLE⚾️"
        first_part = post['mod_text'].split(insta_text)[0].strip()
        #keyword: #Yankees, #Mets or <$>
        #removing the keyword if they are already in text,
        #if not they will be added
        if f' {keyword}' in first_part:
            first_part = first_part.replace(f' {keyword}', '') 
        else:
            first_part += f' {keyword}'
        #this checks if the text is of Insta or others, if Insta additional text is added
        if len(post['mod_text'].split(insta_text)) > 1:
            post['mod_text'] = f'{first_part}\n\n{insta_text}'
        else:
            post['mod_text'] = first_part
        self.listing_ui.refresh()
        
        
    def update_content(self, post: dict, type_: str, value=None):
        if type_ == 'select':
            post['selected'] = value
        elif type_ == 'article':
            post['mod_text'] = value
        elif type_ == 'yankees':
            self.update_keyword(post, '#Yankees')
        elif type_ == 'mets':
            self.update_keyword(post, '#Mets')
        elif type_ == 'paywall':
            self.update_keyword(post, '<$>')
        
        
    def handle_pagination(self, e):
        self.page_num = e.value
        self.listing_ui.refresh()
    
    
    def handle_select_all(self, e):
        for x in self.scraped_data:
            x['selected'] = e.value
        self.listing_ui.refresh()
    
    
    def handle_filter(self):
        self.page_num = 0
        self.listing_ui.refresh()
    
    #Frontend
    @ui.refreshable
    def listing_ui(self):
        medias = social_medias if len(self.media_to_select) == 0 else self.media_to_select
        with ui.element('div').classes('w-full') as self.posts_ui:
            start_index = self.page_num * self.page_size
            end_index = start_index + self.page_size
            scraped_data2 = self.scraped_data.copy() #Shallow copy to main mutability between the original and new
            scraped_data2 = [x for x in scraped_data2 if x['social'] in medias]
            self.total_pages = round(len(scraped_data2)/self.page_size)
            self.pagination_ui.refresh()
            for post in scraped_data2[start_index:end_index]:
                with ui.row(align_items='center')\
                .classes('w-full xl:grid xl:grid-cols-5 mt-5 border border-gray-500 rounded-lg p-5'):
                    with ui.row(align_items='center').classes('w-full'):
                        ui.checkbox('Select', value=post['selected']).on_value_change(
                            lambda e, post=post: self.update_content(post, 'select', e.value)
                        )
                        ui.badge(post['social']).classes('text-h6 uppercase')
                        ui.badge(post['date'])
                    ui.textarea(f"Article - Byline(s): {post['number_bylines']}", value=post['mod_text']).on_value_change(
                        lambda e, post=post: self.update_content(post, 'article', e.value)
                    ).classes('col-span-3 w-full')
                    with ui.button_group().classes('w-full justify-center rounded-lg').props('unelevated'):
                        ui.button('Yankees').on_click(
                            lambda e, post=post: self.update_content(post, 'yankees')
                        ).props('flat')
                        ui.button('Mets').on_click(
                            lambda e, post=post: self.update_content(post, 'mets')
                        ).props('flat')
                        ui.button('Paywall').on_click(
                            lambda e, post=post: self.update_content(post, 'paywall')
                        ).props('flat')
           
                
    def send_notif(self, msg, n_type='info'):
        with self.body:
            ui.notification(
                msg, position='top', type=n_type, 
                timeout=5, multi_line=True, close_button=True).classes('text-white')
           
            
    def operation_buttons(self):
        with ui.row().classes('justify-around w-full my-5'):
            ui.button('Update Posts').props('flat').classes('rounded-lg').on_click(
                self.start_scripts
            )
            ui.checkbox('Select All Posts').classes('rounded-lg').on_value_change(
                lambda e: self.handle_select_all(e)
            )
            ui.button('Delete Posts').props('flat').on_click(self.delete_post)
            ui.button('Commit Posts').props('flat').classes('rounded-lg').on_click(self.commit_post)
            ui.button('View Failed Posts').props('flat').classes('rounded-lg').on_click(self.load_failed_data)
            ui.button('Send Posts to Google Sheet').props('flat').classes('rounded-lg').on_click(
                self.send_to_google_sheet
            )
    
    @ui.refreshable
    def content_ui(self):
        self.total_pages = round(len(self.scraped_data)/self.page_size)
        self.pagination_ui()
        if len(self.scraped_data) == 0:
            self.send_notif("No article to display, hit the `Update posts button` for new posts")
        else:
            self.listing_ui()
        self.pagination_ui()
    
    
    @ui.refreshable
    def pagination_ui(self):
        ui.pagination(0, self.total_pages, value=self.page_num).classes('w-full justify-center mt-5').on_value_change(
            lambda e: self.handle_pagination(e)
        ).props('boundary-links direction-links :max-pages="5"')
    
    
    def filter_ui(self):
        with ui.expansion('Filters').classes('w-full border-4 mb-3')\
        .props('header-class="bg-grey text-h5 text-center text-bold" caption="Filter based on social medias"'):
            ui.select(social_medias, label="Social", multiple=True).classes('w-full')\
                .props('stack-label outline use-chips').bind_value(self, 'media_to_select')
            with ui.row().classes('w-full justify-center'):
                ui.button("Filter", color='gray').props('unelevated').on_click(
                    self.handle_filter
                )
    
    
    def main(self):
        ui.colors(primary='red', info='black', negative='#A04747')
        self.body = ui.query('body').element
        with ui.header().classes('justify-center'):
            ui.label("Latest News Extractor").classes('text-h4')
        self.body_ui()


    @ui.refreshable
    def body_ui(self):
        try:
            with ui.element('div').classes('w-full gap-y-5'):
                self.filter_ui()
                
                self.operation_buttons()
                ui.separator()
                with ui.row().classes('justify-center') as self.progress_ui:
                    self.progress = ui.linear_progress(0, size='lg', show_value=False).props('stripe rounded')
                    ui.label().bind_text(self, 'log_name')
                self.progress_ui.visible = False
                with ui.row().classes('w-full grid grid-cols-6 mt-5'):
                    with ui.label('Articles').classes('w-full justify-center col-span-4 \
                    col-start-2 text-h4 text-center underline underline-offset-8'):
                        self.spinner = ui.spinner('box', size='xl', thickness=20.9).classes('w-full mt-10')
                        self.spinner.visible = False
                        
                self.load_scraped_data()
                self.content_ui()
        except Exception as e:
            self.send_notif(e, 'negative')
    
    