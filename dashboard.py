import json
import requests
import sys
import base64
from copy import deepcopy

WIDGETS_PER_LINE = 10

x_offset = 155
y_offset = 160

host = ''
port = ''
user = ''
password = ''
account = ''
importacao = 0
token = ''
cookies = ''

def get_auth(host, port, user, password, account):
    url = 'https://{}:{}/controller/auth'.format(host, port)
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(user + "@" + account + ":" + password)  
    }
    params = (
        ('action', 'login'),
    )
    response = requests.get(url, headers=headers, params=params)
    global token
    global cookies
    cookies = response.cookies 
    token = response.cookies.get("X-CSRF-TOKEN")

    return 0

def get_dashboards(host, port, user, password, account):
    url = 'https://{}:{}/controller/restui/dashboards/getAllDashboardsByType/false'.format(host, port)
    params = {'output': 'json'}
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(user + "@" + account + ":" + password),
        'X-CSRF-TOKEN' : token
    }
    r = requests.get(url, params=params, headers=headers, cookies=cookies)
    
    return sorted(r.json(), key=lambda k: k['name'])

def delete_dashboards(host, port, user, password, account, id):
    url = 'https://{}:{}/controller/restui/dashboards/deleteDashboards'.format(host, port)
    data = [ 0, (id) ]
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(user + "@" + account + ":" + password),
        'X-CSRF-TOKEN' : token,
        'Content-Type': 'application/json',
        'Accept' : 'application/json, text/plain, */*'
    }
    #print(str(id))
    #print(data)
    r = requests.post(url, data=[data], headers=headers, cookies=cookies)
    #print(r)
    return 0

def get_applications(host, port, user, password, account):
    url = 'https://{}:{}/controller/rest/applications'.format(host, port)
    auth = ('{}@{}'.format(user, account), password)
    params = {'output': 'json'}

    print('Getting apps', url)
    
    r = requests.get(url, auth=auth, params=params)
    return sorted(r.json(), key=lambda k: k['name'])

def put_dashboard(host, port, user, password, account, dashboard):
    url = 'https://{}:{}/controller/CustomDashboardImportExportServlet'.format(host, port)
    auth = ('{}@{}'.format(user, account), password)
    files = {
        'file': (dashboard, open(dashboard, 'rb')),
    }
    print('import dashboard apps', dashboard)
    response = requests.post(url, files=files, auth=auth)
    print (response)

    return 0

def find_dashboard(dashboards, name):
    id = 0
    for i in dashboards:
        if i['name'] == name:
            id = i['id']
            break
    return id

def process(dash):
    get_auth(host, port, user, password, account)
    dashboards = get_dashboards(host, port, user, password, account)

    APPS = get_applications(host, port, user, password, account)
    for application in APPS:
        id = find_dashboard(dashboards, application['name'])
        if id != 0:
            delete_dashboards(host, port, user, password, account, id)
        new_dash = dash
        new_dash['name'] = application['name']
        print('Creating metrics for', application['name'])

        for widget in new_dash['widgetTemplates']:

            if widget['widgetType'] == 'GraphWidget':
                #print('Creating metrics for GraphWidget')
                if widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['entityMatchCriteria']['matchCriteriaType'] != "AllEntities":
                    widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['entityMatchCriteria']['entityNames'][0]['applicationName'] = application['name']
                    widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['entityMatchCriteria']['entityNames'][0]['entityName'] = application['name']
                widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['applicationName'] = application['name']

            if widget['widgetType'] == 'HealthListWidget':
                #print('Creating metrics for HealthListWidget')
                widget['applicationReference']['applicationName'] = application['name']
                widget['applicationReference']['entityName'] = application['name']
                widget['entityReferences'][0]['applicationName'] = application['name']
                widget['entityReferences'][1]['applicationName'] = application['name']
                widget['entityReferences'][2]['applicationName'] = application['name']
                widget['entityReferences'][3]['applicationName'] = application['name']
                widget['entityReferences'][4]['applicationName'] = application['name']
                widget['entityReferences'][5]['applicationName'] = application['name']
                widget['entityReferences'][6]['applicationName'] = application['name']

            if widget['widgetType'] == 'EventListWidget':
                #print('Creating metrics for EventListWidget')
                widget['eventFilterTemplate']['applicationName'] = application['name']

            if widget['widgetType'] == 'MetricLabelWidget':
                #print('Creating metrics for MetricLabelWidget')
                widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['entityMatchCriteria']['entityNames'][0]['applicationName'] = application['name'] 
                widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['entityMatchCriteria']['entityNames'][0]['entityName'] = application['name']
                widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate']['applicationName'] = application['name']

        with open('new_dash_{}.json'.format(application['name']), 'w') as outfile:
            json.dump(new_dash, outfile, indent=4, sort_keys=True)

        print("Importacao", importacao)
        if importacao == '1':
            print("Importacao do Dashboard", 'new_dash_{}.json'.format(application['name']))
            put_dashboard(host, port, user, password, account, 'new_dash_{}.json'.format(application['name']))
           
def main():
    global host
    global port
    global user
    global password
    global account
    global importacao

    try:
        host = sys.argv[1] 
        port = sys.argv[2]
        user = sys.argv[3]
        password = sys.argv[4]
        account = sys.argv[5]
    
        if len(sys.argv) == 7 :
            importacao = sys.argv[6]

        with open('dashboard.json') as json_data:
            d = json.load(json_data)
            process(d)

    except:
        print 'dashboard.py <host> <port> <user> <password> <account>'
        sys.exit(2)

if __name__ == '__main__':
    main()
