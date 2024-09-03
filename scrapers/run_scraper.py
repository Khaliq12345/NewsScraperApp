import forbes, nytimes, nj, fangraph, cbs, ringer, apnews, athletic, courant, fox, mlb, northjersey, nydaily, nypost, sbj, sny, yahoo, si, newsday, wsj
import pandas as pd
import os, pathlib

all_scripts = [
    {"name": "Forbes", "code": "forbes.Forbes().main()"},
    {"name": "Nytimes", "code": "nytimes.NyTimes().main()"},
    {"name": "Nj.com", "code": "nj.Nj().main()"},
    {"name": "Fangraphs", "code": "fangraph.FanGraph().main()"},
    {"name": "CBS", "code": "cbs.CBS().main()"},
    {"name": "Ringer", "code": "ringer.Ringer().main()"},
    {"name": "AP News", "code": "apnews.ApNews().main()"},
    {"name": "Athletic", "code": "athletic.Athletic().main()"},
    {"name": "Courant", "code": "courant.Courant().main()"},
    {"name": "Fox", "code": "fox.Fox().main()"},
    {"name": "MLB", "code": "mlb.MLB().main()"},
    {"name": "The Record", "code": "northjersey.NorthJ().main()"},
    {"name": "New york Daily", "code": "nydaily.NyDaily().main()"},
    {"name": "New york Post", "code": "nypost.NyPost().main()"},
    {"name": "SBJ", "code": "sbj.SBJ().main()"},
    {"name": "SNY", "code": "sny.SNY().main()"},
    {"name": "Yahoo", "code": "yahoo.Yahoo().main()"},
    {"name": "Sports Illustrated", "code": "si.SI().main()"},
    {"name": "Newsday", "code": "newsday.NewsDay().main()"},
    {"name": "WSJ", "code": "wsj.WSJ().main()"},   
]

class MyDb:
    all_posts_df = []
    all_fails = []

def script_runner(code_to_run, db: MyDb):
    posts, fails = eval(code_to_run)
    if len(posts) > 0:
        db.all_posts_df.append(pd.DataFrame(posts))
    if len(fails) > 0:
        db.all_fails.append(pd.DataFrame(fails))

def clean_data(df: pd.DataFrame):
    df.drop_duplicates(subset=['post_id'], inplace=True)
    return df

def save_data(dataframe: pd.DataFrame, fail_df: pd.DataFrame):
    folder_to_save = pathlib.Path(os.getcwd()).as_posix()
    folder_to_save = pathlib.Path(f'{folder_to_save}/outputs')
    folder_to_save.mkdir(exist_ok=True)
    dataframe.to_excel(f'{folder_to_save}/database.xlsx', index=False)
    fail_df.to_excel(f'{folder_to_save}/fails.xlsx', index=False)
 
def start_scripts():
    db = MyDb()
    for a_script in all_scripts:
        script_runner(a_script['code'], db)
    
    if len(db.all_posts_df) > 0:
        dataframe = pd.concat(db.all_posts_df, ignore_index=True)
        dataframe = clean_data(dataframe)
    else:
        dataframe = pd.DataFrame({"Data": "No data"}, index=[0])
    if len(db.all_fails) > 0:
        fail_df = pd.concat(db.all_fails, ignore_index=True)
    else:
        fail_df = pd.DataFrame({"failed": "None"}, index=[0])
        
    save_data(dataframe, fail_df)
    
    return dataframe, fail_df
    # mod.save_to_sql(dataframe, "scraped", if_exists='replace')
    # mod.save_to_sql(fail_df, 'failed', if_exists='replace')
    #dataframe.to_excel('Temporary.xlsx', index=False)