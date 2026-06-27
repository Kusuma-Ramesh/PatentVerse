from googlesearch import search


class PatentAgent:

    def search_patents(self, idea):

        query = f"{idea} patent"

        results = []

        try:
            for url in search(query, num_results=5):
                results.append(url)

        except:
            results.append("No patent information found.")

        return results