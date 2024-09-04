from selectolax.parser import HTMLParser
import pandas as pd
import models as mod
import json

class Athletic:
    def __init__(self):
        self.input_data = mod.LoadData(publication='The Athletic')

    def get_posts(self, soup: HTMLParser):
        scripts = soup.css('script[type="application/ld+json"]')
        for script in scripts:
            if '"@context":"http://schema.org","@id"' in script.text():
                break
        json_data = json.loads(script.text())
        links = [x['url'] for x in json_data['mainEntity']['itemListElement']]
        return links

    def get_data_from_post(self, post: str, author_name: str):
        response = mod.send_requests(post)
        if response:
            soup = HTMLParser(response.text)
            json_str = soup.css_first('script[type="application/ld+json"]').text()
            json_data = json.loads(json_str)
            date = json_data['datePublished'].split('T')[0]
            if mod.less_than_3_days_old(date):
                header = json_data['headline']
                paragraph = json_data['description']
                link = post
                img = json_data['image']['url'][0]
                authors = json_data['author']
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
#     athletic = Athletic()
#     print(athletic.main()[0])
    # df = pd.DataFrame(athletic.input_data.post_items)
    # mod.save_to_sql(df, "scraped", 'replace')
    # print("Done!")