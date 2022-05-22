import PyPDF2
import re
import webbrowser
import pandas as pd

def generate_html(dataframe: pd.DataFrame, *args):
    # get the table HTML from the dataframe
    table_html = dataframe.to_html(table_id='table', escape=False)
    # construct the complete HTML with jQuery Data tables
    # You can disable paging or enable y scrolling on lines 20 and 21 respectively
    html = f"""
    <html>
    <header>
        <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet">
    </header>
    <title>PDF Search Results</title>
    <body>
    <h1><u>PDF Search Results</u></h1>
    <h2>For a keyword: <u>{args}</u> was found <u>{dataframe.shape[0]}</u> results.</h2>
    {table_html}
    <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script>
        $(document).ready( function () {{
            $('#table').DataTable({{
                // paging: true,    
                // scrollY: 400,
            }});
        }});
    </script>
    </body>
    </html>
    """
    return html

def search_pdf(reader, keyword, path):
    pdf = path.split('/')
    results = []
    for p in range(reader.numPages):
        print(f'Checking page {p} in [{pdf[-1]}]')
        page = reader.getPage(p)
        text = page.extractText()

        for line in text.splitlines():
            if re.findall(keyword, line, flags=re.IGNORECASE):
                result = {
                    'file': pdf[-1],
                    'page': p,
                    'line': line,
                    'path': f'<a href="' + path + '" target="_blank">open file</a>'
                }
                results.append(result)

    print(f'All of {reader.numPages} pages checked. Search complete.')

    return results


if __name__ == "__main__":
    path = '/home/p51/PycharmProjects/20220522_Text_Search_in_PDF/pdfs/Artificial Intelligence for Cloud and Edge Computing (2022).pdf'
    keyword = 'recommend'

    # Reader initiation
    f = open(path, 'rb')
    reader = PyPDF2.PdfFileReader(f)

    # Search PDF
    results = search_pdf(reader, keyword, path)
    f.close()

    df = pd.DataFrame(results)

    # Generate and save HTML
    html = generate_html(df, keyword)
    open("results/search_results.html", "w").write(html)
    webbrowser.open("results/search_results.html")
