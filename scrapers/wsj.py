from selectolax.parser import HTMLParser
import pandas as pd
import models as mod
import re
import wsjHelper as hep

lindsey_link = "https://www.wsj.com/news/author/lindsey-adler?id=%7B%22count%22%3A10%2C%22query%22%3A%7B%22and%22%3A%5B%7B%22term%22%3A%7B%22key%22%3A%22AuthorId%22%2C%22value%22%3A%229460%22%7D%7D%2C%7B%22terms%22%3A%7B%22key%22%3A%22Product%22%2C%22value%22%3A%5B%22WSJ.com%22%2C%22Interactive%20Media%22%2C%22WSJPRO%22%2C%22WSJ%20Video%22%5D%7D%7D%5D%7D%2C%22sort%22%3A%5B%7B%22key%22%3A%22LiveDate%22%2C%22order%22%3A%22desc%22%7D%5D%7D%2Fpage%3D0&type=allesseh_content_full"
jared_link = "https://www.wsj.com/news/author/jared-diamond?id=%7B%22count%22%3A10%2C%22query%22%3A%7B%22and%22%3A%5B%7B%22term%22%3A%7B%22key%22%3A%22AuthorId%22%2C%22value%22%3A%227272%22%7D%7D%2C%7B%22terms%22%3A%7B%22key%22%3A%22Product%22%2C%22value%22%3A%5B%22WSJ.com%22%2C%22Interactive%20Media%22%2C%22WSJPRO%22%2C%22WSJ%20Video%22%5D%7D%7D%5D%7D%2C%22sort%22%3A%5B%7B%22key%22%3A%22LiveDate%22%2C%22order%22%3A%22desc%22%7D%5D%7D%2Fpage%3D0&type=allesseh_content_full"

class WSJ:
    def __init__(self):
        self.input_data = mod.LoadData(publication='Wall Street Journal')

    def get_posts(self, response):
        articles = response.json()['collection']
        print(f'Total articles: {len(articles)}')
        return articles

    def get_data_from_post(self, post, author_name: str, author_url: str):
        post_id = post['id']
        link = header = paragraph = ''
        date, authors, img = '5 months ago', [1], 'https://tinyurl.com/5yxk5cua'
        response = mod.send_requests(f'{author_url}?id={post_id}&type=article%7Ccapi', hep.headers, hep.cookies)
        if response:
            json_data = response.json()
            date = json_data['data']['timestamp']
            if mod.less_than_3_days_old(date):
                header = json_data['data']['headline']
                paragraph = json_data['data']['summary']
                link = json_data['data']['url']
                img = json_data['data']['image']['M']['url']
                authors = json_data['data']['byline']
                authors = re.split(r'\s+and\s+', authors)
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
                except Exception as e:
                    print(e)
                    self.input_data.fails.append({"failed": post['link']})
            else:
                self.input_data.to_continue = False
        
    def engine(self, author_url: str, author_name: str):
        if author_name == "Lindsey Adler":
            a_url = lindsey_link
        elif author_name == "Jared Diamond":
            a_url = jared_link
        print(a_url)
        response = mod.send_requests(a_url, headers=hep.headers, cookies=hep.cookies)
        posts = self.get_posts(response)
        for post in posts:
            if self.input_data.to_continue:
                self.get_data_from_post(post, author_name, author_url)
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
#     wsj = WSJ()
#     print(wsj.main())
#     # df = pd.DataFrame(self.input_data.post_items)
#     # df.to_excel('forbes_sample.xlsx', index=False)
#     # print("Done!")