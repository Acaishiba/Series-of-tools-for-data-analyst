import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pymysql
import os
import datetime

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/your/credentials.json'

# get time
now = datetime.datetime.now()

# str -time
formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")


def sync_mysql_to_sheets(spreadsheet_id, sheet_name, mysql_table):
    # Connect to MySQL and retrieve data from the specified table
    conn = pymysql.connect(
        host="127.0.0.1",
        user="xxxx",
        password="0000000",
        database="pools"
    )
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {mysql_table}")
    data = cursor.fetchall()
    headers = [i[0] for i in cursor.description]

    # Authenticate with Google Sheets and retrieve the sheet's ID
    creds, _ = google.auth.default()
    service = build('sheets', 'v4', credentials=creds)
    sheet_metadata = {'properties': {'title': sheet_name}}
    sheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_id = None
    for s in sheet['sheets']:
        if s['properties']['title'] == sheet_name:
            sheet_id = s['properties']['sheetId']
            break

    if sheet_id is None:
        # The sheet doesn't exist yet, so create it with the specified name and headers
        requests = [{
            'addSheet': {
                'properties': {
                    'title': sheet_name,
                    'gridProperties': {
                        'rowCount': len(data) + 1,
                        'columnCount': len(headers)
                    }
                }
            }
        }]
        body = {'requests': requests}
        response = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
        
        requests = [{
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {
                        'frozenRowCount': 1,
                        'rowCount': len(data) + 1,
                        'columnCount': len(headers)
                    }
                },
                'fields': 'gridProperties(frozenRowCount,rowCount,columnCount)',
            }
        }, {
            'updateCells': {
                'start': {
                    'sheetId': sheet_id,
                    'rowIndex': 0,
                    'columnIndex': 0
                },
                'rows': [{'values': [{'userEnteredValue': {'stringValue': h}} for h in headers]}] +
                         [{'values': [{'userEnteredValue': {'stringValue': str(cell)}} for cell in row]} for row in data],
                'fields': 'userEnteredValue'
            }
        }, {
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': len(headers)
                }
            }
        }]
        body = {'requests': requests}
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    else:
        # The sheet already exists, so update it with the retrieved data
        requests = [{
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {
                        'rowCount': len(data) + 1,
                        'columnCount': len(headers)
                    },
                    'title': sheet_name
                },
                'fields': 'title,gridProperties(rowCount,columnCount)'
            }
        }, {
            'updateCells': {
                'start': {
                    'sheetId': sheet_id,
                    'rowIndex': 0,
                    'columnIndex': 0
                },
                'rows': [{'values': [{'userEnteredValue': {'stringValue': h}} for h in headers]}] +
                         [{'values': [{'userEnteredValue': {'stringValue': str(cell)}} for cell in row]} for row in data],
                'fields': 'userEnteredValue'
            }
        }, {
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': len(headers)
                }
            }
        }]
        body = {'requests': requests}
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    print(f"operation compelet --- {sheet_name}",formatted_time)
    return f"{len(data)} rows synced to {sheet_name} sheet in {spreadsheet_id} spreadsheet."

sync_mysql_to_sheets('1DBJolOlFbbbbbbbbbbbbbbbbbbbbbbbbLOY','Sheet1','Pool_avg')