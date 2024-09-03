import pandas as pd
from selectolax.parser import HTMLParser
from urllib.parse import urljoin
import models as mod

class NyTimes:
    def __init__(self):
        self.input_data = mod.LoadData(publication='The New York Times')

    def nytimes_author_cleaner(self, bylines: str):
        authors = []
        author_last = bylines.split('and')[-1]
        for x in bylines.split(','):
            authors.append(x.replace('and', '').replace(author_last, '').strip())
        authors.append(author_last.strip())
        authors = list(set(authors))
        if '' in authors:
            authors.remove('')
        return authors

    def get_posts(self, soup: HTMLParser):
        posts = soup.css('article')
        return posts

    def get_data_from_post(self, post: HTMLParser, author_name: str):
        link = header = paragraph = ''
        date, authors, img = '5 months ago', [1], 'https://tinyurl.com/5yxk5cua'
        if post.css_first('h3'):
            header = post.css_first('h3').text(strip=True)
        if post.css_first('p'):
            paragraph = post.css_first('p').text(strip=True)
        if post.css_first('a'):
            raw_link = post.css_first('a').attributes['href']
            link = urljoin('https://www.nytimes.com/', raw_link)
            date = ', '.join(raw_link.split('/')[1:4])
        if mod.less_than_3_days_old(date):
            if post.css_first('span[class="css-1n7hynb"]'):
                bylines = post.css_first('span[class="css-1n7hynb"]').text()
                authors = self.nytimes_author_cleaner(bylines)
            if post.css_first('img'):
                img = post.css_first('img').attributes['src']
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
#     ny_t = NyTimes()
#     print(ny_t.main())
# #     load_profiles()
# #     # df = pd.DataFrame(input_data.post_items)
# #     # df.to_excel(f'nytimes.xlsx', index=False)
# #     # print("Done!")
    