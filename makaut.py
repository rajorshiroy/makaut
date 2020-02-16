import os
import json

try:
    import requests
    from bs4 import BeautifulSoup
    from tabulate import tabulate
except ModuleNotFoundError:
    # install the third party modules
    os.system('pip install bs4 requests tabulate')

    # re import the installed modules
    import requests
    from bs4 import BeautifulSoup
    from tabulate import tabulate


class Makaut:
    def __init__(self):
        self.user = None
        self.login_status = False
        self.session = requests.session()
        self.marks_table = None
        self.save_user_details = False
        self.cookies = None

    def get_user_details(self):
        if os.path.exists('config/user.json'):
            if input('use saved credentials? (y/n): ').lower() == 'y':
                with open('config/user.json') as f:
                    self.user = json.loads(f.read())
                return
        else:
            self.user = {
                'username': input('username: '),
                'password': input('password: ')
            }
            if input('save username and password? (y/n): ').lower() == 'y':
                self.save_user_details = True

    def login(self):
        print('logging in...')

        # get username and password
        self.get_user_details()

        # set session headers
        self.session.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
            'Referer': 'https://makaut1.ucanapply.com/smartexam/public/student',
        }

        response = self.session.get('https://makaut1.ucanapply.com/smartexam/public/get-login-form?typ=5')

        # get the token from received response
        soup = BeautifulSoup(response.json()['html'], 'html.parser')
        token = soup.find('input', {'name': '_token'})['value']

        data = {
            '_token': token,
            'typ': '5',
            'username': self.user['username'],
            'password': self.user['password']
        }

        # post the final request for login with required data
        response = self.session.post('https://makaut1.ucanapply.com/smartexam/public/checkLogin', data=data)

        # check if login was successful
        if response.json()['status']:
            self.login_status = True
            print('logged in!')

            # save login details if specified
            if self.save_user_details:
                with open('config/user.json', 'w') as f:
                    f.write(json.dumps(self.user, indent=2))

            # save cookies
            with open('config/cookies.json', 'w') as f:
                f.write(json.dumps(dict(self.session.cookies), indent=2))
        else:
            print('login failed!')

    def get_marks(self):
        if self.cookies:
            response = self.session.get('https://makaut1.ucanapply.com/smartexam/public/student/student-marks-display',
                                        cookies=self.cookies)
        else:
            response = self.session.get('https://makaut1.ucanapply.com/smartexam/public/student/student-marks-display')

        with open('marks.html', 'w') as f:
            f.write(response.text)

        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')
        table_rows = table.find_all('tr', recursive=False)
        self.marks_table = {
            'title': table_rows[0].text.strip(),
            'headers': [td.text.strip() for td in table_rows[1].find_all('td')],
            'marks': [[td.text.strip() for td in tr.find_all('td')] for tr in table_rows[2:]],
        }

    def display_marks(self):
        if not self.marks_table:
            self.get_marks()
        print(tabulate(self.marks_table['marks'], headers=self.marks_table['headers'], tablefmt='github'))


if __name__ == '__main__':
    # create the config folder
    os.makedirs('config', exist_ok=True)

    makaut = Makaut()
    makaut.login()
    makaut.display_marks()
