from selectolax.parser import HTMLParser
import pandas as pd
import models as mod
from urllib.parse import urljoin

class MLB:
    def __init__(self):
        self.input_data = mod.LoadData(publication='MLB.com')
        
    def get_posts(self, soup: HTMLParser):
        articles = soup.css('article')
        return articles
    
    def get_data_from_post(self, post, author_names: list):
        link = header = paragraph = ''
        date, img = '5 months ago', 'https://tinyurl.com/5yxk5cua'
        authors = post['post'].css('span[class="article-item__contributor-byline"]')
        authors = [a.text(strip=True).lower().replace('by', '') for a in authors]
        for author_name in author_names:
            if author_name.lower() in authors:
                if post['post'].css_first('h1'):
                    header = post['post'].css_first('h1').text(strip=True)
                if post['post'].css_first('div[class="article-item__preview"] p'):
                    paragraph = post['post'].css_first('div[class="article-item__preview"] p').text(strip=True)
                link = post['link']
                if post['post'].css_first('img'):
                    img = post['post'].css_first('img').attributes['data-srcset'].split(',')[0]
                author_name = author_name
                date = post['date']
                try:
                    valid_posts = mod.save_my_post(
                        publication_table=self.input_data.publication_table,
                        publication=self.input_data.publication,
                        author_name=author_name,
                        header=header,
                        paragraph=paragraph,
                        link=link,
                        date=date,
                        authors=authors,
                        img=img
                    )
                    for p in valid_posts:
                        self.input_data.post_items.append(p)
                except:
                    self.input_data.fails.append({"failed": post['link']})
    
    def loop_until_done(self):
        all_articles = []
        response = mod.send_requests(f'https://www.mlb.com/news/')
        if response:
            soup = HTMLParser(response.text)
            articles = self.get_posts(soup)
            for article in articles:
                date = article.css_first('div[class="article-item__contributor-date"]').attributes['data-date'].split('T')[0]
                if mod.less_than_3_days_old(date):
                    link = article.css_first('a[class="p-button__link"]').attributes['href']
                    link = urljoin('https://www.mlb.com/', link)
                    all_articles.append({
                        'date': date,
                        'link': link,
                        'post': article
                    })
                else:
                    return all_articles
        return all_articles

    def engine(self, author_names: list):
        posts = self.loop_until_done()
        for post in posts:
            self.get_data_from_post(post, author_names)

    def main(self):
        author_names = []
        for idx, row in self.input_data.publication_table.iterrows():
            if pd.isna(row['Article URL']):
                pass
            else:
                author_names.append(row['Author Name'])
        print(author_names)
        self.engine(author_names)
        return self.input_data.post_items, self.input_data.fails
                
# if __name__ == '__main__':
#     mlb = MLB()
#     print(mlb.main())
#     # df = pd.DataFrame(self.input_data.post_items)
#     # df.to_excel('forbes_sample.xlsx', index=False)
#     # print("Done!")
            