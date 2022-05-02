import re
import os
import ftplib
from dotenv import load_dotenv
import requests
import bs4
import PyPDF2


# Load environment variables from .env file (must be in ~)
load_dotenv(f'{os.environ["HOME"]}/.env')

# Download directory
download_directory = os.environ['HOME']

# Get DOs in vLex FTP
ftp_connection = ftplib.FTP(
    host=os.environ['AG2_HOST'],
    user=os.environ['AG2_USER'],
    passwd=os.environ['AG2_PASS'],
)
print(ftp_connection.getwelcome())
ftp_directory = '/DO_Nicaragua/procesados/'
ftp_connection.cwd(ftp_directory)
ftp_files = ftp_connection.nlst()
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
    if f'{file_name}.csv' in ftp_files:
        print(f'{file_name} already in FTP. Skipped.')

    # If file is not in FTP
    elif f'{file_name}.csv' not in ftp_files:
        print(f'Working on {file_name}: {issue["href"]}')

        try:
            pdf_content = requests.get(issue['href']).content

            # Create PDF file
            with open(f'{download_directory}/{file_name}.pdf', 'wb') as pdf_file:
                pdf_file.write(pdf_content)

            # Count PDF pages
            read_pdf = PyPDF2.PdfFileReader(f'{download_directory}/{file_name}.pdf')
            total_pages = read_pdf.numPages

            # Create CSV file
            with open(f'{download_directory}/{file_name}.csv', 'w') as csv_file:
                csv_file.write(f'La Gaceta, Diario Oficial Nº {mo.group(1)} del '
                    f'día {mo.group(2)}/{mo.group(3)}/{mo.group(4)} (contenido '
                    f'completo)||Contenido completo|{mo.group(2)}/{mo.group(3)}/'
                    f'{mo.group(4)}|1|{total_pages}')
        
        except PyPDF2.utils.PdfReadError as error:
            os.remove(f'{download_directory}/{file_name}.pdf')
            with open(f'{download_directory}/{file_name}_error.csv', 'w') as csv_file:
                csv_file.write(f'Link: {issue["href"]}\nError: {error}')
    
    else:
        print(f'An error occurred while processing {file_name}')
