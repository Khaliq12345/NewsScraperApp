import sqlalchemy
from sqlalchemy import text
import config
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from gspread_dataframe import set_with_dataframe
import numpy as np

scopes = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']


def get_table_from_db(table_name):
    engine = sqlalchemy.create_engine(config.connection_string)
    with engine.connect() as conn:
        result = conn.execute(text(f"select * from {table_name}"))
        df = pd.DataFrame(result.all())
        return df
    
def save_to_sql(df, table_name, if_exists: str = 'append'):
    engine = sqlalchemy.create_engine(config.connection_string)
    with engine.begin() as conn:
        if 'mod_text' in df.columns:
            df.to_sql(name=table_name, con=conn, if_exists=if_exists, dtype={"mod_text": sqlalchemy.types.TEXT(collation='utf8mb4_unicode_ci')}, index=False)
        else:
            df.to_sql(name=table_name, con=conn, if_exists=if_exists, index=False)

def open_sheet(sheet_key, gc):
    gs = gc.open_by_key(sheet_key)
    return gs
            
def send_to_gsheet(df: pd.DataFrame, sheet_key):
    service_account = {
        'type': config.type,
        'project_id': config.project_id,
        'private_key_id': config.private_key_id,
        'private_key': config.private_key,
        'client_email': config.client_email,
        'client_id': config.client_id,
        'auth_uri': config.auth_uri,
        'token_uri': config.token_uri,
        'auth_provider_x509_cert_url': config.auth_provider_x509_cert_url,
        'client_x509_cert_url': config.client_x509_cert_url
    }
    credentials = Credentials.from_service_account_info(service_account, scopes=scopes)
    gc = gspread.authorize(credentials)
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)
    gs = gc.open_by_key(sheet_key)
    worksheet1 = gs.worksheet('Sheet1')
    worksheet1.clear()
    set_with_dataframe(worksheet=worksheet1, dataframe=df, include_index=False,
    include_column_header=True, resize=True)
        
def filter_data_to_send(social, df: pd.DataFrame):
    df = df.loc[df['social'] == social]
    if social == 'IG':
        df = df[['mod_text', 'post_link', 'image_url']]
        df.rename(columns={'mod_text': 'Update_Text', 'post_link': 'Update_URL', 'image_url':'Update_Image'}, inplace=True)
    else:
        df = df[['mod_text', 'post_link', 'image_url']]
        df.rename(columns={'mod_text': 'Update_Text', 'post_link': 'Update_URL', 'image_url':'Update_Image'}, inplace=True)
        df['Update_Image'] = np.nan
    return df

def engine_send_to_gsheet(to_commit_df: pd.DataFrame):
    send_to_gsheet(
        filter_data_to_send('Twitter', to_commit_df), 
        config.twitter_sheet
    )
    send_to_gsheet(
        filter_data_to_send('IG', to_commit_df), 
        config.ig_sheet
    )
    send_to_gsheet(
        filter_data_to_send('FB', to_commit_df), 
        config.fb_sheet
    )
    send_to_gsheet(
        filter_data_to_send('LinkedIn', to_commit_df), 
        config.linkedin_sheet
    )