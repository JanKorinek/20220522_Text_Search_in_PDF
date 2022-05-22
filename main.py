import time
import re
import os
import PyPDF2
import pikepdf
import webbrowser

import pandas as pd
import multiprocessing as mp

from PyPDF2.errors import PdfReadError


def repare_pdf(file):
    pdf = file.split('/')
    print("Repairing following PDF: {0}".format(pdf[-1]))
    pdf = pikepdf.Pdf.open(file)
    pdf.save(file + '.tmp')
    pdf.close()
    os.unlink(file)
    os.rename(file + '.tmp', file)


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


def search_pdf(keyword, path):
    # Reader initiation
    f = open(path, 'rb')
    try:
        reader = PyPDF2.PdfFileReader(f)
    except PdfReadError:
        repare_pdf(path)
        f = open(path, 'rb')
        reader = PyPDF2.PdfFileReader(f)

    pdf = path.split('/')
    results = []
    for p in range(reader.numPages):
        print(f'Checking page {p} in [{pdf[-1]}]')
        page = reader.getPage(p)
        try:
            text = page.extractText()
        except:
            continue

        for line in text.splitlines():
            if re.findall(keyword, line, flags=re.IGNORECASE):
                result = {
                    'file': pdf[-1],
                    'page': p,
                    'line': line,
                    'path': f'<a href="' + path + '" target="_blank">open file</a>'
                }
                results.append(result)

    f.close()
    print(f'All of {reader.numPages} pages checked.')

    return results


def run_parallel_pool(keyword, pdfs):
    with mp.Pool(mp.cpu_count()) as pool:
        res = pool.starmap(search_pdf, zip([keyword] * len(pdfs), pdfs))
        pool.close()
    return res


if __name__ == "__main__":
    keyword = 'Terraform'
    # folder = 'pdfs'
    folder = '/media/p51/Data/Data/Library/_Computer_Science/_Projects_Selection/'
    parallel_processing = True

    # Measure time
    t0 = time.time()

    # List all available PDFs in specified folder
    pdfs = [os.path.abspath(os.path.join(root, name))
            for root, dirs, files in os.walk(folder) for name in files if name.endswith('pdf')]

    # Search keywords in PDFs
    if parallel_processing:
        results_flat = [item for sublist in run_parallel_pool(keyword, pdfs) for item in sublist]
    else:
        results_flat = [item for sublist in [search_pdf(keyword, path) for path in pdfs] for item in sublist]

    results_df = pd.DataFrame(results_flat)

    # Generate and save HTML
    html = generate_html(results_df, keyword)
    open("results/search_results.html", "w").write(html)
    webbrowser.open("results/search_results.html")

    # Evaluate time
    t1 = time.time() - t0
    print("Time elapsed (s): ", round(t1, 0))
    print("Time elapsed (min): ", round(t1/60, 1))
    print("Time elapsed (h): ", round(t1/3600, 2))
