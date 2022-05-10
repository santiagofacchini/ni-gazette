import re
import os
import ftplib
import requests
import bs4
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

# Get URL
seed_url = 'http://digesto.asamblea.gob.ni/?project=la-gaceta-diario-oficial-2021'
response = requests.get(seed_url)
print(seed_url, response)

# Parse response
soup_object = bs4.BeautifulSoup(response.content, 'html.parser')
issue_pattern = re.compile(r'La Gaceta, Diario Oficial N°. (\d+) del (\d+)/(\d+)/(\d+)')
issues = soup_object.find_all('a', text=issue_pattern)
print(f'Issues in FTP: {len(issues)}')

for issue in issues:

    # Construct file name
    mo = re.search(issue_pattern, issue.text.strip())
    file_name = f'{mo.group(1).zfill(2)}_{mo.group(2)}{mo.group(3)}{mo.group(4)}'

    # If file exists in FTP
    if f'{file_name}.pdf' in ftp_files and f'{file_name}.csv' in ftp_files:
        try:
            os.remove(f'{download_directory}{file_name}.csv')
            os.remove(f'{download_directory}{file_name}.pdf')
            print(f'{file_name} already in FTP. Skipped.')
        except:
            print(f'{file_name} already in FTP. Skipped.')

    # If file is neither in FTP nor in $HOME
    elif f'{file_name}.csv' not in ftp_files and not os.path.isfile(f'{download_directory}{file_name}.pdf'):
        print(f'Working on {file_name}: {issue["href"]}')

        pdf_content = requests.get(issue['href']).content

        # Create PDF file
        with open(f'{download_directory}raw-{file_name}.pdf', 'wb') as pdf_file:
            pdf_file.write(pdf_content)

        # Count PDF pages
        read_pdf = PyPDF2.PdfFileReader(f'{download_directory}raw-{file_name}.pdf')
        total_pages = read_pdf.numPages

        # Ghostscript
        args = [
            '-dPDFA=1',
            '-dBATCH',
            '-dNOPAUSE',
            '-sColorConversionStrategy=RGB',
            '-sDEVICE=pdfwrite',
            f'-sOutputFile={download_directory}{file_name}.pdf',
            f'{download_directory}raw-{file_name}.pdf',
        ]
        ghostscript.Ghostscript(*args)
        os.remove(f'{download_directory}raw-{file_name}.pdf')

        # Create CSV file
        with open(f'{download_directory}{file_name}.csv', 'w') as csv_file:
            csv_file.write(f'La Gaceta, Diario Oficial Nº {mo.group(1)} del '
                f'día {mo.group(2)}/{mo.group(3)}/{mo.group(4)} (contenido '
                f'completo)||Contenido completo|{mo.group(2)}/{mo.group(3)}/'
                f'{mo.group(4)}|1|{total_pages}')

    else:
        print(f'{file_name} already in {download_directory}. Skipped.')
