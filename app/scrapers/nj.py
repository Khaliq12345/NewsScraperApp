import pandas as pd
from selectolax.parser import HTMLParser
import models as mod
import dateparser

class Nj:
    def __init__(self):
        self.input_data = mod.LoadData(publication='NJ.com')

    def get_posts(self, soup: HTMLParser):
        posts = soup.css('li[class="river-item"]')
        return posts

    def get_data_from_post(self, post: HTMLParser, author_name: str):
        link = header = paragraph = ''
        date, authors, img = '5 months ago', [1], 'https://tinyurl.com/5yxk5cua'
        if post.css_first('h2[class="river-item__headline"]'):
            header = post.css_first('h2[class="river-item__headline"]').text(strip=True)
        if post.css_first('p[class="river-item__summary"]'):
            paragraph = post.css_first('p[class="river-item__summary"]').text(strip=True)
        if post.css_first('a[class="river-item__headline-link"]'):
            link = post.css_first('a[class="river-item__headline-link"]').attributes['href']
        if post.css_first('time'):
            date = post.css_first('time').attributes['datetime']
        if mod.less_than_3_days_old(date):
            if post.css_first('div[class="article__details--byline"]'):
                bylines = post.css_first('div[class="article__details--byline"]').text()
            else:
                bylines = ''
            authors = [bylines]
            if post.css_first('div[class="river-item__image"] img'):
                img = post.css_first('div[class="river-item__image"] img').attributes['src']
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
                try:
                    if self.input_data.to_continue:
                        self.get_data_from_post(post, author_name)
                    else:
                        break
                except BrokenPipeError:
                    pass
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
#     nj = Nj()
#     print(nj.main())
# #     # df = pd.DataFrame(input_data.post_items)
# #     # df.to_excel(f'nytimes.xlsx', index=False)
# #     # print("Done!")
    