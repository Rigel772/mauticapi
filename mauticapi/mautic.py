from rauth import OAuth1Service
import json

class MauticApi(object):
    def __init__(self, host, key, secret, *args, **kwargs):
        """
        Initialize the MauticApi
        Inputs:
         host = with the host name without the last '/' e.g. 'https://www.mauticinstance.com'
         key = Mautic public key
         secret = Mautic secret key

        Optional Inputs in kwargs:
         access_token = Your access token from Mautic
         access_token_secret = Your access token secret from Mautic

        If you don't yet have your access token and access token secret, from the python shell:
         1) Initialize MauticApi (m = MauticApi(host, key, secret))
         2) Call request_and_authorize, and go to the returned URL in your browser (m.request_and_authorize())
         3) Approve the application
         4) Call get_access_token passing the oauth_verifier parameter (m.get_access_token(verifier))
         5) Get the access token from access_token (m.access_token)
         6) Get the access token secret from access_token_secret (m.access_token_secret)
        """
        self.host = host
        self.base_url = self.host + "/api/"
        self.mautic = OAuth1Service(
            name='mautic',
            consumer_key=key,
            consumer_secret=secret,
            request_token_url=self.host + "/oauth/v1/request_token",
            access_token_url=self.host + "/oauth/v1/access_token",
            authorize_url=self.host + "/oauth/v1/authorize",
            base_url=self.base_url)

        if "access_token" in kwargs:
            self.access_token = kwargs.pop("access_token")
            if "access_token_secret" in kwargs:
                self.access_token_secret = kwargs.pop("access_token_secret")
            else:
                raise InvalidToken("Token Secret is missing.")
            self.get_session()

    def request_and_authorize(self):
        """
        Get a valid authorization URL for Mautic.  Use this in your browser.
        """
        self.request_token, self.request_token_secret = self.mautic.get_request_token()
 
        authorize_url = self.mautic.get_authorize_url(self.request_token)
 
        print('Visit this URL in your browser: {url}'.format(url=authorize_url))

    def get_access_token(self, verifier):
        self.access_token, self.access_token_secret = self.mautic.get_access_token(self.request_token,
                                   self.request_token_secret,
                                   method='POST',
                                   data={'oauth_verifier': verifier})

    def get_session(self):
        self.session = self.mautic.get_session((self.access_token, self.access_token_secret))

    def get_contact_id(self, sargs):
        """
        sargs:
            Query Parameters:
            search:  String or search command to filter entities by.
            start:   Starting row for the entities returned. Defaults to 0.
            limit:   Limit number of entities to return. Defaults to the system configuration for pagination (30).
            orderBy: Column to sort by. Can use any column listed in the response.
            orderByDir:  Sort direction: asc or desc.
            publishedOnly:   Only return currently published entities.
            minimal: Return only array of entities without additional lists in it.

        rauth examples: https://github.com/litl/rauth/blob/master/tests/test_session.py

        Search arguments (sargs):
            Search Operators:
            + (plus sign) - Search for the exact string (i.e. if admin, then administrator will not match)
            ! (exclamation mark) - Not equals string
            " " (double quotes) - Search by phrase
            ( ) (parentheses) - Group expressions together.
            OR - By default the expressions will be joined as AND statements. Use the OR operator to change that.

            Search commands:
            is:anonymous
            is:unowned
            is:mine
            email:*
            segment:{segment_alias}
            name:*
            company:*
            owner:*
            ip:*
            common:{segment_alias} + {segment_alias} + ...

        Example: sargs='search=email:vinicius@simbio.com.br OR company:simbio&limit=50'

        Limitations: filter doesn't work on emails with '+' character.
        """
        self.endpoint = "contacts"
        response = self.session.request('GET', self.base_url + self.endpoint, params=sargs)
        if response.status_code == 200:
            contacts = response.json()
            if contacts['total'] != '0':
                return contacts['contacts'][0]['id']
            else:
                return False
        else:
            return False

    def create_contact(self, **kwargs):
        self.endpoint = "contacts/new"
        status_code, contact = self.post(**kwargs)
        if status_code in [200, 201]:
            return True
        else:
            raise InvalidResponseCode("Mautic: Contact not created.  Status Code: {0}".format(status_code))

    def update_contact(self, cid, **kwargs):
        self.endpoint = "contacts/{0}/edit".format(cid)
        response = self.session.patch(self.base_url + self.endpoint, data=json.dumps(kwargs), headers={"Content-Type": "application/json"})
        if response.status_code in [200, 201]:
            return True
        else:
            raise InvalidResponseCode("Mautic: Error updating contact.  Status Code: {0}".format(status_code))

    def add_contact_to_campaign(self, campaign_id, contact_id):
        self.endpoint = "campaigns/{0}/contact/add/{1}".format(campaign_id, contact_id)
        status_code, response = self.post(**{})
        
    def post(self, **kwargs):
        resp = self.session.post(self.base_url + self.endpoint, data=json.dumps(kwargs), headers={"Content-Type": "application/json"})
        return resp.status_code, resp.json()


class BadHost(Exception):
    pass

class InvalidResponseCode(Exception):
    pass
