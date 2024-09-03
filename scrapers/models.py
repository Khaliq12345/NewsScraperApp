import pandas as pd
from pydantic import BaseModel, computed_field, field_validator
import dateparser
from helper_functions import *
#from cloudscraper import create_scraper
from cleantext import clean
from botasaurus.request import Request, request
from botasaurus.user_agent import UserAgent
import os, sys, pathlib
curent_dir = os.getcwd()
sys.path.append(pathlib.Path(curent_dir))

ua = UserAgent()


def less_than_3_days_old(date_str):
    three_days_ago = dateparser.parse('3 days ago')
    date = dateparser.parse(str(date_str))
    dates = (date, three_days_ago)
    match dates:
        case [None, None]:
            return False
        case [None, obj]:
            return False
        case [obj, None]:
            return False
        case [date, three_days_ago] if date > three_days_ago:
            return True
        case _:
            return False


def validate_paragraph(sentence: str) -> str:
    if len(sentence) > 50:
        words = sentence.split()
        reduced_sentence = ''
        for word in words:
            samp = reduced_sentence + ' ' + word
            if len(samp) > 50:
                break
            reduced_sentence += ' ' + word
        sentence = reduced_sentence.strip()
    return sentence


def send_requests(url: str, headers: dict = None, cookies: dict = None):
    try:
        if url:
            req_data = {
                "link": url, 
                'header': headers, 'cookie': cookies}
            return send_req_engine(req_data)
    except TimeoutError:
        print(f'Error with the requests')
        
        
@request(output=None, user_agent=ua.get_random(), max_retry=2)
def send_req_engine(request: Request, data):
    if type(data) == str:
        response = request.get(data, timeout=None)
    elif type(data) == dict:
        header = data.get('header')
        cookie = data.get('cookie')
        response = request.get(data['link'], timeout=None, headers=header, cookies=cookie)
    if response.status_code == 200:
        return response
    else:
        print(f'Error with the requests')


def get_author_pub_handle(table: pd.DataFrame, social, pub, author_name):
    row = table[(table['Author Name'] == author_name)]
    author_handle = row[f'Author {social}']
    pub_handle = row[f'Publication {social}']
    if author_handle.item() == None:
        author_handle = author_name
    else:
        author_handle = author_handle.item().replace('"', '')
    if pub_handle.item() == None:
        pub_handle = pub
    else:
        pub_handle = pub_handle.item().replace('"', '')
    paywall = table['Default Paywall  (Y/N)'][(table['Author Name'] == author_name)].item()
    item = {
        'author': author_handle,
        'publication': pub_handle,
        'paywall': '' if paywall == 'N' else '<$>'
    }
    return item


def make_ig_post(model, handle_info: dict):
    paragraph = validate_paragraph(model.text)
    post = f'''{model.header} by {handle_info['author']} for {handle_info['publication']}: {paragraph}... {handle_info['paywall']} {model.post_link}
    
    👉VISIT THE LINK IN OUR BIO TO READ THIS ARTICLE⚾️'''
    return post


def make_post(model, handle_info: dict):
    paragraph = validate_paragraph(model.text)
    post = f'''{model.header} by {handle_info['author']} for {handle_info['publication']}: {paragraph}... {handle_info['paywall']} {model.post_link}'''
    return post


def save_my_post(publication_table, publication, author_name, header, paragraph, link, date, authors, img):
    posts = []
    for social in ['Twitter', 'IG', 'FB', 'LinkedIn']:
        handle_info = get_author_pub_handle(publication_table, social, publication, author_name)
        post_item = Article(
            header=header, author_name=author_name,
            text=paragraph, post_link=link, publication=publication,
            date=date, number_bylines=len(authors), image_url=img, social=social,
            handle_info=handle_info
        )
        posts.append(post_item.model_dump(exclude={"handle_info"}))
    return posts


class LoadData:
    def __init__(self, publication):
        self.publication = publication
        self.article_table = get_table_from_db('articles')
        self.publication_table = self.article_table[self.article_table['Publication Name'] == publication]
        self.post_items = []
        self.fails = []
        self.to_continue = True


class Article(BaseModel):
    handle_info: dict
    header: str
    text: str
    date: str|int
    post_link: str
    number_bylines: int
    image_url: str
    publication: str
    author_name: str
    selected: bool = False
    social: str
    
    @field_validator('date', mode='after')
    def validate_date(cls, date: str) -> str:
        date_str = str(date)
        try:
           return dateparser.parse(date_str).strftime("%y-%m-%d")
        except:
            return date_str
        
    @field_validator('text', 'header', mode='after')
    def validate_text(cls, text: str) -> str:
        return text.replace('  ', '').strip()
    
    @computed_field
    def mod_text(self) -> str:
        if self.social == 'Twitter':
            return make_post(self, self.handle_info)
        elif self.social == 'IG':
            return make_ig_post(self, self.handle_info)
        elif self.social == 'FB':
            return make_post(self, self.handle_info)
        elif self.social == 'LinkedIn':
            return make_post(self, self.handle_info)
    
    @computed_field
    def post_id(self) -> str:
        dirty_post_id = f"{self.header}{self.social}"
        clean_post_id = clean(dirty_post_id, no_punct=True, no_emoji=True, no_digits=True, no_numbers=True,
                        replace_with_punct='', replace_with_currency_symbol='', replace_with_digit='', replace_with_number='', replace_with_email='',
                        replace_with_phone_number='', replace_with_url='')
        return clean_post_id


