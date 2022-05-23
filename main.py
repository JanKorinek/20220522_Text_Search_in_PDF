import time
import re
import os
import PyPDF2
import pikepdf
import webbrowser

import pandas as pd
import multiprocessing as mp

from typing import List, Dict, Any

def repare_pdf(file: str):
    """Repair PDF by loading and saving via pikepdf library.

    :param file: PDF location
    """
    pdf = file.split('/')
    print("Repairing following PDF: {0}".format(pdf[-1]))
    try:
        # Load and save PDF
        pdf = pikepdf.Pdf.open(file)
        pdf.save(file + '.tmp')
        pdf.close()
        os.unlink(file)
        os.rename(file + '.tmp', file)
    except:
        print(f'Cannot repair following PDF {[pdf[-1]]}')


def generate_html(dataframe: pd.DataFrame, *args) -> str:
    """Generate HTML table of the search results with usage of jQuery template
    script.

    :param dataframe: Keyword search results
    :param args: Can pass e.g. keyword variable
    :return: Generated HTML table code
    """
    # Get the table HTML from the dataframe
    table_html = dataframe.to_html(table_id='table', escape=False)

    # Construct the complete HTML with jQuery Data tables
    # Possible to disable paging or enable y scrolling on lines 20 and 21 respectively
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

def check_pdf(path: str,
              keyword: str = 'placeholder',
              ) -> List[str]:
    """Check PDF if it's compatible with PyPDF2 library. If not, then is excluded
    from further processing.

    :param path: PDF location
    :param keyword: Keyword to search (in this case generalized placeholder)
    :return: Returns PDF location if it's not compatible with PyPDF2
    """
    for_removal = []
    pdf = path.split('/')

    try:
        f = open(path, 'rb')
        reader = PyPDF2.PdfFileReader(f)
    except:
        repare_pdf(path)

    try:
        f = open(path, 'rb')
        reader = PyPDF2.PdfFileReader(f)
        pages = reader.numPages
        page = reader.getPage(0)
        text = page.extractText()
        f.close()
        print(f'All Checks Passed for [{pdf[-1]}]')
    except:
        print(f'Checks Failed for [{pdf[-1]}]. PDF marked for removal from the list.')
        for_removal.append(path)

    return for_removal


def search_pdf(path: str,
               keyword: str,
               ) -> List[Dict[str, Any]]:
    """Search specified keyword(s) within PDF.

    :param path: PDF location
    :param keyword: Keyword to search within PDF
    :return: Matched keyword file, page, sentence and file path
    """
    # Reader initiation
    f = open(path, 'rb')
    reader = PyPDF2.PdfFileReader(f)
    pdf = path.split('/')
    print(f'Searching in [{pdf[-1]}]')

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
    print(f'All of {reader.numPages} pages checked in [{pdf[-1]}]')

    return results


def run_parallel_pool(func: str,
                      pdfs: List[str],
                      keyword: str,
                      ) -> List[Any]:
    """Creates pool for function distribution to all available cores.

    :param func: Function for distribution
    :param pdfs: List of PDFs to process
    :param keyword: Keyword to search within PDF
    :return: Processed PDFs
    """
    with mp.Pool(mp.cpu_count()) as pool:
        res = pool.starmap(eval(func), zip(pdfs, [keyword] * len(pdfs)))
        pool.close()

    return res


if __name__ == "__main__":
    keyword = 'cloud'
    folder = 'pdfs'
    # folder = '/media/p51/Data/Data/Library/_Computer_Science/'
    parallel_processing = True

    # Measure time
    t0 = time.time()

    # List all available PDFs in specified folder
    pdfs = [os.path.abspath(os.path.join(root, name))
            for root, dirs, files in os.walk(folder) for name in files if name.endswith('.pdf')]

    if parallel_processing:
        # PDFs checks
        pdfs_to_remove = [item for sublist in run_parallel_pool('check_pdf', pdfs, keyword) for item in sublist]

        # Removal of incompatible PDFs
        pdfs_passed = [pdf for pdf in pdfs if not pdf in pdfs_to_remove or pdfs_to_remove.remove(pdf)]

        # Search keywords in PDFs
        results_flat = [item for sublist in run_parallel_pool('search_pdf', pdfs_passed, keyword) for item in sublist]
    else:
        # PDFs checks
        pdfs_to_remove = [item for sublist in [check_pdf(path, keyword) for path in pdfs] for item in sublist]

        # Removal of incompatible PDFs
        pdfs_passed = [pdf for pdf in pdfs if not pdf in pdfs_to_remove or pdfs_to_remove.remove(pdf)]

        # Search keywords in PDFs
        results_flat = [item for sublist in [search_pdf(keyword, path) for path in pdfs_passed] for item in sublist]

    results_df = pd.DataFrame(results_flat)

    # Generate and save HTML
    html = generate_html(results_df, keyword)
    open(f"{keyword}_search_results.html", "w").write(html)
    print('Report successfully generated into HTML.')

    webbrowser.open(f"{keyword}_search_results.html")

    # Evaluate time
    print(f"\n'{keyword}' Keyword Search in {len(pdfs_passed)} Books Complete!")
    t1 = time.time() - t0
    print("Time elapsed (s): ", round(t1, 0))
    print("Time elapsed (min): ", round(t1/60, 1))
    print("Time elapsed (h): ", round(t1/3600, 2))
