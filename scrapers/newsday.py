
from selectolax.parser import HTMLParser
import pandas as pd
import models as mod
import json
from algoliasearch.search.client import SearchClient

class NewsDay:
    def __init__(self):
        self.input_data = mod.LoadData(publication='Newsday')
        
    def get_results(self, url):
        results = None
        try:
            query = url.split('/')[-1].replace('%20', ' ')
            client = SearchClient.create("IZXD45EXH7", "1380221e0fdaf65262fc627c43ab1069")
            job_client = client.init_index('prod_ace')
            search_params = {
                "page": 0,
                "hitsPerPage": 20,
                "removeStopWords": ["en"],
                "query": [query]
            }
            results = job_client.search('', search_params)
        except Exception as e:
            pass
        return results

    def get_posts(self, results):
        articles = results['hits']
        return articles[1:]

    def get_data_from_post(self, post, author_name: str):
        date = post['publishedDate']
        try:
            date = date.split('T')[0]
            if mod.less_than_3_days_old(date):
                header = post['headline']
                paragraph = post['lead']
                img = post['topElement']['baseUrl']
                authors = post['authors']
                link = post['url']
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
        except:
            pass
        
    def engine(self, author_url: str, author_name: str):
        results = self.get_results(author_url)
        if results:
            posts = self.get_posts(results)
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
#     nd = NewsDay()
#     print(nd.main())
#     # df = pd.DataFrame(self.input_data.post_items)
#     # df.to_excel('forbes_sample.xlsx', index=False)
#     # print("Done!")