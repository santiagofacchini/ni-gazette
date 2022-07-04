import os
import ftplib
from unittest import skip
import requests
import urllib.parse
import PyPDF2
import ghostscript


# Download directory
download_directory = '/usr/src/app/downloads/'

# Get DOs in vLex FTP
ftp_connection = ftplib.FTP(
    host=os.environ['AG2_HOST'],
    user=os.environ['AG2_USER'],
    passwd=os.environ['AG2_PASS'],
)
print(ftp_connection.getwelcome())
ftp_files = ftp_connection.nlst('/DO_Nicaragua/procesados/')
ftp_connection.quit()

# URL
seed_url = 'http://digesto.asamblea.gob.ni/consultas/util/ws/proxy.php'

# 2022
payload = {
    'hddQueryType': 'getRdds',
    'txtDatePublishFrom': '2022/1/1',
    'txtDatePublishTo': '2022/12/31'
}

response = requests.post(
    url=seed_url,
    data=payload
)

for rdd in response.json()['rdds']:

    # First element in response JSON is empty
    if rdd['numPublica'] == '':
        source_issues = rdd['totalRegistros']
        print(f'Source issues: {source_issues}')
        print(f'vLex issues: {len(ftp_files)/2}')

    # JSON response data
    rdd_date = rdd['fecPublica']
    rdd_number = rdd['numPublica']
    rdd_rddid = rdd['rddid']

    # vLex name format
    vlex_name = f'{rdd_number}_{rdd_date.replace("/", "")}'

    # If file exists in FTP
    if f'{vlex_name}.pdf' in ftp_files and f'{vlex_name}.csv' in ftp_files:
        try:
            os.remove(f'{download_directory}{vlex_name}.csv')
            os.remove(f'{download_directory}{vlex_name}.pdf')
            print(f'{vlex_name} already in FTP. Skipped.')
        except:
            print(f'{vlex_name} already in FTP. Skipped.')

    # If file is neither in FTP nor in $HOME
    elif f'{vlex_name}.csv' not in ftp_files and not os.path.isfile(f'{download_directory}{vlex_name}.pdf'):
        print(f'Working on {vlex_name}: {rdd_rddid}')

        # GET query params
        query_params = {
            'type': 'rdd',
            'rdd': urllib.parse.quote(rdd_rddid, safe=''), # Escape special characters
        }

        # Bytes response -> PDF content
        pdf_content = requests.get(
            url=f'http://digesto.asamblea.gob.ni/consultas/util/pdf.php',
            data=query_params,
        ).content

        # Create raw PDF file
        with open(f'{download_directory}raw-{vlex_name}.pdf', 'wb') as pdf_file:
            pdf_file.write(pdf_content)

        # Count PDF pages
        read_pdf = PyPDF2.PdfFileReader(f'{download_directory}raw-{vlex_name}.pdf')
        total_pages = read_pdf.numPages

        # Ghostscript -> Create PDF/A file
        args = [
            '-dPDFA=1',
            '-dBATCH',
            '-dNOPAUSE',
            '-sColorConversionStrategy=RGB',
            '-sDEVICE=pdfwrite',
            f'-sOutputFile={download_directory}{vlex_name}.pdf',
            f'{download_directory}raw-{vlex_name}.pdf',
        ]
        ghostscript.Ghostscript(*args)

        # Remove raw PDF file
        os.remove(f'{download_directory}raw-{vlex_name}.pdf')

        # Create CSV file
        with open(f'{download_directory}{vlex_name}.csv', 'w') as csv_file:
            csv_file.write(f'La Gaceta, Diario Oficial Nº {rdd_number} del '
            f'día {rdd_date} (contenido completo)||Contenido completo|'
            f'{rdd_date}|1|{total_pages}'
        )

    else:
        print(f'{vlex_name} already in {download_directory}. Skipped.')
