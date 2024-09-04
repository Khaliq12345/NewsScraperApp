from selectolax.parser import HTMLParser
import pandas as pd
import models as mod

class ApNews:
    def __init__(self):
        self.input_data = mod.LoadData(publication='Associated Press')
        
        
    def get_posts(self, soup: HTMLParser):
        articles = soup.css('div[class="PagePromo"]')
        return articles
    
    def get_data_from_post(self, post, author_names: list):
        link = header = paragraph = ''
        date, img = '5 months ago', 'https://tinyurl.com/5yxk5cua'
        response = mod.send_requests(post['link'])
        if response:
            soup = HTMLParser(response.text)
            authors = soup.css('div[class="Page-authors"] span')
            authors = [a.text(strip=True).lower() for a in authors]
            for author_name in author_names:
                if author_name.lower() in authors:
                    if soup.css_first('h1[class="Page-headline"]'):
                        header = soup.css_first('h1[class="Page-headline"]').text(strip=True)
                    if soup.css_first('meta[property="og:description"]'):
                        paragraph = soup.css_first('meta[property="og:description"]').attributes['content']
                    link = post['link']
                    if soup.css_first('img[class="Image"]'):
                        img = soup.css_first('img[class="Image"]').attributes['src']
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
        for i in range(1, 4):
            print(f'Page: {i}')
            response = mod.send_requests(f'https://apnews.com/hub/mlb?p={i}')
            if response:
                soup = HTMLParser(response.text)
                articles = self.get_posts(soup)
                for article in articles:
                    date = article.css_first('div[class="PagePromo-date"] bsp-timestamp').attributes['data-timestamp']
                    if mod.less_than_3_days_old(date):
                        link = article.css_first('a').attributes['href']
                        all_articles.append({
                            'date': date,
                            'link': link,
                        })
        return all_articles
                    

    def engine(self, author_names: list):
        print(f'Ap News')
        posts = self.loop_until_done()
        for post in posts:
            print(post)
            try:
                self.get_data_from_post(post, author_names)
            except BrokenPipeError:
                pass
          
                
    def main(self):
        author_names = []
        for idx, row in self.input_data.publication_table.iterrows():
            if pd.isna(row['Article URL']):
                pass
            else:
                author_names.append(row['Author Name'])
        self.engine(author_names)
        return self.input_data.post_items, self.input_data.fails
                
# if __name__ == '__main__':
#     ap = ApNews()
#     print(ap.main())
    # df = pd.DataFrame(self.input_data.post_items)
    # df.to_excel('forbes_sample.xlsx', index=False)
    # print("Done!")
            