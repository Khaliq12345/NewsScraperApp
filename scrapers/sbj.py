#Sports Business Journal

from selectolax.parser import HTMLParser
import pandas as pd
import models as mod
import json

class SBJ:
    def __init__(self):
        self.input_data = mod.LoadData(publication='Sports Business Journal')

    def get_posts(self, soup: HTMLParser):
        articles = soup.css('article[class="article "]')
        return articles

    def get_data_from_post(self, post: HTMLParser, author_name: str):
        link = header = paragraph = ''
        date, authors, img = '5 months ago', [1], 'https://tinyurl.com/5yxk5cua'
        if post.css_first('h2 a'):
            link = post.css_first('h2 a').attributes['href']
            response = mod.send_requests(link)
            if response:
                soup = HTMLParser(response.text)
                json_str = soup.css_first('script[type="application/ld+json"]').text()
                json_data = json.loads(json_str)
                if soup.css_first('time[itemprop="datePublished"]'):
                    date = soup.css_first('time[itemprop="datePublished"]').attributes['datetime']
                if mod.less_than_3_days_old(date):
                    header = json_data['headline']
                    if soup.css_first('meta[name="description"]'):
                        paragraph = soup.css_first('meta[name="description"]').attributes['content']
                    img = json_data['image']
                    authors = json_data['author'] if type(json_data['author']) == list else [json_data['author']]
                    author_name = author_name
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
                else:
                    self.input_data.to_continue = False
        
    def engine(self, author_url: str, author_name: str):
        response = mod.send_requests(author_url)
        if response:
            soup = HTMLParser(response.text)
            posts = self.get_posts(soup)
            for post in posts:
                if self.input_data.to_continue:
                    self.get_data_from_post(post, author_name)
                else:
                    break
        self.input_data.to_continue = True

    def main(self):
        for idx, row in self.input_data.publication_table.iterrows():
            try:
                if pd.isna(row['Article URL']):
                    pass
                else:
                    print(row['Article URL'], row['Author Name'])
                    self.engine(row['Article URL'], row['Author Name'])
            except Exception as e:
                self.input_data.fails.append({"failed": f"Error scraping one or more posts of {row['Article URL']} with error {e}"})
        return self.input_data.post_items, self.input_data.fails
    
# if __name__ == '__main__':
#     sbj = SBJ()
#     print(sbj.main())
#     # df = pd.DataFrame(self.input_data.post_items)
#     # df.to_excel('forbes_sample.xlsx', index=False)
#     # print("Done!")