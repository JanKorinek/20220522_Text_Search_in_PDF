import time
import re
import os
import PyPDF2
import pikepdf
import webbrowser
import yaml
import logging
import argparse

import pandas as pd
import multiprocessing as mp

from logging.config import dictConfig
from typing import List, Dict, Any


def init_logger(path: str) -> logging.RootLogger:
    """Function responsible for logger creation.

    :param path: Folder where logfile is stored.
    :return: Initialized logger
    """
    # Initialize logger
    with open('logger_conf.yaml') as fin:
        config = yaml.load(fin, Loader=yaml.FullLoader)
        config["handlers"]["file"]["filename"] = config["handlers"]["file"]["filename"].format(path=path)
    dictConfig(config)
    logger = logging.getLogger()

    return logger

def runtime_eval(start: float) -> tuple[Any, Any, Any]:
    """Measure overall runtime of the script.

    :param start: Time when scrip started
    :return: Hours, minutes and seconds floats
    """
    # Evaluate time
    m, s = divmod(time.time() - start, 60)
    h, m = divmod(m, 60)

    return (h, m, round(s,0))

def repare_pdf(file: str):
    """Repair PDF by loading and saving via pikepdf library.

    :param file: PDF location
    """
    pdf = file.split('/')
    logger.info("Repairing following PDF: {0}".format(pdf[-1]))
    try:
        # Load and save PDF
        pdf = pikepdf.Pdf.open(file)
        pdf.save(file + '.tmp')
        pdf.close()
        os.unlink(file)
        os.rename(file + '.tmp', file)
    except:
        logger.info(f'Cannot repair following PDF {[pdf[-1]]}')


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
        logger.info(f'All Checks Passed for [{pdf[-1]}]')
    except:
        for_removal.append(path)
        logger.info(f'Checks Failed for [{pdf[-1]}]. PDF marked for removal from the list.')

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
    logger.info(f'Searching in [{pdf[-1]}]')

    results = []
    for p in range(reader.numPages):
        logger.info(f'Checking page {p} in [{pdf[-1]}]')
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
    logger.info(f'All of {reader.numPages} pages checked in [{pdf[-1]}]')

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

def argparser() -> argparse.ArgumentParser:
    """
    Parsing input arguments for script run.
    :return: Parser object
    """
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--keyword', type=str, default='cloud', help='Keyword or phrase to search within PDFs. e.g')
    parser.add_argument('--folder', type=str, default='/output', help='Target folder to search.')
    parser.add_argument('--xCPU', type=bool, default=True, help='Turn off/on multiprocessing.')

    return parser


if __name__ == "__main__":
    args = argparser().parse_args()

    # Parsing arguments
    keyword = args.keyword
    folder = args.folder
    parallel_processing = args.xCPU

    start = time.time()    # Measure time
    logger = init_logger(folder)  # Loger initialization

    # Logging arguments
    logger.info(f'Keyword is: {keyword}')
    logger.info(f'Folder is: {folder}')
    logger.info(f'xCPU is: {parallel_processing}')

    logger.info('Listing of all available PDFs in specified folder...')
    pdfs = [os.path.abspath(os.path.join(root, name))
            for root, dirs, files in os.walk(folder) for name in files if name.endswith('.pdf')]
    logger.info('Listing of all available PDFs finished successfully!')

    if parallel_processing:
        logger.info('Running PDFs compatibility checks in parallelized manner...')
        pdfs_to_remove = [item for sublist in run_parallel_pool('check_pdf', pdfs, keyword)
                          for item in sublist]
        logger.info('PDFs compatibility checks finished successfully!')

        logger.info('Excluding incompatible PDFs!')
        pdfs_passed = [pdf for pdf in pdfs if not pdf in pdfs_to_remove or pdfs_to_remove.remove(pdf)]

        logger.info('Searching predefined keywords in PDFs in parallelized manner...')
        results_flat = [item for sublist in run_parallel_pool('search_pdf', pdfs_passed, keyword)
                        for item in sublist]
        logger.info('Searching of predefined keywords finished successfully!')
    else:
        logger.info('Running PDFs compatibility checks in serial manner...')
        pdfs_to_remove = [item for sublist in [check_pdf(path, keyword) for path in pdfs]
                          for item in sublist]
        logger.info('PDFs compatibility checks finished successfully!')

        logger.info('Excluding incompatible PDFs!')
        pdfs_passed = [pdf for pdf in pdfs if not pdf in pdfs_to_remove or pdfs_to_remove.remove(pdf)]

        logger.info('Searching predefined keywords in PDFs in serial manner...')
        results_flat = [item for sublist in [search_pdf(keyword, path) for path in pdfs_passed]
                        for item in sublist]
        logger.info('Searching of predefined keywords finished successfully!')

    logger.info('Generating report and saving into HTML...')
    results_df = pd.DataFrame(results_flat)
    html = generate_html(results_df, keyword)
    open(f"/{folder}/{keyword}_search_results.html", "w").write(html)
    logger.info('Report saved and successfully generated into HTML!')

    webbrowser.open(f"/{folder}/{keyword}_search_results.html")   # Opens HTML report automatically in the web browser

    # Runtime evaluation
    logger.info(f"'{keyword}' Keyword Search in {len(pdfs_passed)} Books Complete!")
    runtime = runtime_eval(start)
    logger.info(f"Time Elapsed (h:min:s) - Total processing time:"
                f" %d:%02d:%.1f" % (runtime[0], runtime[1], runtime[2]))
